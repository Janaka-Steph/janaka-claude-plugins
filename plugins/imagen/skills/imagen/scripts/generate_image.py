#!/usr/bin/env python3
"""
imagen - Google Gemini Image Generation Script

Based on sanjay3290/ai-skills.
Detects actual image format via magic bytes and sets correct extension.

Usage:
    python generate_image.py "prompt" [output_path]

Environment variables:
    GEMINI_API_KEY (required) - Your Google Gemini API key
    IMAGE_SIZE (optional) - Image size: "512", "1K" (default), or "2K"
    GEMINI_MODEL (optional) - Model ID (default: gemini-3-pro-image-preview)
"""

import argparse
import base64
import json
import os
import random
import string
import sys
import urllib.request
import urllib.error
from pathlib import Path


# Configuration
DEFAULT_MODEL_ID = "gemini-3-pro-image-preview"
API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_IMAGE_SIZE = "1K"
VALID_SIZES = {"512", "1K", "2K"}

# Magic bytes for image format detection
MAGIC_BYTES = {
    b'\xff\xd8\xff': '.jpg',      # JPEG
    b'\x89PNG\r\n\x1a\n': '.png', # PNG
    b'GIF87a': '.gif',            # GIF87a
    b'GIF89a': '.gif',            # GIF89a
    b'RIFF': '.webp',             # WebP (starts with RIFF, then WEBP)
}

# Unique ID configuration
UNIQUE_ID_LENGTH = 4
UNIQUE_ID_CHARS = string.ascii_lowercase + string.digits  # a-z, 0-9


def generate_unique_id(length: int = UNIQUE_ID_LENGTH) -> str:
    """Generate a random unique ID (e.g., 'a3xz')."""
    return ''.join(random.choices(UNIQUE_ID_CHARS, k=length))


def apply_unique_naming(output_path: Path) -> Path:
    """Apply unique naming convention: ${contextual_name}_${4 letter ID}.ext

    Examples:
        home.jpg -> home_a3xz.jpg
        profile-screen.png -> profile-screen_b2wy.png
        output.jpg -> output_c4km.jpg
    """
    stem = output_path.stem
    suffix = output_path.suffix
    unique_id = generate_unique_id()
    new_name = f"{stem}_{unique_id}{suffix}"
    return output_path.with_name(new_name)


def detect_image_format(image_bytes: bytes) -> str:
    """Detect image format from magic bytes. Returns extension (e.g., '.jpg')."""
    for magic, ext in MAGIC_BYTES.items():
        if image_bytes.startswith(magic):
            # Special case for WebP: verify WEBP signature
            if magic == b'RIFF' and len(image_bytes) >= 12:
                if image_bytes[8:12] != b'WEBP':
                    continue
            return ext
    # Default to JPEG if unknown (current Gemini behavior)
    return '.jpg'


def get_api_endpoint(model_id: str) -> str:
    """Build the API endpoint URL for the given model."""
    return f"{API_BASE_URL}/{model_id}:streamGenerateContent"


def get_api_key() -> str:
    """Get the Gemini API key from environment variable."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set", file=sys.stderr)
        print("\nTo set it:", file=sys.stderr)
        print("  macOS/Linux: export GEMINI_API_KEY='your-key'", file=sys.stderr)
        print("\nGet a free key at: https://aistudio.google.com/", file=sys.stderr)
        sys.exit(1)
    return api_key


def validate_image_size(size: str) -> str:
    """Validate and return the image size."""
    if size not in VALID_SIZES:
        print(f"Warning: Invalid IMAGE_SIZE '{size}'. Using default '{DEFAULT_IMAGE_SIZE}'", file=sys.stderr)
        return DEFAULT_IMAGE_SIZE
    return size


def fix_extension(output_path: Path, detected_ext: str) -> Path:
    """Fix extension to match detected image format."""
    current_ext = output_path.suffix.lower()
    # Normalize .jpeg to .jpg for comparison
    if current_ext == '.jpeg':
        current_ext = '.jpg'
    if current_ext != detected_ext:
        new_path = output_path.with_suffix(detected_ext)
        if output_path.suffix:
            print(f"Note: Changed extension to {detected_ext} (detected from image data)", file=sys.stderr)
        return new_path
    return output_path


def create_output_dir(output_path: Path) -> None:
    """Create output directory if it doesn't exist."""
    output_dir = output_path.parent
    if output_dir and not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)


