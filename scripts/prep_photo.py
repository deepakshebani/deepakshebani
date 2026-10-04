"""Step 3a: prep a photo for ASCII conversion.

1. Remove the background with rembg (human-segmentation model), keeping only
   the largest shape so stray background bits don't print
2. Boost local contrast with OpenCV CLAHE
3. Save grayscale + alpha, so the ASCII step knows exactly where the subject is

Usage:  python scripts/prep_photo.py source-photo.jpg [--crop x0,y0,x1,y1] [--oval] [--hair-clean N]
        current portrait: --crop 225,295,555,770 --oval --hair-clean 400
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
    ap.add_argument("--eyes", help="x,y;x,y eye centres in original pixels, to sharpen the eyes")
    ap.add_argument("--eye-boost", type=float, default=1.0, help="0 = off, 1 = normal, 2 = strong")
    ap.add_argument("--oval", action="store_true", help="fade to black outside an oval around the head")
    ap.add_argument("--hair-clean", type=int, default=0,
                    help="in the top N pixels (of the original photo), drop anything lighter or warmer than hair")
    ap.add_argument("--hair-max", type=float, default=95, help="brightest value still counted as hair")
    args = ap.parse_args()

    src = ImageOps.exif_transpose(Image.open(args.photo)).convert("RGB")
    ox = oy = 0
    if args.crop:
        box = tuple(int(v) for v in args.crop.split(","))
        ox, oy = box[0], box[1]
        src = src.crop(box)
    scale = min(1.0, 1200 / max(src.size))
    src.thumbnail((1200, 1200))

    rgba = np.array(remove_background(src))
    alpha = largest_component(rgba[:, :, 3].astype(np.float32) / 255.0)
    if args.hair_clean:
        n = max(0, int((args.hair_clean - oy) * scale))
        if n:
            rgb = rgba[:n, :, :3].astype(np.float32)
            lum = rgb.mean(axis=2)
            warm = rgb[:, :, 0] > rgb[:, :, 2] + 4      # leaves, brick, skin-toned background
            alpha[:n][(lum > args.hair_max) | warm] = 0   # hair is dark and cool-toned
            alpha = largest_component(alpha)
    alpha = cv2.GaussianBlur(alpha, (0, 0), 1.2)  # soften the cut edge
    if args.oval:
        # soft oval: trims stray background and shoulders, frames the face
        h, w = alpha.shape
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.sqrt(((xx - w / 2) / (w * 0.5)) ** 2 + ((yy - h * 0.48) / (h * 0.52)) ** 2)
        alpha = alpha * np.clip((1.0 - r) / 0.12, 0, 1)

    gray = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    # unsharp mask: ASCII only has ~12 tones, so crisp edges carry the likeness
    blur = cv2.GaussianBlur(gray, (0, 0), 3)
    gray = cv2.addWeighted(gray, 1.8, blur, -0.8, 0)

    # eyes are only a few characters wide in ASCII, so give them extra punch:
    # stronger local contrast, deeper darks (iris, lash line), brighter whites
    if args.eyes and args.eye_boost > 0:
        h, w = gray.shape
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        mask = np.zeros((h, w), np.float32)
        span = 0.065 * w  # eye half-width relative to the crop
        for pt in args.eyes.split(";"):
            ex, ey = (float(v) for v in pt.split(","))
            ex, ey = (ex - ox) * scale, (ey - oy) * scale
            mask = np.maximum(mask, np.exp(-(((xx - ex) / span) ** 2 + ((yy - ey) / (span * 0.6)) ** 2)))
        g = gray.astype(np.float32)
        local = cv2.GaussianBlur(g, (0, 0), span * 0.6)
        k = args.eye_boost
        punched = local + (g - local) * (1 + 1.4 * k)
        punched = np.where(punched < local, punched - (local - punched) * 0.35 * k, punched)
        gray = np.clip(g * (1 - mask) + punched * mask, 0, 255).astype(np.uint8)

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
