# gemini-imagen

Simple Python script for image generation using Google Gemini API.

Based on [sanjay3290/ai-skills/imagen](https://github.com/sanjay3290/ai-skills).

## Features

- Zero dependencies (Python standard library only)
- Forces `.jpg` output (Gemini API always returns JPEG)
- Auto-converts any extension to `.jpg`

## Usage

```bash
python3 scripts/generate_image.py "prompt" "output.jpg"
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
python3 scripts/generate_image.py --size 2K "prompt" "output.jpg"
```

## License

Apache-2.0
