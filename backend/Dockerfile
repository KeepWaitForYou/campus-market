# 校园二手交易平台 - 后端镜像
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai

WORKDIR /app

# MySQL 驱动使用 PyMySQL（纯 Python），无需 apt 编译依赖

# 先装依赖，利用 Docker 层缓存（国内网络：腾讯云 PyPI 主源 + 阿里云备用）
COPY requirements.txt ./
RUN pip install --no-cache-dir \
        -i https://mirrors.cloud.tencent.com/pypi/simple/ \
        --extra-index-url https://mirrors.aliyun.com/pypi/simple/ \
        -r requirements.txt

# 复制项目代码
COPY . .

# 媒体与静态目录
RUN mkdir -p /app/media /app/static

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]