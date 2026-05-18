import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.config import RAW_MIDI_DIR, NOTES_CSV
from backend.services.midi_parser import MidiParser

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


class Preprocessor:
    def __init__(self):
        self.parser = MidiParser()

    def process_dataset(self) -> pd.DataFrame:
        midi_files = sorted(RAW_MIDI_DIR.glob("*.mid")) + sorted(RAW_MIDI_DIR.glob("*.midi"))
        if not midi_files:
            raise FileNotFoundError(
                f"No .mid / .midi files found in {RAW_MIDI_DIR}. "
                "Add MIDI files there and re-run preprocessing."
            )

        all_notes = []
        for midi_path in midi_files:
            logger.info("Parsing %s …", midi_path.name)
            notes = self.parser.extract_notes(midi_path)
            if notes:
                all_notes.extend(notes)
                logger.info("  → %d notes extracted", len(notes))
            else:
                logger.warning("  → skipped (no usable notes)")

        if not all_notes:
            raise ValueError("No notes extracted from any MIDI file.")

        df = pd.DataFrame(all_notes)
        df = df.dropna()
        df = df[df["duration"] > 0]
        df = df[df["step"] >= 0]
        df["pitch"]    = df["pitch"].astype(int).clip(0, 127)
        df["step"]     = df["step"].astype(float)
        df["duration"] = df["duration"].astype(float)

        self.save_notes_csv(df)
        logger.info("Saved %d total notes → %s", len(df), NOTES_CSV)
        return df

    def save_notes_csv(self, notes: pd.DataFrame) -> None:
        NOTES_CSV.parent.mkdir(parents=True, exist_ok=True)
        notes.to_csv(NOTES_CSV, index=False)


if __name__ == "__main__":
    Preprocessor().process_dataset()
