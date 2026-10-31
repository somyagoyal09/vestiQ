from pathlib import Path
from collections import defaultdict
import random

import requests
from datasets import load_dataset
from PIL import Image
from io import BytesIO


PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = (
    PROJECT_ROOT
    / "ai"
    / "dataset"
    / "traditional"
)

TRAIN_DIR = OUTPUT_DIR / "train"
VAL_DIR = OUTPUT_DIR / "val"

DATASET_NAME = (
    "Harshtherocking/indian-fashion-ecommerce"
)

# Final 12 classes for Vestiq
CLASS_MAPPING = {
    "saree": "saree",
    "women_kurta": "women_kurta",
    "leggings_and_salwars": "leggings_salwar",
    "palazzos": "palazzo",
    "lehenga": "lehenga",
    "dupattas": "dupatta",
    "blouse": "blouse",
    "gowns": "gown",
    "kurta_men": "men_kurta",
    "nehru_jackets": "nehru_jacket",
    "sherwanis": "sherwani",
    "dhoti_pants": "dhoti_pants",
}

MAX_IMAGES_PER_CLASS = 1000
TRAIN_IMAGES_PER_CLASS = 800
VAL_IMAGES_PER_CLASS = 200

SEED = 42

random.seed(SEED)


def download_image(image_url):
    try:
        response = requests.get(
            image_url,
            timeout=10
        )

        if response.status_code != 200:
            return None

        return Image.open(
            BytesIO(response.content)
        ).convert("RGB")

    except Exception:
        return None


def count_existing_images():

    counts = defaultdict(int)

    for source_label, target_label in CLASS_MAPPING.items():

        train_folder = TRAIN_DIR / target_label
        val_folder = VAL_DIR / target_label

        train_count = (
            len(list(train_folder.glob("*.jpg")))
            if train_folder.exists()
            else 0
        )

        val_count = (
            len(list(val_folder.glob("*.jpg")))
            if val_folder.exists()
            else 0
        )

        counts[target_label] = (
            train_count + val_count
        )

    return counts


def main():

    TRAIN_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    VAL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("Loading Indian fashion dataset...")
    print(
        f"Dataset: {DATASET_NAME}"
    )

    dataset = load_dataset(
        DATASET_NAME,
        split="train",
        streaming=True
    )

    collected = count_existing_images()

    print("\nExisting images:")

    for label in sorted(CLASS_MAPPING.values()):
        print(
            f"{label:20s} {collected[label]}"
        )

    print("\nCollecting missing images...")

    for sample in dataset:

        source_label = sample.get(
            "class_label"
        )

        if source_label not in CLASS_MAPPING:
            continue

        target_label = CLASS_MAPPING[
            source_label
        ]

        current_count = collected[
            target_label
        ]

        if current_count >= MAX_IMAGES_PER_CLASS:
            continue

        image_url = sample.get(
            "image_url"
        )

        if not image_url:
            continue

        image = download_image(
            image_url
        )

        if image is None:
            continue

        # First 800 images → train
        if current_count < TRAIN_IMAGES_PER_CLASS:

            split_dir = (
                TRAIN_DIR / target_label
            )

        # Next 200 images → validation
        else:

            split_dir = (
                VAL_DIR / target_label
            )

        split_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        file_name = (
            f"{target_label}_{current_count:05d}.jpg"
        )

        output_path = (
            split_dir / file_name
        )

        try:

            image.save(
                output_path,
                format="JPEG",
                quality=90
            )

            collected[target_label] += 1

        except Exception as error:

            print(
                f"Skipping image: {error}"
            )

        total_collected = sum(
            collected.values()
        )

        if total_collected % 500 == 0:
            print(
                "Total collected:",
                total_collected
            )

        # Stop when all 12 classes reach 1000
        if all(
            count >= MAX_IMAGES_PER_CLASS
            for count in collected.values()
        ):

            break

    print(
        "\nDataset preparation complete."
    )

    print(
        "\nFinal class distribution:"
    )

    total = 0

    for label in sorted(
        CLASS_MAPPING.values()
    ):

        count = collected[label]

        print(
            f"{label:20s} {count}"
        )

        total += count

    print(
        f"\nTotal images: {total}"
    )

    print(
        f"Train directory: {TRAIN_DIR}"
    )

    print(
        f"Validation directory: {VAL_DIR}"
    )


if __name__ == "__main__":
    main()