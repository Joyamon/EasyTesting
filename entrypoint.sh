#!/bin/bash
set -e
# 进入项目
cd /var/lib/jenkins/workspace/EasyTesting
#创建虚拟环境
python -m venv EasyTesting_env

pip install --upgrade setuptools wheel
# 激活虚拟环境
source EasyTesting_env/bin/activate

pip3 install -i http://nexus.prod.svc.yafex.io:8081/repository/pypi-proxy/simple/ --trusted-host nexus.prod.svc.yafex.io --no-cache-dir -r requirements.txt

# 迁移数据库
python manage.py makemigrations
python manage.py migrate &
# 运行项目

celery -A EasyTesting worker -l info &
celery -A EasyTesting beat -l info
python manage.py runserver 10.10.50.25:80
