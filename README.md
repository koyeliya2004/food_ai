# AI Calorie & Food Detector

A lightweight web application that uses a **pretrained deep learning model** to identify food from images and provide instant calorie estimates and health insights.

---

## Features

- 📷 **Upload any food photo** – drag & drop or browse
- 🤖 **AI-powered food recognition** – ViT model trained on Food-101 (101 food categories)
- 🔥 **Calorie estimation** – standard serving sizes
- 🏷️ **Health category** – Healthy / Moderate / Unhealthy
- 💡 **Personalized suggestion** – practical dietary advice
- 📱 **Responsive UI** – works great on mobile and desktop
- ⚠️ **Graceful error handling** – low-confidence / unknown images handled cleanly

---

## Tech stack

| Layer     | Technology                                          |
|-----------|-----------------------------------------------------|
| Backend   | Python · FastAPI · Uvicorn                          |
| AI model  | Hugging Face Transformers · `nateraw/food` (ViT)    |
| Frontend  | Vanilla HTML / CSS / JavaScript (served by FastAPI) |
| Nutrition | Local `nutrition_db.json` with fuzzy label matching |

---

## Setup

### Prerequisites

- Python 3.10 or later
- pip / virtualenv

### 1. Clone the repository

```bash
git clone https://github.com/koyeliya2004/food_ai.git
cd food_ai
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

> **Note on PyTorch size:** The default `torch` package is large (~700 MB).
> For a CPU-only install (smaller download), run:
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cpu
> pip install -r requirements.txt
> ```

### 4. Run the server

```bash
# From the backend/ directory
uvicorn app.main:app --reload --port 8000
```

The first run will **automatically download the model** from Hugging Face Hub (~300 MB). Subsequent runs use the local cache.

---

## Usage

1. Open your browser and navigate to **http://localhost:8000**
2. Drag & drop a food photo (or click to browse)
3. Click **Analyze**
4. View the detected food name, estimated calories, health category, and suggestion

### API endpoints

| Method | Path           | Description                           |
|--------|----------------|---------------------------------------|
| GET    | `/healthz`     | Health check – returns `{"status":"ok"}` |
| POST   | `/api/analyze` | Analyze a food image (multipart/form-data, field: `file`) |

Example cURL:

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@pizza.jpg" | python -m json.tool
```

### API response schema

```json
{
  "food_name": "Pizza",
  "confidence": 0.9823,
  "estimated_calories": 400,
  "health_category": "moderate",
  "suggestion": "Pizza can be high in calories. Choose a thin crust...",
  "top_predictions": [
    { "name": "Pizza",      "confidence": 0.9823 },
    { "name": "Focaccia",   "confidence": 0.0043 }
  ],
  "model": "nateraw/food"
}
```

---

## Project structure

```
food_ai/
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py
│       ├── main.py           # FastAPI app, routes, CORS
│       ├── model.py          # Model loading & inference
│       ├── nutrition.py      # Calorie/category lookup with fuzzy matching
│       ├── nutrition_db.json # Nutrition data for 101 food categories
│       └── static/           # Frontend (HTML / CSS / JS)
│           ├── index.html
│           ├── style.css
│           └── app.js
├── LICENSE
└── README.md
```

---

## Model notes

- **Model:** [`nateraw/food`](https://huggingface.co/nateraw/food) – a Vision Transformer (ViT) fine-tuned on the [Food-101 dataset](https://data.vision.ee.ethz.ch/cvl/datasets_extra/food-101/)
- **Categories:** 101 food classes (apple pie, pizza, sushi, …)
- **Hardware:** CPU-friendly, no GPU required
- **Download:** ~300 MB on first run; cached in `~/.cache/huggingface/`
- **Confidence threshold:** 20% – images below this are reported as "unknown"

---

## License

MIT – see [LICENSE](LICENSE).