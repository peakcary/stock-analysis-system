# 脚本更新总结 - 支持 Plan 1 架构

## 📋 更新概览

由于数据架构升级到 **Plan 1 完整分离架构**，以下脚本已进行了相应更新以支持新的 `import_batches`、`raw_import_data` 和 `raw_data_mapping` 表：

---

## ✅ 已更新的文件

### 1. `/scripts/database/create_raw_data_tables.sql`

**状态**: ✅ 已更新

**改动**:
- 添加了 `import_batches` 表定义
- 保留了 `raw_import_data` 表
- 保留了 `raw_data_mapping` 表

**新增内容**:
```sql
CREATE TABLE IF NOT EXISTS import_batches (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    import_date DATE NOT NULL,
    import_type VARCHAR(10) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    record_count INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'success',
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_import_date (import_date),
    INDEX idx_import_type (import_type),
    UNIQUE KEY uk_file_date_type (file_name, import_date, import_type)
);
```

**说明**:
- 这是关键更新！之前这个文件缺少 `import_batches` 表
- 现在包含了 Plan 1 的所有三个表

---

### 2. `/scripts/deployment/deploy.sh`

**状态**: ✅ 已更新

**改动**:
- 第 130-136 行：更新表创建逻辑
  ```bash
  # 旧
  mysql -u root -pPp123456 stock_analysis_dev < ../scripts/database/create_raw_data_table.sql

  # 新
  mysql -u root -pPp123456 stock_analysis_dev < ../scripts/database/create_raw_data_tables.sql  # Plan 1
  mysql -u root -pPp123456 stock_analysis_dev < ../scripts/database/create_raw_data_table.sql   # 备份
  ```

- 第 262-272 行：新增表验证检查
  ```python
  'import_batches',        # Plan 1: 导入批次管理
  'raw_import_data',       # Plan 1: 原始导入数据
  'raw_data_mapping'       # Plan 1: 原始数据映射
  ```

- 第 419-452 行：更新完成提示信息
  ```bash
  echo "🎉 完整部署成功！(包含Plan 1完整分离架构 + 数据库优化 v2.7.3)"
  ```

**影响**:
- ✅ 新安装系统会自动创建 Plan 1 表
- ✅ 现有系统运行 `./deploy.sh --migrate` 时会创建新表
- ✅ 更清晰的部署信息反映新架构

---

### 3. `/scripts/database/init_database.sh`

**状态**: ✅ 已更新

**改动**:
- 第 105-109 行：更新表创建顺序
  ```bash
  # 旧
  execute_sql_file "$SCRIPT_DIR/create_raw_data_table.sql" "创建CSV原始数据表"

  # 新
  execute_sql_file "$SCRIPT_DIR/create_raw_data_tables.sql" "创建Plan 1原始数据表"
  execute_sql_file "$SCRIPT_DIR/create_raw_data_table.sql" "创建CSV备份表"
  ```

- 第 129-144 行：更新完成信息，分类显示表
  ```bash
  echo "  Plan 1 - 完整分离架构:"
  echo "  ✅ import_batches            - 导入批次管理"
  echo "  ✅ raw_import_data           - 原始导入数据"
  echo "  ✅ raw_data_mapping          - 原始数据映射"
  ```

**影响**:
- ✅ 数据库初始化时包含 Plan 1 表
- ✅ 更清晰的表分类和说明

---

## 🆕 新增的文件

### 1. `/scripts/database/migrate_to_plan1.sh`

**状态**: ✅ 已创建

**功能**:
- 自动迁移现有系统到 Plan 1 架构
- 包含数据库备份功能
- 验证表是否成功创建
- 提供回滚方案

**使用方式**:
```bash
# 自动迁移（包含备份）
./scripts/database/migrate_to_plan1.sh

# 跳过备份
./scripts/database/migrate_to_plan1.sh --skip-backup

# 自定义数据库参数
./scripts/database/migrate_to_plan1.sh --host localhost --user root --password yourpass --database stock_analysis_dev
```

**关键特性**:
- ✅ 幂等性设计（可重复执行）
- ✅ 数据库备份 (backup_YYYYMMDD_HHMMSS.sql)
- ✅ 表存在检查（避免重复创建）
- ✅ 完整的验证流程
- ✅ 清晰的回滚说明

---

### 2. `/PLAN1_MIGRATION.md`

**状态**: ✅ 已创建

**内容**:
- Plan 1 架构完整说明
- 升级步骤详解
- 新表详细描述
- 导入逻辑变化
- 验证方法
- 回滚方案
- 常见问题解答

**对象**: 系统管理员和开发人员

---

### 3. `/ARCHITECTURE_CHANGES_v2.7.3.md`

**状态**: ✅ 已创建

