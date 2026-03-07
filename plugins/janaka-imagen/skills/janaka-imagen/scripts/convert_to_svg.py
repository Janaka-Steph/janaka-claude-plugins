#!/usr/bin/env python3
"""
convert_to_svg - Convert raster images to SVG using vtracer.

Ideal for logos, icons, and illustrations. Works best with clean graphics
rather than photographs.

Usage:
    # Basic conversion (color mode)
    python convert_to_svg.py input.png output.svg

    # Binary mode for line art (faster)
    python convert_to_svg.py --svg-mode binary input.png output.svg

    # Logo preset (quantizes colors first for cleaner output)
    python convert_to_svg.py --svg-preset logo input.png output.svg

    # Project palette for cleaner output
    python convert_to_svg.py --svg-palette <project_preset> input.png output.svg

    # Custom settings for cleaner output
    python convert_to_svg.py --filter-speckle 8 --color-precision 4 input.png output.svg

Requirements:
    pip install vtracer pillow
"""

import argparse
import sys
import tempfile
from pathlib import Path


def check_vtracer():
    """Check if vtracer is installed."""
    try:
        import vtracer
        return vtracer
    except ImportError:
        print("Error: vtracer not installed. Install with: pip install vtracer", file=sys.stderr)
        sys.exit(1)


def quantize_to_palette(input_path: Path, colors: list[tuple[int, int, int, int]]) -> Path:
    """
    Quantize image to a fixed color palette for cleaner SVG conversion.

    Args:
        input_path: Path to input image
        colors: List of RGBA tuples to quantize to

    Returns:
        Path to temporary quantized image
    """
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        print("Error: pillow not installed. Install with: pip install pillow", file=sys.stderr)
        sys.exit(1)

    img = Image.open(input_path).convert("RGBA")
    data = np.array(img)

    # Convert colors to numpy arrays
    palette = [np.array(c) for c in colors]

    # Find transparent color (if any)
    transparent = np.array([0, 0, 0, 0])

    result = np.zeros_like(data)

    for y in range(data.shape[0]):
        for x in range(data.shape[1]):
            pixel = data[y, x]

            # If mostly transparent, keep transparent
            if pixel[3] < 128:
                result[y, x] = transparent
                continue

            # Find closest color (RGB distance only)
            min_dist = float('inf')
            closest = palette[0]
            for color in palette:
                dist = np.sum((pixel[:3].astype(float) - color[:3]) ** 2)
                if dist < min_dist:
                    min_dist = dist
                    closest = color

            result[y, x] = closest

    # Save to temp file
    result_img = Image.fromarray(result.astype('uint8'), 'RGBA')
    temp_path = Path(tempfile.mktemp(suffix='.png'))
    result_img.save(temp_path, 'PNG')

    return temp_path


# Preset color palettes
PALETTES = {
    "manito": [
        (42, 157, 143, 255),    # Teal #2A9D8F
        (231, 111, 81, 255),    # Terracotta #E76F51
        (245, 240, 232, 255),   # Sand beige #F5F0E8
        (255, 255, 255, 255),   # White
    ],
}


