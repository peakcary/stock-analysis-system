#!/bin/bash
# 停止脚本 - 指向 scripts/bin/stop.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/scripts/bin/stop.sh" "$@"
