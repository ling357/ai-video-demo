from __future__ import annotations

import time
from pathlib import Path

from zai import ZhipuAiClient

from emotion_video.bigmodel_http import download_file


def generate_video_from_image(
    api_key: str,
    *,
    model: str,
    image_url: str,
    prompt: str,
    quality: str,
    size: str,
    fps: int,
    poll_interval: float = 5.0,
    max_wait_sec: float = 900.0,
) -> str:
    client = ZhipuAiClient(api_key=api_key)
    submitted = client.videos.generations(
        model=model,
        prompt=prompt,
        image_url=image_url,
        quality=quality,
        with_audio=False,
        size=size,
        fps=fps,
    )
    task_id = submitted.id
    if not task_id:
        raise RuntimeError("清影未返回任务 id")

    deadline = time.monotonic() + max_wait_sec
    last_status = ""
    while time.monotonic() < deadline:
        result = client.videos.retrieve_videos_result(task_id)
        last_status = result.task_status
        st = (result.task_status or "").upper()
        if st == "FAIL":
            raise RuntimeError("清影任务失败")
        if st == "SUCCESS":
            if not result.video_result:
                raise RuntimeError("清影成功但无 video_result")
            return result.video_result[0].url
        time.sleep(poll_interval)

    raise TimeoutError(f"清影超时（最后状态: {last_status}）")


def download_video(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    download_file(url, str(path))
