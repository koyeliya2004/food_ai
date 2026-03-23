"""Model loading and inference using a Hugging Face Food-101 image classifier."""

from __future__ import annotations

import io
import logging
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)

# Model identifier on Hugging Face Hub.
# nateraw/food is a ViT fine-tuned on Food-101 (101 food categories, CPU-friendly).
MODEL_ID = "nateraw/food"

# Confidence threshold below which we treat the prediction as "unknown".
CONFIDENCE_THRESHOLD = 0.20

_pipeline = None  # lazy-loaded at startup


def is_model_loaded() -> bool:
    """Return True if the model pipeline has been loaded."""
    return _pipeline is not None


def load_model() -> None:
    """Load the image classification pipeline once at startup."""
    global _pipeline
    if _pipeline is not None:
        return

    try:
        from transformers import pipeline as hf_pipeline  # type: ignore

        logger.info("Loading model '%s' …", MODEL_ID)
        _pipeline = hf_pipeline(
            "image-classification",
            model=MODEL_ID,
            top_k=5,
        )
        logger.info("Model '%s' loaded successfully.", MODEL_ID)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to load model: %s", exc)
        raise


def predict(image_bytes: bytes) -> dict:
    """
    Run inference on *image_bytes* (raw file content).

    Returns:
        {
            "food_name": str,
            "confidence": float,
            "top_predictions": list[{"name": str, "confidence": float}],
            "below_threshold": bool,
            "model": str,
        }
    """
    if _pipeline is None:
        raise RuntimeError("Model is not loaded. Call load_model() first.")

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    raw_results: list[dict] = _pipeline(image)  # type: ignore[arg-type]

    top_predictions = [
        {"name": _pretty_label(r["label"]), "confidence": round(float(r["score"]), 4)}
        for r in raw_results
    ]

    top = top_predictions[0] if top_predictions else {"name": "unknown", "confidence": 0.0}
    below_threshold = top["confidence"] < CONFIDENCE_THRESHOLD

    return {
        "food_name": top["name"],
        "confidence": top["confidence"],
        "top_predictions": top_predictions,
        "below_threshold": below_threshold,
        "model": MODEL_ID,
    }


def _pretty_label(label: str) -> str:
    """Convert 'chicken_wings' → 'Chicken Wings'."""
    return label.replace("_", " ").title()
