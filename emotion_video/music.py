from __future__ import annotations

import random
from pathlib import Path

_AUDIO_EXT = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}


def pick_random_track(music_root: Path, emotion_key: str) -> Path:
    folder = music_root / emotion_key
    if not folder.is_dir():
        raise FileNotFoundError(f"情绪目录不存在: {folder}")
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in _AUDIO_EXT]
    if not files:
        raise FileNotFoundError(
            f"目录 {folder} 下没有音频文件（支持 {', '.join(sorted(_AUDIO_EXT))}），请放入配乐。"
        )
    return random.choice(files)
