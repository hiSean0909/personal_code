# ============================================================
# 翻译助手 Translator Agent — Dockerfile
# 构建说明：docker build -t translator-agent .
# 腾讯云服务器使用国内源加速 apt + pip
# ============================================================

FROM python:3.12-slim

LABEL maintainer="translator-agent"

# 1. 系统层面：apt 换国内源（腾讯云内网 + 阿里云公网双兜底），并安装时区/ca 证书
RUN set -eux; \
    cp /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list.d/debian.sources.bak 2>/dev/null || true; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      sed -i 's|deb.debian.org|mirrors.cloud.tencent.com|g; s|security.debian.org|mirrors.cloud.tencent.com|g' /etc/apt/sources.list.d/debian.sources; \
    fi; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        ca-certificates tzdata curl; \
    rm -rf /var/lib/apt/lists/*; \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime; \
    echo "Asia/Shanghai" > /etc/timezone

ENV TZ=Asia/Shanghai \
    LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 2. pip 换国内源（清华）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --upgrade pip setuptools wheel

WORKDIR /app

# 3. 先复制依赖清单，利用 Docker 层缓存
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 4. 非 root 用户运行，更安全
RUN groupadd -r appuser && useradd -r -g appuser -m -d /app appuser && \
    chown -R appuser:appuser /app

# 5. 复制代码
COPY --chown=appuser:appuser translator_agent.py translator_agent_prompts.md ./

USER appuser

# 6. 暴露端口 + 默认命令
EXPOSE 7860

ENV RUN_MODE=WEB \
    WEB_HOST=0.0.0.0 \
    WEB_PORT=7860

CMD ["python", "translator_agent.py"]
