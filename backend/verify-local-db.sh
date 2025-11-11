#!/bin/bash

echo "🔍 验证本地数据库配置..."
echo ""

# 检查配置文件
echo "1️⃣ 检查配置文件..."
if grep -q "127.0.0.1:3306" backend/.env; then
    echo "   ✅ 配置文件已指向本地数据库"
else
    echo "   ❌ 配置文件仍指向远程数据库"
    exit 1
fi

# 检查MySQL服务
echo ""
echo "2️⃣ 检查MySQL服务..."
if mysqladmin ping -h127.0.0.1 -uroot -pPp123456 2>/dev/null | grep -q "alive"; then
    echo "   ✅ MySQL服务运行正常"
else
    echo "   ❌ MySQL服务未运行"
    exit 1
fi

# 检查数据库连接
echo ""
echo "3️⃣ 检查数据库连接..."
cd backend
source venv/bin/activate
python -c "
from app.core.database import engine
try:
    with engine.connect():
        print('   ✅ 应用可以连接到数据库')
except:
    print('   ❌ 应用无法连接到数据库')
    exit(1)
" 2>/dev/null

if [ $? -ne 0 ]; then
    exit 1
fi

cd ..

# 检查关键表
echo ""
echo "4️⃣ 检查关键数据表..."
cd backend
python -c "
from app.core.database import engine
from sqlalchemy import text

tables = ['stocks', 'concepts', 'daily_trading', 'users', 'admin_users']
all_exist = True

with engine.connect() as conn:
    for table in tables:
        try:
            result = conn.execute(text(f'SELECT COUNT(*) FROM {table}'))
            count = result.fetchone()[0]
            print(f'   ✅ {table:20s} - {count:>8,d} 条')
        except:
            print(f'   ❌ {table:20s} - 不存在')
            all_exist = False

if not all_exist:
    exit(1)
" 2>/dev/null

if [ $? -ne 0 ]; then
    exit 1
fi

cd ..

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║  ✅ 本地数据库配置验证通过！                  ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""
echo "🚀 可以开始部署或启动服务了:"
echo "   • ./scripts/deployment/deploy.sh"
echo "   • ./start-dev.sh"

