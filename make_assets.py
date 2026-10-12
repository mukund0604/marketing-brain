"""Tidelight verified brand assets (fictional): logo lockups drawn with Pillow, plus product packshots
generated once with the logo as reference. These are passed to the image model as references, the way
Zocket's image agent passes verified assets (logo, product images) instead of letting the model improvise.
Output: static/assets/
"""
import math
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
OUT = ROOT / "static" / "assets"
OUT.mkdir(parents=True, exist_ok=True)
DEEP_TIDE, FOG = (18, 59, 74), (233, 236, 234)
FONT = "/System/Library/Fonts/Avenir Next.ttc"


def mark(draw, x, y, w, color, stroke):
    """Tide-line mark: three stacked waves."""
    r = stroke / 2
    for i in range(3):
        yy = y + i * stroke * 2.6
        for t10 in range(0, w * 10 + 1, 3):  # dense round dabs = smooth stroke with round caps
            t = t10 / 10
            cx, cy = x + t, yy + math.sin(t / w * 2 * math.pi) * stroke * 0.9
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)


def lockup(color, name):
    W, H = 1400, 360
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    mark(d, 40, 120, 200, color, 22)
    font = ImageFont.truetype(FONT, 210, index=2)  # Avenir Next Demi Bold
    d.text((290, 40), "tidelight", font=font, fill=color)
    img = img.crop(img.getbbox())
    pad = 30
    out = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    out.paste(img, (pad, pad), img)
    out.save(OUT / name)
    return out


def logos():
    lockup(DEEP_TIDE + (255,), "logo_primary.png")
    lockup(FOG + (255,), "logo_reversed.png")
    sheet = Image.new("RGB", (1400, 700), FOG)  # reference sheet on brand background
    p = Image.open(OUT / "logo_primary.png")
    sheet.paste(p, ((1400 - p.width) // 2, 120), p)
    rv = Image.open(OUT / "logo_reversed.png")
    band = Image.new("RGB", (1400, 300), DEEP_TIDE)
    band.paste(rv, ((1400 - rv.width) // 2, (300 - rv.height) // 2), rv)
    sheet.paste(band, (0, 400))
    sheet.save(OUT / "logo_sheet.png")
    print("logos done")


PACKSHOTS = {
    "fog-shield-spf30": "Fog Shield Mineral SPF 30: a 50 ml matte fog-gray (#E9ECEA) squeeze tube with a deep-tide-blue (#123B4A) flip cap; front label in deep tide blue: the tidelight logo from the reference, then 'fog shield mineral spf 30', 'broad spectrum spf 30', 'tinted · 3 shades', '50 ml'.",
    "kelp-ceramide-cream": "Kelp Ceramide Barrier Cream: a 50 ml brushed-aluminum refillable jar, low and wide, with a fog-gray (#E9ECEA) matte lid; the tidelight logo from the reference printed in deep tide blue on the lid, 'kelp ceramide barrier cream' and '50 ml · refillable' on the jar side.",
    "sea-fennel-c-serum": "Sea Fennel Vitamin C Serum: a 30 ml frosted-glass airless pump bottle with a fog-gray pump; label with the tidelight logo from the reference in deep tide blue, 'sea fennel vitamin c serum', '10% ethyl ascorbic acid' in a small monospace font, and a thin buckthorn-orange (#E8913A) accent line.",
}


def packshots():
    from dotenv import load_dotenv
    from google import genai
    from google.genai import types
    load_dotenv(ROOT / ".env")
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    logo = (OUT / "logo_primary.png").read_bytes()
    for slug, desc in PACKSHOTS.items():
        prompt = (f"Studio packshot of a fictional skincare product. {desc} Reproduce the logo from the attached image exactly "
                  "(lowercase 'tidelight' wordmark with three stacked wave lines to its left); do not invent another logo. "
                  "Product centered, front-facing, label fully legible, on a seamless fog-gray (#E9ECEA) background, soft overcast "
                  "daylight, subtle soft shadow, photorealistic, no props, no text other than the label.")
        r = client.models.generate_content(
            model=os.environ.get("IMAGE_MODEL", "gemini-3-pro-image-preview"),
            contents=[types.Part.from_bytes(data=logo, mime_type="image/png"), prompt],
            config=types.GenerateContentConfig(response_modalities=["IMAGE"], image_config=types.ImageConfig(aspect_ratio="1:1", image_size="1K")))
        for part in r.candidates[0].content.parts:
            if part.inline_data:
                (OUT / f"pack_{slug}.png").write_bytes(part.inline_data.data)
                print("packshot", slug)
                break


if __name__ == "__main__":
    logos()
    if "--packshots" in sys.argv:
        packshots()
