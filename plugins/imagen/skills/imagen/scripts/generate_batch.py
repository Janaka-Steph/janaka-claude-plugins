#!/usr/bin/env python3
"""
generate_batch - Generate multiple images in parallel.

Uses concurrent.futures to run multiple Gemini API requests simultaneously.

Usage:
    # Generate from a JSON file with jobs
    python generate_batch.py jobs.json

    # Generate from command line arguments (prompt:output pairs)
    python generate_batch.py --preset damemano "prompt1" out1.jpg "prompt2" out2.jpg

    # Set max parallel workers (default: 4)
    python generate_batch.py --workers 6 jobs.json

JSON format:
    {
        "preset": "mobile-ui,damemano",
        "jobs": [
            {"prompt": "home screen", "output": "home.jpg"},
            {"prompt": "profile screen", "output": "profile.jpg", "input": "reference.jpg"},
            {"prompt": "settings screen", "output": "settings.jpg"}
        ]
    }

Environment variables:
    GEMINI_API_KEY (required) - Your Google Gemini API key
    IMAGE_SIZE (optional) - Image size: "512", "1K" (default), or "2K"
"""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add parent directory to path for importing generate_image
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from generate_image import (
    get_api_key,
    validate_image_size,
    create_output_dir,
    build_request_body,
    make_api_request,
    extract_image_data,
    save_image,
    get_file_size,
    load_input_image,
    apply_unique_naming,
    DEFAULT_MODEL_ID,
    DEFAULT_IMAGE_SIZE,
)
from generate_with_preset import (
    load_presets,
    build_prompt_with_presets,
)


def generate_single(
    job: dict,
    preset_content: str,
    api_key: str,
    model_id: str,
    image_size: str,
) -> dict:
    """Generate a single image. Returns result dict with status and details."""
    prompt = job["prompt"]
    output_path = Path(job["output"])
    input_paths = job.get("input", job.get("inputs", []))

    # Normalize input_paths to list
    if isinstance(input_paths, str):
        input_paths = [input_paths]

    result = {
        "prompt": prompt,
        "output": str(output_path),
        "status": "pending",
    }

    start_time = time.time()

    try:
        # Load input images if provided
        input_images = None
        if input_paths:
            input_images = []
            for input_path_str in input_paths:
                input_path = Path(input_path_str)
                input_images.append(load_input_image(input_path))

        # Build full prompt with presets
        full_prompt = build_prompt_with_presets(preset_content, prompt)

        # Create output directory
        create_output_dir(output_path)

        # Build and send request
        request_body = build_request_body(full_prompt, image_size, input_images)
        response = make_api_request(api_key, model_id, request_body)

        # Extract and save image
        image_data = extract_image_data(response)
        if not image_data:
            result["status"] = "error"
            result["error"] = "No image data received from API"
            return result

        # Save image
        final_path = save_image(image_data, output_path)

        elapsed = time.time() - start_time
        result["status"] = "success"
        result["final_path"] = str(final_path)
        result["size"] = get_file_size(final_path)
        result["elapsed"] = f"{elapsed:.1f}s"

    except Exception as e:
        elapsed = time.time() - start_time
        result["status"] = "error"
        result["error"] = str(e)
        result["elapsed"] = f"{elapsed:.1f}s"

    return result


