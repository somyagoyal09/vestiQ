# Purpose: detects clothing colour from an image (not used by app code yet)
from collections import Counter

import cv2
import numpy as np


COLOR_NAMES = {
    "black": np.array([0, 0, 0]),
    "white": np.array([255, 255, 255]),
    "red": np.array([220, 40, 40]),
    "orange": np.array([240, 140, 40]),
    "yellow": np.array([235, 210, 40]),
    "green": np.array([60, 150, 80]),
    "blue": np.array([60, 110, 200]),
    "purple": np.array([140, 80, 170]),
    "pink": np.array([230, 130, 160]),
    "brown": np.array([130, 80, 45]),
    "grey": np.array([130, 130, 130]),
    "beige": np.array([210, 190, 150]),
}


def _nearest_color(rgb):
    best_color = None
    best_distance = float("inf")

    pixel = np.array(rgb, dtype=np.float32)

    for name, reference in COLOR_NAMES.items():
        distance = np.linalg.norm(
            pixel - reference
        )

        if distance < best_distance:
            best_distance = distance
            best_color = name

    return best_color


def detect_clothing_color(image_path: str) -> str:
    """
    Detect the dominant clothing color from an image.

    Returns a simple human-readable color name.
    """

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(
            "Unable to read image."
        )

    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB,
    )

    height, width = image.shape[:2]

    # Focus more on the central part of the image,
    # where clothing is usually located.
    y1 = int(height * 0.15)
    y2 = int(height * 0.90)
    x1 = int(width * 0.15)
    x2 = int(width * 0.85)

    crop = image[
        y1:y2,
        x1:x2
    ]

    # Resize for faster processing.
    crop = cv2.resize(
        crop,
        (100, 100),
    )

    pixels = crop.reshape(
        -1,
        3,
    )

    # Remove extremely bright background pixels.
    filtered_pixels = []

    for pixel in pixels:
        r, g, b = pixel

        brightness = (
            int(r)
            + int(g)
            + int(b)
        ) / 3

        if brightness < 245:
            filtered_pixels.append(pixel)

    if not filtered_pixels:
        filtered_pixels = pixels

    # Sample pixels to keep processing lightweight.
    sample = filtered_pixels[
        ::max(
            1,
            len(filtered_pixels) // 1000
        )
    ]

    detected_colors = []

    for pixel in sample:
        detected_colors.append(
            _nearest_color(pixel)
        )

    if not detected_colors:
        return "unknown"

    counts = Counter(
        detected_colors
    )

    return counts.most_common(1)[0][0]