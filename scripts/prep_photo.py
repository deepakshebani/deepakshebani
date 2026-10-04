"""Step 3a: prep a photo for ASCII conversion.

1. Remove the background with rembg (skipped with a warning if rembg is not installed)
2. Boost local contrast with OpenCV CLAHE
3. Composite onto pure white so the background maps to blank space

Usage:  python scripts/prep_photo.py source-photo.jpg
Output: source-prepped.png (grayscale)
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "source-prepped.png"


def remove_background(img: Image.Image) -> Image.Image:
    try:
        from rembg import remove
    except ImportError:
        print("rembg not installed, keeping the original background "
              "(pip install rembg onnxruntime for a cleaner result)")
        return img.convert("RGBA")
    return remove(img)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: python scripts/prep_photo.py <photo>")
    src = Image.open(sys.argv[1])
    src = ImageOps.exif_transpose(src).convert("RGB")

    # keep processing fast and consistent
    src.thumbnail((1200, 1200))

    cut = remove_background(src)  # RGBA
    rgba = np.array(cut)
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0

    gray = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray).astype(np.float32)

    # composite onto white: background -> 255 -> space glyph
    out = gray * alpha + 255.0 * (1.0 - alpha)
    out = np.clip(out, 0, 255).astype(np.uint8)

    # crop to the subject's bounding box with a little padding
    ys, xs = np.where(alpha > 0.1)
    if len(xs):
        pad = 20
        y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, out.shape[0])
        x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, out.shape[1])
        out = out[y0:y1, x0:x1]

    Image.fromarray(out, mode="L").save(OUT)
    print(f"wrote {OUT.name} ({out.shape[1]}x{out.shape[0]})")


if __name__ == "__main__":
    main()
