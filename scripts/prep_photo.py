"""Step 3a: prep a photo for ASCII conversion.

1. Remove the background with rembg (human-segmentation model), keeping only
   the largest shape so stray background bits don't print
2. Boost local contrast with OpenCV CLAHE
3. Save grayscale + alpha, so the ASCII step knows exactly where the subject is

Usage:  python scripts/prep_photo.py source-photo.jpg [--crop x0,y0,x1,y1]
Output: source-prepped.png (grayscale with alpha)
"""
import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "source-prepped.png"


def remove_background(img: Image.Image) -> Image.Image:
    try:
        from rembg import new_session, remove
    except ImportError:
        print("rembg not installed, keeping the original background "
              "(pip install rembg onnxruntime for a cleaner result)")
        return img.convert("RGBA")
    return remove(img, session=new_session("u2net_human_seg"))


def largest_component(alpha: np.ndarray) -> np.ndarray:
    mask = (alpha > 0.5).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    if n <= 2:
        return alpha
    keep = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return alpha * (labels == keep)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--crop", help="x0,y0,x1,y1 in original pixels, e.g. head and shoulders")
    args = ap.parse_args()

    src = ImageOps.exif_transpose(Image.open(args.photo)).convert("RGB")
    if args.crop:
        src = src.crop(tuple(int(v) for v in args.crop.split(",")))
    src.thumbnail((1200, 1200))

    rgba = np.array(remove_background(src))
    alpha = largest_component(rgba[:, :, 3].astype(np.float32) / 255.0)
    alpha = cv2.GaussianBlur(alpha, (0, 0), 1.2)  # soften the cut edge

    gray = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    # unsharp mask: ASCII only has ~12 tones, so crisp edges carry the likeness
    blur = cv2.GaussianBlur(gray, (0, 0), 3)
    gray = cv2.addWeighted(gray, 1.8, blur, -0.8, 0)

    ys, xs = np.where(alpha > 0.1)
    if len(xs):
        pad = 12
        y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, gray.shape[0])
        x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, gray.shape[1])
        gray, alpha = gray[y0:y1, x0:x1], alpha[y0:y1, x0:x1]

    la = np.dstack([gray, (alpha * 255).astype(np.uint8)])
    Image.fromarray(la, mode="LA").save(OUT)
    print(f"wrote {OUT.name} ({la.shape[1]}x{la.shape[0]})")


if __name__ == "__main__":
    main()
