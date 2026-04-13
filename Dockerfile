# Render / 其他容器平台：需本仓库根目录存在本文件（文件名 Dockerfile，首字母大写）
FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# 每类 3 首（bundled_music/，短文件名），合并进 assets/music 后删除副本
RUN cp -r bundled_music/. assets/music/ && rm -rf bundled_music

ENV PYTHONUNBUFFERED=1
# Render 会注入 PORT；Gradio 在 app.py 中读取。
# 本地 assets/music 下大量 mp3 由 .dockerignore 排除；镜像仅含 bundled_music 复制的 12 首。
EXPOSE 10000

CMD ["python", "app.py"]
