---
name: imagen
description: |
  Generate images using Google Gemini Imagen. Supports text-to-image,
  image-to-image transformations, and reusable presets for consistent style.
---

# Gemini Imagen Skill

Generate high-quality images using Google Gemini's Imagen model with optional presets.

## Script Location

The scripts are in the skill's `scripts/` directory. Use the skill's base directory path provided when the skill is loaded.

## Usage

### Text-to-Image (basic)

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py "your prompt" output.jpg
```

### Text-to-Image with Presets

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py \
  --preset <preset_name> \
  "your prompt" \
  output.jpg
```

### Image-to-Image (edit/transform)

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py \
  --input source_image.jpg \
  "transformation instructions" \
  output.jpg
```

### Combined (input image + preset)

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py \
  --input source.jpg \
  --preset <preset_name> \
  "instructions" \
  output.jpg
```

## Options

| Option | Description |
|--------|-------------|
| `--preset, -p` | Preset name(s), comma-separated (e.g., `mobile-ui,damemano`) |
| `--input, -i` | Input image(s) for image-to-image (can use multiple times) |
| `--size` | Output size: `512`, `1K` (default), or `2K` |
| `--remove-bg, -r` | Remove background (requires: `pip install rembg`) |
| `--output-svg, -s` | Convert to SVG (requires: `pip install vtracer`) |
| `--svg-mode` | SVG color mode: `color` (default) or `binary` for B/W |
| `--svg-palette` | SVG color palette for quantization (auto-detected from `--preset`) |
| `--list, -l` | List available presets |
| `--show-prompt` | Show full prompt without generating |

## Discovering Presets

List available presets for the current project:

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py --list
```

Presets are searched in order:
1. `./presets/` (current project)
2. `./design/presets/` (current project)
3. `$IMAGEN_PRESETS_DIR` environment variable
4. Built-in presets in the skill directory

## Built-in Presets

| Preset | Purpose |
|--------|---------|
| `creative` | Brainstorming mode - bold, distinctive, non-generic designs |
| `mobile-ui` | Mobile UI screens - full-bleed, no device frame, 9:19.5 ratio |

## Combining Presets

Multiple presets can be combined with commas: `--preset mobile-ui,damemano`

**How it works:** Presets are concatenated in order into the final prompt. The model receives all instructions together.

**Best practice:** Combine presets that address different aspects:
- `mobile-ui` = format/framing rules (screen ratio, no device frame)
- `damemano` = style rules (colors, typography, brand feel)

**Conflicts:** If presets contradict each other, the model's behavior is unpredictable - it may follow the last instruction, make a compromise, or ignore some rules. Avoid combining presets with conflicting instructions.

## Common Tasks

### Generate mobile UI screen

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py \
  --preset mobile-ui \
  "Login screen with email input, password field, and submit button" \
  login.jpg
```

### Apply project style to mobile screen

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py \
  --preset mobile-ui,<project_preset> \
  "Search results page" \
  search.jpg
```

### Extract element from image

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py \
  --input screen.jpg \
  "Extract the logo on transparent background" \
  logo.png
```

### Creative exploration

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py \
  --preset creative \
  "Landing page concepts for a food delivery app" \
  concepts.jpg
```

### Remove background

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py \
  --remove-bg \
  "app icon" \
  icon.png
```

### Generate SVG logo/icon

```bash
# Color SVG with project palette (recommended for clean output)
python3 $SKILL_DIR/scripts/generate_with_preset.py \
  --preset damemano \
  --remove-bg --output-svg \
  "minimalist app logo" \
  logo.svg

# The --preset automatically sets --svg-palette for color quantization
# This produces much smaller, cleaner SVGs (~25KB vs ~400KB)

# Binary SVG for line art (faster, cleaner)
python3 $SKILL_DIR/scripts/generate_with_preset.py \
  --output-svg --svg-mode binary \
  "simple line icon" \
  icon.svg

# Explicit palette override (if different from --preset)
python3 $SKILL_DIR/scripts/generate_with_preset.py \
  --preset mobile-ui \
  --svg-palette damemano \
  --remove-bg --output-svg \
  "logo on transparent background" \
  logo.svg
```

