# 股票分析系统 - 部署指南 v2.7.0

## 🎉 新功能

### v2.7.0 更新内容
- ✅ **CSV原始数据表**：新增不拆分的原始数据存储
- ✅ **双写机制**：CSV导入时同时写入拆分表和原始表
- ✅ **原始数据API**：提供原始数据查询和导出接口
- ✅ **快速查询**：单表查询，无需JOIN，速度更快
- ✅ **数据审计**：完整保留CSV原始数据，便于对账
- ✅ **环境配置**：修复ADMIN_SECRET_KEY配置问题

## 📋 部署前准备

### 系统要求
- **操作系统**: macOS / Linux / Windows (WSL)
- **Node.js**: >= 16.x
- **Python**: >= 3.8
- **MySQL**: >= 5.7
- **内存**: >= 4GB
- **磁盘空间**: >= 2GB

### 环境检查
```bash
# 检查Node.js
node --version

# 检查Python
python3 --version

# 检查MySQL
mysql --version
mysqladmin ping -h127.0.0.1
```

## 🚀 快速部署

### 方式一：完整部署（推荐）

```bash
cd /path/to/stock-analysis-system

# 执行完整部署（包含所有表创建和优化）
./scripts/deployment/deploy.sh

# 启动服务
./scripts/deployment/start.sh
```

### 方式二：仅创建新表（已部署系统）

如果系统已经部署，只需添加新的原始数据表：

```bash
cd /path/to/stock-analysis-system

# 执行数据库初始化（创建原始数据表）
./scripts/database/init_database.sh

# 或手动执行SQL
mysql -u root -p stock_analysis_dev < scripts/database/create_raw_data_table.sql

# 重启后端服务
kill $(cat logs/backend.pid)
cd backend && source venv/bin/activate
nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 3007 > ../logs/backend.log 2>&1 &
echo $! > ../logs/backend.pid
```

## 📊 数据表结构

### 新增表：stock_concept_raw_data

CSV原始数据表，保存导入时的完整数据，不进行拆分：

```sql
CREATE TABLE stock_concept_raw_data (
    id INT PRIMARY KEY AUTO_INCREMENT,
    import_date DATE NOT NULL,          -- 导入日期
    trade_date DATE NOT NULL,           -- 交易日期
    stock_code VARCHAR(10) NOT NULL,    -- 股票代码
    stock_name VARCHAR(100) NOT NULL,   -- 股票名称
    concept VARCHAR(100) NOT NULL,      -- 概念
    industry VARCHAR(100),              -- 行业
    price DECIMAL(10,2) DEFAULT 0,      -- 价格
    turnover_rate DECIMAL(5,2) DEFAULT 0,    -- 换手率
    net_inflow DECIMAL(15,2) DEFAULT 0, -- 净流入
    pages_count INT DEFAULT 0,          -- 页数
    total_reads INT DEFAULT 0,          -- 总阅读数
    file_name VARCHAR(255),             -- 来源文件名
    row_number INT,                     -- CSV行号
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- 索引优化
    INDEX idx_trade_date (trade_date),
    INDEX idx_stock_code (stock_code),
    INDEX idx_concept (concept),
    INDEX idx_raw_trade_date_stock (trade_date, stock_code),
    INDEX idx_raw_trade_date_concept (trade_date, concept)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 数据流向

```
CSV文件导入
    ↓
┌─────────────────────────────────┐
│  解析CSV，提取字段               │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│  拆分存储（原有）                │     │  原始存储（新增）                │
│  - stocks                       │     │  - stock_concept_raw_data       │
│  - concepts                     │     │    * 完整保留CSV每行数据        │
│  - stock_concepts               │     │    * 包含股票-概念组合          │
│  - daily_stock_data             │     │    * 便于审计和导出             │
└─────────────────────────────────┘     └─────────────────────────────────┘
```

## 🔧 环境配置

### 后端配置（.env）

确保 `backend/.env` 包含以下配置：

```env
# 数据库配置
DATABASE_URL=mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=Pp123456
DATABASE_NAME=stock_analysis_dev

# JWT配置
SECRET_KEY=your-secret-key-here-please-change-in-production-32chars-min
ADMIN_SECRET_KEY=admin-secret-key-here-please-change-in-production-32chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS配置
ALLOWED_ORIGINS=http://localhost:8005,http://127.0.0.1:8005,http://localhost:8006,http://127.0.0.1:8006

# 微信支付配置（可选）
WECHAT_APPID=your_wechat_appid
WECHAT_MCH_ID=your_merchant_id
WECHAT_API_V3_KEY=your_32_character_api_key
WECHAT_CERT_SERIAL=your_cert_serial
WECHAT_CERT_PATH=certs/apiclient_cert.pem
WECHAT_KEY_PATH=certs/apiclient_key.pem
WECHAT_NOTIFY_URL=https://your-domain.com/api/v1/payment/notify

