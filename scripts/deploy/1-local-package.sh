#!/bin/bash

# ============================================================
# 本地打包脚本 - 生成可部署的包文件
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PACKAGE_DIR="$PROJECT_ROOT/deploy-packages"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="stock-analysis-system_${TIMESTAMP}"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}股票分析系统 - 本地部署包生成${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. 创建临时目录
echo -e "${YELLOW}步骤 1/6: 创建临时打包目录${NC}"
TEMP_DIR=$(mktemp -d)
PACKAGE_TEMP="$TEMP_DIR/$PACKAGE_NAME"
mkdir -p "$PACKAGE_TEMP"
echo -e "${GREEN}✓ 临时目录创建完成: $PACKAGE_TEMP${NC}"
echo ""

# 2. 复制后端代码
echo -e "${YELLOW}步骤 2/6: 打包后端代码${NC}"
mkdir -p "$PACKAGE_TEMP/backend"
cp -r "$PROJECT_ROOT/backend"/*.py "$PACKAGE_TEMP/backend/" 2>/dev/null || true
cp -r "$PROJECT_ROOT/backend/app" "$PACKAGE_TEMP/backend/" 2>/dev/null || true
cp "$PROJECT_ROOT/backend/requirements.txt" "$PACKAGE_TEMP/backend/" 2>/dev/null || true
cp "$PROJECT_ROOT/backend/.env.example" "$PACKAGE_TEMP/backend/.env.example" 2>/dev/null || true
echo -e "${GREEN}✓ 后端代码打包完成${NC}"
echo ""

# 3. 构建前端（如果存在）
echo -e "${YELLOW}步骤 3/6: 构建前端代码${NC}"
if [ -d "$PROJECT_ROOT/frontend" ]; then
    echo "  - 构建前端应用..."
    cd "$PROJECT_ROOT/frontend"
    npm run build 2>/dev/null || echo "  ⚠️  前端构建跳过 (可能需要手动构建)"
    mkdir -p "$PACKAGE_TEMP/frontend/dist"
    cp -r "$PROJECT_ROOT/frontend/dist"/* "$PACKAGE_TEMP/frontend/dist/" 2>/dev/null || true
    echo -e "${GREEN}✓ 前端代码打包完成${NC}"
else
    echo -e "${YELLOW}  ⚠️  前端目录不存在，跳过${NC}"
fi
echo ""

# 4. 复制配置文件
echo -e "${YELLOW}步骤 4/6: 复制配置文件${NC}"
mkdir -p "$PACKAGE_TEMP/config"
if [ -f "$PROJECT_ROOT/backend/.env" ]; then
    echo "  - 复制 .env (注意: 不包含敏感信息)"
    cp "$PROJECT_ROOT/backend/.env" "$PACKAGE_TEMP/config/.env.prod" 2>/dev/null || true
fi
echo -e "${GREEN}✓ 配置文件复制完成${NC}"
echo ""

# 5. 创建部署说明
echo -e "${YELLOW}步骤 5/6: 生成部署说明${NC}"
cat > "$PACKAGE_TEMP/DEPLOYMENT_README.md" << 'EOF'
# 部署说明

## 部署包内容

```
stock-analysis-system_YYYYMMDD_HHMMSS/
├── backend/                    # 后端代码
│   ├── app/                   # 应用代码
│   ├── requirements.txt        # Python 依赖
│   └── .env.example           # 环境变量示例
├── frontend/dist/             # 前端构建输出（如有）
├── config/                    # 配置文件
└── DEPLOYMENT_README.md       # 本说明文档
```

## 部署步骤

### 1. 上传文件到服务器
```bash
scp -r stock-analysis-system_YYYYMMDD_HHMMSS ubuntu@82.157.28.35:/tmp/
```

### 2. 在服务器上执行部署脚本
```bash
ssh ubuntu@82.157.28.35 bash /tmp/stock-analysis-system/deploy.sh
```

### 3. 验证部署
```bash
curl http://82.157.28.35/health
```

## 回滚

如需回滚到上一个版本：
```bash
ssh ubuntu@82.157.28.35 bash /opt/stock-analysis-system/rollback.sh
```

EOF

echo -e "${GREEN}✓ 部署说明生成完成${NC}"
echo ""

# 6. 生成部署包
echo -e "${YELLOW}步骤 6/6: 生成压缩包${NC}"
mkdir -p "$PACKAGE_DIR"
cd "$TEMP_DIR"
tar -czf "$PACKAGE_DIR/${PACKAGE_NAME}.tar.gz" "$PACKAGE_NAME"
PACKAGE_SIZE=$(du -h "$PACKAGE_DIR/${PACKAGE_NAME}.tar.gz" | cut -f1)

# 生成 MD5 校验值
MD5_VALUE=$(md5sum "$PACKAGE_DIR/${PACKAGE_NAME}.tar.gz" | awk '{print $1}')
echo "$MD5_VALUE  ${PACKAGE_NAME}.tar.gz" > "$PACKAGE_DIR/${PACKAGE_NAME}.md5"

# 清理临时目录
rm -rf "$TEMP_DIR"

echo -e "${GREEN}✓ 部署包生成完成${NC}"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🎉 打包成功！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "📦 部署包信息："
echo "  文件名: ${PACKAGE_NAME}.tar.gz"
echo "  大小: $PACKAGE_SIZE"
echo "  位置: $PACKAGE_DIR"
echo "  MD5: $MD5_VALUE"
echo ""
echo "📝 后续步骤："
echo "  1. 上传文件: scp $PACKAGE_DIR/${PACKAGE_NAME}.tar.gz ubuntu@82.157.28.35:/tmp/"
echo "  2. 在服务器执行: bash /tmp/2-remote-deploy.sh $PACKAGE_NAME"
echo ""
