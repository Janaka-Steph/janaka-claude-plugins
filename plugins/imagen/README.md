# imagen

Image generation skill using Google Gemini API.

Based on [sanjay3290/ai-skills/imagen](https://github.com/sanjay3290/ai-skills).

## Features

- Zero dependencies (Python standard library only)
- Detects actual image format via magic bytes
- Auto-corrects file extension to match real format
- SVG conversion with vtracer (optional: `pip install vtracer pillow`)
- Background removal with rembg (optional: `pip install rembg`)
- White background removal (luminosity-based, preserves sparkles/light elements)
- **Smart SVG optimization**: Auto-detects project palette from `--preset` for clean SVGs (~25KB vs ~400KB)

## Usage

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py "prompt" "output.jpg"
```

## Configuration

```bash
export GEMINI_API_KEY="your-key"
```

Get a free key: https://aistudio.google.com/

## Image Sizes

| Size | Resolution |
|------|------------|
| `512` | 512x512 |
| `1K` | 1024x1024 (default) |
| `2K` | 2048x2048 |

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py --size 2K "prompt" "output.jpg"
```

## SVG Generation

Generate clean, optimized SVGs in one step:

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py \
  --preset <project_preset> \
  --remove-bg \
  --output-svg \
  "logo icon" \
  logo.svg
```

The `--preset` automatically sets `--svg-palette` for color quantization, producing much smaller and cleaner SVGs.

## License

Apache-2.0
