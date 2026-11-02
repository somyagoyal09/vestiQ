# Purpose: generates outfit combinations (not used by app code yet)
from itertools import product


def generate_outfit_combinations(
    clothing_items: list[dict],
) -> list[dict]:
    """Generate basic top-bottom outfit combinations."""

    tops = [
        item for item in clothing_items
        if item["category"] in ["T-Shirt", "Shirt", "Sweater", "Jacket"]
    ]

    bottoms = [
        item for item in clothing_items
        if item["category"] in ["Jeans", "Trousers", "Skirt"]
    ]

    combinations = []

    for top, bottom in product(tops, bottoms):
        combinations.append({
            "top": top,
            "bottom": bottom,
        })

    return combinations