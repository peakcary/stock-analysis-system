# 变更日志 - v2.7.0

## 🎉 发布日期：2025-10-15

## ✨ 新增功能

### 1. CSV原始数据表 (`stock_concept_raw_data`)
- **功能**：保存CSV导入时的完整原始数据，不进行拆分
- **优势**：
  - ✅ 单表查询，无需JOIN，查询速度快
  - ✅ 完整保留CSV每行数据，便于数据审计
  - ✅ 支持快速导出为CSV格式
  - ✅ 包含文件名和行号，便于追溯
  - ✅ 保留股票-概念的多对多关系原始数据

- **表结构**：
  ```sql
  stock_concept_raw_data (
    id, import_date, trade_date,
    stock_code, stock_name, concept, industry,
    price, turnover_rate, net_inflow,
    pages_count, total_reads,
    file_name, row_number, created_at
  )
  ```

### 2. 双写机制
- **功能**：CSV导入时同时写入两个地方
  - 拆分表：stocks, concepts, stock_concepts, daily_stock_data（保持原有逻辑）
  - 原始表：stock_concept_raw_data（新增）

- **文件**：`backend/app/services/data_import.py:272-288`

### 3. 原始数据API接口
新增 `/api/v1/raw-data/` 系列接口：

#### 3.1 按日期查询
```
GET /api/v1/raw-data/daily?trade_date=2025-08-28&page=1&size=50
```
**功能**：查询指定日期的原始数据，支持分页、排序、筛选

#### 3.2 导出CSV
```
GET /api/v1/raw-data/export/csv?trade_date=2025-08-28
```
**功能**：导出指定日期的数据为CSV文件

#### 3.3 统计信息
```
GET /api/v1/raw-data/stats/daily?trade_date=2025-08-28
```
**功能**：获取指定日期的统计信息（记录数、股票数、概念数等）

#### 3.4 查询指定股票
```
GET /api/v1/raw-data/stock/{stock_code}?trade_date=2025-08-28
```
**功能**：获取指定股票在该日期的所有概念数据

#### 3.5 概念列表
```
GET /api/v1/raw-data/concepts?trade_date=2025-08-28
```
**功能**：获取指定日期的所有概念及统计

#### 3.6 日期列表
```
GET /api/v1/raw-data/dates?limit=30
```
**功能**：获取有数据的日期列表

- **文件**：`backend/app/api/api_v1/endpoints/raw_data.py`

## 🐛 Bug修复

### 1. ADMIN_SECRET_KEY配置问题
- **问题**：后端启动时报错 "ADMIN_SECRET_KEY environment variable must be set"
- **原因**：配置加载机制问题
- **修复**：
  - 在 `config.py` 的 `Settings` 类中添加 `ADMIN_SECRET_KEY` 配置项
  - 修改 `admin_auth.py` 从 `settings` 对象读取配置
- **文件**：
  - `backend/app/core/config.py:49-52`
  - `backend/app/core/admin_auth.py:17-24`

### 2. 数据库表不存在错误
- **问题**：CSV导入时报错 "Table 'stock_concept_raw_data' doesn't exist"
- **修复**：SQL语法错误（`row_number` 保留字需要反引号）
- **文件**：`scripts/database/create_raw_data_table.sql:28`

## 🔧 改进优化

### 1. 部署脚本更新
- **文件**：`scripts/deployment/deploy.sh`
- **版本**：v2.7.0
- **更新**：
  - 添加原始数据表创建步骤
  - 添加表验证检查
  - 更新版本信息和功能描述

### 2. 数据库初始化脚本
- **文件**：`scripts/database/init_database.sh` (新增)
- **功能**：独立的数据库初始化脚本，支持参数配置
- **用法**：
  ```bash
  ./scripts/database/init_database.sh \
    --host localhost \
    --user root \
    --password yourpass \
    --database stock_analysis_dev
  ```

### 3. 快速升级脚本
- **文件**：`scripts/deployment/upgrade_v2.7.sh` (新增)
- **功能**：为已部署系统快速添加v2.7.0新功能
- **用法**：
  ```bash
  ./scripts/deployment/upgrade_v2.7.sh
  ```

