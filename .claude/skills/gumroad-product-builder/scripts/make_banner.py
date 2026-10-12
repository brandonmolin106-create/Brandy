#!/usr/bin/env python3
"""Render X (Twitter) ad banners (1200x675 landscape + 1080x1080 square) for a product.

Usage:
    python make_banner.py --title "TMNT Story Mode" --subtitle "Minecraft adventure map + mod" \
        --price "$19" --out ./x

Requires Pillow:  pip install pillow
Uses DejaVu fonts if present, falls back to Pillow's default font.
"""
import argparse
import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def gradient(size, top, bottom):
    w, h = size
    img = Image.new("RGB", size, top)
    px = img.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        for x in range(w):
            px[x, y] = color
    return img


def draw_centered(draw, text, y, font, fill, width):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) / 2, y), text, font=font, fill=fill)
    return bbox[3] - bbox[1]


def render(size, title, subtitle, price, studio, cta, out_path):
    w, h = size
    img = gradient(size, (12, 10, 30), (70, 20, 110))
    draw = ImageDraw.Draw(img)

    # accent bar
    draw.rectangle([(0, 0), (w, 18)], fill=(255, 200, 40))

    # Scale type off the short edge so square, portrait and landscape all lay out cleanly.
    base = min(w, h)
    title_font = load_font(int(base * 0.085))
    sub_font = load_font(int(base * 0.045))
    price_font = load_font(int(base * 0.09))
    cta_font = load_font(int(base * 0.040))
    studio_font = load_font(int(base * 0.030))

    def wrap_for(text, font):
        # approx chars that fit in 88% of the width at this font size
        avg = font.size * 0.58
        return textwrap.wrap(text, width=max(8, int(w * 0.88 / avg)))

    y = int(h * 0.14)
    for line in wrap_for(title, title_font):
        y += draw_centered(draw, line, y, title_font, (255, 255, 255), w) + int(base * 0.015)

    y += int(base * 0.03)
    for line in wrap_for(subtitle, sub_font):
        y += draw_centered(draw, line, y, sub_font, (220, 220, 235), w) + int(base * 0.01)

    # price pill, placed below whatever text came before it
    bbox = draw.textbbox((0, 0), price, font=price_font)
    pw, ph = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = int(base * 0.03)
    py = max(y + int(base * 0.05), int(h * 0.56))
    draw.rounded_rectangle(
        [((w - pw) / 2 - pad, py - pad / 2), ((w + pw) / 2 + pad, py + ph + pad)],
        radius=int(base * 0.04),
        fill=(255, 200, 40),
    )
    draw.text(((w - pw) / 2, py), price, font=price_font, fill=(20, 15, 40))

    draw_centered(draw, cta, int(h * 0.82), cta_font, (255, 255, 255), w)
    draw_centered(draw, studio, int(h * 0.92), studio_font, (180, 180, 200), w)

    img.save(out_path, "PNG")
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--price", required=True)
    ap.add_argument("--studio", default="Echoes in the Dark  •  @jacksonf5l")
    ap.add_argument("--cta", default="Link below  →  Gumroad")
    ap.add_argument("--out", default=".")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    wide = render((1200, 675), args.title, args.subtitle, args.price, args.studio, args.cta,
                  os.path.join(args.out, "banner-x-1200x675.png"))
    square = render((1080, 1080), args.title, args.subtitle, args.price, args.studio, args.cta,
                    os.path.join(args.out, "banner-square-1080x1080.png"))
    print(wide)
    print(square)


if __name__ == "__main__":
    main()
