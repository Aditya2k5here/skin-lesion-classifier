"""
DermaCare Dataset Utilities

PyTorch Dataset class for skin lesion images and data augmentation/normalization
transforms for training and validation.

Author: DermaCare Team
Version: 2.0.0
"""

import os
import logging
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class SkinLesionDataset(Dataset):
    """
    PyTorch Dataset for Skin Lesion Images (e.g., HAM10000).

    Expects directory structure:
        root_dir/
        ├── akiec/
        │   ├── image1.jpg
        │   ├── image2.jpg
        ├── bcc/
        │   ├── image3.jpg
        ├── ...

    Attributes:
        root_dir: Path to dataset root directory
        transform: Optional image transformations to apply
        classes: Sorted list of class names (directories)
        class_to_idx: Dictionary mapping class names to indices
        samples: List of (image_path, label) tuples
    """

    def __init__(self, root_dir: str, transform=None):
        """
        Initialize the dataset.

        Args:
            root_dir: Path to directory containing class subdirectories
            transform: Optional torchvision transforms to apply
        """
        self.root_dir = root_dir
        self.transform = transform

        # Discover classes from subdirectories (only actual directories)
        self.classes = sorted([
            d for d in os.listdir(root_dir)
            if os.path.isdir(os.path.join(root_dir, d))
        ])
        self.class_to_idx = {cls_name: i for i, cls_name in enumerate(self.classes)}

        # Build list of samples
        self.samples = []
        skipped = 0
        for cls_name in self.classes:
            cls_dir = os.path.join(root_dir, cls_name)
            for img_name in os.listdir(cls_dir):
                if img_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
                    img_path = os.path.join(cls_dir, img_name)
                    self.samples.append((img_path, self.class_to_idx[cls_name]))
                else:
                    skipped += 1

        logger.info(f"Loaded {len(self.samples)} images from {len(self.classes)} classes")
        if skipped > 0:
            logger.debug(f"Skipped {skipped} non-image files")

    def __len__(self) -> int:
        """Return total number of samples."""
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple:
        """
        Get a sample.

        Args:
            idx: Index of sample

        Returns:
            Tuple of (image_tensor, label)
        """
        img_path, label = self.samples[idx]
        try:
            image = Image.open(img_path).convert("RGB")
        except Exception as e:
            logger.warning(f"Failed to load {img_path}: {e}. Using blank image.")
            image = Image.new("RGB", (224, 224), (128, 128, 128))

        if self.transform:
            image = self.transform(image)

        return image, label


def get_transforms(is_train: bool = True) -> transforms.Compose:
    """
    Get data augmentation and normalization transforms.

    Args:
        is_train: If True, apply aggressive augmentation for training.
                 If False, apply only normalization for validation/inference.

    Returns:
        transforms.Compose with appropriate pipeline

    Training Augmentations (aggressive for skin lesion diversity):
        - RandomResizedCrop: Crop and resize to 224x224 (scale 0.7-1.0)
        - RandomHorizontalFlip: 50% chance
        - RandomVerticalFlip: 50% chance (skin lesions have no "up")
        - RandomRotation: ±30 degrees
        - ColorJitter: brightness, contrast, saturation, hue
        - RandomAffine: slight shear for perspective variation
        - Normalize: ImageNet statistics

    Validation Transforms:
        - Resize to 256
        - CenterCrop to 224
        - Normalize: ImageNet statistics
    """

    if is_train:
        return transforms.Compose([
            transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.5),
            transforms.RandomRotation(30),
            transforms.ColorJitter(
                brightness=0.2,
                contrast=0.2,
                saturation=0.2,
                hue=0.05
            ),
            transforms.RandomAffine(
                degrees=0,
                shear=10,
                scale=(0.9, 1.1)
            ),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
    else:
        return transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
