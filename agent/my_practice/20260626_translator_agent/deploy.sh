#!/usr/bin/env bash
# ============================================================
# 腾讯云（/阿里云/华为云）服务器 一键部署脚本（Ubuntu 22.04 / Debian 12 推荐）
# 运行位置：/opt/translator-agent
# 用法：
#   bash deploy.sh install_docker   # 第一次：安装 Docker + Compose + 腾讯云 apt 源
#   bash deploy.sh start            # 构建并启动容器（需已填 .env）
#   bash deploy.sh logs             # 查看实时日志
#   bash deploy.sh stop             # 停止
#   bash deploy.sh restart          # 重启
#   bash deploy.sh update           # 重新构建 + 启动（代码更新后执行）
#   bash deploy.sh status           # 容器状态 + health
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CMD="${1:-status}"

log_info()  { echo -e "\033[36m[INFO]\033[0m  $*"; }
log_ok()    { echo -e "\033[32m[ OK ]\033[0m  $*"; }
log_warn()  { echo -e "\033[33m[WARN]\033[0m  $*"; }
log_err()   { echo -e "\033[31m[ERR ]\033[0m  $*"; }

ensure_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        log_err "未检测到 docker，请先执行：bash deploy.sh install_docker"
        exit 1
    fi
}

ensure_env() {
    if [ ! -f .env ]; then
        log_warn ".env 不存在，已从 .env.example 生成副本，请编辑 .env 填入 DEEPSEEK_API_KEY 后再启动"
        cp .env.example .env || true
        return 1
    fi
    if ! grep -qE '^DEEPSEEK_API_KEY=.+' .env 2>/dev/null; then
        log_err ".env 中未配置 DEEPSEEK_API_KEY，启动会失败"
        return 1
    fi
    return 0
}

case "$CMD" in
install_docker)
    log_info "开始安装 Docker + Docker Compose（使用国内镜像）"

    # 1. 切腾讯云 apt 源（Debian / Ubuntu 通用尝试）
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then
        sudo sed -i \
            's|deb.debian.org|mirrors.cloud.tencent.com|g; s|security.debian.org|mirrors.cloud.tencent.com|g' \
            /etc/apt/sources.list.d/debian.sources
    elif [ -f /etc/apt/sources.list ]; then
        sudo sed -i.bak \
            -e 's|http://archive.ubuntu.com|https://mirrors.cloud.tencent.com|g' \
            -e 's|http://security.ubuntu.com|https://mirrors.cloud.tencent.com|g' \
            -e 's|deb.debian.org|mirrors.cloud.tencent.com|g' \
            /etc/apt/sources.list
    fi

    sudo apt-get update -y
    sudo apt-get install -y ca-certificates curl gnupg lsb-release

    # 2. 安装 Docker（走国内 daocloud 一键脚本，兼容 Debian/Ubuntu/CentOS）
    if ! command -v docker >/dev/null 2>&1; then
        log_info "安装 Docker Engine..."
        curl -fsSL https://get.daocloud.io/docker | sh
        sudo systemctl enable docker
        sudo systemctl start docker
    fi

    # 3. 安装 docker compose 插件
    if ! docker compose version >/dev/null 2>&1; then
        log_info "安装 docker compose 插件..."
        DOCKER_CONFIG=${DOCKER_CONFIG:-/usr/local/lib/docker/cli-plugins}
        sudo mkdir -p "$DOCKER_CONFIG"
        VER=$(curl -fsSL "https://api.github.com/repos/docker/compose/releases/latest" | grep '"tag_name"' | sed -E 's/.*"v?([^"]+)".*/\1/' | head -n1)
        if [ -z "$VER" ]; then VER="v2.29.2"; fi
        sudo curl -SL "https://github.com/docker/compose/releases/download/v${VER}/docker-compose-$(uname -s)-$(uname -m)" \
            -o "$DOCKER_CONFIG/docker-compose"
        sudo chmod +x "$DOCKER_CONFIG/docker-compose"
    fi

    # 4. Docker hub 国内镜像加速
    sudo mkdir -p /etc/docker
    if [ ! -f /etc/docker/daemon.json ] || ! grep -q "mirrors" /etc/docker/daemon.json; then
        cat <<'JSON' | sudo tee /etc/docker/daemon.json >/dev/null
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://hub.rat.dev",
    "https://docker.1panel.live"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "3"
  }
}
JSON
        sudo systemctl daemon-reload
        sudo systemctl restart docker
    fi

    # 5. 当前用户加入 docker 组，避免每次都 sudo
    if [ "$(id -u)" -ne 0 ]; then
        sudo usermod -aG docker "$USER"
        log_warn "已把用户 $USER 加入 docker 组，请退出 SSH 后重新登录生效，或临时执行：newgrp docker"
    fi

    log_ok "安装完成"
    docker --version
    docker compose version
    ;;

start)
    ensure_docker
    ensure_env || exit 1
    log_info "构建镜像 + 启动容器..."
    docker compose up -d --build
    log_ok "已启动。健康状态："
    sleep 2
    docker compose ps
    log_info "查看日志：bash deploy.sh logs"
    ;;

stop)
    ensure_docker
    log_info "停止容器..."
    docker compose down
    log_ok "已停止"
    ;;

restart)
    ensure_docker
    log_info "重启容器..."
    docker compose restart
    docker compose ps
    ;;

update)
    ensure_docker
    log_info "拉新代码已假设到位（通过 upload.ps1 / git），重新构建启动..."
    docker compose up -d --build
    log_ok "更新完成。最近日志："
    docker compose logs --tail=30
    ;;

logs)
    ensure_docker
    docker compose logs -f --tail=100
    ;;

status)
    ensure_docker
    echo "------- 容器状态 -------"
    docker compose ps
    echo "------- 健康检查 -------"
    docker compose ps --format '{{.Name}} -> health={{.Health}}'
    echo "------- 最近 20 行日志 -------"
    docker compose logs --tail=20 || true
    ;;

*)
    echo "用法：bash deploy.sh {install_docker|start|stop|restart|update|logs|status}"
    exit 1
    ;;
esac
