"""Compose a branded 1200x630 social share card per obituary.

Shares (Facebook, texts, email previews) otherwise show a bare portrait. This
paints a newsprint card — portrait, name, lifespan, and the WPR + sponsor mark —
so every share reads as a dignified memorial card. Generated at render from the
locally vendored portrait (text-only until a portrait is vendored).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from config import Newsroom

W, H = 1200, 630
FONTS_DIR = Path(__file__).resolve().parent / "assets" / "fonts"
INK = (27, 26, 24)
MUTED = (111, 106, 97)
RULE = (217, 211, 198)


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    """'#7c2e36' -> (124, 46, 54)."""
    h = value.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

_FONT_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    key = (name, size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(str(FONTS_DIR / name), size)
    return _FONT_CACHE[key]


def _cover(img: Image.Image, w: int, h: int) -> Image.Image:
    """Resize + center-crop to exactly fill w x h."""
    src, dst = img.width / img.height, w / h
    if src > dst:
        nh, nw = h, round(h * src)
    else:
        nw, nh = w, round(w / src)
    img = img.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - w) // 2, (nh - h) // 2
    return img.crop((left, top, left + w, top + h))


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def render_card(
    name: str, lifespan: str, photo_path: Path | None, dest: Path,
    newsroom: Newsroom, sponsor_line: str = "",
) -> None:
    paper = _hex_to_rgb(newsroom.paper)
    accent = _hex_to_rgb(newsroom.accent)
    img = Image.new("RGB", (W, H), paper)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, 8], fill=accent)  # top accent bar

    margin = 70
    text_x, text_w = margin, W - 2 * margin

    if photo_path and Path(photo_path).exists():
        try:
            portrait = _cover(Image.open(photo_path).convert("RGB"), 360, 424)
            px, py = margin, 92
            img.paste(portrait, (px, py))
            draw.rectangle([px, py, px + 360 - 1, py + 424 - 1], outline=RULE, width=2)
            text_x = px + 360 + 54
            text_w = W - text_x - margin
        except Exception:  # noqa: BLE001 — a bad portrait just yields a text card
            pass

    draw.text((text_x, 116), "I N   M E M O R I A M", font=_font("CourierPrime-Regular.ttf", 26), fill=accent)

    name_font = _font("Merriweather-Bold.ttf", 66)
    lines = _wrap(draw, name, name_font, text_w)
    while len(lines) > 3 and name_font.size > 42:
        name_font = _font("Merriweather-Bold.ttf", name_font.size - 6)
        lines = _wrap(draw, name, name_font, text_w)
    y = 168
    for line in lines:
        draw.text((text_x, y), line, font=name_font, fill=INK)
        y += name_font.size + 12

    if lifespan:
        draw.text((text_x, y + 10), lifespan, font=_font("CourierPrime-Regular.ttf", 34), fill=MUTED)

    draw.text((margin, H - 92), newsroom.name.upper(), font=_font("Oswald-SemiBold.ttf", 30), fill=INK)
    footer = sponsor_line or "Obituaries"
    draw.text((margin, H - 52), footer, font=_font("CourierPrime-Regular.ttf", 22), fill=MUTED)

    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, "PNG", compress_level=6)
