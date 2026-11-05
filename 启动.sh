#!/usr/bin/env sh
# AI4En 启动脚本：默认端口 8848，可用环境变量 AI4EN_PORT 覆盖
cd "$(dirname "$0")/app" || exit 1
export PYTHONUTF8=1
exec python3 server.py --port "${AI4EN_PORT:-8848}"
