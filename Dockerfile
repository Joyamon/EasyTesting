# 使用华为云镜像
#FROM swr.cn-north-4.myhuaweicloud.com/hubpaas/python:3.9-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    musl-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 使用华为云PyPI镜像
RUN pip config set global.index-url https://repo.huaweicloud.com/repository/pypi/simple

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

RUN useradd -m -u 1000 django && chown -R django:django /app
USER django

EXPOSE 8000

CMD ["gunicorn", "easy_testing.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]