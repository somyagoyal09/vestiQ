from pathlib import Path

import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


DATA_DIR = Path("ai/dataset/classification")
MODEL_DIR = Path("ai/models")
BASE_MODEL = MODEL_DIR / "vestiq_efficientnet_b0.pth"

IMAGE_SIZE = 224
BATCH_SIZE = 16
EPOCHS = 5
LEARNING_RATE = 0.00002
WEIGHT_DECAY = 0.0001
PATIENCE = 2

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


def main():
    print("Device:", DEVICE)

    train_transforms = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(8),
        transforms.ColorJitter(
            brightness=0.10,
            contrast=0.10,
            saturation=0.10
        ),
        transforms.ToTensor(),
        transforms.Normalize(
            [0.485, 0.456, 0.406],
            [0.229, 0.224, 0.225]
        ),
    ])

    val_transforms = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(
            [0.485, 0.456, 0.406],
            [0.229, 0.224, 0.225]
        ),
    ])

    train_dataset = datasets.ImageFolder(
        DATA_DIR / "train",
        transform=train_transforms
    )

    val_dataset = datasets.ImageFolder(
        DATA_DIR / "val",
        transform=val_transforms
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

    print("\nTraining samples:", len(train_dataset))
    print("Validation samples:", len(val_dataset))

    # Load the already trained 74.10% model
    checkpoint = torch.load(
        BASE_MODEL,
        map_location=DEVICE
    )

    class_names = checkpoint["class_names"]

    model = models.efficientnet_b0(
        weights=None
    )

    model.classifier[1] = nn.Linear(
        model.classifier[1].in_features,
        len(class_names)
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model = model.to(DEVICE)

    print(
        f"\nLoaded existing model with "
        f"validation accuracy: "
        f"{checkpoint['best_val_accuracy'] * 100:.2f}%"
    )

    criterion = nn.CrossEntropyLoss(
        label_smoothing=0.05
    )

    optimizer = AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY
    )

    scheduler = ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=0.5,
        patience=1
    )

    best_accuracy = checkpoint["best_val_accuracy"]

    best_model_path = (
        MODEL_DIR /
        "vestiq_efficientnet_b0_finetuned.pth"
    )

    epochs_without_improvement = 0

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

            running_loss += loss.item()

            predictions = outputs.argmax(dim=1)

            correct += (
                predictions == labels
            ).sum().item()

            total += labels.size(0)

        train_loss = (
            running_loss / len(train_loader)
        )

        train_accuracy = correct / total

        model.eval()

        val_loss_total = 0.0
        val_correct = 0
        val_total = 0

        with torch.no_grad():

            for images, labels in val_loader:

                images = images.to(DEVICE)
                labels = labels.to(DEVICE)

                outputs = model(images)

                loss = criterion(
                    outputs,
                    labels
                )

                val_loss_total += loss.item()

                predictions = outputs.argmax(dim=1)

                val_correct += (
                    predictions == labels
                ).sum().item()

                val_total += labels.size(0)

        val_loss = (
            val_loss_total / len(val_loader)
        )

        val_accuracy = val_correct / val_total

        scheduler.step(val_accuracy)

        current_lr = optimizer.param_groups[0]["lr"]

        print(
            f"\nEpoch {epoch + 1}/{EPOCHS}"
        )

        print(
            f"Train Loss: {train_loss:.4f} | "
            f"Train Accuracy: {train_accuracy:.4f}"
        )

        print(
            f"Val Loss: {val_loss:.4f} | "
            f"Val Accuracy: {val_accuracy:.4f}"
        )

        print(
            f"Learning Rate: {current_lr:.7f}"
        )

        if val_accuracy > best_accuracy:

            best_accuracy = val_accuracy
            epochs_without_improvement = 0

            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "class_names": class_names,
                    "image_size": IMAGE_SIZE,
                    "best_val_accuracy": best_accuracy,
                },
                best_model_path
            )

            print(
                "NEW BEST MODEL SAVED:",
                best_model_path
            )

        else:
            epochs_without_improvement += 1

        if epochs_without_improvement >= PATIENCE:

            print(
                "\nEarly stopping triggered."
            )
            break

    print("\nFine-tuning completed.")
    print(
        f"Best validation accuracy: "
        f"{best_accuracy * 100:.2f}%"
    )


if __name__ == "__main__":
    main()