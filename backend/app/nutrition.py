"""Nutrition logic: maps model label -> calories, health category, suggestion."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Optional

_DB_PATH = Path(__file__).parent / "nutrition_db.json"

# Synonym map: maps alternate names / common variants to canonical DB keys.
_SYNONYMS: dict[str, str] = {
    "chips": "french_fries",
    "fries": "french_fries",
    "french fries": "french_fries",
    "burger": "hamburger",
    "cheeseburger": "hamburger",
    "hot dog": "hot_dog",
    "hotdog": "hot_dog",
    "miso": "miso_soup",
    "ramen noodles": "ramen",
    "noodle soup": "ramen",
    "pasta bolognese": "spaghetti_bolognese",
    "spaghetti": "spaghetti_bolognese",
    "mac and cheese": "macaroni_and_cheese",
    "mac n cheese": "macaroni_and_cheese",
    "fried chicken wings": "chicken_wings",
    "chicken wing": "chicken_wings",
    "dumplings": "dumplings",
    "dim sum": "dumplings",
    "potstickers": "gyoza",
    "gyoza dumplings": "gyoza",
    "chocolate cake slice": "chocolate_cake",
    "cupcake": "cup_cakes",
    "donut": "donuts",
    "doughnut": "donuts",
    "ice cream scoop": "ice_cream",
    "frozen yoghurt": "frozen_yogurt",
    "froyo": "frozen_yogurt",
    "eggs benedict": "eggs_benedict",
    "taco": "tacos",
    "sushi roll": "sushi",
    "california roll": "sushi",
    "salmon": "grilled_salmon",
    "grilled fish": "grilled_salmon",
    "fried fish": "fish_and_chips",
    "salad": "greek_salad",
    "green salad": "greek_salad",
    "pizza slice": "pizza",
    "cheese pizza": "pizza",
    "steak fillet": "filet_mignon",
}


def _normalize(text: str) -> str:
    """Lowercase, strip accents, replace non-alphanumerics with underscores."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text


def _load_db() -> dict:
    with open(_DB_PATH, encoding="utf-8") as f:
        return json.load(f)


_DB: dict = _load_db()


def lookup(label: str) -> dict:
    """
    Return nutrition info for *label*.

    Returns a dict with keys: calories (int|None), health_category (str), suggestion (str).
    Falls back gracefully when label is not found.
    """
    key = _normalize(label)

    # 1. Direct lookup
    if key in _DB:
        return _DB[key]

    # 2. Synonym map (after normalising the label)
    synonym_key_raw = label.lower().strip()
    if synonym_key_raw in _SYNONYMS:
        canonical = _SYNONYMS[synonym_key_raw]
        if canonical in _DB:
            return _DB[canonical]

    # Normalized synonym lookup
    for syn, canonical in _SYNONYMS.items():
        if _normalize(syn) == key:
            if canonical in _DB:
                return _DB[canonical]

    # 3. Partial / substring match against DB keys
    for db_key in _DB:
        if key in db_key or db_key in key:
            return _DB[db_key]

    # 4. Unknown fallback
    return {
        "calories": None,
        "health_category": "unknown",
        "suggestion": (
            "We couldn't find specific nutrition data for this food. "
            "Aim for a balanced plate: half vegetables, a quarter lean protein, "
            "and a quarter whole grains."
        ),
    }
