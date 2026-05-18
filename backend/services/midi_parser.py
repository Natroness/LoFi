import logging
from pathlib import Path
from typing import List, Dict

import pretty_midi

logger = logging.getLogger(__name__)


class MidiParser:
    """Parses a MIDI file and extracts note events."""

    def load_midi(self, path: str | Path) -> pretty_midi.PrettyMIDI | None:
        try:
            midi = pretty_midi.PrettyMIDI(str(path))
            return midi
        except Exception as exc:
            logger.warning("Could not load MIDI %s: %s", path, exc)
            return None

    def extract_notes(self, path: str | Path) -> List[Dict]:
        midi = self.load_midi(path)
        if midi is None:
            return []

        notes: List[Dict] = []
        for instrument in midi.instruments:
            if instrument.is_drum:
                continue
            sorted_notes = sorted(instrument.notes, key=lambda n: n.start)
            prev_start = 0.0
            for note in sorted_notes:
                step     = max(0.0, note.start - prev_start)
                duration = max(0.001, note.end - note.start)
                notes.append({
                    "pitch":    int(note.pitch),
                    "step":     round(float(step), 4),
                    "duration": round(float(duration), 4),
                })
                prev_start = note.start

        if not notes:
            logger.debug("No melodic notes found in %s", path)

        return notes
