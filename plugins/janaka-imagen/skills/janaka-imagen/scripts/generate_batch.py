#!/usr/bin/env python3
"""
generate_batch - Generate multiple images in parallel.

Uses concurrent.futures to run multiple Gemini API requests simultaneously.

Usage:
    # Generate from a JSON file with jobs (RECOMMENDED for complex jobs)
    python generate_batch.py jobs.json

    # Generate from command line arguments (simple jobs only)
    python generate_batch.py --preset <project_preset> "prompt1" --output out1.jpg "prompt2" --output out2.jpg

    # CLI with input images (limited support)
    python generate_batch.py "screen with logo" --output screen1.jpg --input logo.png "screen with mascot" --output screen2.jpg --input mascot.webp

    # Set max parallel workers (default: 4)
    python generate_batch.py --workers 6 jobs.json

JSON format (RECOMMENDED - supports multiple inputs per job):
    {
        "preset": "mobile-ui,<project_preset>",
        "jobs": [
            {"prompt": "home screen", "output": "home.jpg"},
            {"prompt": "profile screen", "output": "profile.jpg", "input": "reference.jpg"},
            {"prompt": "settings screen", "output": "settings.jpg", "inputs": ["logo.png", "mascot.webp"]}
        ]
    }

CLI format (simple jobs only - limited input support):
    python generate_batch.py "prompt1" --output out1.jpg "prompt2" --output out2.jpg

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
    """Parse command line arguments as prompt/output pairs with optional inputs."""
    jobs = []
    i = 0
    current_job = None
    
    while i < len(args):
        arg = args[i]
        
        if arg == "--input" or arg == "-i":
            # Add input to current job
            if not current_job:
                print("Error: --input must come after a prompt", file=sys.stderr)
                sys.exit(1)
            if i + 1 >= len(args):
                print("Error: Missing input path after --input", file=sys.stderr)
                sys.exit(1)
            
            input_path = args[i + 1]
            if "inputs" not in current_job:
                current_job["inputs"] = []
            current_job["inputs"].append(input_path)
            i += 2
        elif arg == "--output" or arg == "-o":
            # Set output path for current job
            if not current_job:
                print("Error: --output must come after a prompt", file=sys.stderr)
                sys.exit(1)
            if i + 1 >= len(args):
                print("Error: Missing output path after --output", file=sys.stderr)
                sys.exit(1)
            current_job["output"] = args[i + 1]
            i += 2
        else:
            # New prompt - save previous job if exists
            if current_job:
                jobs.append(current_job)
            
            # Start new job with prompt
            current_job = {"prompt": arg}
            i += 1
    
    # Add last job
    if current_job:
        jobs.append(current_job)
    
    # Validate jobs have outputs
    for job in jobs:
        if "output" not in job:
            print(f"Error: Missing output for prompt: {job['prompt']}", file=sys.stderr)
            sys.exit(1)
    
    return jobs


def main():
    # Custom parsing to handle --output and --input flags
    preset = None
    workers = 4
    size = None
    model = None
    cli_args = []
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == "--preset" or arg == "-p":
            if i + 1 >= len(sys.argv):
                print("Error: Missing preset name", file=sys.stderr)
                sys.exit(1)
            preset = sys.argv[i + 1]
            i += 2
        elif arg == "--workers" or arg == "-w":
            if i + 1 >= len(sys.argv):
                print("Error: Missing workers count", file=sys.stderr)
                sys.exit(1)
            try:
                workers = int(sys.argv[i + 1])
            except ValueError:
                print("Error: Workers must be a number", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif arg == "--size":
            if i + 1 >= len(sys.argv):
                print("Error: Missing size", file=sys.stderr)
                sys.exit(1)
            size = sys.argv[i + 1]
            i += 2
        elif arg == "--model" or arg == "-m":
            if i + 1 >= len(sys.argv):
                print("Error: Missing model ID", file=sys.stderr)
                sys.exit(1)
            model = sys.argv[i + 1]
            i += 2
        elif arg.startswith("--"):
            # Pass through to CLI parser (like --output, --input)
            cli_args.append(arg)
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
                cli_args.append(sys.argv[i + 1])
                i += 2
            else:
                i += 1
        else:
            cli_args.append(arg)
            i += 1
    
    if not cli_args:
        print("Generate multiple images in parallel\n")
        print("Usage:")
        print("  python generate_batch.py jobs.json")
        print("  python generate_batch.py \"prompt1\" --output out1.jpg \"prompt2\" --output out2.jpg")
        print("\nOptions:")
        print("  --preset PRESET    Preset name(s), comma-separated")
        print("  --workers N       Max parallel workers (default: 4)")
        print("  --size SIZE       Image size: 512, 1K, 2K")
        print("  --model MODEL     Gemini model ID")
        print("\nExamples:")
        print("  # JSON (RECOMMENDED)")
        print("  python generate_batch.py jobs.json")
        print("\n  # CLI with inputs")
        print("  python generate_batch.py \"screen with logo\" --output screen1.jpg --input logo.png")
        sys.exit(1)

    # Get configuration
    api_key = get_api_key()
    model_id = model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL_ID)
    image_size = size or os.environ.get("IMAGE_SIZE", DEFAULT_IMAGE_SIZE)
    image_size = validate_image_size(image_size)

    # Determine if input is JSON file or CLI pairs
    jobs = []

    if len(cli_args) == 1 and cli_args[0].endswith(".json"):
        # Load from JSON file
        json_path = Path(cli_args[0])
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
        jobs = parse_cli_jobs(cli_args)

    if not jobs:
        print("Error: No jobs to process", file=sys.stderr)
        sys.exit(1)

    # Run batch
    results = run_batch(
        jobs=jobs,
        preset=preset,
        max_workers=workers,
        api_key=api_key,
        model_id=model_id,
        image_size=image_size,
    )

    # Exit with error code if any failed
    if any(r["status"] != "success" for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
