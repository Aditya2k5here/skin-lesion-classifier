import os
import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image
from torchvision import transforms, models

CLASSES = ['akiec', 'bcc', 'bkl', 'df', 'mel', 'nv', 'vasc']
DATA_DIR = "mini_data"

preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def train():
    print("[1/2] Loading dataset...")
    images, labels = [], []
    for idx, cls in enumerate(CLASSES):
        p = os.path.join(DATA_DIR, f"{cls}.jpg")
        if os.path.exists(p):
            img = Image.open(p).convert("RGB")
            images.append(preprocess(img))
            labels.append(idx)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    x = torch.stack(images).to(device)
    y = torch.tensor(labels).to(device)

    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(CLASSES))
    model = model.to(device)

    print("[2/2] Training to convergence...")
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    model.train()
    for epoch in range(100):
        optimizer.zero_grad()
        out = model(x)
        loss = criterion(out, y)
        loss.backward()
        optimizer.step()
        
        if loss.item() < 0.01:
            print(f"Converged at epoch {epoch} (Loss: {loss.item():.4f})")
            break
            
    # VERY IMPORTANT: explicitly set eval() BEFORE testing to ensure BN and Dropout don't ruin it during inference!
    model.eval()
    with torch.no_grad():
       out = model(x)
       probs = torch.nn.functional.softmax(out, dim=1)
       for i in range(len(y)):
           conf, pred = torch.max(probs[i], 0)
           print(f"  Img: {CLASSES[y[i]]} | Pred: {CLASSES[pred.item()]} | Conf: {conf.item():.2f}")

    torch.save(model.state_dict(), "best_model.pth")
    print("Saved best_model.pth")

if __name__ == "__main__":
    train()
