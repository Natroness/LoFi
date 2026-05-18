import logging
import shutil
import subprocess
from pathlib import Path

from backend.config import OUTPUT_WAV, SOUNDFONT_PATH

logger = logging.getLogger(__name__)


class WavConverter:
    """Converts a MIDI file to WAV using FluidSynth (via midi2audio or CLI)."""

    def convert_to_wav(
        self,
        midi_path: str | Path | None = None,
        wav_path: str | Path | None = None,
    ) -> Path:
        src = Path(midi_path) if midi_path else Path(
            str(OUTPUT_WAV).replace(".wav", ".mid")
        )
        dst = Path(wav_path) if wav_path else OUTPUT_WAV

        if not src.exists():
            raise FileNotFoundError(f"MIDI file not found: {src}")

        dst.parent.mkdir(parents=True, exist_ok=True)

        # Strategy 1 – midi2audio (wraps FluidSynth, easiest)
        if self._try_midi2audio(src, dst):
            return dst

        # Strategy 2 – call FluidSynth directly
        if self._try_fluidsynth_cli(src, dst):
            return dst

        raise RuntimeError(
            "WAV conversion failed. Make sure FluidSynth is installed "
            "(brew install fluidsynth / apt install fluidsynth) "
            "and a soundfont is available."
        )

    # ------------------------------------------------------------------

    def _soundfont(self) -> Path | None:
        if SOUNDFONT_PATH.exists():
            return SOUNDFONT_PATH
        # Common fallback locations
        for candidate in (
            Path("/usr/share/sounds/sf2/FluidR3_GM.sf2"),
            Path("/usr/share/soundfonts/default.sf2"),
            Path("/usr/local/share/sounds/sf2/FluidR3_GM.sf2"),
            Path.home() / "soundfonts" / "FluidR3_GM.sf2",
        ):
            if candidate.exists():
                logger.info("Using soundfont: %s", candidate)
                return candidate
        return None

    def _try_midi2audio(self, src: Path, dst: Path) -> bool:
        try:
            from midi2audio import FluidSynth as M2AFS  # type: ignore

            sf = self._soundfont()
            kwargs = {"sound_font": str(sf)} if sf else {}
            fs = M2AFS(**kwargs)
            fs.midi_to_audio(str(src), str(dst))
            logger.info("WAV saved via midi2audio → %s", dst)
            return True
        except ImportError:
            logger.debug("midi2audio not available, trying fluidsynth CLI")
        except Exception as exc:
            logger.warning("midi2audio failed: %s", exc)
        return False

    def _try_fluidsynth_cli(self, src: Path, dst: Path) -> bool:
        if not shutil.which("fluidsynth"):
            logger.debug("fluidsynth not on PATH")
            return False

        sf = self._soundfont()
        if sf is None:
            logger.warning("No soundfont found; FluidSynth needs one.")
            return False

        cmd = [
            "fluidsynth", "-ni",
            str(sf),
            str(src),
            "-F", str(dst),
            "-r", "44100",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                logger.info("WAV saved via fluidsynth CLI → %s", dst)
                return True
            logger.warning("fluidsynth exited %d: %s", result.returncode, result.stderr)
        except Exception as exc:
            logger.warning("fluidsynth CLI error: %s", exc)
        return False
