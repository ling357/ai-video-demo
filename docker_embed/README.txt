本目录音频为脚本生成的合成 WAV（无版权限制），每类情绪 3 首，用于 Docker / Render 等无法挂载本地曲库的环境。

重新生成（项目根目录）：
  python scripts/generate_placeholder_bgm.py docker-embed

生成后请提交到 Git，以便镜像构建时 COPY 进 assets/music。