def convert_to_svg(
    input_path: Path,
    output_path: Path,
    colormode: str = "color",
    hierarchical: str = "stacked",
    mode: str = "spline",
    filter_speckle: int = 4,
    color_precision: int = 6,
    layer_difference: int = 16,
    corner_threshold: int = 60,
    length_threshold: float = 4.0,
    max_iterations: int = 10,
    splice_threshold: int = 45,
    path_precision: int = 8,
    preset: str | None = None,
    palette: str | None = None,
) -> Path:
    """
    Convert a raster image to SVG using vtracer.

    Args:
        input_path: Path to input raster image (PNG, JPG, etc.)
        output_path: Path for output SVG file
        colormode: "color" for full color, "binary" for black/white (faster)
        hierarchical: "stacked" (shapes overlap) or "cutout" (shapes have holes)
        mode: "spline" (smooth curves), "polygon" (straight lines), or "none"
        filter_speckle: Remove small artifacts (higher = more filtering)
        color_precision: Color quantization (lower = fewer colors, cleaner)
        layer_difference: Color layer separation threshold
        corner_threshold: Angle threshold for corners (degrees)
        length_threshold: Minimum path segment length
        max_iterations: Curve fitting iterations
        splice_threshold: Angle threshold for splicing paths
        path_precision: Decimal precision for path coordinates
        preset: Optional preset name ("logo" for logo optimization)
        palette: Optional palette name for color quantization ("<project_preset>", etc.)

    Returns:
        Path to the created SVG file
    """
    vtracer = check_vtracer()

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Handle presets
    temp_file = None
    actual_input = input_path

    if preset == "logo" or palette:
        # Quantize colors for cleaner SVG
        palette_colors = PALETTES.get(palette) if palette else None

        if not palette_colors:
            # Default logo palette: extract dominant colors or use generic
            palette_colors = [
                (42, 157, 143, 255),    # Teal
                (231, 111, 81, 255),    # Terracotta
                (255, 255, 255, 255),   # White
                (0, 0, 0, 255),         # Black
            ]

        print(f"  Quantizing to {len(palette_colors)} colors...")
        temp_file = quantize_to_palette(input_path, palette_colors)
        actual_input = temp_file

    # Ensure output has .svg extension
    output_path = output_path.with_suffix(".svg")

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Converting to SVG...")
    print(f"  Input: {input_path}")
    print(f"  Mode: {colormode}")

    try:
        vtracer.convert_image_to_svg_py(
            str(actual_input),
            str(output_path),
            colormode=colormode,
            hierarchical=hierarchical,
            mode=mode,
            filter_speckle=filter_speckle,
            color_precision=color_precision,
            layer_difference=layer_difference,
            corner_threshold=corner_threshold,
            length_threshold=length_threshold,
            max_iterations=max_iterations,
            splice_threshold=splice_threshold,
            path_precision=path_precision,
        )
    except Exception as e:
        print(f"Error: SVG conversion failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Clean up temp file
        if temp_file and temp_file.exists():
            temp_file.unlink()

    if output_path.exists():
        size_kb = output_path.stat().st_size / 1024
        print(f"  Output: {output_path} ({size_kb:.1f} KB)")
        return output_path
    else:
        print(f"Error: SVG file was not created", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Convert raster images to SVG using vtracer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic color conversion
  python convert_to_svg.py logo.png logo.svg

  # Binary mode for line art (much faster)
  python convert_to_svg.py --svg-mode binary icon.png icon.svg

  # Logo preset with project palette (recommended)
  python convert_to_svg.py --svg-preset logo --svg-palette <project_preset> logo.png logo.svg

  # Cleaner output with fewer colors
  python convert_to_svg.py --color-precision 4 --filter-speckle 8 logo.png logo.svg

  # Polygon paths instead of curves
  python convert_to_svg.py --path-mode polygon graphic.png graphic.svg

Tips:
  - Use --svg-preset logo for cleaner output (~25KB vs ~400KB)
  - Use --svg-palette to match your project colors (e.g., <project_preset>)
  - Use --svg-mode binary for line art, logos with solid colors
  - Lower color-precision = fewer colors, simpler SVG
  - Higher filter-speckle = removes more small artifacts
        """
    )

    parser.add_argument("input", help="Input image file (PNG, JPG, etc.)")
    parser.add_argument("output", help="Output SVG file path")

    parser.add_argument("--svg-mode", "-m", choices=["color", "binary"], default="color",
                        help="Color mode: 'color' (default) or 'binary' for B/W")
    parser.add_argument("--hierarchical", choices=["stacked", "cutout"], default="stacked",
                        help="Shape hierarchy: 'stacked' (default) or 'cutout'")
    parser.add_argument("--path-mode", choices=["spline", "polygon", "none"], default="spline",
                        help="Path type: 'spline' (curves), 'polygon' (lines), 'none'")

    parser.add_argument("--svg-preset", choices=["logo"], default=None,
                        help="SVG preset: 'logo' (quantizes colors for cleaner output)")
    parser.add_argument("--svg-palette", choices=list(PALETTES.keys()), default=None,
                        help=f"Color palette for quantization: {', '.join(PALETTES.keys())}")

    parser.add_argument("--filter-speckle", type=int, default=4,
                        help="Speckle filter size (default: 4, higher = cleaner)")
    parser.add_argument("--color-precision", type=int, default=6,
                        help="Color precision 1-8 (default: 6, lower = fewer colors)")
    parser.add_argument("--layer-difference", type=int, default=16,
                        help="Layer color difference threshold (default: 16)")
    parser.add_argument("--corner-threshold", type=int, default=60,
                        help="Corner detection angle in degrees (default: 60)")
    parser.add_argument("--length-threshold", type=float, default=4.0,
                        help="Minimum segment length (default: 4.0)")
    parser.add_argument("--max-iterations", type=int, default=10,
                        help="Curve fitting iterations (default: 10)")
    parser.add_argument("--splice-threshold", type=int, default=45,
                        help="Path splice angle threshold (default: 45)")
    parser.add_argument("--path-precision", type=int, default=8,
                        help="Path coordinate precision (default: 8)")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    convert_to_svg(
        input_path=input_path,
        output_path=output_path,
        colormode=args.svg_mode,
        hierarchical=args.hierarchical,
        mode=args.path_mode,
        filter_speckle=args.filter_speckle,
        color_precision=args.color_precision,
        layer_difference=args.layer_difference,
        corner_threshold=args.corner_threshold,
        length_threshold=args.length_threshold,
        max_iterations=args.max_iterations,
        splice_threshold=args.splice_threshold,
        path_precision=args.path_precision,
        preset=args.svg_preset,
        palette=args.svg_palette,
    )

    print("Done!")


if __name__ == "__main__":
    main()
