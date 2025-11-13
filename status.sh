#!/bin/bash
# 状态检查脚本 - 指向 scripts/bin/status.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/scripts/bin/status.sh" "$@"
