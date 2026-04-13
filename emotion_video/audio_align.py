from __future__ import annotations

import json
import random
import re
import shutil
import subprocess
from pathlib import Path


def _ffprobe_duration(path: Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("未找到 ffprobe（通常随 FFmpeg 一起安装）。")
    r = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr or "ffprobe 失败")
    try:
        return float((r.stdout or "").strip())
    except ValueError as e:
        raise RuntimeError(f"无法解析时长: {r.stdout!r}") from e


def _parse_first_sound_offset(stderr: str, start_epsilon: float = 0.2) -> float | None:
    """
    若开头为静音段，返回第一段 silence_end（有声起点）；
    若首条 silence_start 已明显晚于 0，则认为从头即有声音，返回 0。
    """
    pending_leading = False
    for line in stderr.splitlines():
        if "silence_start" in line:
            m = re.search(r"silence_start:\s*([\d.]+)", line)
            if not m:
                continue
            st = float(m.group(1))
            if st <= start_epsilon:
                pending_leading = True
            elif not pending_leading:
                return 0.0
        if "silence_end" in line and pending_leading:
            m = re.search(r"silence_end:\s*([\d.]+)", line)
            if m:
                return max(0.0, float(m.group(1)))
    return None


def _detect_first_sound_offset(
    audio_path: Path,
    *,
    noise_db: float,
    min_silence_sec: float,
) -> float | None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None
    af = f"silencedetect=noise={noise_db}dB:d={min_silence_sec}"
    r = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-nostats",
            "-i",
            str(audio_path),
            "-af",
            af,
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    stderr = (r.stderr or "") + (r.stdout or "")
    parsed = _parse_first_sound_offset(stderr)
    if parsed is not None:
        return float(parsed)
    return 0.0


def _cache_path(audio_path: Path) -> Path:
    return audio_path.with_suffix(audio_path.suffix + ".seek_cache.json")


def _load_seek_cache(audio_path: Path) -> float | None:
    p = _cache_path(audio_path)
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        mtime = audio_path.stat().st_mtime
        if float(data.get("mtime", -1)) != mtime:
            return None
        if "first_sound_sec" not in data:
            return None
        return float(data["first_sound_sec"])
    except (OSError, ValueError, json.JSONDecodeError, TypeError):
        return None


def _save_seek_cache(audio_path: Path, first_sound_sec: float) -> None:
    p = _cache_path(audio_path)
    payload = {
        "mtime": audio_path.stat().st_mtime,
        "first_sound_sec": first_sound_sec,
    }
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=0), encoding="utf-8")


def compute_bgm_seek_seconds(
    video_path: Path,
    audio_path: Path,
    *,
    noise_db: float,
    min_silence_sec: float,
    fallback_skip_sec: float,
    random_extra_max_sec: float,
    use_cache: bool,
) -> float:
    """
    A2：silencedetect 得到首段有声位置（可缓存）；
    检测失败时用 A1 fallback_skip_sec；
    A3：在 [t0, adur - vdur] 内随机加一段偏移，避免总切到同一位置。
    """
    vdur = _ffprobe_duration(video_path)
    adur = _ffprobe_duration(audio_path)
    if adur <= 0 or vdur <= 0:
        return max(0.0, min(fallback_skip_sec, max(0.0, adur - 0.01)))

    raw: float | None = None
    if use_cache:
        raw = _load_seek_cache(audio_path)

    if raw is None:
        try:
            detected = _detect_first_sound_offset(
                audio_path, noise_db=noise_db, min_silence_sec=min_silence_sec
            )
        except Exception:
            detected = None
        if detected is None:
            raw = fallback_skip_sec
        else:
            raw = float(detected)
            if use_cache:
                try:
                    _save_seek_cache(audio_path, raw)
                except OSError:
                    pass

    t0 = max(0.0, min(float(raw), max(0.0, adur - 0.01)))
    slack = adur - t0 - vdur
    if slack <= 0:
        return round(t0, 3)
    extra = random.uniform(0.0, min(slack, max(0.0, random_extra_max_sec)))
    return round(t0 + extra, 3)
