# 📊 股票分析系统 - 系统设计文档

[![Version](https://img.shields.io/badge/Version-v2.6.0-blue.svg)](./README.md)
[![Last Updated](https://img.shields.io/badge/Updated-2025--09--13-green.svg)](#)

## 📄 文档概述

**文档版本**: v2.6.0  
**创建日期**: 2025-09-13  
**更新日期**: 2025-09-13  
**项目阶段**: 生产环境运行  
**核心功能**: 股票分析、概念分析、用户管理、支付系统  

## 🏗️ 系统架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           前端用户界面层                                    │
├──────────────────────┬──────────────────────┬───────────────────────────────┤
│    管理端前端         │     客户端前端        │      共享组件库               │
│   (React + Ant)      │   (React + Ant)      │   (TypeScript)                │
│   Port: 8006         │   Port: 8005         │   认证/工具/类型              │
└──────────────────────┴──────────────────────┴───────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                            API网关层                                        │
├──────────────────────┬──────────────────────┬───────────────────────────────┤
│    管理员认证         │     用户认证          │      路由分发                 │
│   JWT + 权限控制      │   JWT + 会员限制      │   请求验证/日志               │
└──────────────────────┴──────────────────────┴───────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           后端API服务层                                     │
├──────────────────────┬──────────────────────┬───────────────────────────────┤
│    股票分析API        │     用户管理API       │      支付系统API              │
│   FastAPI            │   FastAPI            │   FastAPI + 微信支付          │
│   Port: 3007         │   SQLAlchemy ORM     │   套餐管理/订单处理            │
└──────────────────────┴──────────────────────┴───────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                          业务逻辑服务层                                      │
├──────────────────────┬──────────────────────┬───────────────────────────────┤
│    数据导入服务        │     概念分析服务      │      图表数据服务             │
│   TXT/CSV处理         │   排名计算/汇总       │   趋势图/对比图               │
│   股票代码标准化       │   概念股票关联        │   历史数据分析                │
└──────────────────────┴──────────────────────┴───────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           数据存储层                                        │
├──────────────────────┬──────────────────────┬───────────────────────────────┤
│     核心数据库        │     缓存系统          │      文件存储                 │
│   MySQL 8.0          │   Redis (可选)        │   日志文件/上传文件            │
│   事务ACID保证        │   热点数据缓存        │   备份数据                    │
└──────────────────────┴──────────────────────┴───────────────────────────────┘
```

### 技术栈选择

**前端技术栈**:
- **React 18+**: 现代化UI框架，组件化开发
- **TypeScript**: 类型安全，提升开发效率
- **Ant Design**: 企业级UI组件库
- **Vite**: 快速构建工具
- **React Router**: 路由管理

**后端技术栈**:
- **FastAPI**: 高性能Python Web框架
- **SQLAlchemy**: Python ORM框架
- **MySQL 8.0**: 关系型数据库
- **Pydantic**: 数据验证和序列化
- **JWT**: 无状态认证

**部署技术栈**:
- **Docker**: 容器化部署
- **Nginx**: 反向代理和静态文件服务
- **MySQL**: 数据持久化
- **Shell Scripts**: 自动化部署脚本

## 💾 数据库设计

### 核心表结构

#### 1. 股票基础数据表
```sql
CREATE TABLE stocks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(20) NOT NULL UNIQUE,
    stock_name VARCHAR(100) NOT NULL,
    market VARCHAR(10) NOT NULL,  -- SH/SZ/BJ
    industry VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    KEY idx_stock_code (stock_code),
    KEY idx_market (market),
    KEY idx_industry (industry),
    KEY idx_active (is_active)
);
```

#### 2. 概念基础数据表
```sql
CREATE TABLE concepts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    concept_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    KEY idx_concept_name (concept_name),
    KEY idx_category (category),
    KEY idx_active (is_active)
);
```

#### 3. 股票概念关联表
```sql
CREATE TABLE stock_concepts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(20) NOT NULL,
    concept_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_stock_concept (stock_code, concept_name),
    KEY idx_stock_code (stock_code),
    KEY idx_concept_name (concept_name),
    KEY idx_active (is_active)
);
```

#### 4. 每日交易数据表
```sql
CREATE TABLE daily_trading (
    id INT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(20) NOT NULL,
    trading_date DATE NOT NULL,
    trading_volume BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_stock_date (stock_code, trading_date),
    KEY idx_stock_code (stock_code),
    KEY idx_trading_date (trading_date),
    KEY idx_volume (trading_volume DESC)
);
```

#### 5. 概念每日汇总表
```sql
CREATE TABLE concept_daily_summary (
    id INT PRIMARY KEY AUTO_INCREMENT,
    concept_name VARCHAR(100) NOT NULL,
    trading_date DATE NOT NULL,
    total_volume BIGINT NOT NULL,
    stock_count INT NOT NULL,
    average_volume DECIMAL(15,2),
    max_volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_concept_date (concept_name, trading_date),
    KEY idx_concept_name (concept_name),
    KEY idx_trading_date (trading_date),
    KEY idx_total_volume (total_volume DESC)
);
```

#### 6. 股票概念排名表
```sql
CREATE TABLE stock_concept_ranking (
    id INT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(20) NOT NULL,
    concept_name VARCHAR(100) NOT NULL,
    trading_date DATE NOT NULL,
    trading_volume BIGINT NOT NULL,
    concept_rank INT NOT NULL,
    concept_total_volume BIGINT,
    volume_percentage DECIMAL(8,5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_stock_concept_date (stock_code, concept_name, trading_date),
    KEY idx_stock_code (stock_code),
    KEY idx_concept_name (concept_name),
    KEY idx_trading_date (trading_date),
    KEY idx_concept_rank (concept_rank),
    KEY idx_volume (trading_volume DESC)
);
```

#### 7. 概念创新高记录表
```sql
CREATE TABLE concept_high_record (
    id INT PRIMARY KEY AUTO_INCREMENT,
    concept_name VARCHAR(100) NOT NULL,
    trading_date DATE NOT NULL,
    total_volume BIGINT NOT NULL,
    is_new_high BOOLEAN DEFAULT FALSE,
    high_type VARCHAR(20), -- 'daily', 'weekly', 'monthly'
    previous_high_volume BIGINT,
    previous_high_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_concept_date (concept_name, trading_date),
    KEY idx_concept_name (concept_name),
    KEY idx_trading_date (trading_date),
    KEY idx_new_high (is_new_high),
    KEY idx_high_type (high_type)
);
```

### 用户系统表结构

#### 8. 客户端用户表
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    membership_level ENUM('free', 'basic', 'premium', 'unlimited') DEFAULT 'free',
    query_limit INT DEFAULT 10,
    queries_used INT DEFAULT 0,
    last_reset_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    KEY idx_username (username),
    KEY idx_email (email),
    KEY idx_membership (membership_level),
    KEY idx_active (is_active)
);
```

#### 9. 管理员用户表
```sql
CREATE TABLE admin_users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    KEY idx_username (username),
    KEY idx_email (email),
    KEY idx_active (is_active),
    KEY idx_superuser (is_superuser)
);
```

### 支付系统表结构

#### 10. 套餐配置表
```sql
CREATE TABLE packages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    query_limit INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CNY',
    duration_days INT DEFAULT 30,
    membership_level ENUM('basic', 'premium', 'unlimited'),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    KEY idx_name (name),
    KEY idx_membership (membership_level),
    KEY idx_active (is_active)
);
```

#### 11. 支付订单表
```sql
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    package_id INT NOT NULL,
    order_no VARCHAR(32) NOT NULL UNIQUE,
    amount DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'paid', 'failed', 'refunded') DEFAULT 'pending',
    payment_method VARCHAR(20) DEFAULT 'wechat_pay',
    prepay_id VARCHAR(64),
    transaction_id VARCHAR(64),
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    KEY idx_user_id (user_id),
    KEY idx_order_no (order_no),
    KEY idx_status (status),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (package_id) REFERENCES packages(id)
);
```

### 数据导入记录表

#### 12. TXT导入记录表
```sql
CREATE TABLE txt_import_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL,
    trading_date DATE NOT NULL,
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    total_records INT DEFAULT 0,
    success_records INT DEFAULT 0,
    error_records INT DEFAULT 0,
    concept_summary_count INT DEFAULT 0,
    ranking_count INT DEFAULT 0,
    new_high_count INT DEFAULT 0,
    error_message TEXT,
    processing_time_seconds INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    KEY idx_trading_date (trading_date),
    KEY idx_status (status),
    KEY idx_created_at (created_at)
);
```

### 索引策略

**查询优化索引**:
```sql
-- 股票概念联合查询优化
CREATE INDEX idx_stock_concept_date ON stock_concept_ranking(stock_code, trading_date);

-- 概念汇总排序优化
CREATE INDEX idx_concept_summary_volume ON concept_daily_summary(trading_date, total_volume DESC);

-- 日期范围查询优化
CREATE INDEX idx_trading_date_volume ON daily_trading(trading_date, trading_volume DESC);

-- 用户查询限制优化
CREATE INDEX idx_user_membership_active ON users(membership_level, is_active);
```

## 🔧 API接口设计

### 股票分析接口

#### 1. 概念汇总接口
```python
GET /api/v1/stock-analysis/concepts/daily-summary
Parameters:
  - trading_date: str (YYYY-MM-DD, 可选)
  - page: int (页码, 默认1)
  - size: int (每页数量, 最大2000)
  - sort_by: str (排序字段: total_volume|stock_count|avg_volume)
  - sort_order: str (排序方式: desc|asc)
  - search: str (概念名称搜索, 可选)

Response:
{
  "trading_date": "2025-09-02",
  "summaries": [
    {
      "concept_name": "融资融券",
      "total_volume": 622580139,
      "stock_count": 2565,
      "avg_volume": 242721.0,
      "max_volume": 12968518,
      "trading_date": "2025-09-02",
      "volume_percentage": 4.86
    }
  ],
  "pagination": {
    "page": 1,
    "size": 50,
    "total": 150,
    "has_more": true
  }
}
```

#### 2. 概念股票列表接口
```python
GET /api/v1/stock-analysis/concept/{concept_name}/stocks
Parameters:
  - trading_date: str (YYYY-MM-DD, 可选)
  - limit: int (返回数量, 默认100)
  - offset: int (偏移量, 默认0)

Response:
{
  "concept_name": "融资融券",
  "trading_date": "2025-09-02",
  "total_volume": 622580139,
  "stock_count": 2565,
  "average_volume": 242721.0,
  "max_volume": 12968518,
  "total_stocks": 2565,
  "stocks": [
    {
      "stock_code": "SH601099",
      "stock_name": "太平洋",
      "trading_volume": 12968518,
      "concept_rank": 1,
      "volume_percentage": 2.08303
    }
  ],
  "pagination": {
    "offset": 0,
    "limit": 100,
    "total": 2565,
    "has_more": true
  }
}
```

#### 3. 个股概念分析接口
```python
GET /api/v1/stock-analysis/stock/{stock_code}/concepts
Parameters:
  - trading_date: str (YYYY-MM-DD, 可选)
  - limit: int (返回数量, 默认50)

Response:
{
  "stock_code": "SH600000",
  "stock_name": "浦发银行",
  "trading_date": "2025-09-02",
  "total_trading_volume": 87654321,
  "concepts": [
    {
      "concept_name": "银行",
      "concept_rank": 1,
      "trading_volume": 87654321,
      "concept_total_volume": 123456789,
      "volume_percentage": 71.02,
      "stock_count": 33
    }
  ],
  "pagination": {
    "total": 15,
    "limit": 50
  }
}
```

#### 4. 股票列表汇总接口
```python
GET /api/v1/stock-analysis/stocks/daily-summary
Parameters:
  - trading_date: str (YYYY-MM-DD, 可选)
  - page: int (页码, 默认1)
  - size: int (每页数量, 最大1000)
  - search: str (股票代码/名称搜索, 可选)

Response:
{
  "trading_date": "2025-09-02",
  "stocks": [
    {
      "stock_code": "SH601099",
      "stock_name": "太平洋",
      "trading_volume": 12968518,
      "concept_count": 15
    }
  ],
  "pagination": {
    "page": 1,
    "size": 50,
    "total": 5432,
    "has_more": true
  }
}
```

### 用户管理接口

#### 5. 用户认证接口
```python
POST /api/v1/auth/login
Body:
{
  "username": "user@example.com",
  "password": "password123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user_info": {
    "id": 1,
    "username": "user@example.com",
    "membership_level": "premium",
    "query_limit": 1000,
    "queries_used": 150
  }
}
```

#### 6. 管理员认证接口
```python
POST /api/v1/admin/auth/login
Body:
{
  "username": "admin",
  "password": "admin123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "admin_info": {
    "id": 1,
    "username": "admin",
    "full_name": "系统管理员",
    "is_superuser": true
  }
}
```

### 数据导入接口

#### 7. TXT文件导入接口
```python
POST /api/v1/txt-import/import
Headers:
  - Content-Type: multipart/form-data
  - Authorization: Bearer {admin_token}
Body:
  - file: TXT文件

Response:
{
  "success": true,
  "message": "导入成功",
  "stats": {
    "trading_data_count": 5432,
    "concept_summary_count": 150,
    "ranking_count": 25680,
    "new_high_count": 12,
    "trading_date": "2025-09-02"
  }
}
```

#### 8. 重新计算接口
```python
POST /api/v1/txt-import/recalculate
Headers:
  - Authorization: Bearer {admin_token}
Body:
{
  "trading_date": "2025-09-02"
}

Response:
{
  "success": true,
  "message": "重新计算完成",
  "stats": {
    "trading_data_count": 5432,
    "concept_summary_count": 150,
    "ranking_count": 25680,
    "new_high_count": 12,
    "trading_date": "2025-09-02"
  }
}
```

### 支付系统接口

#### 9. 套餐列表接口
```python
GET /api/v1/packages

Response:
{
  "packages": [
    {
      "id": 1,
      "name": "基础套餐",
      "description": "100次查询",
      "query_limit": 100,
      "price": 29.90,
      "currency": "CNY",
      "duration_days": 30,
      "membership_level": "basic"
    }
  ]
}
```

#### 10. 创建订单接口
```python
POST /api/v1/payment/create-order
Headers:
  - Authorization: Bearer {user_token}
Body:
{
  "package_id": 1,
  "payment_method": "wechat_pay"
}

Response:
{
  "order_no": "ORD20250913123456789",
  "amount": 29.90,
  "prepay_info": {
    "appId": "wx...",
    "timeStamp": "1694567890",
    "nonceStr": "abc123",
    "package": "prepay_id=wx...",
    "signType": "RSA",
    "paySign": "sign..."
  }
}
```

## 🔄 业务逻辑设计

### 数据处理流程

#### 1. TXT文件导入流程
```python
async def txt_import_workflow(file: UploadFile, admin_user: AdminUser):
    """TXT文件导入工作流"""
    
    # 1. 文件验证和解析
    trading_date = parse_trading_date_from_file(file)
    
    # 2. 检查重复导入
    existing_record = check_existing_import(trading_date)
    if existing_record:
        # 用户确认覆盖导入
        pass
    
    # 3. 数据清理（如果覆盖）
    if overwrite:
        clear_existing_data(trading_date)
    
    # 4. 批量导入交易数据
    trading_data = parse_trading_data(file)
    import_trading_data(trading_data, trading_date)
    
    # 5. 执行核心计算
    calculation_results = perform_calculations(trading_date)
    
    # 6. 更新导入记录
    update_import_record(trading_date, calculation_results)
    
    # 7. 返回统计结果
    return {
        "success": True,
        "stats": calculation_results
    }
```

#### 2. 核心计算逻辑
```python
def perform_calculations(trading_date: date) -> Dict:
    """执行核心计算逻辑"""
    
    # 1. 计算概念每日汇总
    concept_summaries = calculate_concept_daily_summaries(trading_date)
    
    # 2. 计算股票概念排名
    stock_rankings = calculate_stock_concept_rankings(trading_date)
    
    # 3. 检测概念创新高
    new_highs = detect_concept_new_highs(trading_date)
    
    return {
        "concept_summary_count": len(concept_summaries),
        "ranking_count": len(stock_rankings),
        "new_high_count": len(new_highs),
        "trading_date": trading_date.strftime('%Y-%m-%d')
    }

def calculate_concept_daily_summaries(trading_date: date) -> List[Dict]:
    """计算概念每日汇总"""
    
    # SQL逻辑：按概念分组汇总交易量
    query = """
    INSERT INTO concept_daily_summary 
    (concept_name, trading_date, total_volume, stock_count, average_volume, max_volume)
    SELECT 
        sc.concept_name,
        dt.trading_date,
        SUM(dt.trading_volume) as total_volume,
        COUNT(DISTINCT dt.stock_code) as stock_count,
        AVG(dt.trading_volume) as average_volume,
        MAX(dt.trading_volume) as max_volume
    FROM daily_trading dt
    JOIN stock_concepts sc ON dt.stock_code = sc.stock_code
    WHERE dt.trading_date = %s AND sc.is_active = TRUE
    GROUP BY sc.concept_name, dt.trading_date
    ORDER BY total_volume DESC
    """
    
    return execute_query(query, [trading_date])

def calculate_stock_concept_rankings(trading_date: date) -> List[Dict]:
    """计算股票概念排名"""
    
    # SQL逻辑：在每个概念内按交易量排名
    query = """
    INSERT INTO stock_concept_ranking 
    (stock_code, concept_name, trading_date, trading_volume, concept_rank, 
     concept_total_volume, volume_percentage)
    SELECT 
        dt.stock_code,
        sc.concept_name,
        dt.trading_date,
        dt.trading_volume,
        ROW_NUMBER() OVER (
            PARTITION BY sc.concept_name 
            ORDER BY dt.trading_volume DESC
        ) as concept_rank,
        cds.total_volume as concept_total_volume,
        (dt.trading_volume * 100.0 / cds.total_volume) as volume_percentage
    FROM daily_trading dt
    JOIN stock_concepts sc ON dt.stock_code = sc.stock_code
    JOIN concept_daily_summary cds ON sc.concept_name = cds.concept_name 
        AND dt.trading_date = cds.trading_date
    WHERE dt.trading_date = %s AND sc.is_active = TRUE
    ORDER BY sc.concept_name, concept_rank
    """
    
    return execute_query(query, [trading_date])
```

### 股票代码匹配逻辑

#### 智能代码匹配
```python
def intelligent_stock_code_matching(stock_code: str) -> List[str]:
    """智能股票代码匹配，处理不同表间格式差异"""
    
    possible_codes = [stock_code]
    
    if stock_code.startswith(('SH', 'SZ', 'BJ')):
        # 如果输入有前缀，添加去前缀的版本
        possible_codes.append(stock_code[2:])
    else:
        # 如果输入没有前缀，添加各种前缀版本
        possible_codes.extend([
            f'SH{stock_code}', 
            f'SZ{stock_code}', 
            f'BJ{stock_code}'
        ])
    
    return possible_codes

def find_stock_with_matching_codes(db: Session, stock_code: str) -> Optional[Stock]:
    """使用智能匹配查找股票"""
    
    possible_codes = intelligent_stock_code_matching(stock_code)
    
    for code in possible_codes:
        stock = db.query(Stock).filter(Stock.stock_code == code).first()
        if stock:
            return stock
    
    return None
```

### 用户认证与权限控制

#### JWT认证逻辑
```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建JWT访问令牌"""
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """验证JWT令牌"""
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """获取当前用户"""
    
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
```

#### 查询次数限制逻辑
```python
async def check_query_limit(user: User) -> bool:
    """检查用户查询次数限制"""
    
    # 检查是否需要重置计数（每月重置）
    if should_reset_query_count(user):
        reset_user_query_count(user)
    
    # 无限次会员不受限制
    if user.membership_level == "unlimited":
        return True
    
    # 检查是否超出限制
    if user.queries_used >= user.query_limit:
        return False
    
    # 增加使用次数
    increment_user_query_count(user)
    return True

def should_reset_query_count(user: User) -> bool:
    """判断是否需要重置查询计数"""
    
    today = date.today()
    last_reset = user.last_reset_date
    
    if last_reset is None:
        return True
    
    # 每月1号重置
    if today.month != last_reset.month or today.year != last_reset.year:
        return True
    
    return False
```

### 支付系统逻辑

#### 微信支付流程
```python
async def create_wechat_order(user: User, package: Package) -> Dict:
    """创建微信支付订单"""
    
    # 1. 生成订单号
    order_no = generate_order_number()
    
    # 2. 创建订单记录
    order = Order(
        user_id=user.id,
        package_id=package.id,
        order_no=order_no,
        amount=package.price,
        status="pending"
    )
    save_order(order)
    
    # 3. 调用微信支付API
    prepay_result = await wechat_pay_api.create_prepay_order(
        order_no=order_no,
        amount=int(package.price * 100),  # 分为单位
        description=package.name,
        user_openid=user.openid
    )
    
    # 4. 更新订单预支付信息
    order.prepay_id = prepay_result["prepay_id"]
    update_order(order)
    
    # 5. 返回支付参数
    return {
        "order_no": order_no,
        "amount": package.price,
        "prepay_info": prepay_result
    }

async def handle_payment_callback(payment_data: Dict) -> bool:
    """处理支付回调"""
    
    # 1. 验证回调签名
    if not verify_wechat_signature(payment_data):
        return False
    
    # 2. 查找订单
    order_no = payment_data["out_trade_no"]
    order = get_order_by_number(order_no)
    if not order:
        return False
    
    # 3. 更新订单状态
    order.status = "paid"
    order.transaction_id = payment_data["transaction_id"]
    order.paid_at = datetime.now()
    update_order(order)
    
    # 4. 升级用户会员
    await upgrade_user_membership(order.user_id, order.package_id)
    
    return True

async def upgrade_user_membership(user_id: int, package_id: int):
    """升级用户会员等级"""
    
    user = get_user_by_id(user_id)
    package = get_package_by_id(package_id)
    
    # 更新会员等级和查询限制
    user.membership_level = package.membership_level
    user.query_limit = package.query_limit
    user.queries_used = 0  # 重置使用次数
    user.last_reset_date = date.today()
    
    update_user(user)
```

## 🎨 前端架构设计

### 组件架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           应用根组件                                        │
├──────────────────────┬──────────────────────┬───────────────────────────────┤
│    管理端App          │     客户端App         │      共享认证组件             │
│   AdminApp.tsx       │   ClientApp.tsx      │   AuthContext.tsx             │
└──────────────────────┴──────────────────────┴───────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           路由管理层                                        │
├──────────────────────┬──────────────────────┬───────────────────────────────┤
│    管理端路由         │     客户端路由        │      权限路由守卫             │
│   React Router       │   React Router       │   ProtectedRoute              │
└──────────────────────┴──────────────────────┴───────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           页面组件层                                        │
├──────────────────────┬──────────────────────┬───────────────────────────────┤
│    数据导入页面       │     概念分析页面      │      个股分析页面             │
│   DataImportPage     │   ConceptAnalysisPage │   NewStockAnalysisPage       │
│                      │                      │   (概念驱动模式)              │
├──────────────────────┼──────────────────────┼───────────────────────────────┤
│    用户管理页面       │     支付管理页面      │      仪表盘页面               │
│   UserManagement     │   PaymentModal       │   Dashboard                   │
└──────────────────────┴──────────────────────┴───────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           业务组件层                                        │
├──────────────────────┬──────────────────────┬───────────────────────────────┤
│    数据表格组件       │     搜索组件          │      图表组件                 │
│   Table/Pagination   │   SearchInput        │   Chart/Trend                │
├──────────────────────┼──────────────────────┼───────────────────────────────┤
│    表单组件           │     弹窗组件          │      状态组件                 │
│   Form/Input         │   Modal/Drawer       │   Loading/Error               │
└──────────────────────┴──────────────────────┴───────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           服务层                                            │
├──────────────────────┬──────────────────────┬───────────────────────────────┤
│    API客户端          │     认证服务          │      工具函数                 │
│   adminApiClient     │   auth-utils         │   utils/format               │
│   userApiClient      │   token管理          │   types定义                   │
└──────────────────────┴──────────────────────┴───────────────────────────────┘
```

### 核心组件设计

#### 1. 新股票分析页面 (概念驱动模式)
```typescript
interface NewStockAnalysisPageProps {}

interface ConceptSummary {
  concept_name: string;
  total_volume: number;
  stock_count: number;
  avg_volume: number;
  max_volume: number;
  trading_date: string;
  volume_percentage: number;
}

interface StockInfo {
  stock_code: string;
  stock_name: string;
  trading_volume: number;
  concept_rank: number;
  volume_percentage: number;
}

const NewStockAnalysisPage: React.FC = () => {
  // 状态管理
  const [conceptSummaries, setConceptSummaries] = useState<ConceptSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [tradingDate, setTradingDate] = useState<string>('2025-09-02');
  const [searchText, setSearchText] = useState('');
  
  // 股票列表弹窗状态
  const [stockModalVisible, setStockModalVisible] = useState(false);
  const [selectedConceptName, setSelectedConceptName] = useState<string>('');
  const [stockList, setStockList] = useState<StockInfo[]>([]);
  
  // 核心逻辑函数
  const fetchConceptSummaries = async () => {
    // 获取概念汇总数据
  };
  
  const fetchConceptStocks = async (conceptName: string) => {
    // 获取概念下股票列表
  };
  
  const handleViewStocks = async (conceptName: string) => {
    // 处理查看股票操作
  };
  
  return (
    // JSX 渲染逻辑
  );
};
```

#### 2. 认证上下文组件
```typescript
interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  login: (credentials: LoginCredentials) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  
  // 自动令牌刷新逻辑
  useEffect(() => {
    const refreshToken = async () => {
      const token = localStorage.getItem('access_token');
      if (token && !isTokenExpired(token)) {
        try {
          const userData = await validateToken(token);
          setUser(userData);
        } catch (error) {
          logout();
        }
      }
      setLoading(false);
    };
    
    refreshToken();
  }, []);
  
  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await apiClient.post('/auth/login', credentials);
      const { access_token, user_info } = response.data;
      
      localStorage.setItem('access_token', access_token);
      setUser(user_info);
      return true;
    } catch (error) {
      return false;
    }
  };
  
  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
  };
  
  return (
    <AuthContext.Provider value={{ 
      isAuthenticated: !!user, 
      user, 
      login, 
      logout, 
      loading 
    }}>
      {children}
    </AuthContext.Provider>
  );
};
```

#### 3. API客户端配置
```typescript
import axios, { AxiosInstance } from 'axios';

