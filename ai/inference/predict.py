from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms


# ============================================================
# PATHS
# ============================================================

AI_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = AI_ROOT / "models"

WESTERN_MODEL_PATH = (
    MODELS_DIR / "vestiq_efficientnet_b0.pth"
)

TRADITIONAL_MODEL_PATH = (
    MODELS_DIR / "vestiq_traditional_efficientnet_b0.pth"
)


# ============================================================
# SETTINGS
# ============================================================

IMAGE_SIZE = 224

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# IMAGE TRANSFORM
# ============================================================

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


# ============================================================
# MODEL LOADING
# ============================================================

def load_checkpoint(model_path: Path):
    """
    Load a trained model checkpoint.
    """

    if not model_path.exists():
        return None

    return torch.load(
        model_path,
        map_location=DEVICE,
    )


def build_model(checkpoint):
    """
    Recreate EfficientNet-B0 using the
    class names stored inside the checkpoint.
    """

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


# ============================================================
# IMAGE PREPARATION
# ============================================================

def prepare_image(image_path: str):
    """
    Load and preprocess image for EfficientNet-B0.
    """

    image = Image.open(
        image_path
    ).convert("RGB")

    image_tensor = transform(image)

    return image_tensor.unsqueeze(0).to(
        DEVICE
    )


# ============================================================
# GENERIC PREDICTION
# ============================================================

def predict_with_model(
    model,
    class_names,
    image_tensor,
):
    """
    Run prediction using a loaded model.
    """

    with torch.no_grad():

        outputs = model(
            image_tensor
        )

        probabilities = torch.softmax(
            outputs,
            dim=1,
        )

        confidence, predicted_index = (
            probabilities.max(dim=1)
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


# ============================================================
# WESTERN MODEL
# ============================================================

def predict_western(
    image_path: str,
):
    """
    Predict using the Western Fashionpedia model.
    """

    checkpoint = load_checkpoint(
        WESTERN_MODEL_PATH
    )

    if checkpoint is None:
        raise FileNotFoundError(
            "Western model not found: "
            f"{WESTERN_MODEL_PATH}"
        )

    model, class_names = build_model(
        checkpoint
    )

    image_tensor = prepare_image(
        image_path
    )

    result = predict_with_model(
        model,
        class_names,
        image_tensor,
    )

    result["domain"] = "western"

    return result


# ============================================================
# TRADITIONAL MODEL
# ============================================================

def predict_traditional(
    image_path: str,
):
    """
    Predict using the Traditional/Indian
    clothing model.
    """

    checkpoint = load_checkpoint(
        TRADITIONAL_MODEL_PATH
    )

    if checkpoint is None:
        raise FileNotFoundError(
            "Traditional model not found: "
            f"{TRADITIONAL_MODEL_PATH}"
        )

    model, class_names = build_model(
        checkpoint
    )

    image_tensor = prepare_image(
        image_path
    )

    result = predict_with_model(
        model,
        class_names,
        image_tensor,
    )

    result["domain"] = "traditional"

    return result


# ============================================================
# MAIN PREDICTION FUNCTION
# ============================================================

def predict_clothing(
    image_path: str,
    domain: str = "auto",
):
    """
    Predict clothing category.

    domain:
        auto
        western
        traditional

    If a specific domain is provided,
    only that model is used.

    In auto mode, all available models are
    evaluated and the highest-confidence result
    is returned.
    """

    domain = (
        domain or "auto"
    ).strip().lower()

    valid_domains = {
        "auto",
        "western",
        "traditional",
    }

    if domain not in valid_domains:
        raise ValueError(
            "domain must be one of: "
            "auto, western, traditional"
        )

    # --------------------------------------------------------
    # WESTERN ONLY
    # --------------------------------------------------------

    if domain == "western":

        return predict_western(
            image_path
        )

    # --------------------------------------------------------
    # TRADITIONAL ONLY
    # --------------------------------------------------------

    if domain == "traditional":

        return predict_traditional(
            image_path
        )

    # --------------------------------------------------------
    # AUTO MODE
    # --------------------------------------------------------

    predictions = []

    if WESTERN_MODEL_PATH.exists():

        predictions.append(
            predict_western(
                image_path
            )
        )

    if TRADITIONAL_MODEL_PATH.exists():

        predictions.append(
            predict_traditional(
                image_path
            )
        )

    if not predictions:

        raise FileNotFoundError(
            "No clothing model was found."
        )

    best_prediction = max(
        predictions,
        key=lambda item: item["confidence"],
    )

    return best_prediction


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    image_path = input(
        "Enter image path: "
    ).strip()

    result = predict_clothing(
        image_path,
        domain="auto",
    )

    print("\nPrediction:")
    print(
        "Domain:",
        result["domain"],
    )
    print(
        "Category:",
        result["category"],
    )
    print(
        "Confidence:",
        f"{result['confidence']}%",
    )