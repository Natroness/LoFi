import logging

import pretty_midi

from backend.config import TEMPO

logger = logging.getLogger(__name__)

# General MIDI drum note numbers
KICK  = 36
SNARE = 38
HIHAT = 42

# Lo-fi velocities (quiet / behind the melody)
VEL_KICK  = 80
VEL_SNARE = 65
VEL_HIHAT = 45


def _beat_times(midi: pretty_midi.PrettyMIDI) -> list[float]:
    """Return all quarter-beat start times for the duration of the MIDI."""
    end_time   = midi.get_end_time()
    beat_dur   = 60.0 / TEMPO          # seconds per beat
    half_beat  = beat_dur / 2.0
    times: list[float] = []
    t = 0.0
    while t < end_time:
        times.append(t)
        t += half_beat
    return times


def _add_note(instrument: pretty_midi.Instrument, pitch: int, start: float,
              velocity: int, duration: float = 0.05) -> None:
    instrument.notes.append(
        pretty_midi.Note(velocity=velocity, pitch=pitch, start=start, end=start + duration)
    )


class DrumEngine:
    """Adds a minimal lo-fi drum pattern to an existing PrettyMIDI object."""

    def add_kick(self, midi: pretty_midi.PrettyMIDI, drum: pretty_midi.Instrument) -> None:
        beat_dur  = 60.0 / TEMPO
        end_time  = midi.get_end_time()
        t = 0.0
        bar = 0
        while t < end_time:
            beat_in_bar = bar % 4
            if beat_in_bar in (0, 2):         # beats 1 and 3
                _add_note(drum, KICK, t, VEL_KICK)
            t    += beat_dur
            bar  += 1

    def add_snare(self, midi: pretty_midi.PrettyMIDI, drum: pretty_midi.Instrument) -> None:
        beat_dur = 60.0 / TEMPO
        end_time = midi.get_end_time()
        t   = 0.0
        bar = 0
        while t < end_time:
            beat_in_bar = bar % 4
            if beat_in_bar in (1, 3):         # beats 2 and 4
                _add_note(drum, SNARE, t, VEL_SNARE)
            t    += beat_dur
            bar  += 1

    def add_hihat(self, midi: pretty_midi.PrettyMIDI, drum: pretty_midi.Instrument) -> None:
        beat_dur  = 60.0 / TEMPO
        half_beat = beat_dur / 2.0
        end_time  = midi.get_end_time()
        t = 0.0
        while t < end_time:
            _add_note(drum, HIHAT, t, VEL_HIHAT)
            t += half_beat

    def add_drums(self, midi: pretty_midi.PrettyMIDI) -> pretty_midi.PrettyMIDI:
        drum = pretty_midi.Instrument(program=0, is_drum=True, name="drums")
        self.add_hihat(midi, drum)
        self.add_kick(midi, drum)
        self.add_snare(midi, drum)
        midi.instruments.append(drum)
        logger.info("Drum track added (%d events)", len(drum.notes))
        return midi
