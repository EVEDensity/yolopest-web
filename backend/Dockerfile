FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖（libgl1 供 OpenCV 使用）
RUN apt-get update && apt-get install -y \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# ── 第1层：Python依赖（变更最少，缓存命中率最高） ──
COPY requirements.txt .
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn --no-cache-dir -r requirements.txt

# ── 第2层：本地 ultralytics（偶尔变更） ──
COPY ultralytics /app/ultralytics/
RUN pip install -e /app/ultralytics

# ── 第3层：应用代码（变更最频繁） ──
COPY . .

# 确保静态文件目录存在
RUN mkdir -p app/static app/static/videos app/static/images app/static/results app/static/avatars

# 使用 Gunicorn + Uvicorn workers（生产就绪）
CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
