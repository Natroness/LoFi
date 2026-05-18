import logging
from typing import List, Dict

import numpy as np
import pandas as pd
import tensorflow as tf

from backend.config import (
    GENERATED_NOTES, MODEL_PATH, NOTES_CSV, SEQUENCE_LENGTH, TEMPERATURE,
)
from backend.services.dataset_builder import DatasetBuilder

logger = logging.getLogger(__name__)

FEATURES = ["pitch", "step", "duration"]


class MusicGenerator:
    def __init__(self):
        self._model = None
        self._builder = None
        self._seed: np.ndarray | None = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_model(self):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Trained model not found at {MODEL_PATH}. "
                "Run training first: python -m backend.services.trainer"
            )
        self._model = tf.keras.models.load_model(str(MODEL_PATH))
        logger.info("Model loaded from %s", MODEL_PATH)

    def _prepare_seed(self):
        if not NOTES_CSV.exists():
            raise FileNotFoundError(
                f"notes.csv not found at {NOTES_CSV}. "
                "Run preprocessing first: python -m backend.services.preprocess"
            )
        notes_df = pd.read_csv(NOTES_CSV)
        if len(notes_df) < SEQUENCE_LENGTH:
            raise ValueError(
                f"notes.csv has only {len(notes_df)} rows; need {SEQUENCE_LENGTH}."
            )

        self._builder = DatasetBuilder()
        data = notes_df[FEATURES].to_numpy(dtype=np.float32)
        self._builder.normalize_data(data)

        norm = (data - self._builder.min_vals) / (
            self._builder.max_vals - self._builder.min_vals + 1e-8
        )
        start = np.random.randint(0, len(norm) - SEQUENCE_LENGTH)
        self._seed = norm[start : start + SEQUENCE_LENGTH].copy()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def sample_prediction(self, prediction: float, temperature: float) -> float:
        """Apply temperature scaling to a scalar prediction."""
        if temperature <= 0:
            return float(prediction)
        noise = np.random.normal(0, temperature * 0.05)
        return float(np.clip(prediction + noise, 0.0, 1.0))

    def generate_notes(
        self,
        seed_sequence: np.ndarray | None = None,
        count: int | None = None,
    ) -> List[Dict]:
        if self._model is None:
            self._load_model()
        if self._builder is None or self._seed is None:
            self._prepare_seed()

        seq   = (seed_sequence.copy() if seed_sequence is not None else self._seed.copy())
        n     = count or GENERATED_NOTES
        temp  = TEMPERATURE

        generated: List[Dict] = []
        for _ in range(n):
            inp = seq[np.newaxis, :, :]           # (1, seq_len, 3)
            p_norm, s_norm, d_norm = self._model.predict(inp, verbose=0)

            p = self.sample_prediction(float(p_norm[0][0]), temp)
            s = self.sample_prediction(float(s_norm[0][0]), temp)
            d = self.sample_prediction(float(d_norm[0][0]), temp)

            # Denormalize
            raw = np.array([[p, s, d]], dtype=np.float32)
            raw_denorm = self._builder.denormalize(raw)[0]

            pitch    = int(np.clip(round(raw_denorm[0]), 0, 127))
            step     = float(max(0.01, raw_denorm[1]))
            duration = float(max(0.01, raw_denorm[2]))

            generated.append({"pitch": pitch, "step": step, "duration": duration})

            next_note = np.array([[p, s, d]], dtype=np.float32)
            seq = np.vstack([seq[1:], next_note])

        logger.info("Generated %d notes", len(generated))
        return generated
