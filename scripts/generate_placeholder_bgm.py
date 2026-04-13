"""
生成与各情绪文件夹对应的占位 BGM（WAV），体现：
  happy  大调 + 快速    calm   大调 + 慢速
  tense  小调 + 快速    sad    小调 + 慢速
仅作 Demo 占位，可替换为自有版权音乐。用法（项目根目录）:
  python scripts/generate_placeholder_bgm.py
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

SR = 44100
DURATION_SEC = 20.0


def _hz(root: float, semitones: float) -> float:
    return root * (2.0 ** (semitones / 12.0))


def triad(root: float, major: bool) -> tuple[float, float, float]:
    third = 4 if major else 3
    return root, _hz(root, third), _hz(root, 7)


def render_arpeggio(
    path: Path,
    *,
    root: float,
    major: bool,
    bpm: float,
    notes_per_beat: float,
    peak: float = 0.22,
) -> None:
    """notes_per_beat: 每拍分解和弦音数，越大越快。"""
    freqs = triad(root, major)
    beat_sec = 60.0 / bpm
    note_sec = beat_sec / notes_per_beat
    segs: list[tuple[float, float, float]] = []
    t = 0.0
    i = 0
    while t < DURATION_SEC:
        end = min(t + note_sec, DURATION_SEC)
        segs.append((t, end, freqs[i % 3]))
        t = end
        i += 1

    n_samples = int(SR * DURATION_SEC)
    frames: list[float] = []
    si = 0
    for j in range(n_samples):
        t = j / SR
        while si < len(segs) - 1 and t >= segs[si][1]:
            si += 1
        a, b, freq = segs[si]
        if not (a <= t < b):
            frames.append(0.0)
            continue
        pos = (t - a) / (b - a) if b > a else 0.0
        env = math.sin(math.pi * pos)
        frames.append(env * peak * math.sin(2 * math.pi * freq * t))

    m = max(abs(x) for x in frames) or 1.0
    if m > 0.95:
        frames = [x / m * 0.92 for x in frames]

    path.parent.mkdir(parents=True, exist_ok=True)
    packed = b"".join(
        struct.pack("<h", int(max(-32767, min(32767, x * 32767)))) for x in frames
    )
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(packed)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    music = root / "assets" / "music"
    specs = {
        # key: (major?, bpm, notes_per_beat, root_hz, peak)
        "happy": (True, 108, 6, 261.63, 0.24),
        "calm": (True, 52, 2, 196.0, 0.18),
        "tense": (False, 118, 8, 220.0, 0.23),
        "sad": (False, 48, 2, 174.61, 0.2),
    }
    for name, (major, bpm, npb, hz, pk) in specs.items():
        out = music / name / "placeholder_bgm.wav"
        render_arpeggio(out, root=hz, major=major, bpm=bpm, notes_per_beat=npb, peak=pk)
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()
