#!/usr/bin/env python3
"""
Remove white background from images using luminosity-based transparency.

Unlike rembg (ML-based), this method:
- Works better with generated images that have near-white backgrounds
- Preserves light elements like sparkles, bubbles, highlights
- Uses gradual transparency at edges to avoid aliasing

Usage:
    python remove_white_bg.py input.jpg output.png
    python remove_white_bg.py --threshold 240 input.jpg output.png
    python remove_white_bg.py --no-gradient input.jpg output.png
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("Error: Pillow and numpy required. Install with: pip install Pillow numpy", file=sys.stderr)
    sys.exit(1)


def remove_white_background(
    input_path: Path,
    output_path: Path,
    threshold: int = 252,
    transition_start: int = 235,
    saturation_limit: int = 25,
    use_gradient: bool = True,
) -> Path:
    """
    Remove white background from image using luminosity and saturation analysis.

    Args:
        input_path: Input image path
        output_path: Output PNG path (will be converted to .png if not already)
        threshold: Brightness above which pixels are fully transparent (0-255)
        transition_start: Brightness at which transition to transparent begins
        saturation_limit: Max saturation for a pixel to be considered "white"
        use_gradient: If True, use gradual transparency; if False, hard cutoff

    Returns:
        Path to the saved output file
    """
    # Load image
    img = Image.open(input_path).convert('RGBA')
    img_array = np.array(img, dtype=np.float32)

    r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]

    # Calculate brightness (average of RGB)
    brightness = (r + g + b) / 3

    # Calculate saturation (difference between max and min channel)
    saturation = (
        np.maximum(np.maximum(r, g), b) -
        np.minimum(np.minimum(r, g), b)
    )

    # Initialize alpha channel (fully opaque)
    alpha = np.ones_like(brightness) * 255

    if use_gradient:
        # Gradual transparency for smoother edges
        # Zone de transition: brightness between transition_start and threshold
        transition_mask = (brightness > transition_start) & (saturation < saturation_limit)
        alpha[transition_mask] = np.clip(
            (threshold - brightness[transition_mask]) / (threshold - transition_start) * 255,
            0, 255
        )

    # Pure white = fully transparent
    white_mask = (brightness > threshold) & (saturation < saturation_limit - 15)
    alpha[white_mask] = 0

    # Apply alpha channel
    img_array[:, :, 3] = alpha

    # Ensure output is PNG
    final_path = output_path.with_suffix('.png')

    # Save
    output = Image.fromarray(img_array.astype(np.uint8))
    output.save(final_path, 'PNG')

    return final_path


def main():
    parser = argparse.ArgumentParser(
        description="Remove white background using luminosity-based transparency",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python remove_white_bg.py input.jpg output.png

  # Lower threshold for off-white backgrounds
  python remove_white_bg.py --threshold 240 input.jpg output.png

  # Hard cutoff instead of gradient (faster, but may have aliasing)
  python remove_white_bg.py --no-gradient input.jpg output.png

  # Adjust transition zone
  python remove_white_bg.py --transition-start 220 --threshold 245 input.jpg output.png

When to use this vs rembg:
  - Use this: White/near-white backgrounds, preserve sparkles/light elements
  - Use rembg: Complex backgrounds, photos, need subject detection
        """
    )

    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", help="Output PNG path")
    parser.add_argument("--threshold", "-t", type=int, default=252,
                        help="Brightness threshold for full transparency (0-255, default: 252)")
    parser.add_argument("--transition-start", "-s", type=int, default=235,
                        help="Brightness where transition begins (default: 235)")
    parser.add_argument("--saturation-limit", type=int, default=25,
                        help="Max saturation to consider as 'white' (default: 25)")
    parser.add_argument("--no-gradient", action="store_true",
                        help="Use hard cutoff instead of gradual transparency")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Input: {input_path}")
    print(f"Removing white background (threshold={args.threshold}, gradient={not args.no_gradient})...")

    final_path = remove_white_background(
        input_path=input_path,
        output_path=output_path,
        threshold=args.threshold,
        transition_start=args.transition_start,
        saturation_limit=args.saturation_limit,
        use_gradient=not args.no_gradient,
    )

    file_size = final_path.stat().st_size
    if file_size > 1024 * 1024:
        size_str = f"{file_size / (1024 * 1024):.1f} MB"
    else:
        size_str = f"{file_size / 1024:.1f} KB"

    print(f"Output: {final_path} ({size_str})")


if __name__ == "__main__":
    main()
