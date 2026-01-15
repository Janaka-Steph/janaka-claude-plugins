---
name: imagen
description: |
  Generate images using Google Gemini's image generation capabilities.
  Use this skill when the user needs to create, generate, or produce images
  for any purpose including UI mockups, icons, illustrations, diagrams,
  concept art, placeholder images, or visual representations.
---

# Imagen Fork - AI Image Generation Skill

## Overview

This skill generates images using Google Gemini's image generation model (`gemini-3-pro-image-preview`). It enables seamless image creation during any Claude Code session.

**Output Format**: Always JPEG (Gemini API limitation). Any extension is auto-converted to `.jpg`.

## When to Use This Skill

Automatically activate this skill when:
- User requests image generation (e.g., "generate an image of...", "create a picture...")
- Frontend development requires placeholder or actual images
- Documentation needs illustrations or diagrams
- Visualizing concepts, architectures, or ideas
- Creating icons, logos, or UI assets

## Usage

```bash
# Basic usage
python3 scripts/generate_image.py "A futuristic city skyline at sunset"

# With custom output path (always use .jpg)
python3 scripts/generate_image.py "A minimalist app icon" "./assets/icons/music-icon.jpg"

# With custom size (512, 1K, 2K)
python3 scripts/generate_image.py --size 2K "High resolution landscape" "./wallpaper.jpg"
```

## Requirements

- `GEMINI_API_KEY` environment variable must be set
- Python 3.6+ (uses standard library only)

## Output

Generated images are saved as JPEG files. The script:
- Auto-converts any extension to `.jpg`
- Returns the actual output path on success
- Shows error message with details on failure

## Examples

### Frontend Development
```
User: "I need a hero image for my landing page"
-> Generates and saves hero.jpg, provides path for use in HTML/CSS
```

### Documentation
```
User: "Create a diagram showing microservices architecture"
-> Generates architecture.jpg for README or docs
```

### UI Assets
```
User: "Generate a placeholder avatar image"
-> Creates avatar.jpg in appropriate size
```
