"""
将「分类」目录下按调式/速度整理好的配乐，复制到 assets/music 下四种情绪目录：

  大调快速 → happy    大调慢速 → calm
  小调快速 → tense    小调慢速 → sad

「特殊」不参与自动映射，请手动按需复制。

用法（项目根目录）:  python scripts/import_music_from_fenlei.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

MAPPING = {
    "大调快速": "happy",
    "大调慢速": "calm",
    "小调快速": "tense",
    "小调慢速": "sad",
}

_AUDIO_EXT = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src_root = root / "分类"
    if not src_root.is_dir():
        raise SystemExit(f"未找到目录: {src_root}")

    music_assets = root / "assets" / "music"
    copied = 0
    for cn_name, emotion in MAPPING.items():
        src_dir = src_root / cn_name
        if not src_dir.is_dir():
            print(f"跳过（不存在）: {src_dir}")
            continue
        dst_dir = music_assets / emotion
        dst_dir.mkdir(parents=True, exist_ok=True)
        for f in sorted(src_dir.iterdir()):
            if not f.is_file():
                continue
            if f.suffix.lower() not in _AUDIO_EXT:
                continue
            dst = dst_dir / f.name
            shutil.copy2(f, dst)
            copied += 1
            print(f"{emotion} <- {f.name}", flush=True)

    # 去掉合成占位，避免与真曲随机混抽
    for emotion in MAPPING.values():
        ph = music_assets / emotion / "placeholder_bgm.wav"
        if ph.is_file():
            ph.unlink()
            print(f"已删除占位: {ph}")

    print(f"完成，共复制 {copied} 个音频文件。")


if __name__ == "__main__":
    main()