def load_input_image(image_path: Path) -> tuple[str, str]:
    """Load an image file and return (base64_data, mime_type)."""
    if not image_path.exists():
        print(f"Error: Input image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    image_bytes = image_path.read_bytes()
    base64_data = base64.b64encode(image_bytes).decode("utf-8")

    # Detect MIME type from magic bytes
    ext = detect_image_format(image_bytes)
    mime_types = {
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_types.get(ext, "image/jpeg")

    return base64_data, mime_type


def build_request_body(prompt: str, image_size: str, input_images: list[tuple[str, str]] | None = None) -> bytes:
    """Build the JSON request body for the API.

    Args:
        prompt: Text prompt for generation
        image_size: Output image size (512, 1K, 2K)
        input_images: Optional list of (base64_data, mime_type) tuples for image-to-image
    """
    parts = []

    # Add input images first if provided (image-to-image mode)
    if input_images:
        for base64_data, mime_type in input_images:
            parts.append({
                "inlineData": {
                    "mimeType": mime_type,
                    "data": base64_data
                }
            })

    # Add text prompt
    parts.append({"text": prompt})

    request_data = {
        "contents": [
            {
                "role": "user",
                "parts": parts
            }
        ],
        "generationConfig": {
            "responseModalities": ["IMAGE", "TEXT"],
            "imageConfig": {
                "image_size": image_size
            }
        }
    }
    return json.dumps(request_data).encode("utf-8")


def make_api_request(api_key: str, model_id: str, request_body: bytes) -> dict:
    """Make the API request and return the response."""
    endpoint = get_api_endpoint(model_id)
    url = f"{endpoint}?key={api_key}"

    headers = {
        "Content-Type": "application/json"
    }

    req = urllib.request.Request(url, data=request_body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"Error: API request failed with HTTP status {e.code}", file=sys.stderr)
        if error_body:
            try:
                error_json = json.loads(error_body)
                print(f"Response: {json.dumps(error_json, indent=2)}", file=sys.stderr)
            except json.JSONDecodeError:
                print(f"Response: {error_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: Failed to connect to API: {e.reason}", file=sys.stderr)
        sys.exit(1)


def extract_image_data(response: dict) -> str:
    """Extract base64 image data from the API response."""
    try:
        # Handle both streaming array and single object responses
        if isinstance(response, list):
            candidates = response[0].get("candidates", [])
        else:
            candidates = response.get("candidates", [])

        if not candidates:
            raise ValueError("No candidates in response")

        parts = candidates[0].get("content", {}).get("parts", [])

        for part in parts:
            if "inlineData" in part:
                return part["inlineData"].get("data", "")

        raise ValueError("No image data found in response parts")
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error: Failed to parse response: {e}", file=sys.stderr)
        print(f"Response: {json.dumps(response, indent=2)}", file=sys.stderr)
        sys.exit(1)


def save_image(image_data: str, output_path: Path, apply_unique_id: bool = True) -> Path:
    """Decode, detect format, apply unique naming, fix extension, and save the image.

    Args:
        image_data: Base64 encoded image data
        output_path: Desired output path (e.g., home.jpg)
        apply_unique_id: If True, applies unique naming (home.jpg -> home_a3xz.jpg)

    Returns:
        Final path where the image was saved
    """
    try:
        image_bytes = base64.b64decode(image_data)
        detected_ext = detect_image_format(image_bytes)

        # Apply unique naming convention: ${contextual_name}_${4 letter ID}.ext
        if apply_unique_id:
            output_path = apply_unique_naming(output_path)

        # Fix extension to match detected format
        final_path = fix_extension(output_path, detected_ext)
        final_path.write_bytes(image_bytes)
        return final_path
    except Exception as e:
        print(f"Error: Failed to save image: {e}", file=sys.stderr)
        sys.exit(1)


def get_file_size(path: Path) -> str:
    """Get human-readable file size."""
    size = path.stat().st_size
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Google Gemini AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_image.py "A sunset over mountains"
  python generate_image.py "An app icon" ./icons/app.jpg
  python generate_image.py --size 2K "High-res landscape" ./wallpaper.jpg

Note: Detects actual image format via magic bytes and auto-corrects extension.

Environment Variables:
  GEMINI_API_KEY    Your Google Gemini API key (required)
  IMAGE_SIZE        Image size: 512, 1K (default), or 2K
  GEMINI_MODEL      Model ID for image generation
        """
    )
    parser.add_argument("prompt", help="Text description of the image to generate")
    parser.add_argument("output", nargs="?", default="./generated-image.jpg",
                        help="Output file path (default: ./generated-image.jpg)")
    parser.add_argument("--size", choices=["512", "1K", "2K"],
                        help="Image size (overrides IMAGE_SIZE env var)")
    parser.add_argument("--model", "-m",
                        help=f"Gemini model ID (default: {DEFAULT_MODEL_ID})")

    args = parser.parse_args()

    # Get configuration
    api_key = get_api_key()
    model_id = args.model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL_ID)
    image_size = args.size or os.environ.get("IMAGE_SIZE", DEFAULT_IMAGE_SIZE)
    image_size = validate_image_size(image_size)
    output_path = Path(args.output)

    # Create output directory
    create_output_dir(output_path)

    # Display info
    print(f"Generating image with prompt: \"{args.prompt}\"")
    print(f"Model: {model_id}")
    print(f"Image size: {image_size}")
    print(f"Output path: {output_path}")
    print()

    # Build and send request
    request_body = build_request_body(args.prompt, image_size)
    response = make_api_request(api_key, model_id, request_body)

    # Extract and save image
    image_data = extract_image_data(response)
    if not image_data:
        print("Error: No image data received from API", file=sys.stderr)
        sys.exit(1)

    # Save image (detects format and fixes extension if needed)
    final_path = save_image(image_data, output_path)

    # Verify and report success
    if final_path.exists() and final_path.stat().st_size > 0:
        file_size = get_file_size(final_path)
        print("Success! Image generated and saved.")
        print(f"File: {final_path}")
        print(f"Size: {file_size}")
    else:
        print(f"Error: Failed to save image to {final_path}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
