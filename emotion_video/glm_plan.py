from __future__ import annotations

import json
import re
from dataclasses import dataclass

from emotion_video.bigmodel_http import chat_completions
from emotion_video.categories import Category, allowed_keys


@dataclass(frozen=True)
class EmotionPlan:
    emotion_key: str
    image_prompt: str
    video_prompt: str


def _extract_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        text = m.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            data = json.loads(text[start : end + 1])
        else:
            raise
    if not isinstance(data, dict):
        raise ValueError("模型输出不是 JSON 对象")
    return data


def _system_prompt(categories: list[Category]) -> str:
    lines = [
        "你是影视分镜与配乐选曲助手。用户会给出带情感色彩的描述。",
        "你必须只输出一个 JSON 对象，不要 Markdown，不要解释。字段如下：",
        '- "emotion_key": 字符串，必须从下列 key 中精确选一个；',
        '- "image_prompt": 用于静态首帧的文生图描述（中文为主，可夹英文关键词），构图清晰、主体明确；',
        '- "video_prompt": 用于图生视频的动态描述，写在首帧基础上的动作、镜头与氛围延续（中文为主）。',
        "",
        "可选的 emotion_key 及含义：",
    ]
    for c in categories:
        extra = f"；配乐库取向：{c.music_profile}" if c.music_profile else ""
        lines.append(f"- {c.key}: {c.description}{extra}")
    lines.append("")
    lines.append("若情感不明显，emotion_key 选 calm。")
    return "\n".join(lines)


def plan_from_user_text(
    api_key: str,
    model: str,
    categories: list[Category],
    user_text: str,
) -> EmotionPlan:
    keys = allowed_keys(categories)
    content = chat_completions(
        api_key,
        model=model,
        messages=[
            {"role": "system", "content": _system_prompt(categories)},
            {"role": "user", "content": user_text.strip()},
        ],
    )
    data = _extract_json(content)
    ek = str(data.get("emotion_key", "")).strip()
    if ek not in keys:
        ek = "calm" if "calm" in keys else next(iter(keys))
    ip = str(data.get("image_prompt", "")).strip()
    vp = str(data.get("video_prompt", "")).strip()
    if not ip:
        ip = user_text.strip() or "电影感画面，柔和光线，细腻质感"
    if not vp:
        vp = "镜头缓慢推进，微风与光影轻微变化，情绪延续，电影感"
    return EmotionPlan(emotion_key=ek, image_prompt=ip, video_prompt=vp)
