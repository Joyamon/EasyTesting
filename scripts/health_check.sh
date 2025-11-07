#!/bin/bash
# scripts/health_check.sh

set -e

echo "执行健康检查..."

MAX_RETRIES=30
RETRY_COUNT=0

until curl -f http://localhost/health/ || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
    echo "等待应用启动... ($((RETRY_COUNT+1))/$MAX_RETRIES)"
    sleep 10
    RETRY_COUNT=$((RETRY_COUNT+1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "应用启动超时!"
    exit 1
fi

echo "应用健康检查通过!"