// 管理员API客户端
export const adminApiClient: AxiosInstance = axios.create({
  baseURL: 'http://localhost:3007',
  timeout: 30000,
});

// 请求拦截器 - 添加认证令牌
adminApiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器 - 处理认证错误
adminApiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 清除过期令牌，跳转到登录页
      localStorage.removeItem('admin_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 用户API客户端
export const userApiClient: AxiosInstance = axios.create({
  baseURL: 'http://localhost:3007',
  timeout: 30000,
});

// 类似的拦截器配置...
```

### 状态管理策略

#### React Hooks状态管理
```typescript
// 自定义Hook：API数据获取
export const useConceptSummary = (tradingDate: string) => {
  const [data, setData] = useState<ConceptSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await adminApiClient.get(
        `/api/v1/stock-analysis/concepts/daily-summary?trading_date=${tradingDate}&size=500`
      );
      setData(response.data.summaries || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [tradingDate]);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  return { data, loading, error, refetch: fetchData };
};

// 自定义Hook：用户认证状态
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

## 🚀 部署和运维设计

### Docker容器化部署

#### 1. 后端Dockerfile
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 3007

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3007"]
```

#### 2. 前端Dockerfile
```dockerfile
FROM node:18-alpine

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 使用nginx服务静态文件
FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### 3. Docker Compose配置
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: stock_backend
    ports:
      - "3007:3007"
    environment:
      - DATABASE_URL=mysql://root:password@mysql:3306/stock_analysis
      - JWT_SECRET_KEY=your-secret-key
    depends_on:
      - mysql
    volumes:
      - ./backend/logs:/app/logs

  frontend:
    build: ./frontend
    container_name: stock_frontend
    ports:
      - "8006:80"
    depends_on:
      - backend

  client:
    build: ./client
    container_name: stock_client
    ports:
      - "8005:80"
    depends_on:
      - backend

  mysql:
    image: mysql:8.0
    container_name: stock_mysql
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=stock_analysis
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql

volumes:
  mysql_data:
```

### 自动化部署脚本

#### deploy.sh脚本逻辑
```bash
#!/bin/bash

# 股票分析系统 - 部署脚本 v2.6.0
echo "🚀 股票分析系统部署 v2.6.0"
echo "========================="

# 环境检查
check_environment() {
    echo "🔍 环境检查..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker未安装"
        exit 1
    fi
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js未安装"
        exit 1
    fi
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3未安装"
        exit 1
    fi
    
    echo "✅ 环境检查通过"
}

# 数据库初始化
setup_database() {
    echo "🗃️ 数据库初始化..."
    
    # 检查MySQL连接
    mysql -h127.0.0.1 -uroot -e "SELECT 1;" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "❌ MySQL连接失败"
        exit 1
    fi
    
    # 创建数据库
    mysql -h127.0.0.1 -uroot -e "CREATE DATABASE IF NOT EXISTS stock_analysis;"
    
    # 执行表结构
    mysql -h127.0.0.1 -uroot stock_analysis < database/init.sql
    
    echo "✅ 数据库初始化完成"
}

# 后端设置
setup_backend() {
    echo "🐍 后端设置..."
    
    cd backend
    
    # 创建虚拟环境
    python3 -m venv venv
    source venv/bin/activate
    
    # 安装依赖
    pip install -r requirements.txt
    
    # 创建管理员账户
    python create_admin.py
    
    cd ..
    echo "✅ 后端设置完成"
}

# 前端设置
setup_frontend() {
    echo "⚛️ 前端设置..."
    
    # 管理端前端
    cd frontend
    npm install
    npm run build
    cd ..
    
    # 客户端前端
    cd client
    npm install
    npm run build
    cd ..
    
    echo "✅ 前端设置完成"
}

# 主执行流程
main() {
    check_environment
    setup_database
    setup_backend
    setup_frontend
    
    echo ""
    echo "🎉 部署完成！"
    echo "📊 管理端: http://localhost:8006"
    echo "👥 客户端: http://localhost:8005"
    echo "🔧 API文档: http://localhost:3007/docs"
}

# 执行主流程
main
```

### 监控和日志设计

#### 1. 应用日志配置
```python
import logging
from logging.handlers import RotatingFileHandler

# 日志配置
def setup_logging():
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 文件处理器 - 自动轮转
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # 根日志器配置
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger
```

#### 2. 性能监控
```python
import time
from functools import wraps

def monitor_performance(func):
    """性能监控装饰器"""
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # 记录性能指标
            logger.info(f"{func.__name__} executed in {execution_time:.3f}s")
            
            # 慢查询告警
            if execution_time > 5.0:
                logger.warning(f"Slow query detected: {func.__name__} took {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {str(e)}")
            raise
    
    return wrapper

# 使用示例
@monitor_performance
async def get_concept_summary(trading_date: str):
    # API逻辑
    pass
```

#### 3. 健康检查端点
```python
from fastapi import APIRouter

health_router = APIRouter()

@health_router.get("/health")
async def health_check():
    """系统健康检查"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "v2.6.0",
        "checks": {}
    }
    
    # 数据库连接检查
    try:
        db.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # 磁盘空间检查
    import shutil
    total, used, free = shutil.disk_usage("/")
    free_percent = free / total * 100
    
    if free_percent < 10:
        health_status["checks"]["disk"] = f"warning: {free_percent:.1f}% free"
    else:
        health_status["checks"]["disk"] = f"healthy: {free_percent:.1f}% free"
    
    return health_status
```

## 📋 开发规范与维护

### 代码规范

#### 1. Python后端规范
```python
# 类型注解
from typing import List, Dict, Optional, Union
from pydantic import BaseModel

# 数据模型定义
class ConceptSummaryResponse(BaseModel):
    concept_name: str
    total_volume: int
    stock_count: int
    avg_volume: float
    max_volume: int
    trading_date: str
    volume_percentage: float

# 函数注解
async def get_concept_summary(
    trading_date: Optional[str] = None,
    page: int = 1,
    size: int = 50
) -> Dict[str, Union[List[ConceptSummaryResponse], Dict]]:
    """获取概念汇总数据
    
    Args:
        trading_date: 交易日期，格式YYYY-MM-DD
        page: 页码，从1开始
        size: 每页数量，最大2000
        
    Returns:
        包含概念汇总数据和分页信息的字典
        
    Raises:
        HTTPException: 当参数验证失败或数据查询错误时
    """
    pass

# 错误处理
try:
    result = await some_operation()
    return {"success": True, "data": result}
except ValidationError as e:
    logger.warning(f"Validation error: {e}")
    raise HTTPException(status_code=422, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

#### 2. TypeScript前端规范
```typescript
// 接口定义
interface ConceptSummary {
  concept_name: string;
  total_volume: number;
  stock_count: number;
  avg_volume: number;
  max_volume: number;
  trading_date: string;
  volume_percentage: number;
}

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  pagination?: {
    page: number;
    size: number;
    total: number;
    has_more: boolean;
  };
}

// React组件规范
interface NewStockAnalysisPageProps {
  initialDate?: string;
}

const NewStockAnalysisPage: React.FC<NewStockAnalysisPageProps> = ({
  initialDate = '2025-09-02'
}) => {
  // 状态定义
  const [conceptSummaries, setConceptSummaries] = useState<ConceptSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  // 副作用
  useEffect(() => {
    fetchConceptSummaries();
  }, [tradingDate]);
  
  // 事件处理
  const handleSearch = useCallback((value: string) => {
    setSearchText(value);
  }, []);
  
  return (
    <div>
      {/* JSX */}
    </div>
  );
};

export default NewStockAnalysisPage;
```

### 版本控制规范

#### Git提交消息规范
```bash
# 格式：<type>(<scope>): <subject>

# 类型说明：
feat:     新功能
fix:      bug修复
docs:     文档更新
style:    代码格式调整
refactor: 重构
test:     测试相关
chore:    构建过程或辅助工具的变动

# 示例：
feat(api): 新增概念股票列表API
fix(frontend): 修复股票代码搜索问题
docs(readme): 更新v2.6.0功能说明
refactor(database): 优化股票代码匹配逻辑
```

#### 分支管理策略
```bash
# 主分支
main          # 生产环境代码
develop       # 开发环境代码

# 功能分支
feature/concept-driven-analysis    # 概念驱动分析功能
feature/payment-system            # 支付系统功能
feature/admin-management          # 管理员管理功能

# 修复分支
hotfix/login-bug-fix              # 紧急修复分支

# 发布分支
release/v2.6.0                    # 版本发布分支
```

### 测试策略

#### 1. 后端单元测试
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestStockAnalysisAPI:
    """股票分析API测试"""
    
    def test_get_concept_summary_success(self):
        """测试获取概念汇总成功"""
        response = client.get(
            "/api/v1/stock-analysis/concepts/daily-summary",
            params={"trading_date": "2025-09-02", "size": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "summaries" in data
        assert "pagination" in data
    
    def test_get_concept_summary_invalid_date(self):
        """测试无效日期参数"""
        response = client.get(
            "/api/v1/stock-analysis/concepts/daily-summary",
            params={"trading_date": "invalid-date"}
        )
        assert response.status_code == 422
    
    def test_get_concept_stocks_success(self):
        """测试获取概念股票列表成功"""
        response = client.get(
            "/api/v1/stock-analysis/concept/融资融券/stocks",
            params={"trading_date": "2025-09-02", "limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "stocks" in data
        assert data["concept_name"] == "融资融券"

@pytest.fixture
def sample_trading_data():
    """测试用交易数据"""
    return [
        {"stock_code": "SH600000", "trading_volume": 1000000, "trading_date": "2025-09-02"},
        {"stock_code": "SZ000001", "trading_volume": 2000000, "trading_date": "2025-09-02"},
    ]
```

#### 2. 前端组件测试
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import NewStockAnalysisPage from './NewStockAnalysisPage';

// Mock API客户端
jest.mock('../../../shared/admin-auth', () => ({
  adminApiClient: {
    get: jest.fn()
  }
}));

describe('NewStockAnalysisPage', () => {
  beforeEach(() => {
    // 重置mock
    jest.clearAllMocks();
  });
  
  test('renders page title correctly', () => {
    render(<NewStockAnalysisPage />);
    expect(screen.getByText('股票分析 - 概念驱动视图')).toBeInTheDocument();
  });
  
  test('fetches concept summaries on mount', async () => {
    const mockResponse = {
      data: {
        summaries: [
          {
            concept_name: '融资融券',
            total_volume: 622580139,
            stock_count: 2565,
            avg_volume: 242721.0,
            max_volume: 12968518,
            trading_date: '2025-09-02',
            volume_percentage: 4.86
          }
        ],
        pagination: { total: 1 }
      }
    };
    
    (adminApiClient.get as jest.Mock).mockResolvedValue(mockResponse);
    
    render(<NewStockAnalysisPage />);
    
    await waitFor(() => {
      expect(screen.getByText('融资融券')).toBeInTheDocument();
    });
  });
  
  test('handles search functionality', async () => {
    render(<NewStockAnalysisPage />);
    
    const searchInput = screen.getByPlaceholderText('搜索概念名称...');
    fireEvent.change(searchInput, { target: { value: '银行' } });
    
    // 验证搜索功能
    await waitFor(() => {
      expect(searchInput).toHaveValue('银行');
    });
  });
});
```

### 性能优化指南

#### 1. 数据库优化
```sql
-- 创建复合索引优化查询
CREATE INDEX idx_concept_date_volume ON concept_daily_summary(trading_date, total_volume DESC);

-- 分区表处理历史数据（按月分区）
ALTER TABLE daily_trading PARTITION BY RANGE (YEAR(trading_date) * 100 + MONTH(trading_date))
(
  PARTITION p202409 VALUES LESS THAN (202410),
  PARTITION p202410 VALUES LESS THAN (202411),
  PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 查询优化：使用EXPLAIN分析
EXPLAIN SELECT 
  concept_name, 
  total_volume, 
  stock_count 
FROM concept_daily_summary 
WHERE trading_date = '2025-09-02' 
ORDER BY total_volume DESC 
LIMIT 50;
```

#### 2. 前端性能优化
```typescript
import { memo, useCallback, useMemo } from 'react';

// 组件memo化
const ConceptListItem = memo<ConceptListItemProps>(({ concept, onViewStocks }) => {
  const handleClick = useCallback(() => {
    onViewStocks(concept.concept_name);
  }, [concept.concept_name, onViewStocks]);
  
  const formattedVolume = useMemo(() => {
    return concept.total_volume.toLocaleString();
  }, [concept.total_volume]);
  
  return (
    <div onClick={handleClick}>
      <span>{concept.concept_name}</span>
      <span>{formattedVolume}</span>
    </div>
  );
});

// 虚拟滚动优化大列表
import { FixedSizeList as List } from 'react-window';

const VirtualizedConceptList: React.FC<{ concepts: ConceptSummary[] }> = ({ concepts }) => {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style}>
      <ConceptListItem concept={concepts[index]} />
    </div>
  );
  
  return (
    <List
      height={400}
      itemCount={concepts.length}
      itemSize={60}
      width="100%"
    >
      {Row}
    </List>
  );
};
```

#### 3. API性能优化
```python
from functools import lru_cache
from sqlalchemy import text

# 缓存常用查询结果
@lru_cache(maxsize=128)
def get_concept_list_cached() -> List[str]:
    """获取概念列表（缓存1小时）"""
    return db.query(Concept.concept_name).filter(Concept.is_active == True).all()

# 使用原生SQL优化复杂查询
async def get_concept_summary_optimized(trading_date: str, limit: int = 50):
    """优化的概念汇总查询"""
    
    # 使用原生SQL避免ORM开销
    query = text("""
        SELECT 
            concept_name,
            total_volume,
            stock_count,
            average_volume,
            max_volume,
            trading_date,
            (total_volume * 100.0 / (
                SELECT SUM(total_volume) 
                FROM concept_daily_summary 
                WHERE trading_date = :trading_date
            )) as volume_percentage
        FROM concept_daily_summary
        WHERE trading_date = :trading_date
        ORDER BY total_volume DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {
        "trading_date": trading_date,
        "limit": limit
    }).fetchall()
    
    return [dict(row) for row in result]

