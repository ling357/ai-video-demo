from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def merge_video_bgm(
    video_path: Path,
    audio_path: Path,
    out_path: Path,
    *,
    audio_seek_sec: float = 0.0,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("未找到 ffmpeg，请安装并加入 PATH（Windows 可 choco/scoop 安装）。")
    seek = max(0.0, float(audio_seek_sec))
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video_path),
        "-ss",
        f"{seek:.3f}",
        "-stream_loop",
        "-1",
        "-i",
        str(audio_path),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or "ffmpeg 失败")
