FROM registry.cn-hangzhou.aliyuncs.com/google_containers/python:3.9-alpine

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app/

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建SQLite数据库目录（如果需要）
RUN mkdir -p /app/data

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 应用数据库迁移
RUN python manage.py migrate

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]