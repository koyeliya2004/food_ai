/* app.js – AI Calorie & Food Detector frontend logic */

const API_BASE = "";  // Same origin; change to "http://localhost:8000" for separate dev

const dropZone       = document.getElementById("dropZone");
const fileInput      = document.getElementById("fileInput");
const previewWrapper = document.getElementById("previewWrapper");
const previewImg     = document.getElementById("previewImg");
const btnChange      = document.getElementById("btnChange");
const btnAnalyze     = document.getElementById("btnAnalyze");
const btnText        = document.getElementById("btnText");
const btnSpinner     = document.getElementById("btnSpinner");
const btnReset       = document.getElementById("btnReset");
const errorBanner    = document.getElementById("errorBanner");
const resultsCard    = document.getElementById("resultsCard");

// Result elements
const resultFoodName  = document.getElementById("resultFoodName");
const resultConfidence= document.getElementById("resultConfidence");
const confidenceBar   = document.getElementById("confidenceBar");
const resultCalories  = document.getElementById("resultCalories");
const resultBadge     = document.getElementById("resultBadge");
const resultSuggestion= document.getElementById("resultSuggestion");
const predictionList  = document.getElementById("predictionList");
const topPredictions  = document.getElementById("topPredictions");
const modelMeta       = document.getElementById("modelMeta");

let selectedFile = null;

// ─── Drag-and-drop ─────────────────────────────────────────────────────────

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("drag-over");
});

dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});

dropZone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") fileInput.click();
});

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) handleFile(fileInput.files[0]);
});

// ─── File handling ──────────────────────────────────────────────────────────

function handleFile(file) {
  const allowedTypes = ["image/jpeg", "image/png", "image/webp", "image/gif"];
  if (!allowedTypes.includes(file.type)) {
    showError("Please upload a JPEG, PNG, WebP, or GIF image.");
    return;
  }

  selectedFile = file;
  hideError();
  hideResults();

  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
    previewImg.alt = file.name;
  };
  reader.readAsDataURL(file);

  dropZone.hidden = true;
  previewWrapper.hidden = false;
  btnAnalyze.disabled = false;
}

// ─── Change photo ───────────────────────────────────────────────────────────

btnChange.addEventListener("click", () => {
  resetUpload();
  fileInput.value = "";
  fileInput.click();
});

// ─── Analyze ────────────────────────────────────────────────────────────────

btnAnalyze.addEventListener("click", analyze);

async function analyze() {
  if (!selectedFile) return;

  setLoading(true);
  hideError();
  hideResults();

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const response = await fetch(`${API_BASE}/api/analyze`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      let msg = `Server error (${response.status})`;
      try {
        const data = await response.json();
        if (data.detail) msg = data.detail;
      } catch (_) { /* ignore */ }
      throw new Error(msg);
    }

    const data = await response.json();
    showResults(data);
  } catch (err) {
    if (err.name === "TypeError") {
      showError("Could not reach the server. Make sure the backend is running.");
    } else {
      showError(err.message || "An unexpected error occurred.");
    }
  } finally {
    setLoading(false);
  }
}

// ─── Display results ─────────────────────────────────────────────────────────

function showResults(data) {
  // Food name
  resultFoodName.textContent = data.food_name || "Unknown";

  // Confidence
  const pct = Math.round((data.confidence || 0) * 100);
  resultConfidence.textContent = `${pct}%`;
  confidenceBar.style.width = `${pct}%`;

  // Calories
  resultCalories.textContent = data.estimated_calories != null
    ? `${data.estimated_calories} kcal`
    : "N/A";

  // Health badge
  const cat = (data.health_category || "unknown").toLowerCase();
  resultBadge.textContent = cat.charAt(0).toUpperCase() + cat.slice(1);
  resultBadge.className = `badge badge-${cat}`;

  // Suggestion
  resultSuggestion.textContent = data.suggestion || "—";

  // Top predictions
  predictionList.innerHTML = "";
  if (data.top_predictions && data.top_predictions.length > 1) {
    data.top_predictions.slice(1).forEach((p) => {
      const li = document.createElement("li");
      const score = Math.round((p.confidence || 0) * 100);
      li.innerHTML = `<span>${escapeHtml(p.name)}</span><span class="pred-score">${score}%</span>`;
      predictionList.appendChild(li);
    });
    topPredictions.hidden = false;
  } else {
    topPredictions.hidden = true;
  }

  // Model meta
  modelMeta.textContent = data.model ? `Model: ${data.model}` : "";

  resultsCard.hidden = false;
  resultsCard.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ─── Reset ───────────────────────────────────────────────────────────────────

btnReset.addEventListener("click", () => {
  resetUpload();
  hideResults();
  hideError();
  selectedFile = null;
  fileInput.value = "";
  window.scrollTo({ top: 0, behavior: "smooth" });
});

function resetUpload() {
  dropZone.hidden = false;
  previewWrapper.hidden = true;
  previewImg.src = "";
  btnAnalyze.disabled = true;
}

// ─── UI helpers ──────────────────────────────────────────────────────────────

function setLoading(loading) {
  if (loading) {
    btnText.textContent = "Analyzing…";
    btnSpinner.hidden = false;
    btnAnalyze.disabled = true;
  } else {
    btnText.textContent = "Analyze";
    btnSpinner.hidden = true;
    btnAnalyze.disabled = false;
  }
}

function showError(msg) {
  errorBanner.textContent = msg;
  errorBanner.hidden = false;
  errorBanner.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function hideError() {
  errorBanner.hidden = true;
  errorBanner.textContent = "";
}

function hideResults() {
  resultsCard.hidden = true;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
