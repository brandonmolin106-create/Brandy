#!/usr/bin/env python3
"""Render Instagram ad banners (1080x1080 feed + 1080x1920 story) for a product.

Usage:
    python make_banner.py --title "TMNT Story Mode" --subtitle "Minecraft adventure map + mod" \
        --price "$19" --out ./instagram

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

    y = int(h * 0.18)
    title_font = load_font(int(w * 0.085))
    for line in textwrap.wrap(title, width=16):
        y += draw_centered(draw, line, y, title_font, (255, 255, 255), w) + 18

    y += 30
    sub_font = load_font(int(w * 0.045))
    for line in textwrap.wrap(subtitle, width=30):
        y += draw_centered(draw, line, y, sub_font, (220, 220, 235), w) + 12

    # price pill
    price_font = load_font(int(w * 0.09))
    bbox = draw.textbbox((0, 0), price, font=price_font)
    pw, ph = bbox[2] - bbox[0], bbox[3] - bbox[1]
    py = int(h * 0.62)
    pad = 36
    draw.rounded_rectangle(
        [((w - pw) / 2 - pad, py - pad / 2), ((w + pw) / 2 + pad, py + ph + pad)],
        radius=40,
        fill=(255, 200, 40),
    )
    draw.text(((w - pw) / 2, py), price, font=price_font, fill=(20, 15, 40))

    cta_font = load_font(int(w * 0.045))
    draw_centered(draw, cta, int(h * 0.80), cta_font, (255, 255, 255), w)

    studio_font = load_font(int(w * 0.032))
    draw_centered(draw, studio, int(h * 0.92), studio_font, (180, 180, 200), w)

    img.save(out_path, "PNG")
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--price", required=True)
    ap.add_argument("--studio", default="Echoes in the Dark  •  @jacksonsworld16")
    ap.add_argument("--cta", default="Link in bio  →  Gumroad")
    ap.add_argument("--out", default=".")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    feed = render((1080, 1080), args.title, args.subtitle, args.price, args.studio, args.cta,
                  os.path.join(args.out, "banner-feed-1080x1080.png"))
    story = render((1080, 1920), args.title, args.subtitle, args.price, args.studio, args.cta,
                   os.path.join(args.out, "banner-story-1080x1920.png"))
    print(feed)
    print(story)


if __name__ == "__main__":
    main()
