# imagen Reference

## Setup

### 1. Get a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Click "Get API Key"
3. Create a new API key or use an existing one

### 2. Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY = "your-api-key-here"

# To persist across sessions, add to your PowerShell profile:
Add-Content $PROFILE "`n`$env:GEMINI_API_KEY = 'your-api-key-here'"
```

**Windows (CMD):**
```cmd
set GEMINI_API_KEY=your-api-key-here

# To persist, use System Properties > Environment Variables
```

**macOS/Linux:**
```bash
export GEMINI_API_KEY="your-api-key-here"

# Add to ~/.zshrc or ~/.bashrc to persist
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.zshrc
```

## API Reference

### Model

- **Model ID**: `gemini-3-pro-image-preview` (configurable via `--model` flag or `GEMINI_MODEL` env var)
- **Endpoint**: `https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent`

### Image Sizes

| Size | Description |
|------|-------------|
| `512` | 512x512 pixels - Fast, good for icons/thumbnails |
| `1K` | 1024x1024 pixels - Default, balanced quality/speed |
| `2K` | 2048x2048 pixels - High resolution, slower |

## Script Parameters

### Python Script (Cross-Platform)

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py [options] <prompt> [output_path]
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `prompt` | Yes | - | Text description of desired image |
| `output_path` | No | `./generated-image.jpg` | Where to save the image |
| `--preset, -p` | No | - | Preset name(s), comma-separated |
| `--input, -i` | No | - | Input image(s) for image-to-image |
| `--size` | No | `1K` | Image size (512, 1K, or 2K) |
| `--remove-bg` | No | - | Remove background with rembg (ML-based) |
| `--remove-white-bg` | No | - | Remove white background (luminosity-based, preserves sparkles) |
| `--output-svg, -s` | No | - | Convert output to SVG (requires vtracer) |
| `--svg-mode` | No | `color` | SVG color mode: `color` or `binary` |
| `--svg-palette` | No | auto | SVG color palette for quantization (auto-detected from `--preset`) |

### SVG Conversion Script

```bash
python3 $SKILL_DIR/scripts/convert_to_svg.py [options] <input> <output>
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `input` | Yes | - | Input image file (PNG, JPG, etc.) |
| `output` | Yes | - | Output SVG file path |
| `--svg-mode, -m` | No | `color` | Color mode: `color` or `binary` for B/W |
| `--svg-preset` | No | - | SVG preset: `logo` (quantizes colors for cleaner output) |
| `--svg-palette` | No | - | Color palette for quantization (e.g., `<project_preset>`) |
| `--filter-speckle` | No | `4` | Speckle filter size (higher = cleaner) |
| `--color-precision` | No | `6` | Color precision 1-8 (lower = fewer colors) |

### SVG Auto-Optimization

When using `--output-svg` in `generate_with_preset.py`, the tool automatically:
- Applies the `logo` preset to quantize colors
- Detects the project palette from `--preset` (ignores built-ins like `creative`, `mobile-ui`)
- Produces clean, optimized SVGs (~25KB instead of ~400KB)

Override with explicit `--svg-palette` if needed.

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | - | Your Google Gemini API key |
| `IMAGE_SIZE` | No | `1K` | Image size (512, 1K, or 2K) |

## Usage Examples

### Basic Generation

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py "A serene mountain landscape at dawn"
```

### With Preset

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py --preset mobile-ui "Login screen" "./login.jpg"
```

### Custom Output Path

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py "Minimalist logo design" "./assets/logo.jpg"
```

### High Resolution

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py --size 2K "Detailed portrait" "./high-res.jpg"
```

