from __future__ import annotations

import json
from typing import Any, Mapping

import httpx

BASE = "https://open.bigmodel.cn"


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _api_error(body: Mapping[str, Any]) -> str | None:
    err = body.get("error")
    if isinstance(err, dict):
        msg = err.get("message") or err.get("code")
        if msg:
            return str(msg)
    return None


def chat_completions(
    api_key: str,
    *,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.6,
    timeout: float = 120.0,
) -> str:
    url = f"{BASE}/api/paas/v4/chat/completions"
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, headers=_headers(api_key), json=payload)
        data = r.json()
    if r.status_code >= 400:
        raise RuntimeError(_api_error(data) or r.text or f"HTTP {r.status_code}")
    msg = _api_error(data)
    if msg:
        raise RuntimeError(msg)
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"对话接口无 choices 返回: {json.dumps(data, ensure_ascii=False)[:800]}")
    content = (choices[0].get("message") or {}).get("content")
    if not content or not isinstance(content, str):
        raise RuntimeError("对话接口未返回文本 content")
    return content


def image_generations(
    api_key: str,
    *,
    model: str,
    prompt: str,
    size: str,
    timeout: float = 180.0,
) -> str:
    url = f"{BASE}/api/paas/v4/images/generations"
    payload = {"model": model, "prompt": prompt, "size": size}
    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, headers=_headers(api_key), json=payload)
        data = r.json()
    if r.status_code >= 400:
        raise RuntimeError(_api_error(data) or r.text or f"HTTP {r.status_code}")
    msg = _api_error(data)
    if msg:
        raise RuntimeError(msg)
    items = data.get("data") or []
    if not items or not isinstance(items[0], dict):
        raise RuntimeError(f"图像接口无 data[0]: {json.dumps(data, ensure_ascii=False)[:800]}")
    url_out = items[0].get("url")
    if not url_out:
        raise RuntimeError("图像接口未返回 url")
    return str(url_out)


def download_file(url: str, dest: str, timeout: float = 600.0) -> None:
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        with client.stream("GET", url) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)
