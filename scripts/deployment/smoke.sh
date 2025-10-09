#!/bin/bash

# 简易冒烟测试脚本
# 用法： ./scripts/deployment/smoke.sh [BACKEND_PORT] (默认 3007)

BACKEND_PORT=${1:-3007}
BASE="http://localhost:$BACKEND_PORT"

pass_cnt=0
fail_cnt=0

check() {
  local name="$1"
  local url="$2"
  local code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "$url")
  if [ "$code" = "200" ] || [ "$code" = "204" ]; then
    echo "✅ $name ($code)"
    pass_cnt=$((pass_cnt+1))
  else
    echo "❌ $name ($code) - $url"
    fail_cnt=$((fail_cnt+1))
  fi
}

echo "🔍 冒烟测试 - API: $BASE"
check "健康检查" "$BASE/health"
check "根路径" "$BASE/"
check "API 文档" "$BASE/docs"

# 常用公开接口（需确保路由存在，失败不阻断）
curl -s -o /dev/null -w "%{http_code}" --max-time 3 "$BASE/api/v1/payment/packages" >/dev/null 2>&1 && \
  echo "✅ 支付套餐接口 (GET /api/v1/payment/packages)" || \
  echo "⚠️ 支付套餐接口不可达或需鉴权"

echo "\n结果: 通过 $pass_cnt 项, 失败 $fail_cnt 项"
if [ $fail_cnt -gt 0 ]; then
  exit 1
fi
exit 0

