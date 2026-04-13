# Render / 其他容器平台：需本仓库根目录存在本文件（文件名 Dockerfile，首字母大写）
FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
# Render 会注入 PORT；Gradio 在 app.py 中读取。
# 配乐建议挂持久盘并设 MUSIC_ROOT（见 .env.example），勿把大体积 mp3 打进镜像。
EXPOSE 10000

CMD ["python", "app.py"]