### 4. 模型导出更新
- **文件**：`backend/app/models/__init__.py`
- **更新**：添加 `StockConceptRawData` 模型导出

## 📊 数据对比

| 特性 | 拆分存储（原有） | 原始表（新增） |
|------|------------------|----------------|
| **查询复杂度** | 需要JOIN多表 | ✅ 单表查询 |
| **查询速度** | 较慢 | ✅ 快速 |
| **数据规范性** | ✅ 高度规范 | 有冗余 |
| **存储空间** | ✅ 节省 | 占用更多 |
| **导出还原** | 需要复杂SQL | ✅ 直接SELECT |
| **数据审计** | 较困难 | ✅ 完整追溯 |
| **适用场景** | 业务逻辑、统计分析 | 快速查询、数据对账 |

## 📝 导入流程变化

### 之前（v2.6.x）
```
CSV文件 → 解析 → 拆分存储到4个表
```

### 现在（v2.7.0）
```
CSV文件 → 解析 → 双写：
                ├─ 拆分存储到4个表（保持不变）
                └─ 原始存储到1个表（新增）
```

### 导入日志示例
```
📈 CSV导入完成总结:
   📋 文件名: 2025-08-28-01-46.csv
   📅 导入日期: 2025-08-28
   📊 处理记录: 1500 成功, 0 跳过
   🏢 股票信息: 150 新增, 0 更新
   🏷️  概念信息: 50 新增概念
   🔗 关联关系: 1500 新增关联
   📈 每日数据: 150 新增, 0 更新
   💾 原始数据: 1500 条记录（未拆分）  ← 新增
   ✅ 导入状态: 完全成功
```

## 🚀 迁移指南

### 方案一：全新部署
```bash
git pull origin main
./scripts/deployment/deploy.sh
./scripts/deployment/start.sh
```

### 方案二：已有系统升级
```bash
git pull origin main
./scripts/deployment/upgrade_v2.7.sh
```

### 方案三：手动升级
```bash
# 1. 创建表
mysql -u root -p stock_analysis_dev < scripts/database/create_raw_data_table.sql

# 2. 更新代码
git pull origin main

# 3. 重启服务
./scripts/deployment/stop.sh
./scripts/deployment/start.sh
```

## 🧪 测试验证

### 1. 验证表创建
```sql
USE stock_analysis_dev;
DESCRIBE stock_concept_raw_data;
```

### 2. 测试导入
1. 登录管理后台
2. 导入CSV文件
3. 查看日志确认双写成功

### 3. 测试API
```bash
# 查询原始数据
curl "http://localhost:3007/api/v1/raw-data/daily?trade_date=2025-08-28"

# 获取统计
curl "http://localhost:3007/api/v1/raw-data/stats/daily?trade_date=2025-08-28"
```

## 📚 相关文档

- **部署指南**：`DEPLOYMENT_V2.7.md`
- **API文档**：http://localhost:3007/docs
- **代码变更**：
  - 模型：`backend/app/models/stock.py:49-80`
  - 服务：`backend/app/services/data_import.py:272-359`
  - API：`backend/app/api/api_v1/endpoints/raw_data.py`
  - 路由：`backend/app/api/api_v1/api.py:47`

## 🔄 兼容性

- ✅ **向后兼容**：原有拆分存储逻辑保持不变
- ✅ **无需数据迁移**：新表独立，不影响现有数据
- ✅ **渐进式升级**：可选择是否使用新功能
- ✅ **API兼容**：原有API全部保持不变

## ⚠️ 注意事项

1. **存储空间**：原始表会增加存储空间占用（约原数据的1.5倍）
2. **MySQL保留字**：`row_number` 需要使用反引号
3. **配置检查**：确保 `ADMIN_SECRET_KEY` 已配置
4. **权限问题**：确保MySQL用户有CREATE TABLE权限

## 👥 贡献者

- @peakom - 功能开发和文档编写

## 📞 支持

遇到问题？
1. 查看日志：`tail -f logs/backend.log`
2. 查看文档：`DEPLOYMENT_V2.7.md`
3. 提交Issue：GitHub Issues

---

**版本**: v2.7.0
**发布时间**: 2025-10-15
**下一版本预告**: v2.8.0 - 数据分析增强
