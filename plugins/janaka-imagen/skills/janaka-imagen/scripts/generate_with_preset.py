#!/usr/bin/env python3
"""
imagen with presets - Generate images with reusable prompt templates.

Supports both text-to-image and image-to-image generation.
Optional background removal with rembg or luminosity-based method.

Presets are text files containing instructions that get prepended to your prompt.
The tool searches for presets in this order:
1. ./code/docs/presets/, ./docs/presets/, ./design/presets/, or ./presets/ (current working directory)
2. IMAGEN_PRESETS_DIR environment variable
3. Built-in presets (imagen/presets/)

Usage:
    # Text-to-image
    python generate_with_preset.py --preset creative "your prompt" output.jpg
    python generate_with_preset.py --preset mobile-ui,<project_preset> "login screen" output.jpg

    # Image-to-image (edit/transform existing image)
    python generate_with_preset.py --input photo.jpg "extract the logo" logo.png
    python generate_with_preset.py --input screen.jpg --preset <project_preset> "refine colors" output.jpg

    # Multiple reference images
    python generate_with_preset.py -i navbar.png -i menu.png "combine these designs" output.jpg

    # Remove background with rembg (ML-based, for complex backgrounds)
    python generate_with_preset.py --remove-bg "logo icon" logo.png

    # Remove white background (luminosity-based, preserves sparkles/light elements)
    python generate_with_preset.py --remove-white-bg "icon with sparkles" icon.png

    # List presets
    python generate_with_preset.py --list

Environment variables:
    GEMINI_API_KEY (required) - Your Google Gemini API key
    IMAGEN_PRESETS_DIR (optional) - Additional presets directory
    IMAGE_SIZE (optional) - Image size: "512", "1K" (default), or "2K"
"""

import argparse
import os
import sys
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
from convert_to_svg import convert_to_svg
from remove_white_bg import remove_white_background


def get_preset_dirs() -> list[Path]:
    """Get list of directories to search for presets, in priority order."""
    dirs = []

    # 1. Current working directory presets (check multiple common locations)
    for subdir in ["code/docs/presets", "docs/presets", "design/presets", "presets"]:
        cwd_presets = Path.cwd() / subdir
        if cwd_presets.is_dir():
            dirs.append(cwd_presets)

    # 2. Environment variable
    env_dir = os.environ.get("IMAGEN_PRESETS_DIR")
    if env_dir:
        env_path = Path(env_dir)
        if env_path.is_dir():
            dirs.append(env_path)

    # 3. Built-in presets (relative to this script)
    builtin = SCRIPT_DIR.parent / "presets"
    if builtin.is_dir():
        dirs.append(builtin)

    return dirs


def find_preset(name: str) -> Path | None:
    """Find a preset file by name. Returns None if not found."""
    # Allow both "name" and "name.txt"
    filename = name if name.endswith(".txt") else f"{name}.txt"

    for preset_dir in get_preset_dirs():
        preset_path = preset_dir / filename
        if preset_path.is_file():
            return preset_path

    return None


def load_preset(name: str) -> str:
    """Load preset content by name. Exits if not found."""
    preset_path = find_preset(name)
    if not preset_path:
        print(f"Error: Preset '{name}' not found.", file=sys.stderr)
        print(f"Searched in: {[str(d) for d in get_preset_dirs()]}", file=sys.stderr)
        print(f"Use --list to see available presets.", file=sys.stderr)
        sys.exit(1)

    return preset_path.read_text(encoding="utf-8").strip()


def load_presets(preset_names: str) -> str:
    """Load and combine multiple presets (comma-separated). Returns combined text."""
    names = [n.strip() for n in preset_names.split(",") if n.strip()]
    if not names:
        return ""

    contents = []
    for name in names:
        content = load_preset(name)
        contents.append(f"# Preset: {name}\n{content}")

    return "\n\n".join(contents)


