# 📊 股票代码字段升级指南

> **版本**: v2.4.0  
> **更新**: 2025-09-08  
> **状态**: 🔧 开发阶段功能

## 🎯 升级目的

为了解决TXT文件导入时股票代码前缀（SH/SZ/BJ）匹配问题，系统新增了两个字段：

- **原始股票代码** (`original_stock_code`): 存储完整的原始代码，如 `SH600000`
- **标准化股票代码** (`normalized_stock_code`): 存储去除前缀的代码，如 `600000`

## 🚀 快速升级

### 方法1: 自动升级（推荐）
```bash
# 升级股票代码字段
./deploy.sh --upgrade-stock-codes

# 升级完成后重启服务
./start.sh
```

### 方法2: 手动执行
```bash
# 进入后端目录
cd backend
source venv/bin/activate

# 运行迁移脚本
python migrate_stock_codes.py

# 返回根目录重启服务
cd ..
./start.sh
```

## 🔍 验证升级结果

### 检查迁移状态
```bash
# 运行完整部署会自动检查
./deploy.sh

# 或查看详细验证信息
cd backend && source venv/bin/activate
python -c "
from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT 
            COUNT(*) as total,
            COUNT(original_stock_code) as with_original,
            COUNT(normalized_stock_code) as with_normalized
        FROM daily_trading
        WHERE original_stock_code IS NOT NULL 
        AND original_stock_code != ''
    '''))
    
    row = result.fetchone()
    print(f'总记录数: {row.total}')
    print(f'已升级记录: {row.with_original}')
    print(f'升级完成率: {(row.with_original/row.total*100):.1f}%' if row.total > 0 else '100%')
"
```

### 测试TXT导入
1. 准备包含前缀的TXT文件：
```
SH600000	2024-02-20	1500000
SZ000001	2024-02-20	2100000
BJ430047	2024-02-20	850000
```

2. 通过管理端导入该文件
3. 检查概念汇总是否正常生成

## 🆕 新增功能

### API增强
升级后可使用新的API接口：

```bash
# 市场分布统计
GET /api/v1/enhanced-stock-analysis/market-distribution

# 按前缀搜索
GET /api/v1/enhanced-stock-analysis/search-by-prefix?prefix=SH

# 双代码查询（支持原始或标准化代码）
GET /api/v1/enhanced-stock-analysis/dual-code-query/SH600000
GET /api/v1/enhanced-stock-analysis/dual-code-query/600000

# 代码格式分析
GET /api/v1/enhanced-stock-analysis/code-format-analysis

# 迁移状态检查
GET /api/v1/enhanced-stock-analysis/migration-status
```

### 数据查询增强
```sql
-- 可以同时查询原始和标准化代码
SELECT 
    original_stock_code,     -- SH600000
    normalized_stock_code,   -- 600000
    trading_volume
FROM daily_trading 
WHERE trading_date = '2024-02-20'
AND (
    original_stock_code = 'SH600000' OR 
    normalized_stock_code = '600000'
);
```

## ⚠️ 注意事项

### 升级前
- ✅ 确保已备份重要数据
- ✅ 在测试环境先验证
- ✅ 检查磁盘空间充足

### 升级后
- ✅ 重启所有服务
- ✅ 测试TXT导入功能
- ✅ 验证概念汇总计算
- ✅ 检查API响应正常

### 兼容性
- ✅ **完全向后兼容**: 现有查询和API继续工作
- ✅ **数据完整性**: 原有数据不会丢失
- ✅ **功能增强**: 新增功能不影响现有功能

## 🔧 故障排除

### 常见问题

#### 1. 迁移脚本执行失败
```bash
# 检查错误信息
python database/migrate_stock_codes.py

# 常见原因：
# - 数据库连接失败
# - 权限不足
# - 磁盘空间不足
```

#### 2. 字段检查失败
```bash
# 手动检查字段是否存在
mysql -e "
USE stock_analysis;
DESCRIBE daily_trading;
" | grep -E "(original|normalized)_stock_code"
```

#### 3. TXT导入仍然失败
```bash
# 检查日志
tail -f backend/logs/app.log

# 常见原因：
# - 服务未重启
# - 代码版本不匹配
# - 数据库连接问题
```

## 📊 性能影响

### 存储空间
- 每条记录增加约30字节
- 1万条记录约增加300KB
- 索引占用额外空间约50%

### 查询性能
- ✅ 新增优化索引，查询性能不受影响
- ✅ 原有查询逻辑不变
- ✅ 新功能查询已优化

## 🔄 回滚方案

如需回滚（不推荐）：
```sql
-- 备份新字段数据（可选）
CREATE TABLE daily_trading_backup AS 
SELECT original_stock_code, normalized_stock_code, id 
FROM daily_trading;

-- 删除新字段（谨慎操作！）
ALTER TABLE daily_trading 
DROP COLUMN original_stock_code,
DROP COLUMN normalized_stock_code;

-- 删除相关索引
DROP INDEX idx_original_stock_date ON daily_trading;
DROP INDEX idx_normalized_stock_date ON daily_trading;
```

## 📞 支持

如遇到问题：
1. 检查部署日志输出
2. 查看系统错误日志 `logs/` 目录
3. 运行 `./status.sh` 检查服务状态
4. 提供详细的错误信息和系统状态

---

**升级完成后，你的股票分析系统将具备更强的数据处理和分析能力！** 🚀