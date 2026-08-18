"""
DermaCare ML Model Architecture

Implements MobileNetV2-based transfer learning for skin condition classification.
Uses pre-trained ImageNet weights for faster convergence and better generalization.

Author: DermaCare Team
Version: 1.0.0
"""

import torch
import torch.nn as nn
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights


def get_model(num_classes: int = 7) -> nn.Module:
    """
    Create and adapt MobileNetV2 model for skin condition classification.

    Uses transfer learning with ImageNet pre-trained weights, replacing the
    final classification layer for the target number of skin condition classes.

    Args:
        num_classes: Number of output classes (default: 7 for HAM10000)

    Returns:
        nn.Module: MobileNetV2 model adapted for skin classification

    Model Details:
        - Base: MobileNetV2 (lightweight, ~3.5M parameters)
        - Pre-training: ImageNet (1000 classes)
        - Output layer: Custom linear classifier + dropout
        - Dropout: 0.4 for regularization
        - Input: 3-channel RGB images (normalized with ImageNet stats)
        - Output: num_classes probabilities

    Example:
        >>> model = get_model(num_classes=7)
        >>> input_tensor = torch.randn(1, 3, 224, 224)
        >>> output = model(input_tensor)
        >>> print(output.shape)  # torch.Size([1, 7])
    """

    # Load pre-trained MobileNetV2 from ImageNet
    weights = MobileNet_V2_Weights.DEFAULT
    model = mobilenet_v2(weights=weights)

    # Get number of input features for the classifier
    in_features = model.classifier[1].in_features

    # Replace final classifier layer with custom head for our classes
    # Original: Linear(1280, 1000)
    # Custom:   Dropout(0.4) -> Linear(1280, num_classes)
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.4, inplace=True),
        nn.Linear(in_features, num_classes)
    )

    return model

