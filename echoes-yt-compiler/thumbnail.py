#!/usr/bin/env python3
"""YouTube thumbnail (1280x720): subject frame on the right, 2-3 huge words on the left.

    WORK=<work dir> FFMPEG=<ffmpeg> python3 thumbnail.py <clip.mp4> <seconds> "LINE ONE" "LINE TWO" out.jpg
"""
import os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

WORK = os.path.abspath(os.environ.get('WORK', '.'))
FF = os.environ.get('FFMPEG', 'ffmpeg')
TW, TH = 1280, 720
CYAN = (58, 225, 240)


def grab(clip, t):
    png = os.path.join(WORK, 'out', '_thumb_src.png')
    os.makedirs(os.path.dirname(png), exist_ok=True)
    subprocess.run([FF, '-y', '-loglevel', 'error', '-ss', str(t), '-i', clip, '-frames:v', '1', png], check=True)
    return Image.open(png).convert('RGB')


def main(clip, t, line1, line2, out):
    src = grab(clip, float(t))
    sw, sh = src.size
    crop = src.crop((max(0, (sw - 540) // 2), int(sh * 0.08), max(0, (sw - 540) // 2) + 540, int(sh * 0.08) + 720))
    crop = crop.resize((int(540 * TH / 720), TH), Image.LANCZOS)
    crop = ImageEnhance.Contrast(crop).enhance(1.12)
    crop = ImageEnhance.Color(crop).enhance(1.1)
    crop = ImageEnhance.Brightness(crop).enhance(1.05).filter(ImageFilter.UnsharpMask(2, 80, 2))

    bg = Image.open(os.path.join(WORK, 'assets', 'starfield.png')).convert('RGB')
    bg = bg.resize((TW, int(bg.height * TW / bg.width))).crop((0, 0, TW, TH))
    bg = ImageEnhance.Brightness(bg).enhance(0.55)
    glow = Image.new('RGB', (TW, TH), (0, 0, 0))
    ImageDraw.Draw(glow).ellipse((TW - 700, 40, TW - 60, TH + 120), fill=(30, 120, 170))
    bg = Image.blend(bg, Image.eval(glow.filter(ImageFilter.GaussianBlur(120)), lambda v: v), 0.5)

    x0 = TW - crop.width - 10
    mask = np.ones((TH, crop.width), np.float32)
    ramp = 170
    mask[:, :ramp] *= np.linspace(0, 1, ramp)[None, :] ** 1.4       # feather into the background
    mask[-90:, :] *= np.linspace(1, 0.35, 90)[:, None]
    bg.paste(crop, (x0, 0), Image.fromarray((mask * 255).astype('uint8')))

    d = ImageDraw.Draw(bg)
    font = os.path.join(WORK, 'fonts', 'Anton-Regular.ttf')

    def fit(text, max_w, size):
        while size > 40:
            f = ImageFont.truetype(font, size)
            if d.textlength(text, font=f) <= max_w:
                return f
            size -= 6
        return ImageFont.truetype(font, size)

    f1, f2 = fit(line1, 640, 210), fit(line2, 660, 210)
    y = (TH - (f1.size + f2.size) * 1.08) / 2 - 10
    for text, f, col in ((line1, f1, (255, 255, 255)), (line2, f2, CYAN)):
        shadow = Image.new('L', (TW, TH), 0)
        ImageDraw.Draw(shadow).text((62, y + 12), text, font=f, fill=255)
        bg.paste((0, 0, 0), (0, 0), shadow.filter(ImageFilter.GaussianBlur(10)))
        d.text((56, y), text, font=f, fill=col, stroke_width=9, stroke_fill=(0, 0, 0))
        y += f.size * 1.08
    bg.save(out, quality=92)
    print('wrote', out)


if __name__ == '__main__':
    main(*sys.argv[1:6])
