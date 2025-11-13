#!/bin/bash
# 启动脚本 - 指向 scripts/bin/start.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/scripts/bin/start.sh" "$@"
