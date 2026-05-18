import logging
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pretty_midi

from backend.config import OUTPUT_MIDI, TEMPO

logger = logging.getLogger(__name__)


class MidiWriter:
    """Converts a list of note dicts into a PrettyMIDI object and saves it."""

    def create_midi(self, notes: List[Dict]) -> pretty_midi.PrettyMIDI:
        midi = pretty_midi.PrettyMIDI(initial_tempo=TEMPO)
        instrument = pretty_midi.Instrument(
            program=pretty_midi.instrument_name_to_program("Acoustic Grand Piano"),
            name="melody",
        )

        current_time = 0.0
        for note in notes:
            pitch    = int(np.clip(int(note["pitch"]), 0, 127))
            step     = max(0.01, float(note["step"]))
            duration = max(0.01, float(note["duration"]))
            velocity = 70

            start = current_time + step
            end   = start + duration
            instrument.notes.append(
                pretty_midi.Note(velocity=velocity, pitch=pitch, start=start, end=end)
            )
            current_time = start

        midi.instruments.append(instrument)
        return midi

    def save_midi(self, midi: pretty_midi.PrettyMIDI, path: Optional[Path] = None) -> Path:
        out_path = Path(path) if path else OUTPUT_MIDI
        out_path.parent.mkdir(parents=True, exist_ok=True)
        midi.write(str(out_path))
        logger.info("MIDI saved → %s", out_path)
        return out_path
