from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)


DATA_DIR = Path("ai/dataset/classification")
MODEL_PATH = Path("ai/models/vestiq_efficientnet_b0.pth")

IMAGE_SIZE = 224
BATCH_SIZE = 32

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


def main():

    print("Device:", DEVICE)

    val_transforms = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])

    val_dataset = datasets.ImageFolder(
        DATA_DIR / "val",
        transform=val_transforms
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0
    )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=DEVICE
    )

    class_names = checkpoint["class_names"]

    model = models.efficientnet_b0(weights=None)

    model.classifier[1] = nn.Linear(
        model.classifier[1].in_features,
        len(class_names)
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model = model.to(DEVICE)
    model.eval()

    all_predictions = []
    all_labels = []

    print("\nEvaluating model...\n")

    with torch.no_grad():

        for images, labels in val_loader:

            images = images.to(DEVICE)

            outputs = model(images)

            predictions = outputs.argmax(dim=1)

            all_predictions.extend(
                predictions.cpu().numpy()
            )

            all_labels.extend(
                labels.numpy()
            )

    accuracy = accuracy_score(
        all_labels,
        all_predictions
    )

    print("=" * 60)
    print(f"Overall Accuracy: {accuracy * 100:.2f}%")
    print("=" * 60)

    print("\nClassification Report:\n")

    print(
        classification_report(
            all_labels,
            all_predictions,
            target_names=class_names,
            digits=4,
            zero_division=0
        )
    )

    print("\nConfusion Matrix:\n")

    matrix = confusion_matrix(
        all_labels,
        all_predictions
    )

    print(matrix)

    print("\nClass names:")
    for index, name in enumerate(class_names):
        print(f"{index}: {name}")


if __name__ == "__main__":
    main()