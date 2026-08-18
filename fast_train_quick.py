#!/usr/bin/env python3
"""
Fast training script - trains on a sample of the full dataset for quick model validation.
Useful for testing the pipeline before full training.
"""
import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from backend.ml.dataset import SkinLesionDataset, get_transforms
from backend.ml.model import get_model

MODEL_PATH = os.path.join(os.path.dirname(__file__), "backend", "ml", "best_model.pth")
DATASET_PATH = os.path.join(os.path.dirname(__file__), "backend", "dataset")

def train_fast():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n{'='*60}")
    print(f"🚀 DermaCare - Fast Training Mode")
    print(f"{'='*60}")
    print(f"Device: {device}")
    print(f"Dataset path: {DATASET_PATH}")

    # Check dataset
    train_dir = os.path.join(DATASET_PATH, "train")
    val_dir = os.path.join(DATASET_PATH, "val")

    if not os.path.exists(train_dir):
        print("❌ Training dataset not found!")
        print("Please run: python organize_data.py")
        sys.exit(1)

    # Load datasets
    print("\n📂 Loading training dataset...")
    full_train_dataset = SkinLesionDataset(train_dir, transform=get_transforms(is_train=True))
    print(f"   Total training images: {len(full_train_dataset)}")

    # For fast training, use a sample
    sample_size = min(2000, len(full_train_dataset))  # Use up to 2000 images for speed
    train_dataset, _ = random_split(full_train_dataset, [sample_size, len(full_train_dataset) - sample_size])

    if os.path.exists(val_dir):
        val_dataset = SkinLesionDataset(val_dir, transform=get_transforms(is_train=False))
        print(f"   Validation images: {len(val_dataset)}")
    else:
        val_dataset = None
        print("   No validation dataset found")

    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False, num_workers=0) if val_dataset else None

    # Model setup
    print("\n🧠 Initializing model...")
    num_classes = len(full_train_dataset.classes)
    print(f"   Classes: {full_train_dataset.classes}")

    model = get_model(num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # Training loop
    print(f"\n⏱️  Training for 4 epochs...")
    print(f"{'='*60}")

    best_acc = 0.0

    for epoch in range(4):
        # Train
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0

        print(f"\nEpoch {epoch+1}/4")
        for batch_idx, (inputs, labels) in enumerate(train_loader):
            inputs, labels = inputs.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            train_total += labels.size(0)
            train_correct += (predicted == labels).sum().item()

            if (batch_idx + 1) % max(1, len(train_loader) // 5) == 0:
                progress = (batch_idx + 1) / len(train_loader) * 100
                print(f"  Train [{progress:.0f}%] Loss: {train_loss/(batch_idx+1):.4f}")

        train_acc = 100 * train_correct / train_total
        print(f"  Train Accuracy: {train_acc:.1f}%")

        # Validate
        if val_loader:
            model.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0

            with torch.no_grad():
                for inputs, labels in val_loader:
                    inputs, labels = inputs.to(device), labels.to(device)
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)

                    val_loss += loss.item()
                    _, predicted = torch.max(outputs.data, 1)
                    val_total += labels.size(0)
                    val_correct += (predicted == labels).sum().item()

            val_acc = 100 * val_correct / val_total
            print(f"  Val Accuracy: {val_acc:.1f}%")

            if val_acc > best_acc:
                best_acc = val_acc
                torch.save(model.state_dict(), MODEL_PATH)
                print(f"  ✓ Saved best model!")

    # Save final model
    torch.save(model.state_dict(), MODEL_PATH)
    print(f"\n{'='*60}")
    print(f"✅ Training complete!")
    print(f"Model saved to: {MODEL_PATH}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    train_fast()
