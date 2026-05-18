import logging
from typing import Tuple

import numpy as np
import pandas as pd

from backend.config import SEQUENCE_LENGTH

logger = logging.getLogger(__name__)

FEATURES = ["pitch", "step", "duration"]


class DatasetBuilder:
    """Converts a notes DataFrame into training sequences."""

    def __init__(self):
        self.min_vals: np.ndarray | None = None
        self.max_vals: np.ndarray | None = None

    def normalize_data(self, data: np.ndarray) -> np.ndarray:
        self.min_vals = data.min(axis=0)
        self.max_vals = data.max(axis=0)
        rng = self.max_vals - self.min_vals
        rng[rng == 0] = 1.0  # avoid divide-by-zero
        return (data - self.min_vals) / rng

    def denormalize(self, data: np.ndarray) -> np.ndarray:
        if self.min_vals is None or self.max_vals is None:
            raise RuntimeError("Call normalize_data before denormalize.")
        rng = self.max_vals - self.min_vals
        rng[rng == 0] = 1.0
        return data * rng + self.min_vals

    def create_sequences(
        self, notes_df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        if len(notes_df) < SEQUENCE_LENGTH + 1:
            raise ValueError(
                f"Dataset has only {len(notes_df)} notes; need at least "
                f"{SEQUENCE_LENGTH + 1}. Add more MIDI files."
            )

        data = notes_df[FEATURES].to_numpy(dtype=np.float32)
        norm = self.normalize_data(data)

        X, y_pitch, y_step, y_dur = [], [], [], []
        for i in range(len(norm) - SEQUENCE_LENGTH):
            X.append(norm[i : i + SEQUENCE_LENGTH])
            target = norm[i + SEQUENCE_LENGTH]
            y_pitch.append(target[0])
            y_step.append(target[1])
            y_dur.append(target[2])

        X       = np.array(X, dtype=np.float32)
        y_pitch = np.array(y_pitch, dtype=np.float32)
        y_step  = np.array(y_step,  dtype=np.float32)
        y_dur   = np.array(y_dur,   dtype=np.float32)

        logger.info("Sequences: X=%s  y_pitch=%s", X.shape, y_pitch.shape)
        return X, y_pitch, y_step, y_dur
