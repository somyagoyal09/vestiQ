# Purpose: detects dominant colour from an image (not used by app code yet)
from collections import Counter

from PIL import Image


COLOR_RANGES = {
    "black": lambda r, g, b: max(r, g, b) < 55,
    "white": lambda r, g, b: min(r, g, b) > 215,
    "grey": lambda r, g, b: abs(r - g) < 18 and abs(g - b) < 18 and 55 <= (r + g + b) / 3 <= 210,
    "red": lambda r, g, b: r > 125 and r > g * 1.35 and r > b * 1.35,
    "pink": lambda r, g, b: r > 150 and b > 100 and g < r * 0.85,
    "orange": lambda r, g, b: r > 150 and g > 65 and g < r * 0.85 and b < 100,
    "yellow": lambda r, g, b: r > 145 and g > 125 and b < 105,
    "green": lambda r, g, b: g > 85 and g > r * 1.20 and g > b * 1.10,
    "blue": lambda r, g, b: b > 95 and b > r * 1.20 and b > g * 1.05,
    "purple": lambda r, g, b: r > 80 and b > 90 and b > g * 1.15 and r > g * 1.10,
    "brown": lambda r, g, b: r > 55 and g > 35 and b < 85 and r > b * 1.20 and g < r * 0.85,
    "beige": lambda r, g, b: r > 150 and g > 125 and b > 85 and abs(r - g) < 55 and r > b * 1.25,
}


def _classify_pixel(rgb):
    r, g, b = rgb

    for color, rule in COLOR_RANGES.items():
        if rule(r, g, b):
            return color

    return "other"


def detect_dominant_color(image_path: str) -> str:
    image = Image.open(image_path).convert("RGB")
    image.thumbnail((160, 160))

    pixels = list(image.getdata())

    classified = []
    for pixel in pixels:
        color = _classify_pixel(pixel)
        if color != "other":
            classified.append(color)

    if not classified:
        return "unknown"

    counts = Counter(classified)
    return counts.most_common(1)[0][0]
