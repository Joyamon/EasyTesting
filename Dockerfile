#FROM registry-harbor.yafex.cn/base/nginx-uwsgi:3.11.5v1
FROM registry-harbor.yafex.cn/base/nginx-uwsgi:3.8.10v4
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh
