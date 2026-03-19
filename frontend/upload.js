const backendModeEl = document.getElementById("backend-mode");
const uploadFormEl = document.getElementById("upload-form");
const corpusFileEl = document.getElementById("corpus-file");
const uploadStatusEl = document.getElementById("upload-status");
const rawOutputSectionEl = document.getElementById("raw-output");
const rawOutputTextEl = document.getElementById("raw-output-text");

async function loadHealth() {
  try {
    const response = await fetch("/health");
    if (!response.ok) {
      throw new Error("Failed to load backend status");
    }
    const payload = await response.json();
    backendModeEl.textContent = payload.backend;
  } catch (error) {
    backendModeEl.textContent = "unavailable";
    setUploadStatus(error.message, "error");
  }
}

function setUploadStatus(message, kind = "info") {
  uploadStatusEl.textContent = message;
  uploadStatusEl.className = `status ${kind}`;
}

uploadFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = corpusFileEl.files[0];
  rawOutputTextEl.textContent = "";
  rawOutputSectionEl.classList.add("hidden");

  if (!file) {
    setUploadStatus("Choose a .txt file first.", "error");
    return;
  }

  if (!file.name.toLowerCase().endsWith(".txt")) {
    setUploadStatus("Only .txt uploads are supported.", "error");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  setUploadStatus("Uploading corpus...", "info");

  try {
    const response = await fetch("/corpus/upload", {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Upload failed");
    }
    setUploadStatus(payload.message, "success");
    if (payload.raw_output) {
      rawOutputTextEl.textContent = payload.raw_output;
      rawOutputSectionEl.classList.remove("hidden");
    }
  } catch (error) {
    setUploadStatus(error.message, "error");
  }
});

loadHealth();
