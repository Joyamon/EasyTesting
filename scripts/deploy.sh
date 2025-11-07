#!/bin/bash
# scripts/deploy.sh

set -e

echo "开始部署 EasyTesting..."

# 拉取最新镜像
docker-compose pull

# 停止现有服务
docker-compose down

# 启动新服务
docker-compose up -d

# 执行数据库迁移
docker-compose exec web python manage.py migrate --noinput

# 收集静态文件
docker-compose exec web python manage.py collectstatic --noinput

# 健康检查
./scripts/health_check.sh

echo "部署完成!"