#!/bin/bash

# 股票分析系统自动部署脚本
# 服务器配置: 2核2G阿里云ECS

set -e

# 配置变量
SERVER_IP="47.92.236.28"
SERVER_USER="root"
SERVER_PASS="Pp123456"

echo "🚀 开始部署股票分析系统到 $SERVER_IP..."

# 检查sshpass是否安装
if ! command -v sshpass &> /dev/null; then
    echo "安装sshpass..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install sshpass
    else
        sudo apt-get install -y sshpass
    fi
fi

# 1. 初始化服务器环境
echo "📦 初始化服务器环境..."
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
# 更新系统
apt update && apt upgrade -y

# 安装基础软件
apt install -y nginx mysql-server python3 python3-pip python3-venv nodejs npm git curl wget unzip

# 配置防火墙
ufw allow ssh
ufw allow http
ufw allow https  
ufw allow 3007/tcp
ufw --force enable

# 创建应用目录
mkdir -p /opt/stock-analysis
mkdir -p /var/log/stock-analysis

echo "✅ 服务器环境初始化完成"
EOF

# 2. 打包并上传代码
echo "📤 打包并上传应用代码..."

# 打包本地代码
tar -czf stock-analysis.tar.gz \
    --exclude=node_modules \
    --exclude=venv \
    --exclude=.git \
    --exclude=__pycache__ \
    --exclude=*.pyc \
    --exclude=.DS_Store \
    --exclude=dist \
    backend/ frontend/ 

# 上传到服务器
sshpass -p "$SERVER_PASS" scp stock-analysis.tar.gz "$SERVER_USER@$SERVER_IP:/opt/stock-analysis/"

# 解压代码
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /opt/stock-analysis
tar -xzf stock-analysis.tar.gz
rm stock-analysis.tar.gz
echo "✅ 代码上传完成"
EOF

# 3. 配置MySQL
echo "🗄️ 配置MySQL数据库..."
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
# MySQL安全配置
mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'StockDB2024!';"
mysql -e "FLUSH PRIVILEGES;"

# 创建数据库和用户
mysql -u root -pStockDB2024! -e "CREATE DATABASE IF NOT EXISTS stock_analysis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -pStockDB2024! -e "CREATE USER IF NOT EXISTS 'stockapp'@'localhost' IDENTIFIED BY 'StockApp2024!';"
mysql -u root -pStockDB2024! -e "GRANT ALL PRIVILEGES ON stock_analysis.* TO 'stockapp'@'localhost';"
mysql -u root -pStockDB2024! -e "FLUSH PRIVILEGES;"

echo "✅ MySQL配置完成"
EOF

# 4. 配置后端
echo "⚙️ 配置Python后端..."
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /opt/stock-analysis/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 更新配置文件以使用生产数据库
sed -i 's/DATABASE_URL = "sqlite:\/\/\/\.\/stock_analysis\.db"/DATABASE_URL = "mysql+pymysql:\/\/stockapp:StockApp2024!@localhost\/stock_analysis"/' app/core/config.py

# 初始化数据库
python -c "
from app.core.database import engine, Base
from app.models import user, payment
Base.metadata.create_all(bind=engine)
print('数据库表创建完成')
"

# 创建管理员用户
python -c "
from sqlalchemy.orm import sessionmaker
from app.core.database import engine
from app.models.user import User
from app.core.security import get_password_hash
from datetime import datetime

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

admin_user = db.query(User).filter(User.username == 'admin').first()
if not admin_user:
    admin_user = User(
        username='admin',
        email='admin@stockanalysis.com',
        hashed_password=get_password_hash('admin123'),
        is_active=True,
        membership_type='free',
        queries_remaining=9999,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(admin_user)
    db.commit()
    print('管理员用户创建完成: admin/admin123')
else:
    print('管理员用户已存在')
db.close()
"

echo "✅ 后端配置完成"
EOF

# 5. 构建前端
echo "🎨 构建前端..."
cd frontend

# 更新API地址为服务器地址
find src -name "*.ts" -o -name "*.tsx" | xargs sed -i.bak "s/localhost:3007/$SERVER_IP:3007/g"

npm install
npm run build

# 上传前端构建文件
tar -czf frontend-dist.tar.gz dist/
sshpass -p "$SERVER_PASS" scp frontend-dist.tar.gz "$SERVER_USER@$SERVER_IP:/opt/stock-analysis/"

sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /opt/stock-analysis
tar -xzf frontend-dist.tar.gz
rm frontend-dist.tar.gz
echo "✅ 前端构建完成"
EOF

# 6. 配置Nginx
echo "🌐 配置Nginx..."
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
# 删除默认配置
rm -f /etc/nginx/sites-enabled/default

# 创建应用配置
cat > /etc/nginx/sites-available/stock-analysis << 'NGINX_EOF'
server {
    listen 80;
    server_name 47.92.236.28;
    
    # 前端静态文件
    location / {
        root /opt/stock-analysis/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:3007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 简化导入API
    location /simple-import/ {
        proxy_pass http://127.0.0.1:3007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 100M;
    }
}
NGINX_EOF

# 启用站点
ln -sf /etc/nginx/sites-available/stock-analysis /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
systemctl enable nginx

echo "✅ Nginx配置完成"
EOF

# 7. 创建系统服务
echo "🔧 创建后端服务..."
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
cat > /etc/systemd/system/stock-analysis-backend.service << 'SERVICE_EOF'
[Unit]
Description=Stock Analysis Backend API
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/stock-analysis/backend
Environment=PYTHONPATH=/opt/stock-analysis/backend
ExecStart=/opt/stock-analysis/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 3007 --workers 1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# 启动服务
systemctl daemon-reload
systemctl enable stock-analysis-backend
systemctl start stock-analysis-backend

echo "✅ 后端服务配置完成"
EOF

# 8. 优化系统性能
echo "⚡ 系统性能优化..."
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
# 创建swap分区
if [ ! -f /swapfile ]; then
    fallocate -l 1G /swapfile
    chmod 600 /swapfile  
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# MySQL优化
cat > /etc/mysql/mysql.conf.d/performance.cnf << 'MYSQL_CONF_EOF'
[mysqld]
innodb_buffer_pool_size = 256M
max_connections = 50
query_cache_size = 32M
query_cache_type = 1
MYSQL_CONF_EOF

systemctl restart mysql

echo "✅ 性能优化完成"
EOF

# 9. 最终检查
echo "🔍 检查服务状态..."
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
echo "服务状态检查:"
systemctl is-active stock-analysis-backend && echo "✅ 后端服务正常" || echo "❌ 后端服务异常"
systemctl is-active nginx && echo "✅ Nginx服务正常" || echo "❌ Nginx服务异常"  
systemctl is-active mysql && echo "✅ MySQL服务正常" || echo "❌ MySQL服务异常"

echo "端口监听检查:"
netstat -tlnp | grep -E ':80|:3007|:3306' || echo "检查端口监听状态"

echo "内存使用情况:"
free -h
EOF

# 清理本地文件
rm -f stock-analysis.tar.gz frontend-dist.tar.gz

echo ""
echo "🎉 部署完成！"
echo "🌐 访问地址: http://47.92.236.28"
echo "👤 管理员账号: admin"
echo "🔑 管理员密码: admin123"
echo ""
echo "⚠️ 安全提醒："
echo "1. 请立即登录系统修改默认密码"
echo "2. 建议配置SSH密钥认证"
echo "3. 定期监控服务器资源使用情况"