# 批量操作优化
async def bulk_insert_trading_data(trading_data: List[Dict]) -> int:
    """批量插入交易数据"""
    
    # 使用批量插入提升性能
    stmt = """
        INSERT INTO daily_trading (stock_code, trading_date, trading_volume)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE trading_volume = VALUES(trading_volume)
    """
    
    values = [
        (item['stock_code'], item['trading_date'], item['trading_volume'])
        for item in trading_data
    ]
    
    db.executemany(stmt, values)
    return len(values)
```

## 📈 版本历史与路线图

### 版本发布历史

#### v2.6.0 (2025-09-13) - 概念驱动重构
- 🚀 **核心功能**: 股票分析页面重构为概念驱动模式
- 📊 **数据结构**: 两层数据展示（概念汇总→股票详情）
- ⚡ **性能优化**: API参数限制提升，支持大数据量查询
- 🎯 **用户体验**: 搜索、排序、分页等完整交互功能

#### v2.5.1 (2025-09-12) - 重新计算功能修复
- 🔧 **Bug修复**: 重新计算按钮网络连接失败问题
- ⏱️ **超时优化**: API超时策略优化，长操作支持
- 🏗️ **架构改进**: 导入和重新计算逻辑统一

#### v2.5.0 (2025-09-11) - 页面功能重构
- 📋 **功能明确**: 三个分析页面职责明确分离
- 🔍 **数据一致**: 股票代码匹配逻辑统一
- 📊 **排序优化**: 概念列表严格按交易量排序

#### v2.4.2 (2025-09-11) - 认证系统重构
- 🔐 **JWT优化**: 自动令牌刷新机制
- 👥 **权限分离**: 管理员和用户权限明确区分
- 🛡️ **安全增强**: 超级管理员权限控制

#### v2.4.1 (2025-09-08) - 股票分析增强
- 🔍 **代码支持**: SH/SZ/BJ前缀智能识别
- 📊 **界面重构**: 概念分析卡片式设计
- 🎨 **体验优化**: 响应式设计和错误处理

### 未来版本规划

#### v2.7.0 (计划2025-09-20) - 数据可视化增强
- 📈 **图表系统**: 概念趋势图和股票排名图表
- 🎯 **交互式图表**: 支持时间范围选择和钻取分析
- 📊 **仪表盘**: 管理端数据概览仪表盘
- 🔄 **实时更新**: WebSocket实时数据推送

#### v2.8.0 (计划2025-10-01) - 移动端适配
- 📱 **响应式优化**: 移动端界面适配
- 👆 **触摸交互**: 移动端手势操作支持
- 🔔 **推送通知**: 关键数据变化通知
- 📲 **PWA支持**: 渐进式Web应用

#### v3.0.0 (计划2025-10-15) - 微服务架构
- 🏗️ **架构升级**: 微服务化拆分
- 🚀 **容器编排**: Kubernetes部署支持
- 📊 **监控系统**: 完整的监控和告警体系
- 🔄 **CI/CD**: 自动化部署流水线

---

## 📞 维护和支持

### 文档维护规范

**更新频率**: 每次版本发布时必须更新
**负责人**: 开发团队技术负责人
**审核流程**: 代码审查 → 文档更新 → 测试验证 → 发布

### 问题反馈渠道

**Bug报告**: GitHub Issues
**功能建议**: 开发团队内部讨论
**紧急问题**: 直接联系技术负责人

### 技术债务管理

**代码重构**: 每个版本预留20%时间进行重构
**性能优化**: 定期性能测试和优化
**安全更新**: 及时更新依赖库和安全补丁

---

**文档维护**: 技术团队 | **最后更新**: 2025-09-13 | **下次更新**: v2.7.0发布时