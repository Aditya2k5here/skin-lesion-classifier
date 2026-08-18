"""
DermaCare — Fast Training Script (Quick Mode)

Trains on the REAL dataset but with fewer epochs and smaller sample for quick iteration.
Use this for testing; use train.py for the full training run.

Usage:
    python -m backend.ml.fast_train       (from project root)
    python backend/ml/fast_train.py       (standalone)
"""

import os
import sys
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler, Subset
from collections import Counter
import random

# Handle imports
try:
    from backend.ml.dataset import SkinLesionDataset, get_transforms
    from backend.ml.model import get_model
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from backend.ml.dataset import SkinLesionDataset, get_transforms
    from backend.ml.model import get_model

MODEL_PATH = os.path.join(os.path.dirname(__file__), "best_model.pth")
DATASET_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dataset"))

# Quick training config
MAX_SAMPLES_PER_CLASS = 300   # cap per class for speed
EPOCHS = 6
BATCH_SIZE = 32
LEARNING_RATE = 5e-4


def balanced_subset(dataset, max_per_class):
    """Create a balanced subset with at most max_per_class images per class."""
    class_indices = {}
    for i, (_, label) in enumerate(dataset.samples):
        class_indices.setdefault(label, []).append(i)

    selected = []
    for label, indices in class_indices.items():
        random.shuffle(indices)
        selected.extend(indices[:max_per_class])

    random.shuffle(selected)
    return selected


def fast_train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n{'='*60}")
    print(f"  [FAST] DermaCare — Fast Training (Quick Mode)")
    print(f"{'='*60}")
    print(f"  Device: {device}")
    print(f"  Max per class: {MAX_SAMPLES_PER_CLASS}")
    print(f"  Epochs: {EPOCHS}")

    train_dir = os.path.join(DATASET_PATH, "train")
    val_dir = os.path.join(DATASET_PATH, "val")

    if not os.path.exists(train_dir):
        print(f"\n  [ERROR] Dataset not found at {train_dir}")
        print(f"     Run: python organize_data.py")
        sys.exit(1)

    # Load full dataset
    full_train = SkinLesionDataset(train_dir, transform=get_transforms(is_train=True))
    val_dataset = SkinLesionDataset(val_dir, transform=get_transforms(is_train=False))

    class_names = full_train.classes
    num_classes = len(class_names)
    print(f"  Classes: {class_names}")

    # Create balanced subset
    subset_indices = balanced_subset(full_train, MAX_SAMPLES_PER_CLASS)
    train_subset = Subset(full_train, subset_indices)
    print(f"  Training on {len(train_subset)} images (balanced subset)")
    print(f"  Validating on {len(val_dataset)} images")

    # Compute sample weights for the subset
    subset_labels = [full_train.samples[i][1] for i in subset_indices]
    counts = Counter(subset_labels)
    sample_weights = [1.0 / counts[label] for label in subset_labels]
    sampler = WeightedRandomSampler(sample_weights, len(sample_weights), replacement=True)

    train_loader = DataLoader(train_subset, batch_size=BATCH_SIZE, sampler=sampler, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    # Model
    print(f"\n  [MODEL] Initializing model...")
    model = get_model(num_classes=num_classes).to(device)

    # Weighted loss
    total = len(subset_labels)
    class_weights = torch.tensor([
        total / (num_classes * max(counts.get(i, 1), 1))
        for i in range(num_classes)
    ], dtype=torch.float32).to(device)

    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)

    # Freeze backbone for first 2 epochs
    freeze_epochs = 2
    best_acc = 0.0
    start = time.time()

    print(f"\n  [TIME] Training...\n")

    for epoch in range(EPOCHS):
        if epoch < freeze_epochs:
            for p in model.features.parameters():
                p.requires_grad = False
            if epoch == 0:
                print(f"  [LOCK] Backbone frozen (epochs 1-{freeze_epochs})")
        elif epoch == freeze_epochs:
            for p in model.features.parameters():
                p.requires_grad = True
            print(f"  [UNLOCK] Backbone unfrozen")

        # Train
        model.train()
        train_loss = 0.0
        correct = 0
        total_samples = 0

        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            correct += (preds == labels).sum().item()
            total_samples += labels.size(0)

        train_acc = correct / total_samples

        # Validate
        model.eval()
        val_correct = 0
        val_total = 0
        class_correct = Counter()
        class_total = Counter()

        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                _, preds = torch.max(outputs, 1)
                val_correct += (preds == labels).sum().item()
                val_total += labels.size(0)
                for p, t in zip(preds.cpu().numpy(), labels.cpu().numpy()):
                    class_total[t] += 1
                    if p == t:
                        class_correct[t] += 1

        val_acc = val_correct / val_total
        per_class = [class_correct.get(i, 0) / max(class_total.get(i, 0), 1) for i in range(num_classes)]
        balanced_acc = sum(per_class) / len(per_class)

        saved = ""
        if balanced_acc > best_acc:
            best_acc = balanced_acc
            torch.save(model.state_dict(), MODEL_PATH)
            saved = " [SAVE] SAVED"

        print(f"  Epoch {epoch+1}/{EPOCHS} | "
              f"Train: {train_acc:.1%} | "
              f"Val: {val_acc:.1%} | "
              f"Balanced: {balanced_acc:.1%}{saved}")

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"  [OK] Done in {elapsed/60:.1f} min | Best balanced acc: {best_acc:.1%}")
    print(f"  Model: {MODEL_PATH}")
    print(f"{'='*60}\n")

    # Print per-class breakdown
    print(f"  Per-class validation accuracy:")
    for i, name in enumerate(class_names):
        ct = class_total.get(i, 0)
        cc = class_correct.get(i, 0)
        acc = cc / ct if ct > 0 else 0
        bar = "#" * max(1, int(acc * 20))
        print(f"    {name:>6s}: {acc:5.1%}  {bar}  ({cc}/{ct})")


if __name__ == "__main__":
    fast_train()
