from pathlib import Path
from collections import Counter
from datasets import load_dataset
from PIL import Image


DATASET_NAME = "detection-datasets/fashionpedia"

OUTPUT_DIR = Path("ai/dataset/processed")

SELECTED_CLASSES = {
    "dress": "dress",
    "top": "top, t-shirt, sweatshirt",
    "shirt_blouse": "shirt, blouse",
    "pants": "pants",
    "skirt": "skirt",
    "shorts": "shorts",
    "jacket": "jacket",
    "coat": "coat",
    "sweater": "sweater",
    "cardigan": "cardigan",
    "jumpsuit": "jumpsuit",
    "shoes": "shoe",
}


def main():
    print("Loading Fashionpedia...")

    dataset = load_dataset(DATASET_NAME)

    train_dataset = dataset["train"]
    category_names = train_dataset.features[
        "objects"
    ]["category"].feature.names

    category_to_output = {
        source_name: output_name
        for output_name, source_name in SELECTED_CLASSES.items()
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    counts = Counter()
    saved_crops = 0

    print("\nStarting preprocessing...")
    print("Selected classes:", len(SELECTED_CLASSES))

    for index, sample in enumerate(train_dataset):

        image = sample["image"].convert("RGB")
        objects = sample["objects"]

        for category_id, bbox in zip(
            objects["category"],
            objects["bbox"]
        ):
            category_name = category_names[category_id]

            if category_name not in category_to_output:
                continue

            output_class = category_to_output[category_name]

            x, y, width, height = bbox

            x1 = max(0, int(x))
            y1 = max(0, int(y))
            x2 = min(image.width, int(x + width))
            y2 = min(image.height, int(y + height))

            if x2 <= x1 or y2 <= y1:
                continue

            crop = image.crop((x1, y1, x2, y2))

            class_dir = OUTPUT_DIR / output_class
            class_dir.mkdir(parents=True, exist_ok=True)

            filename = (
                f"{sample['image_id']}_"
                f"{counts[output_class]}.jpg"
            )

            crop.save(
                class_dir / filename,
                "JPEG",
                quality=90
            )

            counts[output_class] += 1
            saved_crops += 1

        if (index + 1) % 1000 == 0:
            print(
                f"Processed {index + 1}/{len(train_dataset)} "
                f"images | Crops: {saved_crops}"
            )

    print("\nPreprocessing completed.")
    print("\nSaved samples:")

    for class_name, count in counts.most_common():
        print(f"{class_name:15s}: {count}")

    print(f"\nTotal crops saved: {saved_crops}")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
    