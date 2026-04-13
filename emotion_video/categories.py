from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Category:
    key: str
    description: str
    music_profile: str


def load_categories(path: Path) -> list[Category]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw.get("categories") or []
    out: list[Category] = []
    for it in items:
        if isinstance(it, dict) and it.get("key"):
            out.append(
                Category(
                    key=str(it["key"]),
                    description=str(it.get("description", "")),
                    music_profile=str(it.get("music_profile", "")),
                )
            )
    if not out:
        raise RuntimeError(f"分类文件为空或格式错误: {path}")
    return out


def allowed_keys(categories: list[Category]) -> set[str]:
    return {c.key for c in categories}
