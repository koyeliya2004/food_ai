"""FastAPI application – AI Calorie & Food Detector."""

from __future__ import annotations

import logging
import pathlib
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .model import is_model_loaded, load_model, predict
from .nutrition import lookup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    try:
        load_model()
    except Exception as exc:  # pragma: no cover
        logger.warning("Model could not be loaded at startup: %s. Will retry on first request.", exc)
    yield


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Calorie & Food Detector",
    description="Upload a food image to identify the food item and get calorie/health info.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------------


class Prediction(BaseModel):
    name: str
    confidence: float


class AnalyzeResponse(BaseModel):
    food_name: str
    confidence: float
    estimated_calories: Optional[int]
    health_category: str
    suggestion: str
    top_predictions: list[Prediction]
    model: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/healthz", tags=["meta"])
def healthz() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalyzeResponse, tags=["inference"])
async def analyze(file: UploadFile = File(...)) -> AnalyzeResponse:
    """
    Accept a food image upload and return food detection + nutrition info.

    - Accepted file types: image/jpeg, image/png, image/webp, image/gif
    - Returns structured JSON with food name, calories, health category, and a suggestion.
    """
    # --- Validate content type ---
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    content_type = (file.content_type or "").split(";")[0].strip()
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{content_type}'. Please upload a JPEG, PNG, WebP, or GIF image.",
        )

    # --- Read file ---
    try:
        image_bytes = await file.read()
    except Exception as exc:
        logger.error("Failed to read uploaded file: %s", exc)
        raise HTTPException(status_code=400, detail="Could not read the uploaded file.")

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # --- Inference ---
    try:
        if not is_model_loaded():
            try:
                load_model()
            except Exception as exc:
                logger.error("Model loading failed: %s", exc)
                raise HTTPException(
                    status_code=503,
                    detail="AI model is not available. Please try again later.",
                )
        result = predict(image_bytes)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Inference error: %s", exc)
        raise HTTPException(status_code=500, detail="Model inference failed. Please try again.")

    # --- Handle low-confidence / unknown ---
    if result["below_threshold"]:
        return AnalyzeResponse(
            food_name="Unknown",
            confidence=result["confidence"],
            estimated_calories=None,
            health_category="unknown",
            suggestion=(
                "The image wasn't clear enough to identify food. "
                "Try a well-lit, close-up photo of the dish."
            ),
            top_predictions=[Prediction(**p) for p in result["top_predictions"]],
            model=result["model"],
        )

    # --- Nutrition lookup ---
    nutrition = lookup(result["food_name"])

    return AnalyzeResponse(
        food_name=result["food_name"],
        confidence=result["confidence"],
        estimated_calories=nutrition["calories"],
        health_category=nutrition["health_category"],
        suggestion=nutrition["suggestion"],
        top_predictions=[Prediction(**p) for p in result["top_predictions"]],
        model=result["model"],
    )


# ---------------------------------------------------------------------------
# Serve static frontend (must be mounted last so API routes take priority)
# ---------------------------------------------------------------------------

_STATIC_DIR = pathlib.Path(__file__).parent / "static"
if _STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="static")
