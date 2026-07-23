#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

IMAGE_NAME="${IMAGE_NAME:-lanhu-mcp-server}"
IMAGE_TAG="${IMAGE_TAG:-local}"
DOCKERFILE="${DOCKERFILE:-Dockerfile}"
BUILD_CONTEXT="${BUILD_CONTEXT:-.}"
PLATFORM="${PLATFORM:-}"
NO_CACHE="${NO_CACHE:-false}"
PULL="${PULL:-false}"

show_help() {
  cat <<'EOF'
用法:
  ./build-image.sh [额外 docker build 参数]

环境变量:
  IMAGE_NAME      镜像名称，默认 lanhu-mcp-server
  IMAGE_TAG       镜像标签，默认 local
  DOCKERFILE      Dockerfile 路径，默认 Dockerfile
  BUILD_CONTEXT   构建上下文，默认 .
  PLATFORM        构建平台，例如 linux/amd64；为空时使用 Docker 默认平台
  HTTP_PROXY      透传到 Dockerfile 的 HTTP_PROXY build-arg
  HTTPS_PROXY     透传到 Dockerfile 的 HTTPS_PROXY build-arg
  NO_CACHE=true   启用 --no-cache
  PULL=true       启用 --pull

示例:
  ./build-image.sh
  IMAGE_TAG=v1.0.0 ./build-image.sh
  PLATFORM=linux/amd64 NO_CACHE=true ./build-image.sh
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  show_help
  exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "错误：未找到 docker 命令，请先安装 Docker。" >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "错误：Docker 服务不可用，请先启动 Docker。" >&2
  exit 1
fi

if [[ ! -f "$DOCKERFILE" ]]; then
  echo "错误：未找到 Dockerfile：$DOCKERFILE" >&2
  exit 1
fi

cmd=(docker build)

if [[ -n "$PLATFORM" ]]; then
  cmd+=(--platform "$PLATFORM")
fi

if [[ "$NO_CACHE" == "true" ]]; then
  cmd+=(--no-cache)
fi

if [[ "$PULL" == "true" ]]; then
  cmd+=(--pull)
fi

if [[ -n "${HTTP_PROXY:-}" ]]; then
  cmd+=(--build-arg "HTTP_PROXY=$HTTP_PROXY")
fi

if [[ -n "${HTTPS_PROXY:-}" ]]; then
  cmd+=(--build-arg "HTTPS_PROXY=$HTTPS_PROXY")
fi

export DOCKER_BUILDKIT="${DOCKER_BUILDKIT:-1}"

echo "开始构建镜像：${IMAGE_NAME}:${IMAGE_TAG}"
echo "Dockerfile：$DOCKERFILE"
echo "构建上下文：$BUILD_CONTEXT"

cmd+=("$@" -f "$DOCKERFILE" -t "${IMAGE_NAME}:${IMAGE_TAG}" "$BUILD_CONTEXT")
"${cmd[@]}"

echo "镜像构建完成：${IMAGE_NAME}:${IMAGE_TAG}"