### Convert existing image to SVG

```bash
python3 $SKILL_DIR/scripts/convert_to_svg.py input.png output.svg

# Binary mode for line art
python3 $SKILL_DIR/scripts/convert_to_svg.py --svg-mode binary icon.png icon.svg

# Logo preset (quantizes colors for cleaner output)
python3 $SKILL_DIR/scripts/convert_to_svg.py --svg-preset logo input.png output.svg

# Project-specific palette for best results
python3 $SKILL_DIR/scripts/convert_to_svg.py --svg-palette damemano logo.png logo.svg
```

**Tip:** For logos with gradients or anti-aliasing, use `--svg-preset logo` or `--svg-palette` to quantize colors first. This produces much cleaner SVGs (typically 25KB vs 400KB+).

## SVG Optimization

When using `--output-svg`, the tool automatically:
1. Applies the `logo` preset for color quantization
2. Uses the project palette from `--preset` (if not a built-in like `creative` or `mobile-ui`)

This ensures clean, optimized SVGs on the first generation. Override with `--svg-palette` if needed.

## Correcting/Fixing UI Screens

When asked to "correct" or "fix" an existing UI screen:
- **Use `--input`** to pass the original image
- **Keep everything else intact** — Only change the specific elements mentioned in the prompt
- The goal is to fix identified issues while preserving the overall design, layout, and style
- Do NOT regenerate from scratch with a completely different design

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py \
  --input original-screen.jpg \
  --preset mobile-ui \
  "Fix the navbar: change from 4 items to 3 items (Buscar, +, Yo)" \
  original-screen-fixed.jpg
```

## Batch Generation (Parallel)

**IMPORTANT:** When generating more than 1 image, ALWAYS use `generate_batch.py`. It runs requests in parallel and is 3-5x faster than sequential calls.

```bash
# From command line (prompt/output pairs)
python3 $SKILL_DIR/scripts/generate_batch.py \
  --preset mobile-ui,damemano \
  "home screen" home.jpg \
  "profile screen" profile.jpg \
  "settings screen" settings.jpg

# From JSON file (better for many images)
python3 $SKILL_DIR/scripts/generate_batch.py jobs.json

# Control parallelism (default: 4 workers)
python3 $SKILL_DIR/scripts/generate_batch.py --workers 8 jobs.json
```

### JSON Batch Format

```json
{
  "preset": "mobile-ui,damemano",
  "jobs": [
    {"prompt": "home screen with search bar", "output": "home.jpg"},
    {"prompt": "user profile page", "output": "profile.jpg"},
    {"prompt": "settings menu", "output": "settings.jpg", "input": "reference.jpg"}
  ]
}
```

### Batch Options

| Option | Description |
|--------|-------------|
| `--preset, -p` | Preset name(s), overrides JSON preset |
| `--workers, -w` | Max parallel workers (default: 4) |
| `--size` | Image size: `512`, `1K` (default), `2K` |

### When to Use Batch

- **2+ images**: Always use batch (mandatory for multiple images)
- **Same preset**: All images share the preset (set once)
- **Progress tracking**: Shows real-time progress with success/failure status

## Environment

Requires `GEMINI_API_KEY` environment variable to be set.

## File Naming Convention

Generated images automatically use unique naming to avoid collisions:

```
${contextual_name}_${4 letter ID}.ext
```

**Examples:**
- `home.jpg` → `home_a3xz.jpg`
- `profile-screen.png` → `profile-screen_b2wy.png`
- `logo.svg` → `logo_c4km.svg`

This means:
- **You never need to manually track sequence numbers** (no more `home-18.jpg` → `home-19.jpg`)
- **Files never overwrite each other** — each generation gets a unique 4-character ID
- **The contextual name you provide is preserved** — just with a unique suffix

The 4-letter ID uses lowercase letters and digits (a-z, 0-9), giving 1.6 million combinations per base name.

## Notes

- The script auto-detects image format via magic bytes and corrects file extensions
- Output directory is created automatically if it doesn't exist
- For project-specific presets, create a `presets/` or `design/presets/` folder in the project root
