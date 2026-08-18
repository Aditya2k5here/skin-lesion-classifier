import sys
import os
import torch
import torch.nn.functional as F
from PIL import Image
from backend.ml.inference import preprocess, CLASSES, device
from backend.ml.model import get_model

def main():
    model_path = "backend/ml/best_model.pth"
    model = get_model(num_classes=7)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    
    # Random tensor
    tensor = torch.randn(1, 3, 224, 224).to(device)
    
    with torch.no_grad():
        out = model(tensor)
        probs = F.softmax(out[0], dim=0)
        
    print(f"Logits: {out[0]}")
    print(f"Probs: {probs}")
    conf, idx = torch.max(probs, 0)
    print(f"Prediction: {CLASSES[idx.item()]} with confidence {conf.item():.4f}")

if __name__ == "__main__":
    main()
