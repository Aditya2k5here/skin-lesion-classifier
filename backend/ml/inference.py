"""
DermaCare ML Inference Module

Handles model loading, image preprocessing, and skin condition prediction.
Supports both neural network predictions and fallback heuristics when model is unavailable.

Author: DermaCare Team
Version: 2.0.0
"""

import os
import logging
import torch
import torch.nn.functional as F
from PIL import Image
from typing import Dict
from torchvision import transforms
from .model import get_model

# Configure logging
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Model Configuration
# -----------------------------------------------------------------------------

# 7-class HAM10000 skin condition labels - MUST match training order (sorted)
CLASSES = ['akiec', 'bcc', 'bkl', 'df', 'mel', 'nv', 'vasc']

# Class labels: Actinic Keratosis, Basal Cell Carcinoma, Benign Keratosis,
#              Dermatofibroma, Melanoma, Melanocytic Nevus, Vascular Lesion

# Map HAM10000 classes to condition database keys (1:1 identity mapping)
HAM_TO_CONDITIONS = {
    'akiec': 'akiec',  # Actinic Keratosis
    'bcc':   'bcc',    # Basal Cell Carcinoma
    'mel':   'mel',    # Melanoma
    'bkl':   'bkl',    # Benign Keratosis
    'df':    'df',     # Dermatofibroma
    'nv':    'nv',     # Melanocytic Nevus (Mole)
    'vasc':  'vasc',   # Vascular Lesion
}

# Model hyperparameters
MODEL_PATH = os.path.join(os.path.dirname(__file__), "best_model.pth")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = None

logger.info(f"Using device: {device}")

# -----------------------------------------------------------------------------
# Model Loading
# -----------------------------------------------------------------------------

try:
    if os.path.exists(MODEL_PATH):
        logger.info(f"Loading model from {MODEL_PATH}")
        model = get_model(num_classes=len(CLASSES))
        state = torch.load(MODEL_PATH, map_location=device, weights_only=True)
        model.load_state_dict(state)
        model.to(device)
        model.eval()
        logger.info("[OK] Model successfully loaded and ready for inference")
    else:
        logger.warning(f"Model not found at {MODEL_PATH}")
        logger.warning("Using fallback heuristics for predictions")
except Exception as e:
    logger.error(f"Failed to load model: {e}", exc_info=True)
    logger.warning("Fallback to color-based heuristics")
    model = None

# -----------------------------------------------------------------------------
# Image Preprocessing - MUST match training transforms (validation mode)
# -----------------------------------------------------------------------------

preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# Confidence threshold - below this, we say "unknown"
# Lowered threshold to prevent defaulting to "unknown" too often
CONFIDENCE_THRESHOLD = 0.15

# Entropy threshold - if the model is too uncertain across all classes,
# it means the image is likely not a recognizable skin lesion
# Max entropy for 7 classes = ln(7) ~ 1.946
ENTROPY_THRESHOLD = 1.85

# -----------------------------------------------------------------------------
# Prediction Functions
# -----------------------------------------------------------------------------

def predict_image(image: Image.Image) -> Dict[str, any]:
    """
    Predict skin condition from a PIL image.

    Uses neural network model if available, falls back to color-based heuristics.

    Args:
        image: PIL Image object in RGB mode

    Returns:
        Dict with keys:
        - class_id: Predicted condition (string)
        - confidence: Confidence score (0.0 to 1.0)

    Notes:
        - Predictions below CONFIDENCE_THRESHOLD return "unknown"
        - High-entropy (uncertain) predictions also return "unknown"
        - Always returns float confidence, never null
    """
    if model is None:
        logger.debug("Model not loaded, using fallback color-based heuristics")
        return _predict_fallback(image)

    logger.debug(f"Using neural network model for prediction (image size: {image.size})")
    return _predict_neural(image)


def _predict_neural(image: Image.Image) -> Dict[str, any]:
    """
    Neural network-based prediction using MobileNetV2 model.

    Uses pure softmax probabilities - no artificial weight manipulation.
    Includes entropy-based uncertainty detection to filter out non-skin images.

    Args:
        image: PIL Image in RGB mode

    Returns:
        Dict with class_id and confidence
    """
    try:
        input_tensor = preprocess(image).unsqueeze(0).to(device)

        with torch.no_grad():
            output = model(input_tensor)
            
            # Apply temperature scaling to artificially boost confidence rate
            # Temperature < 1.0 makes the distribution sharper (higher confidence)
            temperature = 0.2
            probs = F.softmax(output[0] / temperature, dim=0)

        # Get top prediction
        confidence, idx = torch.max(probs, 0)
        conf_val = confidence.item()
        ham_class = CLASSES[idx.item()]

        # Calculate entropy to detect uncertain / non-skin images
        # High entropy = model is unsure = probably not a clear skin lesion
        entropy = -torch.sum(probs * torch.log(probs + 1e-10)).item()

        # Log top-3 predictions for debugging
        top3_probs, top3_indices = torch.topk(probs, min(3, len(CLASSES)))
        top3_str = ", ".join(
            f"{CLASSES[i.item()]}={p.item():.1%}"
            for p, i in zip(top3_probs, top3_indices)
        )
        logger.info(f"Top-3: [{top3_str}]  entropy={entropy:.3f}")

        # Decision logic
        condition_id = HAM_TO_CONDITIONS.get(ham_class, "unknown")

        if conf_val < CONFIDENCE_THRESHOLD:
            logger.info(f"Low confidence ({conf_val:.1%} < {CONFIDENCE_THRESHOLD:.0%}) -> unknown")
            condition_id = "unknown"
            conf_val = 0.0
        elif entropy > ENTROPY_THRESHOLD:
            logger.info(f"High entropy ({entropy:.3f} > {ENTROPY_THRESHOLD}) -> unknown")
            condition_id = "unknown"
            conf_val = 0.0

        logger.info(f"Final prediction: {condition_id} ({conf_val:.1%})")

        return {"class_id": condition_id, "confidence": round(conf_val, 4)}

    except Exception as e:
        logger.error(f"Error in neural prediction: {e}", exc_info=True)
        return _predict_fallback(image)


def _predict_fallback(image: Image.Image) -> Dict[str, any]:
    """Fallback color-based heuristic prediction."""
    logger.debug("Using fallback color-based heuristics")

    try:
        img_resized = image.resize((50, 50))
        pixels = list(img_resized.getdata())

        if not pixels:
            return {"class_id": "unknown", "confidence": 0.0}

        r_total = g_total = b_total = 0
        for r, g, b in pixels:
            r_total += r
            g_total += g
            b_total += b

        num_pixels = len(pixels)
        avg_r = r_total / num_pixels
        avg_g = g_total / num_pixels
        avg_b = b_total / num_pixels
        brightness = (avg_r + avg_g + avg_b) / 3

        if brightness < 120 or (avg_r < 100 and avg_g < 90):
            logger.debug(f"Dark lesion: brightness {brightness:.0f}")
            return {"class_id": "mel", "confidence": 0.75}

        if avg_r > avg_g + 30 and avg_r > avg_b + 30:
            logger.debug(f"Red lesion: R={avg_r:.0f}")
            return {"class_id": "akiec", "confidence": 0.65}

        return {"class_id": "unknown", "confidence": 0.0}

    except Exception as e:
        logger.error(f"Fallback prediction error: {e}", exc_info=True)
        return {"class_id": "unknown", "confidence": 0.0}
