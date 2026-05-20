from pathlib import Path

# Root
BASE_DIR = Path(__file__).resolve().parent

# Data paths
RAW_MIDI_DIR   = BASE_DIR / "data" / "raw_midi"
PROCESSED_DIR  = BASE_DIR / "data" / "processed"
NOTES_CSV      = PROCESSED_DIR / "notes.csv"

# Model
MODELS_DIR     = BASE_DIR / "models"
MODEL_PATH     = MODELS_DIR / "lofi_model.keras"

# Outputs
OUTPUTS_DIR    = BASE_DIR / "outputs"
OUTPUT_MIDI    = OUTPUTS_DIR / "generated.mid"
OUTPUT_WAV     = OUTPUTS_DIR / "generated.wav"

# Soundfont — project-local takes priority; fallbacks resolved in wav_converter._soundfont()
SOUNDFONTS_DIR = BASE_DIR / "soundfonts"
SOUNDFONT_PATH = SOUNDFONTS_DIR / "FluidR3_GM.sf2"
# Hyperparameters
SEQUENCE_LENGTH   = 50
EPOCHS            = 50
BATCH_SIZE        = 64
LEARNING_RATE     = 0.001
GENERATED_NOTES   = 300
TEMPERATURE       = 1.0
TEMPO             = 90.0   # BPM

# Ensure required directories exist
for _dir in (RAW_MIDI_DIR, PROCESSED_DIR, MODELS_DIR, OUTPUTS_DIR, SOUNDFONTS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)
