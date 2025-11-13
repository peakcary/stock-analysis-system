#!/bin/bash

# ============================================================
# 服务器端部署脚本 - 在生产服务器上执行
# 使用方式: bash 2-remote-deploy.sh stock-analysis-system_20250113_120000
# ============================================================

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
PACKAGE_NAME="$1"
if [ -z "$PACKAGE_NAME" ]; then
    echo -e "${RED}❌ 错误: 请指定部署包名称${NC}"
    echo "用法: bash 2-remote-deploy.sh stock-analysis-system_YYYYMMDD_HHMMSS"
    exit 1
fi

PROJECT_PATH="/opt/stock-analysis-system"
UPLOAD_DIR="/tmp"
BACKUP_DIR="/opt/backups"
CURRENT_VERSION_FILE="$PROJECT_PATH/.version"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}股票分析系统 - 服务器部署${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. 验证部署包
echo -e "${YELLOW}步骤 1/8: 验证部署包${NC}"
if [ ! -f "$UPLOAD_DIR/$PACKAGE_NAME.tar.gz" ]; then
    echo -e "${RED}❌ 部署包不存在: $UPLOAD_DIR/$PACKAGE_NAME.tar.gz${NC}"
    exit 1
fi

# 验证 MD5
if [ -f "$UPLOAD_DIR/$PACKAGE_NAME.md5" ]; then
    echo "  - 验证文件完整性..."
    cd "$UPLOAD_DIR"
    md5sum -c "$PACKAGE_NAME.md5" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 文件完整性验证通过${NC}"
    else
        echo -e "${RED}❌ 文件完整性验证失败${NC}"
        exit 1
    fi
fi
echo ""

# 2. 备份当前版本
echo -e "${YELLOW}步骤 2/8: 备份当前版本${NC}"
mkdir -p "$BACKUP_DIR"

if [ -d "$PROJECT_PATH" ]; then
    CURRENT_VERSION=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/stock-analysis-system_${CURRENT_VERSION}"

    echo "  - 备份当前版本到: $BACKUP_PATH"
    cp -r "$PROJECT_PATH" "$BACKUP_PATH"

    # 保存版本信息
    echo "$CURRENT_VERSION" > "$BACKUP_DIR/.last-backup"

    echo -e "${GREEN}✓ 备份完成${NC}"
else
    echo -e "${YELLOW}⚠️  项目目录不存在，跳过备份${NC}"
fi
echo ""

# 3. 停止服务
echo -e "${YELLOW}步骤 3/8: 停止服务${NC}"
echo "  - 停止 Gunicorn..."
pkill -9 gunicorn 2>/dev/null || true
sleep 2
echo -e "${GREEN}✓ 服务已停止${NC}"
echo ""

# 4. 解包新版本
echo -e "${YELLOW}步骤 4/8: 解包新版本${NC}"
echo "  - 提取文件..."
cd "$UPLOAD_DIR"
tar -xzf "$PACKAGE_NAME.tar.gz"

# 清理旧项目目录
if [ -d "$PROJECT_PATH" ]; then
    rm -rf "$PROJECT_PATH"
fi

# 创建新项目目录
mkdir -p "$PROJECT_PATH"
cp -r "$UPLOAD_DIR/$PACKAGE_NAME"/* "$PROJECT_PATH/"

# 清理上传文件
rm -rf "$UPLOAD_DIR/$PACKAGE_NAME" "$UPLOAD_DIR/$PACKAGE_NAME.tar.gz" "$UPLOAD_DIR/$PACKAGE_NAME.md5"

# 修复权限
sudo chown -R ubuntu:ubuntu "$PROJECT_PATH"

echo -e "${GREEN}✓ 文件部署完成${NC}"
echo ""

# 5. 更新配置
echo -e "${YELLOW}步骤 5/8: 更新配置文件${NC}"
if [ -f "$PROJECT_PATH/config/.env.prod" ]; then
    echo "  - 部署生产环境配置..."
    cp "$PROJECT_PATH/config/.env.prod" "$PROJECT_PATH/backend/.env"
else
    echo -e "${YELLOW}⚠️  生产配置文件不存在，使用现有配置${NC}"
    if [ ! -f "$PROJECT_PATH/backend/.env" ]; then
        cp "$PROJECT_PATH/backend/.env.example" "$PROJECT_PATH/backend/.env" 2>/dev/null || true
    fi
fi
echo -e "${GREEN}✓ 配置文件已更新${NC}"
echo ""

# 6. 安装依赖
echo -e "${YELLOW}步骤 6/8: 安装依赖${NC}"
cd "$PROJECT_PATH/backend"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "  - 创建 Python 虚拟环境..."
    python3 -m venv venv
fi

# 激活并安装依赖
source venv/bin/activate
echo "  - 升级 pip..."
pip install --upgrade pip -q 2>/dev/null || true

echo "  - 安装 Python 依赖..."
pip install -r requirements.txt -q 2>/dev/null || true

echo -e "${GREEN}✓ 依赖安装完成${NC}"
echo ""

# 7. 启动服务
echo -e "${YELLOW}步骤 7/8: 启动服务${NC}"
echo "  - 启动 Gunicorn..."
cd "$PROJECT_PATH/backend"
source venv/bin/activate

nohup gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:3007 \
  --access-logfile /var/log/gunicorn-access.log \
  --error-logfile /var/log/gunicorn-error.log \
  --daemon \
  app.main:app

sleep 3

# 启动 Nginx
echo "  - 启动 Nginx..."
sudo systemctl start nginx 2>/dev/null || true
sudo systemctl enable nginx 2>/dev/null || true

echo -e "${GREEN}✓ 服务已启动${NC}"
echo ""

# 8. 验证部署
echo -e "${YELLOW}步骤 8/8: 验证部署${NC}"
echo ""

# 检查进程
echo "  后端进程:"
ps aux | grep -E '[g]unicorn|[a]pp.main' | grep -v grep | wc -l | xargs echo "    运行进程数:"

# 检查端口
echo "  监听端口:"
netstat -tlnp 2>/dev/null | grep -E '3007|:80 ' | awk '{print "    " $4 " (" $7 ")"}' || true

# 测试 API
echo ""
echo "  API 测试:"
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3007/health)
if [ "$HEALTH_STATUS" == "200" ]; then
    echo -e "    ${GREEN}✓ 健康检查通过 (HTTP $HEALTH_STATUS)${NC}"
else
    echo -e "    ${YELLOW}⚠️  健康检查返回 HTTP $HEALTH_STATUS${NC}"
fi

# 保存版本信息
echo "$PACKAGE_NAME" > "$CURRENT_VERSION_FILE"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🎉 部署成功！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo "📋 部署信息："
echo "  版本: $PACKAGE_NAME"
echo "  路径: $PROJECT_PATH"
echo "  时间: $(date)"
echo ""

echo "🔗 访问地址:"
echo "  API 文档: http://82.157.28.35/docs"
echo "  健康检查: http://82.157.28.35/health"
echo "  前端应用: http://82.157.28.35/"
echo ""

echo "📚 常用命令:"
echo "  查看后端日志: tail -f /var/log/gunicorn-error.log"
echo "  查看 Nginx 日志: tail -f /var/log/nginx/stock-analysis-error.log"
echo "  重启后端: pkill -9 gunicorn; cd $PROJECT_PATH/backend && source venv/bin/activate && nohup gunicorn ... &"
echo "  回滚版本: bash $PROJECT_PATH/rollback.sh"
echo ""
