"""
DermaCare Model Training - Full Dataset Trainer

Trains MobileNetV2 on the real HAM10000 + ISIC2019 dataset (~28K images).
Handles severe class imbalance via weighted sampling + weighted loss.
Uses cosine-annealing LR, aggressive augmentation, and early stopping.

Usage:
    python -m backend.ml.train            (from project root)
    python backend/ml/train.py            (standalone)

Author: DermaCare Team
"""

import os
import sys
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler
from collections import Counter

# Handle imports whether run as module or standalone
try:
    from backend.ml.dataset import SkinLesionDataset, get_transforms
    from backend.ml.model import get_model
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from backend.ml.dataset import SkinLesionDataset, get_transforms
    from backend.ml.model import get_model

MODEL_PATH = os.path.join(os.path.dirname(__file__), "best_model.pth")
DATASET_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dataset"))

# -----------------------------------------------------------------------------
# Training Configuration
# -----------------------------------------------------------------------------

CONFIG = {
    "epochs": 15,
    "batch_size": 32,
    "learning_rate": 3e-4,
    "weight_decay": 1e-4,
    "patience": 5,          # early stopping patience
    "num_workers": 0,       # 0 for Windows compatibility
    "freeze_epochs": 3,     # freeze backbone for first N epochs (transfer learning warmup)
}


def compute_class_weights(labels, num_classes):
    """Compute inverse-frequency class weights for CrossEntropyLoss."""
    counts = Counter(labels)
    total = float(sum(counts.values()))
    weights = []
    for i in range(num_classes):
        c = counts.get(i, 1)
        # inverse frequency, clamped to avoid extreme weights
        w = total / (num_classes * c)
        w = min(w, 10.0)  # cap at 10x
        weights.append(w)
    return torch.tensor(weights, dtype=torch.float32)


def compute_sample_weights(dataset):
    """Compute per-sample weights for WeightedRandomSampler."""
    labels = [label for _, label in dataset.samples]
    counts = Counter(labels)
    sample_weights = [1.0 / counts[label] for label in labels]
    return sample_weights, labels


