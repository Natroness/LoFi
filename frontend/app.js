const API_BASE = "http://127.0.0.1:5000";

const generateBtn  = document.getElementById("generateBtn");
const btnText      = document.getElementById("btnText");
const spinner      = document.getElementById("spinner");
const player       = document.getElementById("player");
const audioPlayer  = document.getElementById("audioPlayer");
const statusMsg    = document.getElementById("statusMsg");
const visualizer   = document.getElementById("visualizer");

let isGenerating = false;

// ── Public entry point ───────────────────────────────────────────────

async function generateBeat() {
  if (isGenerating) return;
  setLoading(true);
  hideStatus();
  hidePlayer();

  try {
    const res  = await fetch(`${API_BASE}/generate`, { method: "POST" });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || `Server error ${res.status}`);
    }

    showStatus(`Beat ready — ${data.note_count} notes generated.`, "success");
    loadAudio(`${API_BASE}${data.wav_url}?t=${Date.now()}`);
  } catch (err) {
    const msg = err.message.includes("Failed to fetch")
      ? "Cannot reach the backend. Is the Flask server running on port 5000?"
      : err.message;
    showStatus(msg, "error");
  } finally {
    setLoading(false);
  }
}

// ── Download ─────────────────────────────────────────────────────────

function downloadBeat() {
  const link = document.createElement("a");
  link.href = `${API_BASE}/download`;
  link.download = "lofi_beat.wav";
  link.click();
}

// ── Audio ─────────────────────────────────────────────────────────────

function loadAudio(url) {
  audioPlayer.src = url;
  audioPlayer.load();
  player.classList.remove("hidden");
  audioPlayer.play().catch(() => {
    // Autoplay blocked — user will press play manually, that's fine
  });
}

audioPlayer.addEventListener("play",  () => visualizer.classList.add("playing"));
audioPlayer.addEventListener("pause", () => visualizer.classList.remove("playing"));
audioPlayer.addEventListener("ended", () => visualizer.classList.remove("playing"));

// ── UI helpers ────────────────────────────────────────────────────────

function setLoading(loading) {
  isGenerating          = loading;
  generateBtn.disabled  = loading;
  spinner.classList.toggle("hidden", !loading);
  btnText.textContent   = loading ? "Generating…" : "Generate Beat";
}

function showStatus(message, type = "info") {
  statusMsg.textContent = message;
  statusMsg.className   = `status-msg ${type}`;
  statusMsg.classList.remove("hidden");
}

function hideStatus() {
  statusMsg.classList.add("hidden");
}

function hidePlayer() {
  player.classList.add("hidden");
  visualizer.classList.remove("playing");
}