def run_batch(
    jobs: list[dict],
    preset: str | None,
    max_workers: int,
    api_key: str,
    model_id: str,
    image_size: str,
) -> list[dict]:
    """Run multiple generation jobs in parallel. Returns list of results."""

    # Load presets once
    preset_content = ""
    if preset:
        preset_content = load_presets(preset)

    results = []
    total = len(jobs)

    print(f"Starting batch generation: {total} images, {max_workers} parallel workers")
    if preset:
        print(f"Preset: {preset}")
    print(f"Model: {model_id}, Size: {image_size}")
    print()

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all jobs
        future_to_job = {
            executor.submit(
                generate_single,
                job,
                preset_content,
                api_key,
                model_id,
                image_size,
            ): job
            for job in jobs
        }

        # Process completed jobs as they finish
        completed = 0
        for future in as_completed(future_to_job):
            completed += 1
            result = future.result()
            results.append(result)

            # Print progress
            status_icon = "✓" if result["status"] == "success" else "✗"
            elapsed = result.get("elapsed", "")
            if result["status"] == "success":
                print(f"[{completed}/{total}] {status_icon} {result['final_path']} ({result['size']}, {elapsed})")
            else:
                print(f"[{completed}/{total}] {status_icon} {result['output']} - ERROR: {result.get('error', 'Unknown')}")

    total_elapsed = time.time() - start_time

    # Summary
    print()
    successful = sum(1 for r in results if r["status"] == "success")
    failed = total - successful
    print(f"Batch complete: {successful} succeeded, {failed} failed, {total_elapsed:.1f}s total")

    return results


def parse_cli_jobs(args: list[str]) -> list[dict]:
    """Parse command line arguments as prompt/output pairs."""
    jobs = []
    i = 0
    while i < len(args):
        if i + 1 >= len(args):
            print(f"Error: Missing output path for prompt: {args[i]}", file=sys.stderr)
            sys.exit(1)
        jobs.append({
            "prompt": args[i],
            "output": args[i + 1],
        })
        i += 2
    return jobs


def main():
    parser = argparse.ArgumentParser(
        description="Generate multiple images in parallel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From JSON file
  python generate_batch.py jobs.json

  # From command line (prompt output pairs)
  python generate_batch.py --preset damemano "home screen" home.jpg "profile" profile.jpg

  # With more workers
  python generate_batch.py --workers 8 jobs.json

JSON format:
  {
    "preset": "mobile-ui,damemano",
    "jobs": [
      {"prompt": "screen 1", "output": "out1.jpg"},
      {"prompt": "screen 2", "output": "out2.jpg", "input": "ref.jpg"}
    ]
  }
        """
    )

    parser.add_argument("input", nargs="*",
                        help="JSON file path, or prompt/output pairs")
    parser.add_argument("--preset", "-p",
                        help="Preset name(s), comma-separated")
    parser.add_argument("--workers", "-w", type=int, default=4,
                        help="Max parallel workers (default: 4)")
    parser.add_argument("--size", choices=["512", "1K", "2K"],
                        help="Image size (overrides IMAGE_SIZE env var)")
    parser.add_argument("--model", "-m",
                        help=f"Gemini model ID (default: {DEFAULT_MODEL_ID})")

    args = parser.parse_args()

    if not args.input:
        parser.print_help()
        sys.exit(1)

    # Get configuration
    api_key = get_api_key()
    model_id = args.model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL_ID)
    image_size = args.size or os.environ.get("IMAGE_SIZE", DEFAULT_IMAGE_SIZE)
    image_size = validate_image_size(image_size)

    # Determine if input is JSON file or CLI pairs
    jobs = []
    preset = args.preset

    if len(args.input) == 1 and args.input[0].endswith(".json"):
        # Load from JSON file
        json_path = Path(args.input[0])
        if not json_path.exists():
            print(f"Error: JSON file not found: {json_path}", file=sys.stderr)
            sys.exit(1)

        with open(json_path) as f:
            data = json.load(f)

        jobs = data.get("jobs", [])
        # JSON preset is used if --preset not specified
        if not preset:
            preset = data.get("preset")
    else:
        # Parse CLI prompt/output pairs
        jobs = parse_cli_jobs(args.input)

    if not jobs:
        print("Error: No jobs to process", file=sys.stderr)
        sys.exit(1)

    # Run batch
    results = run_batch(
        jobs=jobs,
        preset=preset,
        max_workers=args.workers,
        api_key=api_key,
        model_id=model_id,
        image_size=image_size,
    )

    # Exit with error code if any failed
    if any(r["status"] != "success" for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