**内容**:
- 架构变更总结
- 完整改动清单（按文件）
- 性能影响分析
- 验证清单
- 故障排除指南

**对象**: 开发人员和架构师

---

## 📊 脚本依赖关系

```
部署流程:
  deploy.sh
    ├─ create_raw_data_tables.sql (新 - Plan 1)
    ├─ create_raw_data_table.sql  (旧 - 备份)
    └─ init_database.sh
        ├─ create_raw_data_tables.sql
        └─ create_raw_data_table.sql

迁移流程:
  migrate_to_plan1.sh
    └─ create_raw_data_tables.sql
```

---

## 🔍 关键更新要点

### 为什么需要更新脚本？

1. **新表支持**
   - `import_batches`: 导入批次管理
   - `raw_import_data`: 原始数据保存（新功能）
   - `raw_data_mapping`: 数据追踪（新功能）

2. **导入逻辑改变**
   - 每次导入都会创建一个批次记录
   - 所有原始数据都被保存
   - 业务数据处理和原始数据分离

3. **双格式支持**
   - CSV 导入保存原始数据到 raw_import_data
   - TXT 导入也保存原始数据到 raw_import_data
   - 统一的原始数据保存机制

---

## ✅ 验证清单

部署后，请验证：

```bash
# 1. 检查表是否存在
mysql -u root -p stock_analysis_dev -e "
SHOW TABLES LIKE 'import_batches';
SHOW TABLES LIKE 'raw_import_data';
SHOW TABLES LIKE 'raw_data_mapping';
SHOW TABLES LIKE 'stock_concept_raw_data';
"

# 2. 检查表结构
mysql -u root -p stock_analysis_dev << EOF
DESCRIBE import_batches;
DESCRIBE raw_import_data;
DESCRIBE raw_data_mapping;
EOF

# 3. 系统检查
./status.sh

# 4. 导入测试
# 上传一个 CSV 文件进行测试
# 检查数据是否在 raw_import_data 中
```

---

## 📝 迁移指南

### 新安装

```bash
cd /path/to/stock-analysis-system
./scripts/deployment/deploy.sh
# Plan 1 表会自动创建
```

### 现有系统升级

```bash
# 方法 1: 自动迁移（推荐）
./scripts/database/migrate_to_plan1.sh
./scripts/deployment/deploy.sh --migrate
./stop.sh && ./start.sh

# 方法 2: 手动升级
./scripts/deployment/deploy.sh --migrate
./stop.sh && ./start.sh
```

---

## 🔙 回滚方案

```bash
# 如果需要回滚，使用迁移脚本创建的备份：
mysql -u root -p < backup_20251017_143000.sql

# 或手动删除新表
mysql -u root -p stock_analysis_dev << EOF
DROP TABLE IF EXISTS raw_data_mapping;
DROP TABLE IF EXISTS raw_import_data;
DROP TABLE IF EXISTS import_batches;
EOF
```

---

## 📞 故障排除

**问题**: 部署失败，提示表不存在
```
解决: 确认 SQL 脚本存在
ls -l scripts/database/create_raw_data_tables.sql
```

**问题**: 迁移脚本权限错误
```
解决: 添加执行权限
chmod +x scripts/database/migrate_to_plan1.sh
```

**问题**: 新表创建失败，MySQL 密码错误
```
解决: 在脚本中检查并更新密码
grep "Pp123456" scripts/database/migrate_to_plan1.sh
grep "Pp123456" scripts/deployment/deploy.sh
```

---

## 📈 后续工作

| 任务 | 状态 | 优先级 |
|------|------|--------|
| 原始数据到业务数据的映射函数 | 🔄 进行中 | 高 |
| API 接口支持原始数据查询 | 📋 计划中 | 中 |
| 自动数据映射处理 | 📋 计划中 | 中 |
| 审计日志记录 | 📋 计划中 | 低 |

---

## 📚 相关文档

- ✅ [PLAN1_MIGRATION.md](./PLAN1_MIGRATION.md) - 完整迁移指南
- ✅ [ARCHITECTURE_CHANGES_v2.7.3.md](./ARCHITECTURE_CHANGES_v2.7.3.md) - 架构变更详解
- 📖 [数据导入逻辑](./backend/app/services/data_import.py) - 导入实现代码
- 📖 [数据模型](./backend/app/models/stock.py) - 数据模型定义

---

## 📞 技术支持

遇到问题？

1. 查看日志文件
   ```bash
   tail -f logs/backend.log
   ```

2. 运行系统检查
   ```bash
   ./status.sh
   ```

3. 查看本文档及相关指南

4. 检查数据库连接
   ```bash
   mysqladmin ping
   ```

---

**版本**: v2.7.3
**更新日期**: 2025-10-17
**状态**: ✅ 完成并测试
