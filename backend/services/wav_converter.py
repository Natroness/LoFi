import logging
import shutil
import subprocess
from pathlib import Path

from backend.config import OUTPUT_MIDI, OUTPUT_WAV, SOUNDFONT_PATH

logger = logging.getLogger(__name__)


class WavConverter:
    """Converts a MIDI file to WAV using the FluidSynth CLI directly."""

    def convert_to_wav(
        self,
        midi_path: str | Path | None = None,
        wav_path: str | Path | None = None,
    ) -> Path:
        src = Path(midi_path) if midi_path else OUTPUT_MIDI
        dst = Path(wav_path) if wav_path else OUTPUT_WAV

        if not src.exists():
            raise FileNotFoundError(f"MIDI file not found: {src}")

        dst.parent.mkdir(parents=True, exist_ok=True)

        if self._try_fluidsynth_cli(src, dst):
            return dst

        raise RuntimeError(
            "WAV conversion failed.\n"
            "  • Ensure FluidSynth is installed: brew install fluid-synth\n"
            "  • Ensure a SoundFont (.sf2) is available (see _soundfont fallback list)\n"
            "  • Check server logs for the specific FluidSynth error"
        )

    # ------------------------------------------------------------------

    def _soundfont(self) -> Path:
        """
        Return the first existing SoundFont from an ordered candidate list.
        Raises FileNotFoundError with a clear message if none are found.
        """
        candidates = (
            SOUNDFONT_PATH,
            # Homebrew fluid-synth bundled fonts
            Path("/opt/homebrew/Cellar").parent / "opt" / "fluid-synth" / "share" / "fluid-synth" / "sf2" / "VintageDreamsWaves-v2.sf2",
            Path("/opt/homebrew/share/fluid-soundfont/FluidR3_GM.sf2"),
            Path("/opt/homebrew/share/soundfonts/FluidR3_GM.sf2"),
            Path("/opt/homebrew/share/sounds/sf2/FluidR3_GM.sf2"),
            # Homebrew Cellar versioned path (fluid-synth 2.5.x)
            Path("/opt/homebrew/Cellar/fluid-synth/2.5.4/share/fluid-synth/sf2/VintageDreamsWaves-v2.sf2"),
            # Linux system paths
            Path("/usr/local/share/sounds/sf2/FluidR3_GM.sf2"),
            Path("/usr/share/sounds/sf2/FluidR3_GM.sf2"),
            Path("/usr/share/soundfonts/default.sf2"),
        )
        for candidate in candidates:
            if candidate.exists():
                logger.info("Using soundfont: %s", candidate)
                return candidate

        raise FileNotFoundError(
            "No SoundFont (.sf2) found. Options:\n"
            "  • Place FluidR3_GM.sf2 in backend/soundfonts/\n"
            "  • brew install fluid-synth  (includes VintageDreamsWaves)\n"
            "  • Download FluidR3_GM.sf2 from https://github.com/FluidSynth/fluidsynth/wiki/SoundFont"
        )

    def _try_fluidsynth_cli(self, src: Path, dst: Path) -> bool:
        if not shutil.which("fluidsynth"):
            logger.error(
                "fluidsynth not found on PATH. Install it: brew install fluid-synth"
            )
            return False

        try:
            sf = self._soundfont()
        except FileNotFoundError as exc:
            logger.error("%s", exc)
            return False

        # FluidSynth 2.x requires all options BEFORE soundfont and MIDI arguments.
        # Placing -F or -r after the .sf2 path causes "illegal option" errors.
        cmd = [
            "fluidsynth",
            "-ni",
            "-F", str(dst),
            "-r", "44100",
            str(sf),
            str(src),
        ]
        logger.debug("FluidSynth cmd: %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0 and dst.exists() and dst.stat().st_size > 0:
                logger.info("WAV saved via fluidsynth CLI → %s", dst)
                return True
            logger.error(
                "FluidSynth exited %d.\nstdout: %s\nstderr: %s",
                result.returncode,
                result.stdout.strip(),
                result.stderr.strip(),
            )
        except subprocess.TimeoutExpired:
            logger.error("FluidSynth timed out after 120 s")
        except Exception as exc:
            logger.error("FluidSynth CLI error: %s", exc)

        return False
