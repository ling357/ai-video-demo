from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from emotion_video.bigmodel_http import download_file, image_generations
from emotion_video.categories import load_categories
from emotion_video.config import Settings
from emotion_video.glm_plan import plan_from_user_text
from emotion_video.audio_align import compute_bgm_seek_seconds
from emotion_video.merge import merge_video_bgm
from emotion_video.music import pick_random_track
from emotion_video import qingying


@dataclass
class PipelineResult:
    emotion_key: str
    image_prompt: str
    video_prompt: str
    image_url: str
    image_local_path: Path | None
    video_raw_path: Path | None
    music_path: Path | None
    final_path: Path | None
    log: str


def run_pipeline(
    settings: Settings,
    user_text: str,
    progress=None,
) -> PipelineResult:
    log_lines: list[str] = []
    categories = load_categories(settings.categories_path)

    def log(msg: str) -> None:
        log_lines.append(msg)
        if progress:
            progress(msg)

    plan = plan_from_user_text(
        settings.zhipu_api_key,
        settings.glm_model,
        categories,
        user_text,
    )
    log(f"GLM 规划: emotion={plan.emotion_key}")

    if settings.debug_glm_only:
        try:
            music = pick_random_track(settings.music_root, plan.emotion_key)
        except FileNotFoundError as e:
            return PipelineResult(
                plan.emotion_key,
                plan.image_prompt,
                plan.video_prompt,
                "",
                None,
                None,
                None,
                None,
                "\n".join(log_lines + [str(e)]),
            )
        return PipelineResult(
            plan.emotion_key,
            plan.image_prompt,
            plan.video_prompt,
            "",
            None,
            None,
            music,
            None,
            "\n".join(log_lines + [f"DEBUG_GLM_ONLY: 已选曲 {music.name}"]),
        )

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex[:10]

    log("请求文生图 glm-image …")
    image_url = image_generations(
        settings.zhipu_api_key,
        model=settings.image_model,
        prompt=plan.image_prompt,
        size=settings.image_size,
    )
    log("文生图 URL 已返回，下载首帧预览 …")
    image_local = settings.output_dir / f"{run_id}_ref.jpg"
    download_file(image_url, str(image_local))

    if settings.debug_stop_after_image:
        return PipelineResult(
            plan.emotion_key,
            plan.image_prompt,
            plan.video_prompt,
            image_url,
            image_local,
            None,
            None,
            None,
            "\n".join(log_lines + ["DEBUG_STOP_AFTER_IMAGE: 已停止"]),
        )

    log("提交清影图生视频（轮询中）…")
    video_url = qingying.generate_video_from_image(
        settings.zhipu_api_key,
        model=settings.video_model,
        image_url=image_url,
        prompt=plan.video_prompt,
        quality=settings.video_quality,
        size=settings.video_size,
        fps=settings.video_fps,
    )
    raw_path = settings.output_dir / f"{run_id}_video_raw.mp4"
    log("下载视频文件 …")
    qingying.download_video(video_url, raw_path)

    log("选取配乐 …")
    music_path = pick_random_track(settings.music_root, plan.emotion_key)
    log(f"配乐: {music_path.name}")

    final_path = settings.output_dir / f"{run_id}_final.mp4"
    seek_sec = 0.0
    if settings.music_align_enabled:
        log("计算 BGM 切入位置（跳过片头静音 + 随机窗）…")
        seek_sec = compute_bgm_seek_seconds(
            raw_path,
            music_path,
            noise_db=settings.music_silence_noise_db,
            min_silence_sec=settings.music_silence_min_sec,
            fallback_skip_sec=settings.music_fallback_skip_sec,
            random_extra_max_sec=settings.music_random_extra_max_sec,
            use_cache=settings.music_seek_cache,
        )
        log(f"BGM 从 {seek_sec:.2f}s 起混入")
    log("FFmpeg 合成 …")
    merge_video_bgm(raw_path, music_path, final_path, audio_seek_sec=seek_sec)

    return PipelineResult(
        plan.emotion_key,
        plan.image_prompt,
        plan.video_prompt,
        image_url,
        image_local,
        raw_path,
        music_path,
        final_path,
        "\n".join(log_lines),
    )
