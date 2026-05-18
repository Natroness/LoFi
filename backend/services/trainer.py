import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.config import (
    BATCH_SIZE, EPOCHS, MODEL_PATH, MODELS_DIR, NOTES_CSV, OUTPUTS_DIR,
)
from backend.services.dataset_builder import DatasetBuilder
from backend.services.model_builder import ModelBuilder

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


class Trainer:
    def train(self):
        if not NOTES_CSV.exists():
            raise FileNotFoundError(
                f"notes.csv not found at {NOTES_CSV}. Run preprocessing first."
            )

        notes_df = pd.read_csv(NOTES_CSV)
        logger.info("Loaded %d notes from %s", len(notes_df), NOTES_CSV)

        builder = DatasetBuilder()
        X, y_pitch, y_step, y_dur = builder.create_sequences(notes_df)

        model_builder = ModelBuilder()
        model = model_builder.build_model()
        model = model_builder.compile_model(model)

        checkpoint_cb = _checkpoint_callback()
        early_stop_cb = _early_stop_callback()

        logger.info("Training for up to %d epochs …", EPOCHS)
        history = model.fit(
            X,
            {"pitch": y_pitch, "step": y_step, "duration": y_dur},
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            validation_split=0.1,
            callbacks=[checkpoint_cb, early_stop_cb],
            verbose=1,
        )

        self.save_model(model)
        self.plot_loss(history)
        return model, history

    def save_model(self, model) -> None:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        model.save(MODEL_PATH)
        logger.info("Model saved → %s", MODEL_PATH)

    def plot_loss(self, history) -> None:
        try:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots()
            ax.plot(history.history["loss"],     label="train loss")
            ax.plot(history.history["val_loss"], label="val loss")
            ax.set_xlabel("Epoch")
            ax.set_ylabel("Loss")
            ax.legend()
            out = OUTPUTS_DIR / "training_loss.png"
            fig.savefig(out)
            logger.info("Loss plot saved → %s", out)
            plt.close(fig)
        except Exception as exc:
            logger.warning("Could not save loss plot: %s", exc)


def _checkpoint_callback():
    from tensorflow.keras.callbacks import ModelCheckpoint
    return ModelCheckpoint(
        filepath=str(MODELS_DIR / "checkpoint.keras"),
        save_best_only=True,
        monitor="val_loss",
        verbose=0,
    )


def _early_stop_callback():
    from tensorflow.keras.callbacks import EarlyStopping
    return EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)


if __name__ == "__main__":
    Trainer().train()
