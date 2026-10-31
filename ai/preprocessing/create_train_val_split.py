from pathlib import Path
import random
import shutil

SOURCE_DIR = Path("ai/dataset/processed")
OUTPUT_DIR = Path("ai/dataset/classification")

MAX_SAMPLES_PER_CLASS = 1500
TRAIN_RATIO = 0.8
SEED = 42


def main():
    random.seed(SEED)

    train_dir = OUTPUT_DIR / "train"
    val_dir = OUTPUT_DIR / "val"

    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)

    total_train = 0
    total_val = 0

    print("Creating balanced dataset...\n")

    for class_dir in sorted(SOURCE_DIR.iterdir()):

        if not class_dir.is_dir():
            continue

        images = [
            file for file in class_dir.iterdir()
            if file.suffix.lower() in {".jpg", ".jpeg", ".png"}
        ]

        random.shuffle(images)

        selected_images = images[:MAX_SAMPLES_PER_CLASS]

        split_index = int(len(selected_images) * TRAIN_RATIO)

        train_images = selected_images[:split_index]
        val_images = selected_images[split_index:]

        train_class_dir = train_dir / class_dir.name
        val_class_dir = val_dir / class_dir.name

        train_class_dir.mkdir(parents=True, exist_ok=True)
        val_class_dir.mkdir(parents=True, exist_ok=True)

        for image in train_images:
            shutil.copy2(image, train_class_dir / image.name)

        for image in val_images:
            shutil.copy2(image, val_class_dir / image.name)

        total_train += len(train_images)
        total_val += len(val_images)

        print(
            f"{class_dir.name:15s} "
            f"total={len(images):6d} "
            f"train={len(train_images):4d} "
            f"val={len(val_images):4d}"
        )

    print("\nDataset split completed.")
    print(f"Training images:   {total_train}")
    print(f"Validation images: {total_val}")
    print(f"Total used:        {total_train + total_val}")


if __name__ == "__main__":
    main()