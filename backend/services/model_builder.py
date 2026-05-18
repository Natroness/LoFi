import logging

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

from backend.config import LEARNING_RATE, SEQUENCE_LENGTH

logger = logging.getLogger(__name__)


class ModelBuilder:
    """Builds and compiles the LSTM-based note prediction model."""

    def build_model(self) -> keras.Model:
        inputs = keras.Input(shape=(SEQUENCE_LENGTH, 3), name="note_sequence")

        x = layers.LSTM(128, return_sequences=False, name="lstm")(inputs)
        x = layers.Dropout(0.3, name="dropout")(x)
        x = layers.Dense(128, activation="relu", name="dense_shared")(x)

        pitch_out = layers.Dense(1, name="pitch")(x)
        step_out  = layers.Dense(1, activation="relu", name="step")(x)
        dur_out   = layers.Dense(1, activation="relu", name="duration")(x)

        model = keras.Model(inputs=inputs, outputs=[pitch_out, step_out, dur_out])
        logger.info("Model built: %d params", model.count_params())
        return model

    def compile_model(self, model: keras.Model) -> keras.Model:
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
            loss={
                "pitch":    "mse",
                "step":     "mse",
                "duration": "mse",
            },
            loss_weights={"pitch": 1.0, "step": 1.0, "duration": 1.0},
        )
        return model
