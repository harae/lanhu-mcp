FROM docker.1ms.run/python:3.10-slim

WORKDIR /app

ARG HTTP_PROXY
ARG HTTPS_PROXY

ENV HTTP_PROXY=${HTTP_PROXY}
ENV HTTPS_PROXY=${HTTPS_PROXY}
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium && playwright install-deps chromium

# 复制服务代码、扩展模块、静态页面和默认模板。
COPY lanhu_mcp_server.py ./
COPY lanhu_mcp_ext.py ./
COPY lanhu_mcp_templates.py ./
COPY static/ ./static/
COPY db/ ./db/

# 运行时写入路径：
# - /app/data: 截图、资源缓存、留言板数据
# - /app/logs: 日志
# - /app/db: 默认 markdown 模板 + 账号 Cookie + 用户自定义覆盖模板
RUN mkdir -p /app/data /app/logs /app/db \
    && find /app/db -type d -exec chmod 755 {} \; \
    && find /app/db -type f -exec chmod 644 {} \;

# 为 db 声明卷，容器首次启动时会带着镜像中的默认模板初始化卷内容，
# 后续用户编辑 account_cookies.json 和 markdown 覆盖模板可持久化。
VOLUME ["/app/db"]

ENV HTTP_PROXY=
ENV HTTPS_PROXY=

EXPOSE 8000

CMD ["python", "lanhu_mcp_server.py"]