def list_presets() -> None:
    """List all available presets."""
    preset_dirs = get_preset_dirs()

    if not preset_dirs:
        print("No preset directories found.")
        print("\nCreate a 'presets/' folder in your project or set IMAGEN_PRESETS_DIR.")
        return

    print("Available presets:\n")

    seen = set()
    for preset_dir in preset_dirs:
        presets = sorted(preset_dir.glob("*.txt"))
        if presets:
            print(f"  {preset_dir}/")
            for p in presets:
                name = p.stem
                if name not in seen:
                    # Show first line as description
                    first_line = p.read_text(encoding="utf-8").split("\n")[0][:60]
                    print(f"    {name:20} {first_line}...")
                    seen.add(name)
            print()


def build_prompt_with_presets(preset_content: str, user_prompt: str) -> str:
    """Combine preset instructions with user prompt."""
    if not preset_content:
        return user_prompt

    return f"""{preset_content}

---

USER REQUEST:
{user_prompt}"""


def remove_background(input_path: Path, output_path: Path) -> Path:
    """Remove background from image using rembg. Returns output path."""
    try:
        from rembg import remove
        from PIL import Image
    except ImportError:
        print("Error: rembg not installed. Install with: pip install rembg", file=sys.stderr)
        sys.exit(1)

    print("Removing background...")

    # Load image
    input_image = Image.open(input_path)

    # Remove background
    output_image = remove(input_image)

    # Ensure output is PNG for transparency
    final_path = output_path.with_suffix(".png")

    # Save with transparency
    output_image.save(final_path, "PNG")

    # Remove original if different from output
    if input_path != final_path and input_path.exists():
        input_path.unlink()

    return final_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate images with reusable prompt presets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Text-to-image with creative mode
  python generate_with_preset.py --preset creative "landing page concepts" output.jpg

  # Combine presets (mobile-ui rules + project style)
  python generate_with_preset.py --preset mobile-ui,<project_preset> "search screen" output.jpg

  # Image-to-image: extract or transform
  python generate_with_preset.py --input screen.jpg "extract the logo on transparent background" logo.png
  python generate_with_preset.py --input photo.jpg --preset <project_preset> "apply brand colors" output.jpg

  # Multiple reference images (use -i multiple times)
  python generate_with_preset.py -i navbar.png -i menu.png "profile page using navbar from first image and menu from second" output.jpg

  # Remove background (output as PNG with transparency)
  python generate_with_preset.py --remove-bg "app icon on white" icon.png
  python generate_with_preset.py --input photo.jpg --remove-bg "extract subject" subject.png

  # Convert to SVG (requires: pip install vtracer)
  python generate_with_preset.py --output-svg "simple logo" logo.svg
  python generate_with_preset.py --output-svg --svg-mode binary "line art icon" icon.svg

  # List available presets
  python generate_with_preset.py --list

Preset search order:
  1. ./presets/ or ./design/presets/ (current directory)
  2. $IMAGEN_PRESETS_DIR
  3. Built-in presets (imagen/presets/)
        """
    )

    parser.add_argument("--list", "-l", action="store_true",
                        help="List available presets and exit")
    parser.add_argument("--input", "-i", metavar="IMAGE", action="append", dest="inputs",
                        help="Input image(s) for reference (can be used multiple times)")
    parser.add_argument("--preset", "-p",
                        help="Preset name(s) to use, comma-separated (e.g., 'creative' or 'mobile-ui,<project_preset>')")
    parser.add_argument("--remove-bg", "-r", action="store_true",
                        help="Remove background with rembg (ML-based, for complex backgrounds)")
    parser.add_argument("--remove-white-bg", "-w", action="store_true",
                        help="Remove white background (luminosity-based, preserves sparkles/light elements)")
    parser.add_argument("--output-svg", "-s", action="store_true",
                        help="Convert output to SVG (requires: pip install vtracer)")
    parser.add_argument("--svg-mode", choices=["color", "binary"], default="color",
                        help="SVG color mode: 'color' (default) or 'binary' for B/W line art")
    parser.add_argument("--svg-palette",
                        help="SVG color palette for quantization (e.g., '<project_preset>'). Auto-detected from --preset if not specified.")
    parser.add_argument("--show-prompt", action="store_true",
                        help="Show the full prompt (preset + user) and exit without generating")
    parser.add_argument("--size", choices=["512", "1K", "2K"],
                        help="Image size (overrides IMAGE_SIZE env var)")
    parser.add_argument("--model", "-m",
                        help=f"Gemini model ID (default: {DEFAULT_MODEL_ID})")
    parser.add_argument("prompt", nargs="?",
                        help="Text description of the image to generate")
    parser.add_argument("output", nargs="?", default="./generated-image.jpg",
                        help="Output file path (default: ./generated-image.jpg)")

    args = parser.parse_args()

    # Handle --list
    if args.list:
        list_presets()
        return

    # Require prompt for generation
    if not args.prompt:
        parser.print_help()
        sys.exit(1)

    # Load presets
    preset_content = ""
    if args.preset:
        preset_content = load_presets(args.preset)

    # Build full prompt
    full_prompt = build_prompt_with_presets(preset_content, args.prompt)

    # Handle --show-prompt
    if args.show_prompt:
        print("=" * 60)
        print("FULL PROMPT:")
        print("=" * 60)
        print(full_prompt)
        print("=" * 60)
        return

    # Get configuration
    api_key = get_api_key()
    model_id = args.model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL_ID)
    image_size = args.size or os.environ.get("IMAGE_SIZE", DEFAULT_IMAGE_SIZE)
    image_size = validate_image_size(image_size)
    output_path = Path(args.output)

    # Load input images if provided (image-to-image mode)
    input_images = None
    if args.inputs:
        input_images = []
        for input_path_str in args.inputs:
            input_path = Path(input_path_str)
            input_images.append(load_input_image(input_path))

    # Create output directory
    create_output_dir(output_path)

    # Display info
    if args.inputs:
        print(f"Input images: {', '.join(args.inputs)}")
    if args.preset:
        print(f"Presets: {args.preset}")
    print(f"User prompt: \"{args.prompt}\"")
    print(f"Model: {model_id}")
    print(f"Image size: {image_size}")
    print(f"Output: {output_path}")
    print()

    # Build and send request
    request_body = build_request_body(full_prompt, image_size, input_images)
    response = make_api_request(api_key, model_id, request_body)

    # Extract and save image
    image_data = extract_image_data(response)
    if not image_data:
        print("Error: No image data received from API", file=sys.stderr)
        sys.exit(1)

    # Save image
    final_path = save_image(image_data, output_path)

    # Remove background if requested
    if args.remove_bg:
        # Use final_path (which has unique ID) as base for PNG output
        final_path = remove_background(final_path, final_path)
    elif args.remove_white_bg:
        # Use luminosity-based removal (better for generated images with white bg)
        print("Removing white background...")
        final_path = remove_white_background(final_path, final_path.with_suffix('.png'))

    # Convert to SVG if requested
    if args.output_svg:
        # Determine SVG palette: explicit --svg-palette, or first project preset from --preset
        svg_palette = args.svg_palette
        if not svg_palette and args.preset:
            # Extract first preset that's not a built-in (creative, mobile-ui)
            builtin_presets = {"creative", "mobile-ui"}
            for preset_name in args.preset.split(","):
                preset_name = preset_name.strip()
                if preset_name and preset_name not in builtin_presets:
                    svg_palette = preset_name
                    break

        # Use final_path (which has unique ID) as base for SVG output
        svg_path = convert_to_svg(
            input_path=final_path,
            output_path=final_path.with_suffix(".svg"),
            colormode=args.svg_mode,
            preset="logo",  # Always use logo preset for cleaner SVG
            palette=svg_palette,
        )
        # Keep the raster as intermediate, report SVG as main output
        final_path = svg_path

    # Verify and report
    if final_path.exists() and final_path.stat().st_size > 0:
        file_size = get_file_size(final_path)
        print("Success! Image generated.")
        print(f"File: {final_path}")
        print(f"Size: {file_size}")
    else:
        print(f"Error: Failed to save image to {final_path}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
