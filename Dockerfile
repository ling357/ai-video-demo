# Render / 其他容器平台：需本仓库根目录存在本文件（文件名 Dockerfile，首字母大写）
FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# 每类 3 首合成 WAV（仓库内 docker_embed/），合并进 assets/music 后删除副本以减小层内冗余
RUN cp -r docker_embed/. assets/music/ && rm -rf docker_embed

ENV PYTHONUNBUFFERED=1
# Render 会注入 PORT；Gradio 在 app.py 中读取。
# 大体积 mp3 由 .dockerignore 排除；镜像内仅有上述 embed_*.wav，本地曲库仍用 assets/music。
EXPOSE 10000

CMD ["python", "app.py"]