### Small/Fast Generation

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py --size 512 "Simple icon" "./icon.jpg"
```

### Image-to-Image

```bash
python3 $SKILL_DIR/scripts/generate_with_preset.py --input source.jpg "Extract the logo" logo.png
```

## Prompt Tips

### For Best Results

1. **Be specific**: "A red sports car" vs "A cherry red 1967 Mustang convertible"
2. **Include style**: "in watercolor style", "photorealistic", "minimalist flat design"
3. **Mention lighting**: "golden hour lighting", "soft diffused light", "dramatic shadows"
4. **Specify composition**: "close-up", "wide angle", "from above", "centered"

### Advanced Prompting Techniques

These techniques produce significantly better results for photorealistic and professional imagery:

#### Camera & Lens Specifications
Include specific photography parameters for authentic looks:
- **Lens focal length**: "85mm f/1.4 lens", "50mm prime", "35mm wide angle"
- **Aperture**: "shallow depth of field at f/1.8", "deep focus at f/8"
- **Camera angle**: "eye-level shot", "low angle looking up", "3/4 profile view"

Example: `"Portrait shot with 85mm f/1.4 lens, shallow depth of field, subject sharp against soft bokeh background"`

#### Lighting Architecture
Specify complete lighting setups for professional results:
- **Three-point lighting**: key light, fill light, rim/back light
- **Catchlights**: reflections in eyes for portraits
- **Shadow quality**: "soft shadows", "dramatic hard shadows", "subtle rim light"

Example: `"Professional headshot with three-point lighting setup, soft key light from left, subtle fill light, rim light for hair separation, visible catchlights in eyes"`

#### Film Stock & Era Aesthetics
Reference specific film stocks or eras for authentic period looks:
- **Film stocks**: "Kodak Portra 400 color palette", "Fujifilm Pro 400H tones", "Kodak Tri-X grain"
- **Era aesthetics**: "1990s disposable camera quality", "early-2000s digital camera look", "1970s Polaroid style"
- **Grain and texture**: "subtle film grain", "realistic sensor noise"

Example: `"Casual portrait with Kodak Portra 400 color tones, natural film grain, 1990s aesthetic, soft warm highlights"`

#### Facial Consistency (for portraits/people)
When generating or editing images with faces, explicitly state preservation requirements:
- `"Keep the facial features exactly consistent"`
- `"Preserve original face structure and proportions"`
- `"Do not alter or change the face"`

#### Material & Texture Details
Add realistic texture specifications:
- **Skin**: "natural skin texture with visible pores", "subtle skin imperfections"
- **Fabric**: "fine wool texture visible", "silk sheen and drape"
- **Surfaces**: "brushed metal finish", "weathered wood grain"

Example: `"Close-up portrait showing natural skin texture with visible pores, fine fabric detail on collar, realistic hair strands"`

#### Composition Framing
Be precise about framing and subject positioning:
- **Shot types**: "chest-up framing", "3/4 body shot", "full body"
- **Positioning**: "centered subject", "rule of thirds placement", "mirror selfie angle"
- **Aspect ratio context**: "portrait orientation", "landscape format", "square crop"

### Example Prompts by Use Case

**UI/Frontend:**
- "A modern dashboard UI mockup with dark theme, showing analytics charts"
- "Clean minimalist app icon for a task management app, rounded square shape"
- "Hero image for a SaaS landing page, abstract gradient with geometric shapes"

**Documentation:**
- "Simple architecture diagram showing microservices connected by arrows"
- "Flowchart illustrating user authentication process"

**Placeholders:**
- "Professional headshot placeholder, silhouette style, neutral gray background"
- "Product image placeholder, simple box shape with 'Image Coming Soon' text"

**Marketing/Creative:**
- "Isometric illustration of a modern office workspace"
- "Gradient abstract background suitable for presentation slides"

**Professional Portraits (using advanced techniques):**
- "Corporate headshot, 85mm f/2.8 lens, three-point studio lighting, navy blue suit, neutral gray backdrop, subtle catchlights, chest-up framing, natural skin texture"
- "Casual lifestyle portrait, Kodak Portra 400 tones, natural window light, soft shadows, 3/4 body shot, authentic film grain, early-2000s digital aesthetic"

**E-commerce & Product Photography:**
- "Product photo of leather watch, 100mm macro lens, soft diffused lighting, visible leather texture and stitching, clean white background, subtle reflection"
- "Fashion flat-lay, overhead shot, soft natural lighting, fabric texture visible, minimalist composition"

## Troubleshooting

### "GEMINI_API_KEY not set"
Ensure the environment variable is set in your current shell:

**Windows (PowerShell):**
```powershell
echo $env:GEMINI_API_KEY  # Should show your key
```

**macOS/Linux:**
```bash
echo $GEMINI_API_KEY  # Should show your key
```

### "API request failed with HTTP status 400"
- Check your prompt for special characters that may break JSON
- Ensure the prompt isn't empty
- Verify API key is valid

### "API request failed with HTTP status 429"
- Rate limited - wait a moment and retry
- Consider upgrading your API quota

### "No image data found in response"
- The model may have refused the prompt (content policy)
- Try rephrasing the prompt
- Check if the model returned an error message in the response

### Image is corrupted/won't open
- Ensure Python 3.6+ is installed
- Check if the full response was received (network issues)
- Verify output path is writable

### Windows-specific issues
- Make sure Python is in your PATH
- Use forward slashes or escaped backslashes in paths

## API Costs

Check [Google AI pricing](https://ai.google.dev/pricing) for current Gemini API costs. Image generation typically costs more than text generation.

## Limitations

- Maximum prompt length varies by model
- Some content types may be restricted by Google's content policy
- Generated images are subject to Google's terms of service
- Rate limits apply based on your API tier
