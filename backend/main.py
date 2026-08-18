"""
DermaCare ML API - Skin Condition Detection Service

This FastAPI application provides real-time skin lesion classification
using a MobileNetV2 neural network trained on the HAM10000 dataset.

Endpoints:
- GET  /              - Welcome message
- GET  /health        - Health check with model status
- POST /analyze       - Upload image for analysis

Author: DermaCare Team
Version: 1.0.0
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import logging
from io import BytesIO
from typing import Dict, Any
from PIL import Image
import os

from backend.ml.inference import predict_image

# ─────────────────────────────────────────────────────────────────────────────
# Application Setup
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="DermaCare ML API",
    version="1.0.0",
    description="AI-powered skin condition detection service",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend (development: allow all, production: restrict)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Production: restrict to ["https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Load Clinical Data
# ─────────────────────────────────────────────────────────────────────────────

CONDITIONS_FILE = os.path.join(os.path.dirname(__file__), "data", "conditions.json")
CONDITIONS_DATA: Dict[str, Dict[str, str]] = {}

try:
    with open(CONDITIONS_FILE, "r", encoding="utf-8") as f:
        CONDITIONS_DATA = json.load(f)
    logger.info(f"Loaded {len(CONDITIONS_DATA)} skin conditions from {CONDITIONS_FILE}")
except FileNotFoundError:
    logger.error(f"Conditions file not found: {CONDITIONS_FILE}")
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in conditions file: {e}")
except Exception as e:
    logger.error(f"Unexpected error loading conditions: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
def read_root() -> Dict[str, str]:
    """Root endpoint - returns welcome message and documentation link."""
    return {
        "message": "Welcome to DermaCare ML API",
        "version": "1.0.0",
        "docs": "http://localhost:8000/docs",
        "health": "http://localhost:8000/health"
    }


@app.get("/health")
def health_check() -> JSONResponse:
    """
    Health check endpoint for frontend.

    Returns:
        JSONResponse containing:
        - model_loaded: Boolean indicating if ML model is ready
        - api_version: API version number
    """
    try:
        from backend.ml.inference import model as _model
        model_loaded = _model is not None

        logger.info("Health check passed")
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "model_loaded": model_loaded,
                "api_version": "1.0.0"
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "api_version": "1.0.0"
            }
        )


@app.post("/analyze")
async def analyze_skin(file: UploadFile = File(...)) -> JSONResponse:
    """
    Analyze uploaded skin image and return AI prediction.

    Args:
        file: Image file (JPEG, PNG, or other image format)

    Returns:
        JSONResponse containing:
        - model_loaded: Whether ML model was used
        - prediction: Classification results with confidence and clinical info

    Raises:
        HTTPException 400: If file is not an image
        HTTPException 413: If file is too large
        HTTPException 500: If processing fails
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        logger.warning(f"Invalid file type received: {file.content_type}")
        raise HTTPException(
            status_code=400,
            detail="File provided is not an image. Please upload JPEG, PNG, or similar image format."
        )

    # Validate file size (10MB max)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    file_size = file.size or 0
    if file_size > MAX_FILE_SIZE:
        logger.warning(f"File too large: {file_size} bytes")
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024:.0f}MB."
        )

    try:
        logger.info(f"Processing image: {file.filename}")

        # Read and process image
        contents = await file.read()
        image = Image.open(BytesIO(contents)).convert("RGB")
        logger.debug(f"Image loaded: {image.size}")

        # Get prediction from ML model
        prediction_result = predict_image(image)
        predicted_class_id = prediction_result.get("class_id", "unknown")
        confidence = prediction_result.get("confidence", 0.0)

        # Lookup condition information
        condition_info = CONDITIONS_DATA.get(predicted_class_id)
        if not condition_info:
            logger.warning(f"Condition not found in database: {predicted_class_id}")
            condition_info = CONDITIONS_DATA.get("unknown", {
                "name": "Unknown",
                "description": "The AI could not confidently identify the condition.",
                "cause": "Unable to determine",
                "cure": "Please consult a dermatologist for professional evaluation."
            })

        # Check if model was used
        from backend.ml.inference import model as _model
        model_loaded = _model is not None

        # Construct response
        response = {
            "status": "success",
            "model_loaded": model_loaded,
            "prediction": {
                "class_id": predicted_class_id,
                "confidence": confidence,
                "name": condition_info.get("name", "Unknown"),
                "description": condition_info.get("description", ""),
                "cause": condition_info.get("cause", ""),
                "cure": condition_info.get("cure", "")
            }
        }

        logger.info(f"Analysis complete: {predicted_class_id} ({confidence:.1%} confidence)")
        return JSONResponse(status_code=200, content=response)

    except Image.UnidentifiedImageError:
        logger.error("Unable to identify image format")
        raise HTTPException(
            status_code=400,
            detail="Unable to read the image file. Please ensure it's a valid image."
        )
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing image. Please try again."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Startup/Shutdown Events
# ─────────────────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup_event():
    """Called when application starts."""
    logger.info("DermaCare API starting up...")
    logger.info(f"Conditions database: {len(CONDITIONS_DATA)} conditions loaded")
    logger.info(f"CORS enabled for all origins (development mode)")


@app.on_event("shutdown")
def shutdown_event():
    """Called when application shuts down."""
    logger.info("DermaCare API shutting down...")

