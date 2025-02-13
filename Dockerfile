# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 暴露服务端口
EXPOSE 5000

# 启动命令
CMD ["gunicorn", "workflow_manager.app:app", "-b", "0.0.0.0:5000", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--timeout", "120"]