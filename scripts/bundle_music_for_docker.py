"""
从 assets/music/<情绪>/ 中各取前 3 首 .mp3（按文件名排序），复制到 bundled_music/<情绪>/01..03.mp3，
供 Docker 镜像内置。请在确认版权归属后使用。

用法（项目根目录）:  python scripts/bundle_music_for_docker.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "music"
DST = ROOT / "bundled_music"
EMOTIONS = ("happy", "calm", "sad", "tense")


def main() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    for emotion in EMOTIONS:
        folder = SRC / emotion
        if not folder.is_dir():
            raise SystemExit(f"缺少目录: {folder}")
        mp3s = sorted(
            p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".mp3"
        )
        if len(mp3s) < 3:
            raise SystemExit(f"{emotion} 下不足 3 首 mp3（当前 {len(mp3s)}）")
        for i, src in enumerate(mp3s[:3], start=1):
            out = DST / emotion / f"{i:02d}.mp3"
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out)
            print(f"{emotion}: {src.name} -> {out.relative_to(ROOT)}")
    print("完成。请 git add bundled_music 并提交。")


if __name__ == "__main__":
    main()
