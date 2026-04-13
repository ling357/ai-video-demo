from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    zhipu_api_key: str
    glm_model: str
    image_model: str
    image_size: str
    video_model: str
    video_quality: str
    video_size: str
    video_fps: int
    debug_glm_only: bool
    debug_stop_after_image: bool
    music_root: Path
    categories_path: Path
    output_dir: Path
    music_align_enabled: bool
    music_silence_noise_db: float
    music_silence_min_sec: float
    music_fallback_skip_sec: float
    music_random_extra_max_sec: float
    music_seek_cache: bool


def load_settings() -> Settings:
    key = (os.environ.get("ZHIPU_API_KEY") or "").strip()
    if not key:
        raise RuntimeError(
            "未设置 ZHIPU_API_KEY。请在项目根目录复制 .env.example 为 .env 并填入密钥。"
        )
    return Settings(
        zhipu_api_key=key,
        glm_model=os.environ.get("GLM_MODEL", "glm-4-flash").strip(),
        image_model=os.environ.get("IMAGE_MODEL", "glm-image").strip(),
        image_size=os.environ.get("IMAGE_SIZE", "1280x1280").strip(),
        video_model=os.environ.get("VIDEO_MODEL", "cogvideox-3").strip(),
        video_quality=os.environ.get("VIDEO_QUALITY", "speed").strip(),
        video_size=os.environ.get("VIDEO_SIZE", "1920x1080").strip(),
        video_fps=int(os.environ.get("VIDEO_FPS", "30")),
        debug_glm_only=os.environ.get("DEBUG_GLM_ONLY", "false").lower()
        in ("1", "true", "yes"),
        debug_stop_after_image=os.environ.get("DEBUG_STOP_AFTER_IMAGE", "false").lower()
        in ("1", "true", "yes"),
        music_root=ROOT / "assets" / "music",
        categories_path=ROOT / "music_categories.json",
        output_dir=ROOT / "output",
        music_align_enabled=os.environ.get("MUSIC_ALIGN_ENABLED", "true").lower()
        in ("1", "true", "yes"),
        music_silence_noise_db=float(os.environ.get("MUSIC_SILENCE_NOISE_DB", "-35")),
        music_silence_min_sec=float(os.environ.get("MUSIC_SILENCE_MIN_SEC", "0.3")),
        music_fallback_skip_sec=float(os.environ.get("MUSIC_FALLBACK_SKIP_SEC", "15")),
        music_random_extra_max_sec=float(
            os.environ.get("MUSIC_RANDOM_EXTRA_MAX_SEC", "90")
        ),
        music_seek_cache=os.environ.get("MUSIC_SEEK_CACHE", "true").lower()
        in ("1", "true", "yes"),
    )
