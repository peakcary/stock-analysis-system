#!/bin/bash

# 🔍 部署诊断脚本
# 专门用于诊断新机器上的部署问题

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 股票分析系统部署诊断${NC}"
echo "================================"

# 1. 基础环境检查
echo -e "${YELLOW}1. 基础环境检查${NC}"
echo "Node.js: $(node --version 2>/dev/null || echo '❌ 未安装')"

PYTHON_VERSION=$(python3 --version 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+' || echo "未知")
echo "Python: $(python3 --version 2>/dev/null || echo '❌ 未安装')"

if [[ "$PYTHON_VERSION" != "未知" ]]; then
    if python3 -c "
import sys
v = sys.version_info
if 3.8 <= v.major + v.minor/10 <= 3.12:
    print('✅ 版本兼容')
    exit(0)
else:
    print('⚠️  版本可能不兼容，推荐3.10-3.12')
    exit(1)
" 2>/dev/null; then
        :
    else
        echo -e "  ${YELLOW}建议: 使用pyenv安装Python 3.10-3.12${NC}"
        echo "  # brew install pyenv"
        echo "  # pyenv install 3.11"
        echo "  # pyenv global 3.11"
    fi
fi

echo "MySQL: $(mysql --version 2>/dev/null || echo '❌ 未安装')"
echo "Git: $(git --version 2>/dev/null || echo '❌ 未安装')"
echo

# 2. MySQL服务检查
echo -e "${YELLOW}2. MySQL服务检查${NC}"
if command -v brew >/dev/null 2>&1; then
    if brew services list 2>/dev/null | grep mysql | grep started >/dev/null; then
        echo "✅ MySQL服务运行正常"
    else
        echo "❌ MySQL服务未启动"
        echo -e "  ${GREEN}修复命令: brew services start mysql${NC}"
    fi
else
    echo "⚠️  未使用Homebrew管理MySQL"
fi

if mysqladmin ping -h127.0.0.1 2>/dev/null >/dev/null; then
    echo "✅ MySQL连接正常"
    
    # 检查数据库权限
    if mysql -uroot -pPp123456 -e "SELECT 1" 2>/dev/null >/dev/null; then
        echo "✅ 数据库认证正常"
    else
        echo "❌ 数据库认证失败"
        echo -e "  ${GREEN}可能需要设置MySQL密码:${NC}"
        echo "  # mysql_secure_installation"
        echo "  # 或修改 backend/app/core/config.py 中的密码"
    fi
else
    echo "❌ MySQL连接失败"
    echo -e "  ${GREEN}修复建议:${NC}"
    echo "  1. 检查MySQL服务: brew services start mysql"
    echo "  2. 检查端口占用: lsof -i:3306"
    echo "  3. 重置密码: mysql_secure_installation"
fi
echo

# 3. Python环境详细检查
echo -e "${YELLOW}3. Python环境详细检查${NC}"

# 检查pip
if python3 -m pip --version >/dev/null 2>&1; then
    echo "✅ pip可用"
else
    echo "❌ pip不可用"
    echo -e "  ${GREEN}修复: python3 -m ensurepip --upgrade${NC}"
fi

# 检查虚拟环境模块
if python3 -c "import venv" 2>/dev/null; then
    echo "✅ venv模块可用"
else
    echo "❌ venv模块不可用"
    echo -e "  ${GREEN}可能需要安装: brew install python@3.11${NC}"
fi

# 测试虚拟环境创建
echo "测试虚拟环境创建..."
TEST_VENV_DIR="/tmp/test_venv_$$"
if python3 -m venv "$TEST_VENV_DIR" 2>/dev/null; then
    echo "✅ 虚拟环境创建成功"
    rm -rf "$TEST_VENV_DIR"
else
    echo "❌ 虚拟环境创建失败"
    echo -e "  ${GREEN}可能的解决方案:${NC}"
    echo "  1. 重新安装Python: brew reinstall python@3.11"
    echo "  2. 使用conda: conda create -n stock-analysis python=3.11"
fi
echo

# 4. 网络连接检查
echo -e "${YELLOW}4. 网络连接检查${NC}"

# 检查pip源
if curl -s --connect-timeout 5 https://pypi.tuna.tsinghua.edu.cn/simple/ >/dev/null; then
    echo "✅ 清华pip源连接正常"
else
    echo "⚠️  清华pip源连接异常，将使用默认源"
fi

# 检查npm源
if curl -s --connect-timeout 5 https://registry.npmjs.org/ >/dev/null; then
    echo "✅ npm源连接正常"
else
    echo "⚠️  npm源连接异常"
    echo -e "  ${GREEN}建议设置淘宝源: npm config set registry https://registry.npmmirror.com${NC}"
fi
echo

# 5. 磁盘空间检查
echo -e "${YELLOW}5. 磁盘空间检查${NC}"
AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}')
echo "当前目录可用空间: $AVAILABLE_SPACE"

# 检查是否有足够空间（至少需要2GB）
AVAILABLE_MB=$(df -m . | awk 'NR==2 {print $4}')
if [ "$AVAILABLE_MB" -gt 2048 ]; then
    echo "✅ 磁盘空间充足"
else
    echo "⚠️  磁盘空间不足，建议清理后再部署"
fi
echo

# 6. 权限检查
echo -e "${YELLOW}6. 权限检查${NC}"
if [ -w "." ]; then
    echo "✅ 目录写入权限正常"
else
    echo "❌ 目录写入权限不足"
    echo -e "  ${GREEN}修复: chmod u+w .${NC}"
fi

# 检查执行权限
if [ -x "./deploy.sh" ]; then
    echo "✅ deploy.sh执行权限正常"
else
    echo "❌ deploy.sh执行权限不足"
    echo -e "  ${GREEN}修复: chmod +x ./deploy.sh${NC}"
fi
echo

# 7. 生成修复脚本
echo -e "${YELLOW}7. 生成环境修复脚本${NC}"

cat > "fix-environment.sh" << 'EOF'
#!/bin/bash

# 自动环境修复脚本
echo "🔧 开始修复环境..."

# 修复Homebrew MySQL
if command -v brew >/dev/null 2>&1; then
    echo "启动MySQL服务..."
    brew services start mysql
fi

# 修复Python虚拟环境问题
echo "检查Python环境..."
if ! python3 -c "import venv" 2>/dev/null; then
    echo "重新安装Python..."
    brew reinstall python@3.11
fi

# 修复pip源
echo "配置pip源..."
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << 'PIPCONF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
timeout = 60
PIPCONF

# 修复npm源
echo "配置npm源..."
npm config set registry https://registry.npmmirror.com

echo "✅ 环境修复完成，请重新运行 ./deploy.sh"
EOF

chmod +x fix-environment.sh
echo -e "${GREEN}✅ 修复脚本已生成: fix-environment.sh${NC}"
echo

# 8. 总结建议
echo -e "${BLUE}📋 诊断总结${NC}"
echo "================================"
echo "如果发现问题："
echo "1. 运行修复脚本: ./fix-environment.sh"
echo "2. 手动修复MySQL: brew services start mysql && mysql_secure_installation"
echo "3. Python版本问题: 使用pyenv管理Python版本"
echo "4. 网络问题: 配置国内镜像源"
echo
echo "部署建议："
echo "• 优先使用: ./deploy.sh --migrate (仅更新数据库)"
echo "• 完整部署: ./deploy.sh (首次安装)"
echo "• 遇到卡住: Ctrl+C 后检查日志 logs/"
echo
echo -e "${GREEN}🎯 诊断完成！${NC}"