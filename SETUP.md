# DermaCare - Setup & Deployment Guide

Complete guide for setting up, running, and deploying the DermaCare AI skin detection system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Running the Application](#running-the-application)
4. [Model Training](#model-training)
5. [Production Deployment](#production-deployment)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **OS**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **RAM**: 4GB minimum (8GB+ recommended)
- **Storage**: 2GB for dependencies + models
- **GPU**: NVIDIA GPU with CUDA 11.0+ (optional, for faster inference)

### Software Requirements

- **Python**: 3.8 - 3.11
- **Node.js**: 18+ and npm 9+
- **Git**: For version control
- **PowerShell**: 5.1+ (Windows only)

### Development Tools (Optional)

- Visual Studio Code
- PyCharm
- Git GUI
- NVIDIA CUDA Toolkit (for GPU support)

---

## Local Development Setup

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd Derma-Care
```

### Step 2: Setup Python Environment

#### Windows

```powershell
# Create virtual environment
python -m venv venv

# Activate
.\venv\Scripts\activate
```

#### macOS / Linux

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt
```

**GPU Support (Optional):**

```bash
# For CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Step 4: Setup Node.js Frontend

```bash
cd frontend
npm install
cd ..
```

### Step 5: Verify Installation

```bash
# Check Python
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"

# Check Node.js
node --version
npm --version
```

---

## Running the Application

### Option 1: Full Stack (Windows)

```powershell
.\start_app.ps1
```

This starts:

- Backend API on <http://localhost:8000>
- Frontend on <http://localhost:3000>

### Option 2: Backend Only

#### Windows

```powershell
.\run.ps1
```

#### macOS / Linux

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

### Option 3: Frontend Only

```bash
cd frontend
npm run dev
```

### Option 4: Manual Full Stack

**Terminal 1 - Backend:**

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**

```bash
cd frontend
npm run dev
```

### Verify Running

- **Backend Health**: <http://localhost:8000/health>
- **API Docs**: <http://localhost:8000/docs>
- **Frontend**: <http://localhost:3000>
- **Backend Logs**: <http://localhost:8000/>

---

## Model Training

### Quick Training (Fast Validation)

For testing the pipeline with limited data:

```bash
# 2000 images, 4 epochs (~10-15 minutes on CPU)
python fast_train_quick.py
```

### Full Training

For production model:

```bash
cd backend/ml
python train.py
```

**Expected Training Time:**

- GPU (RTX 3060): ~2-3 hours
- CPU: ~12-24 hours

**Dataset Requirements:**

- Minimum: 100 images per class
- Recommended: 1000+ images per class
- Format: Organized in `backend/dataset/train/` and `backend/dataset/val/`

### Dataset Organization

```
backend/dataset/
├── train/
│   ├── akiec/     # Actinic Keratosis
│   ├── bcc/       # Basal Cell Carcinoma
│   ├── bkl/       # Benign Keratosis
│   ├── df/        # Dermatofibroma
│   ├── mel/       # Melanoma
│   ├── nv/        # Melanocytic Nevus
│   └── vasc/      # Vascular Lesion
└── val/
    ├── akiec/
    ├── bcc/
    └── ...
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Code reviewed and tested
- [ ] All dependencies pinned to versions
- [ ] Environment variables configured
- [ ] Model weights included
- [ ] Frontend built for production
- [ ] CORS settings updated for domain
- [ ] SSL/HTTPS certificates ready
- [ ] Rate limiting configured
- [ ] Logging configured
- [ ] Error monitoring setup

### Deployment to Cloud

#### AWS EC2

```bash
# Create Ubuntu 20.04 instance
# SSH into instance

# Install dependencies
sudo apt update
sudo apt install python3.10 python3.10-venv nodejs npm

# Clone and setup
git clone <repo>
cd Derma-Care
python3.10 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Setup frontend
cd frontend && npm install && npm run build

# Start services (use systemd or supervisor)
```

#### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/

EXPOSE 8000 3000

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0"]
```

```bash
# Build and run
docker build -t dermacare .
docker run -p 8000:8000 -p 3000:3000 dermacare
```

#### Heroku Deployment

```bash
# Install Heroku CLI
heroku login

# Create app
heroku create dermacare

# Add buildpacks
heroku buildpacks:add heroku/python
heroku buildpacks:add heroku/nodejs

# Deploy
git push heroku main
```

### Production Configuration

**Backend Settings (`backend/main.py`):**

```python
# Update CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

**Environment Variables:**

```bash
# .env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com
DATABASE_URL=postgresql://...
```

### Monitoring & Logging

```python
# Add application monitoring
import logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('/var/log/dermacare.log'),
        logging.StreamHandler()
    ]
)
```

---

## Troubleshooting

### Backend Issues

#### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
python -m uvicorn backend.main:app --port 8001
```

#### Model Not Loading

```bash
# Check model exists
ls -la backend/ml/best_model.pth

# If missing, train model
python fast_train_quick.py

# Verify PyTorch
python -c "import torch; print(torch.__version__)"
```

#### CORS Error

- Ensure backend is running on port 8000
- Check frontend is on port 3000
- Verify CORS middleware is added

### Frontend Issues

#### Dependencies Not Installing

```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

#### Next.js Build Errors

```bash
# Clear build cache
rm -rf .next

# Rebuild
npm run build

# Check for TypeScript errors
npx tsc --noEmit
```

### Common Errors

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'torch'` | Run `pip install -r backend/requirements.txt` |
| `CUDA out of memory` | Use CPU or reduce batch size |
| `Port 3000 already in use` | Change port: `npm run dev -- -p 3001` |
| `API connection refused` | Check backend is running: `curl http://localhost:8000/health` |
| `SSL certificate error` | Update certificates or disable SSL in development |

### Performance Optimization

**Backend:**

- Use GPU for faster inference
- Implement caching for repeated predictions
- Add request queuing for high load

**Frontend:**

- Enable compression: `npm run build` creates optimized bundle
- Use CDN for static assets
- Implement lazy loading for images

---

## Support

- 📧 Email: <support@dermacare.ai>
- 🐛 Issues: GitHub Issues
- 💬 Community: Discord Server
- 📚 Docs: Full documentation

---

**Last Updated**: April 2026
**Version**: 1.0.0
**Status**: Production Ready