def print_dataset_stats(dataset, name):
    """Print per-class image counts."""
    labels = [label for _, label in dataset.samples]
    counts = Counter(labels)
    print(f"\n  [STATS] {name} Dataset ({len(dataset)} images):")
    for cls_name in dataset.classes:
        idx = dataset.class_to_idx[cls_name]
        count = counts.get(idx, 0)
        bar = "#" * max(1, count // 200)
        print(f"     {cls_name:>6s}: {count:>5d}  {bar}")


def evaluate(model, loader, criterion, device, class_names):
    """Run validation and return loss, accuracy, and per-class accuracy."""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    class_correct = Counter()
    class_total = Counter()

    with torch.no_grad():
        for inputs, labels in loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

            for pred, true in zip(preds.cpu().numpy(), labels.cpu().numpy()):
                class_total[true] += 1
                if pred == true:
                    class_correct[true] += 1

    avg_loss = running_loss / total
    accuracy = correct / total

    print(f"     Per-class accuracy:")
    per_class_accs = []
    for i, name in enumerate(class_names):
        ct = class_total.get(i, 0)
        cc = class_correct.get(i, 0)
        acc = cc / ct if ct > 0 else 0.0
        per_class_accs.append(acc)
        status = "[Y]" if acc >= 0.5 else "[N]"
        print(f"       {status} {name:>6s}: {acc:6.1%}  ({cc}/{ct})")

    balanced_acc = sum(per_class_accs) / len(per_class_accs)
    print(f"     Balanced Accuracy: {balanced_acc:.1%}")

    return avg_loss, accuracy, balanced_acc


def train_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"\n{'='*64}")
    print(f"  [TRAIN] DermaCare - Full Dataset Training")
    print(f"{'='*64}")
    print(f"  Device:       {device}")
    print(f"  Dataset:      {DATASET_PATH}")
    print(f"  Model save:   {MODEL_PATH}")
    print(f"  Epochs:       {CONFIG['epochs']}")
    print(f"  Batch size:   {CONFIG['batch_size']}")
    print(f"  Learning rate: {CONFIG['learning_rate']}")

    # -- Load datasets --
    train_dir = os.path.join(DATASET_PATH, "train")
    val_dir = os.path.join(DATASET_PATH, "val")

    if not os.path.exists(train_dir):
        print(f"\n  [ERROR] Training directory not found: {train_dir}")
        print(f"     Run: python organize_data.py")
        sys.exit(1)

    train_dataset = SkinLesionDataset(train_dir, transform=get_transforms(is_train=True))
    val_dataset = SkinLesionDataset(val_dir, transform=get_transforms(is_train=False))

    if len(train_dataset) == 0:
        print("  [ERROR] Training dataset is empty!")
        sys.exit(1)

    class_names = train_dataset.classes
    num_classes = len(class_names)
    print(f"  Classes:      {num_classes} > {class_names}")

    print_dataset_stats(train_dataset, "Train")
    print_dataset_stats(val_dataset, "Val")

    # -- Weighted sampling (handles class imbalance) --
    sample_weights, all_labels = compute_sample_weights(train_dataset)
    sampler = WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(sample_weights),
        replacement=True
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=CONFIG["batch_size"],
        sampler=sampler,
        num_workers=CONFIG["num_workers"],
        pin_memory=(device.type == "cuda")
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=CONFIG["batch_size"],
        shuffle=False,
        num_workers=CONFIG["num_workers"],
        pin_memory=(device.type == "cuda")
    )

    # -- Model --
    print(f"\n  [MODEL] Initializing MobileNetV2 (transfer learning)...")
    model = get_model(num_classes=num_classes).to(device)

    # -- Weighted loss (handles class imbalance in loss too) --
    class_weights = compute_class_weights(all_labels, num_classes).to(device)
    print(f"  Class weights: {[f'{w:.2f}' for w in class_weights.tolist()]}")
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    # -- Optimizer with weight decay --
    optimizer = optim.AdamW(
        model.parameters(),
        lr=CONFIG["learning_rate"],
        weight_decay=CONFIG["weight_decay"]
    )

    # -- Cosine annealing scheduler --
    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=CONFIG["epochs"],
        eta_min=1e-6
    )

    # -- Training loop --
    best_balanced_acc = 0.0
    best_epoch = 0
    patience_counter = 0
    start_time = time.time()

    print(f"\n{'='*64}")
    print(f"  [TIME]  Starting training...")
    print(f"{'='*64}")

    for epoch in range(CONFIG["epochs"]):
        epoch_start = time.time()
        current_lr = optimizer.param_groups[0]['lr']
        print(f"\n  -- Epoch {epoch+1}/{CONFIG['epochs']} (lr={current_lr:.2e}) --")

        # Freeze backbone for warmup epochs (only train classifier head)
        if epoch < CONFIG["freeze_epochs"]:
            for param in model.features.parameters():
                param.requires_grad = False
            if epoch == 0:
                print(f"     [LOCK] Backbone frozen (warmup phase, epochs 1-{CONFIG['freeze_epochs']})")
        elif epoch == CONFIG["freeze_epochs"]:
            for param in model.features.parameters():
                param.requires_grad = True
            print(f"     [UNLOCK] Backbone unfrozen - fine-tuning all layers")

        # -- Train phase --
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for batch_idx, (inputs, labels) in enumerate(train_loader):
            inputs, labels = inputs.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

            # Progress indicator every 25%
            if (batch_idx + 1) % max(1, len(train_loader) // 4) == 0:
                progress = (batch_idx + 1) / len(train_loader) * 100
                batch_acc = correct / total * 100
                print(f"     [{progress:5.1f}%] loss={running_loss/total:.4f}  acc={batch_acc:.1f}%")

        train_loss = running_loss / total
        train_acc = correct / total
        print(f"  [TRAIN] Train - Loss: {train_loss:.4f}  Acc: {train_acc:.1%}")

        # -- Validation phase --
        print(f"  [STATS] Validating...")
        val_loss, val_acc, balanced_acc = evaluate(model, val_loader, criterion, device, class_names)
        print(f"  [VAL] Val   - Loss: {val_loss:.4f}  Acc: {val_acc:.1%}  Balanced: {balanced_acc:.1%}")

        epoch_time = time.time() - epoch_start
        print(f"  [TIME]  Epoch time: {epoch_time:.0f}s")

        # -- Step scheduler --
        scheduler.step()

        # -- Save best model (by balanced accuracy) --
        if balanced_acc > best_balanced_acc:
            best_balanced_acc = balanced_acc
            best_epoch = epoch + 1
            patience_counter = 0
            torch.save(model.state_dict(), MODEL_PATH)
            print(f"  [SAVE] NEW BEST! Saved model (balanced acc: {balanced_acc:.1%})")
        else:
            patience_counter += 1
            print(f"  [WAIT] No improvement ({patience_counter}/{CONFIG['patience']})")

        # -- Early stopping --
        if patience_counter >= CONFIG["patience"]:
            print(f"\n  [STOP] Early stopping triggered after {epoch+1} epochs")
            break

    total_time = time.time() - start_time
    print(f"\n{'='*64}")
    print(f"  [OK] Training complete!")
    print(f"  Best balanced accuracy: {best_balanced_acc:.1%} (epoch {best_epoch})")
    print(f"  Total time: {total_time/60:.1f} minutes")
    print(f"  Model saved to: {MODEL_PATH}")
    print(f"{'='*64}\n")


if __name__ == "__main__":
    train_model()