# 支付功能配置
PAYMENT_ENABLED=true
PAYMENT_MOCK_MODE=true  # 开发环境设为true，生产环境设为false
```

## 📡 API接口

### 新增API：原始数据查询

#### 1. 查询指定日期的原始数据
```bash
GET /api/v1/raw-data/daily?trade_date=2025-08-28&page=1&size=50

# 响应示例
{
  "success": true,
  "trade_date": "2025-08-28",
  "total": 1500,
  "page": 1,
  "size": 50,
  "data": [
    {
      "stock_code": "600036",
      "stock_name": "招商银行",
      "concept": "金融科技",
      "industry": "银行",
      "price": 45.20,
      "turnover_rate": 2.35,
      "net_inflow": 1234.56,
      "pages_count": 120,
      "total_reads": 5000
    }
  ]
}
```

#### 2. 导出CSV
```bash
GET /api/v1/raw-data/export/csv?trade_date=2025-08-28

# 返回CSV文件
股票代码,股票名称,全部页数,热帖首页页阅读总数,价格,行业,概念,换手,净流入
600036,招商银行,120,5000,45.20,银行,金融科技,2.35,1234.56
```

#### 3. 获取统计信息
```bash
GET /api/v1/raw-data/stats/daily?trade_date=2025-08-28

# 响应
{
  "total_records": 1500,
  "stock_count": 150,
  "concept_count": 50,
  "total_net_inflow": 123456.78
}
```

#### 4. 查询指定股票
```bash
GET /api/v1/raw-data/stock/600036?trade_date=2025-08-28

# 返回该股票在所有概念下的数据
```

#### 5. 获取概念列表
```bash
GET /api/v1/raw-data/concepts?trade_date=2025-08-28

# 返回当日所有概念及统计
```

## 🧪 测试验证

### 1. 验证表是否创建
```bash
mysql -u root -p stock_analysis_dev -e "DESCRIBE stock_concept_raw_data;"
```

### 2. 测试CSV导入
1. 登录管理后台：http://localhost:8006
2. 用户名/密码：`admin` / `admin123`
3. 进入【数据导入】页面
4. 上传CSV文件
5. 查看导入日志，应该看到：
   ```
   💾 同步写入原始数据表: 1500 条记录
   ```

### 3. 测试原始数据API
```bash
# 获取指定日期的数据
curl "http://localhost:3007/api/v1/raw-data/daily?trade_date=2025-08-28&page=1&size=10"

# 获取统计
curl "http://localhost:3007/api/v1/raw-data/stats/daily?trade_date=2025-08-28"
```

### 4. 验证数据完整性
```bash
# 查询原始数据表记录数
mysql -u root -p stock_analysis_dev -e "
SELECT
    trade_date,
    COUNT(*) as total_records,
    COUNT(DISTINCT stock_code) as stock_count,
    COUNT(DISTINCT concept) as concept_count
FROM stock_concept_raw_data
GROUP BY trade_date
ORDER BY trade_date DESC
LIMIT 10;
"
```

## 🔍 故障排查

### 问题1：表创建失败
```bash
# 错误：row_number语法错误
# 解决：确保使用反引号
mysql -u root -p stock_analysis_dev -e "SHOW CREATE TABLE stock_concept_raw_data;"
```

### 问题2：导入失败 - 表不存在
```bash
# 手动创建表
mysql -u root -p stock_analysis_dev < scripts/database/create_raw_data_table.sql

# 重启后端
kill $(cat logs/backend.pid)
cd backend && source venv/bin/activate
nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 3007 > ../logs/backend.log 2>&1 &
```

### 问题3：ADMIN_SECRET_KEY错误
```bash
# 确保.env文件包含
grep ADMIN_SECRET_KEY backend/.env

# 如果没有，添加
echo "ADMIN_SECRET_KEY=admin-secret-key-here-please-change-in-production-32chars" >> backend/.env
```

### 问题4：API无法访问
```bash
# 检查后端是否运行
lsof -i:3007

# 查看日志
tail -f logs/backend.log

# 重启服务
./scripts/deployment/stop.sh
./scripts/deployment/start.sh
```

## 📚 更多资源

- **API文档**: http://localhost:3007/docs
- **管理后台**: http://localhost:8006
- **客户端**: http://localhost:8005
- **GitHub**: https://github.com/your-repo/stock-analysis-system

## 🆘 获取帮助

遇到问题？

1. 查看日志：`tail -f logs/backend.log`
2. 检查配置：`cat backend/.env`
3. 验证表：`mysql -u root -p stock_analysis_dev -e "SHOW TABLES;"`
4. 重新部署：`./scripts/deployment/deploy.sh`

---

**部署脚本版本**: v2.7.0
**文档更新时间**: 2025-10-15
