import logging
import traceback
from pathlib import Path

from flask import Flask, jsonify, send_file
from flask_cors import CORS

from backend.config import OUTPUT_MIDI, OUTPUT_WAV
from backend.services.drum_engine import DrumEngine
from backend.services.generator import MusicGenerator
from backend.services.midi_writer import MidiWriter
from backend.services.wav_converter import WavConverter

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Module-level singletons (model loaded once on first /generate call)
_generator: MusicGenerator | None = None


def get_generator() -> MusicGenerator:
    global _generator
    if _generator is None:
        _generator = MusicGenerator()
    return _generator


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/generate", methods=["POST"])
def generate():
    try:
        gen         = get_generator()
        notes       = gen.generate_notes()

        writer      = MidiWriter()
        midi_obj    = writer.create_midi(notes)

        drum_eng    = DrumEngine()
        midi_obj    = drum_eng.add_drums(midi_obj)

        writer.save_midi(midi_obj, OUTPUT_MIDI)

        converter   = WavConverter()
        wav_path    = converter.convert_to_wav(OUTPUT_MIDI, OUTPUT_WAV)

        return jsonify({
            "status":   "ok",
            "wav_url":  "/download",
            "note_count": len(notes),
        })

    except FileNotFoundError as exc:
        logger.error("FileNotFoundError: %s", exc)
        return jsonify({"error": str(exc)}), 404

    except ValueError as exc:
        logger.error("ValueError: %s", exc)
        return jsonify({"error": str(exc)}), 422

    except Exception as exc:
        logger.error("Unexpected error: %s\n%s", exc, traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred. Check server logs."}), 500


@app.route("/download", methods=["GET"])
def download():
    if not OUTPUT_WAV.exists():
        return jsonify({"error": "No generated file found. Run /generate first."}), 404
    return send_file(
        str(OUTPUT_WAV),
        mimetype="audio/wav",
        as_attachment=True,
        download_name="lofi_beat.wav",
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
