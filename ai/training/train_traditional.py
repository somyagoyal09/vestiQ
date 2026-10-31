from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRAIN_DIR = (
    PROJECT_ROOT
    / "ai"
    / "dataset"
    / "traditional"
    / "train"
)

VAL_DIR = (
    PROJECT_ROOT
    / "ai"
    / "dataset"
    / "traditional"
    / "val"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "ai"
    / "models"
)

MODEL_PATH = (
    MODEL_DIR
    / "vestiq_traditional_efficientnet_b0.pth"
)


IMAGE_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 5
LEARNING_RATE = 0.001

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


def main():

    print("Device:", DEVICE)

    print("\nLoading dataset...")

    train_transform = transforms.Compose([
        transforms.Resize(
            (IMAGE_SIZE, IMAGE_SIZE)
        ),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ToTensor(),
        transforms.Normalize(
            [0.485, 0.456, 0.406],
            [0.229, 0.224, 0.225]
        ),
    ])

    val_transform = transforms.Compose([
        transforms.Resize(
            (IMAGE_SIZE, IMAGE_SIZE)
        ),
        transforms.ToTensor(),
        transforms.Normalize(
            [0.485, 0.456, 0.406],
            [0.229, 0.224, 0.225]
        ),
    ])

    train_dataset = datasets.ImageFolder(
        TRAIN_DIR,
        transform=train_transform
    )

    val_dataset = datasets.ImageFolder(
        VAL_DIR,
        transform=val_transform
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0
    )

    class_names = train_dataset.classes

    print(
        "\nClasses:",
        class_names
    )

    print(
        "Training images:",
        len(train_dataset)
    )

    print(
        "Validation images:",
        len(val_dataset)
    )

    print("\nLoading EfficientNet-B0...")

    weights = (
        models.EfficientNet_B0_Weights.DEFAULT
    )

    model = models.efficientnet_b0(
        weights=weights
    )

    # Freeze pretrained backbone
    for parameter in model.features.parameters():
        parameter.requires_grad = False

    # Replace classifier
    model.classifier[1] = nn.Linear(
        model.classifier[1].in_features,
        len(class_names)
    )

    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()

    optimizer = torch.optim.Adam(
        model.classifier[1].parameters(),
        lr=LEARNING_RATE
    )

    best_accuracy = 0.0

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("\nStarting training...")

    for epoch in range(EPOCHS):

        model.train()

        running_loss = 0.0
        correct = 0
        total = 0

        for images, labels in train_loader:

            images = images.to(DEVICE)
            labels = labels.to(DEVICE)

            optimizer.zero_grad()

            outputs = model(images)

            loss = criterion(
                outputs,
                labels
            )

            loss.backward()

            optimizer.step()

            running_loss += (
                loss.item()
                * images.size(0)
            )

            _, predictions = torch.max(
                outputs,
                1
            )

            total += labels.size(0)

            correct += (
                predictions == labels
            ).sum().item()

        train_loss = (
            running_loss
            / len(train_dataset)
        )

        train_accuracy = (
            correct / total
        )

        # Validation
        model.eval()

        val_correct = 0
        val_total = 0
        val_loss_total = 0.0

        with torch.no_grad():

            for images, labels in val_loader:

                images = images.to(DEVICE)
                labels = labels.to(DEVICE)

                outputs = model(images)

                loss = criterion(
                    outputs,
                    labels
                )

                val_loss_total += (
                    loss.item()
                    * images.size(0)
                )

                _, predictions = torch.max(
                    outputs,
                    1
                )

                val_total += labels.size(0)

                val_correct += (
                    predictions == labels
                ).sum().item()

        val_loss = (
            val_loss_total
            / len(val_dataset)
        )

        val_accuracy = (
            val_correct / val_total
        )

        print(
            f"\nEpoch {epoch + 1}/{EPOCHS}"
        )

        print(
            f"Train Loss: {train_loss:.4f}"
        )

        print(
            f"Train Accuracy: "
            f"{train_accuracy * 100:.2f}%"
        )

        print(
            f"Validation Loss: {val_loss:.4f}"
        )

        print(
            f"Validation Accuracy: "
            f"{val_accuracy * 100:.2f}%"
        )

        # Save best model
        if val_accuracy > best_accuracy:

            best_accuracy = val_accuracy

            torch.save(
                {
                    "model_state_dict":
                        model.state_dict(),
                    "class_names":
                        class_names,
                    "image_size":
                        IMAGE_SIZE,
                    "validation_accuracy":
                        best_accuracy,
                },
                MODEL_PATH
            )

            print(
                "Best model saved."
            )

    print(
        "\nTraining complete."
    )

    print(
        f"Best validation accuracy: "
        f"{best_accuracy * 100:.2f}%"
    )

    print(
        f"Model saved at:\n"
        f"{MODEL_PATH}"
    )


if __name__ == "__main__":
    main()