#!/bin/bash

# ============================================================
# 生产环境回滚脚本 - 在生产服务器上执行
# 用法: bash 3-rollback.sh [版本时间戳]
# 示例: bash 3-rollback.sh 20251113_160054
#       bash 3-rollback.sh  (不指定则回滚到最近的备份)
# ============================================================

set -e

# 颜色定义
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
RED='\\033[0;31m'
BLUE='\\033[0;34m'
NC='\\033[0m'

# 配置
BACKUP_DIR="/opt/backups"
PROJECT_PATH="/opt/stock-analysis-system"
BACKUP_VERSION="${1:-}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}股票分析系统 - 版本回滚${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 列出可用备份
echo -e "${YELLOW}可用备份版本:${NC}"
if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]; then
    echo -e "${RED}❌ 备份目录不存在或为空: $BACKUP_DIR${NC}"
    exit 1
fi

# 显示所有备份
echo ""
backups=()
for backup in $(ls -1dt "$BACKUP_DIR"/stock-analysis-system_* 2>/dev/null | head -5); do
    backup_name=$(basename "$backup")
    backup_date=$(stat -f %Sm -t '%Y-%m-%d %H:%M:%S' "$backup" 2>/dev/null || date -d @$(stat -c %Y "$backup" 2>/dev/null) '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "未知")
    backups+=("$backup_name")
    echo "  • $backup_name (备份时间: $backup_date)"
done

echo ""

# 如果未指定版本，使用最新备份
if [ -z "$BACKUP_VERSION" ]; then
    BACKUP_VERSION="${backups[0]}"
    echo -e "${YELLOW}未指定版本,将使用最近的备份: $BACKUP_VERSION${NC}"
    echo ""
fi

# 验证备份存在
BACKUP_PATH="$BACKUP_DIR/$BACKUP_VERSION"
if [ ! -d "$BACKUP_PATH" ]; then
    echo -e "${RED}❌ 备份不存在: $BACKUP_PATH${NC}"
    exit 1
fi

# 确认回滚
echo -e "${YELLOW}⚠️  警告: 这将回滚到版本 $BACKUP_VERSION${NC}"
read -p "确认回滚? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}回滚已取消${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}开始回滚流程...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 步骤 1: 停止服务
echo -e "${YELLOW}步骤 1/5: 停止服务${NC}"
echo "  - 停止 Gunicorn..."
pkill -9 gunicorn 2>/dev/null || true
sleep 2
echo -e "${GREEN}✓ Gunicorn 已停止${NC}"
echo ""

# 步骤 2: 备份当前版本
echo -e "${YELLOW}步骤 2/5: 备份当前版本${NC}"
FAILED_VERSION=$(date +%Y%m%d_%H%M%S)
FAILED_BACKUP="$BACKUP_DIR/stock-analysis-system_failed_${FAILED_VERSION}"
echo "  - 备份失败版本到: $FAILED_BACKUP"
cp -r "$PROJECT_PATH" "$FAILED_BACKUP" 2>/dev/null || true
echo -e "${GREEN}✓ 失败版本已备份${NC}"
echo ""

# 步骤 3: 恢复备份
echo -e "${YELLOW}步骤 3/5: 恢复备份版本${NC}"
echo "  - 清理当前项目目录..."
rm -rf "$PROJECT_PATH"
echo "  - 恢复备份版本..."
cp -r "$BACKUP_PATH" "$PROJECT_PATH"
echo "  - 修复权限..."
sudo chown -R ubuntu:ubuntu "$PROJECT_PATH"
echo -e "${GREEN}✓ 备份版本已恢复${NC}"
echo ""

# 步骤 4: 启动服务
echo -e "${YELLOW}步骤 4/5: 启动服务${NC}"
echo "  - 启动 Gunicorn..."
cd "$PROJECT_PATH/backend"

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
fi

nohup gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:3007 \
  --access-logfile /var/log/gunicorn-access.log \
  --error-logfile /var/log/gunicorn-error.log \
  --daemon \
  app.main:app

sleep 3

echo "  - 启动 Nginx..."
sudo systemctl start nginx 2>/dev/null || true
echo -e "${GREEN}✓ 服务已启动${NC}"
echo ""

# 步骤 5: 验证回滚
echo -e "${YELLOW}步骤 5/5: 验证回滚${NC}"
echo ""

echo "  后端进程:"
ps aux | grep -E '[g]unicorn|[a]pp.main' | grep -v grep | wc -l | xargs echo "    运行进程数:"

echo ""
echo "  监听端口:"
netstat -tlnp 2>/dev/null | grep -E '3007|:80 ' | awk '{print "    " $4 " (" $7 ")"}' || true

echo ""
echo "  API 健康检查:"
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3007/health)
if [ "$HEALTH_STATUS" == "200" ]; then
    echo -e "    ${GREEN}✓ 健康检查通过 (HTTP $HEALTH_STATUS)${NC}"
else
    echo -e "    ${YELLOW}⚠️  健康检查返回 HTTP $HEALTH_STATUS${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🎉 版本回滚成功！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo "📋 回滚信息："
echo "  回滚版本: $BACKUP_VERSION"
echo "  项目路径: $PROJECT_PATH"
echo "  失败版本备份: $FAILED_BACKUP"
echo "  回滚时间: $(date)"
echo ""

echo "🔍 后续操作："
echo "  查看后端日志: tail -f /var/log/gunicorn-error.log"
echo "  查看 Nginx 日志: tail -f /var/log/nginx/stock-analysis-error.log"
echo "  再次回滚: bash $PROJECT_PATH/scripts/deploy/3-rollback.sh [版本]"
echo ""
