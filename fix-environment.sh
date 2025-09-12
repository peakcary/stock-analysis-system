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
