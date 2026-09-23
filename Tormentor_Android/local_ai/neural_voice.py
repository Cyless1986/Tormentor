"""Local male neural TTS. The model is loaded once per server process."""
from pathlib import Path
import io
import sys
import wave
import re

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/piper-python"))
from piper import PiperVoice, SynthesisConfig
import numpy as np

_voice = None


def synthesize(text, dark=True):
    global _voice
    if _voice is None:
        _voice = PiperVoice.load(str(ROOT / "tools/piper-model/de_DE-thorsten-high.onnx"))
    # Explicit English IPA avoids the German reading of these table terms.
    text = re.sub(r"\bdungeon\s*master\b", "[[dˈʌndʒən mˈæstɚ]]", text, flags=re.IGNORECASE)
    text = re.sub(r"\bdungeon\b", "[[dˈʌndʒən]]", text, flags=re.IGNORECASE)
    result = io.BytesIO()
    with wave.open(result, "wb") as output:
        _voice.synthesize_wav(text, output, syn_config=SynthesisConfig(length_scale=0.96 if dark else 1.03, noise_scale=0.667, noise_w_scale=0.8))
    if not dark:
        return result.getvalue()
    # About two semitones lower, slightly slower overall, with no artificial echo.
    with wave.open(io.BytesIO(result.getvalue()), "rb") as source:
        rate=source.getframerate()
        samples=np.frombuffer(source.readframes(source.getnframes()), dtype="<i2").astype(np.float32)
    ratio=2 ** (-2 / 12)
    pitched=np.interp(np.arange(0, len(samples)-1, ratio), np.arange(len(samples)), samples)
    final=io.BytesIO()
    with wave.open(final, "wb") as output:
        output.setnchannels(1);output.setsampwidth(2);output.setframerate(rate)
        output.writeframes(np.clip(pitched, -32768, 32767).astype("<i2").tobytes())
    return final.getvalue()


if __name__ == "__main__":
    text="Ich bin Tormentor. Willkommen zurück, Dungeonmaster. Hinter der alten Tür hörst du fließendes Wasser. Eine einzelne Fackel erhellt den Weg in die Tiefe. Wage den nächsten Schritt."
    for dark in (False, True):
        target=ROOT / ("verification/tormentor-dunkel.wav" if dark else "verification/tormentor-aussprache.wav")
        target.write_bytes(synthesize(text, dark=dark))
        print(str(target))
