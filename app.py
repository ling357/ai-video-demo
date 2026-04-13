"""
情感提示词 → GLM 规划 → 智谱 glm-image 文生图 → 清影图生视频 → 分类配乐 + FFmpeg 合成。

运行（在项目根目录）:
  pip install -r requirements.txt
  复制 .env.example 为 .env，填入 ZHIPU_API_KEY
  在 assets/music/<情绪>/ 下放入 mp3/wav
  python app.py
"""

from __future__ import annotations

import os
import sys

# Render / 云平台会设置 PORT，且必须监听 0.0.0.0
def _gradio_bind() -> tuple[str, int]:
    port_s = os.environ.get("PORT")
    if port_s:
        return "0.0.0.0", int(port_s)
    return "127.0.0.1", int(os.environ.get("GRADIO_SERVER_PORT", "7860"))
import traceback
from pathlib import Path


def _ensure_localhost_bypasses_proxy() -> None:
    """Gradio 启动时会请求 127.0.0.1/.../startup-events；若走系统代理常返回 502。"""
    add = ("127.0.0.1", "localhost", "::1")
    for key in ("NO_PROXY", "no_proxy"):
        cur = os.environ.get(key, "")
        parts = [p.strip() for p in cur.split(",") if p.strip()]
        for a in add:
            if a not in parts:
                parts.append(a)
        os.environ[key] = ",".join(parts)


_ensure_localhost_bypasses_proxy()

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import gradio as gr

from emotion_video.config import load_settings
from emotion_video.pipeline import run_pipeline


def _run(user_text: str):
    user_text = (user_text or "").strip()
    if not user_text:
        return None, None, None, "", "请输入情感或场景描述。"
    try:
        settings = load_settings()
    except RuntimeError as e:
        return None, None, None, "", str(e)

    log_lines: list[str] = []

    def progress(msg: str) -> None:
        log_lines.append(msg)

    try:
        r = run_pipeline(settings, user_text, progress=progress)
    except Exception:
        err = traceback.format_exc()
        return None, None, None, "\n".join(log_lines), err

    detail = (
        f"emotion_key: {r.emotion_key}\n\n"
        f"image_prompt:\n{r.image_prompt}\n\n"
        f"video_prompt:\n{r.video_prompt}\n\n"
        f"image_url:\n{r.image_url or '(无)'}"
    )
    full_log = "\n".join(log_lines) + "\n\n---\n" + r.log
    img = str(r.image_local_path) if r.image_local_path else None
    vid = str(r.final_path) if r.final_path else None
    aud = str(r.music_path) if r.music_path else None
    return img, vid, aud, detail, full_log


with gr.Blocks(title="情感视听 Demo（清影 + 配乐）") as demo:
    gr.Markdown(
        "## 情感视听 Demo\n"
        "输入带情绪色彩的描述：系统将调用 **GLM** 规划情绪与画面文案，**固定先文生图**（glm-image），再以该图调用 **清影** 生成视频，"
        "并从 `assets/music/<情绪>/` 随机选曲（仅四种：happy / calm / sad / tense，对应「分类」下大调快、大调慢、小调慢、小调快），用 FFmpeg 合成成片。"
    )
    inp = gr.Textbox(
        label="情感 / 场景描述",
        lines=3,
        placeholder="例如：雨后傍晚独自在站台等车，有点失落但又平静。",
    )
    btn = gr.Button("生成", variant="primary")
    ref_img = gr.Image(label="文生图首帧（本地）", type="filepath")
    out_vid = gr.Video(label="成片（视频 + 所选 BGM）")
    out_aud = gr.Audio(label="所选配乐", type="filepath")
    plan_md = gr.Textbox(label="规划摘要", lines=12)
    log_box = gr.Textbox(label="运行日志", lines=16)

    btn.click(_run, inp, [ref_img, out_vid, out_aud, plan_md, log_box])

if __name__ == "__main__":
    _host, _port = _gradio_bind()
    demo.launch(
        ssr_mode=False,
        server_name=_host,
        server_port=_port,
        inbrowser=False,
    )
