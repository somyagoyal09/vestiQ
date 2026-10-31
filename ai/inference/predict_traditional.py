from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms


MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "models"
    / "vestiq_traditional_efficientnet_b0.pth"
)

IMAGE_SIZE = 224

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


def load_traditional_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Traditional model not found. "
            "Expected: ai/models/vestiq_traditional_efficientnet_b0.pth"
        )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=DEVICE,
    )

    class_names = checkpoint["class_names"]

    model = models.efficientnet_b0(
        weights=None
    )

    model.classifier[1] = nn.Linear(
        model.classifier[1].in_features,
        len(class_names),
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model = model.to(DEVICE)
    model.eval()

    return model, class_names


transform = transforms.Compose([
    transforms.Resize(
        (IMAGE_SIZE, IMAGE_SIZE)
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        [0.485, 0.456, 0.406],
        [0.229, 0.224, 0.225],
    ),
])


def predict_traditional(image_path: str):
    model, class_names = load_traditional_model()

    image = Image.open(
        image_path
    ).convert("RGB")

    image_tensor = transform(image)
    image_tensor = image_tensor.unsqueeze(0)
    image_tensor = image_tensor.to(DEVICE)

    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.softmax(
            outputs,
            dim=1,
        )
        confidence, predicted_index = probabilities.max(
            dim=1
        )

    predicted_class = class_names[
        predicted_index.item()
    ]

    return {
        "category": predicted_class,
        "confidence": round(
            confidence.item() * 100,
            2,
        ),
    }
