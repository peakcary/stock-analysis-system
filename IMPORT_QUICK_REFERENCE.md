# 数据导入系统快速参考

## 文件位置导航

### 前端组件
```
DataImportPage.tsx (主导入页面，1000+行)
├─ CSV导入区域 (CSV Basic Data Import)
├─ TXT导入区域 (TXT Heat Data Import)
├─ TTV导入区域 (TTV Video Data Import) - NEW
├─ EEE导入区域 (EEE Energy Data Import) - NEW
└─ 股票列表 + 多条件搜索

HistoricalDataImport.tsx (历史数据导入，750行)
├─ 5步流程: 文件选择 → 预览 → 确认 → 进度 → 完成
├─ 大文件优化: 分块上传 + 流式处理
└─ 异步支持: <10MB同步, 10-100MB异步, >100MB分块

TxtImportRecords.tsx / TtvImportRecords.tsx / EeeImportRecords.tsx
└─ 导入历史记录列表
```

### 后端服务

#### 核心服务层
```
DataImportService
├─ import_csv_data()    - CSV导入 (两遍处理)
├─ import_txt_data()    - TXT导入 (覆盖模式)
└─ import_daily_batch() - 批量导入 CSV+TXT

UniversalImportService (通用导入)
├─ parse_file_content()      - 文件解析
├─ import_file()             - 文件导入
├─ perform_calculations()    - 计算汇总
└─ 支持动态文件类型 (TTV, EEE等)

TxtImportService (传统TXT导入)
├─ parse_txt_content()
└─ import_daily_trading()
```

#### API端点层
```
/api/v1/import-csv
├─ POST
├─ 验证: 文件类型, 大小 ≤100MB
└─ 返回: {imported_records, skipped_records, stats}

/api/v1/import-txt
├─ POST
├─ 验证: 文件类型, 大小 ≤50MB
└─ 返回: {imported_records, stats}

/api/v1/universal-import/import
├─ POST
├─ 参数: file_type, trading_date, mode
└─ 动态处理: TTV, EEE等

/api/v1/universal-import/{fileType}/check-date
├─ POST
├─ 检查日期是否已有数据
└─ 返回: {exists, count}

/api/v1/historical-txt-import/preview
├─ POST
├─ 文件预览 (日期分布)
└─ 用于大文件预处理

/api/v1/historical-txt-import/import-sync
├─ POST
├─ 同步导入 (<10MB)
└─ 直接返回结果

/api/v1/historical-txt-import/import-async
├─ POST
├─ 异步导入 (10-100MB)
└─ 返回 task_id，需要轮询

/api/v1/historical-txt-import/progress/{taskId}
├─ GET
├─ 轮询导入进度 (每2秒)
└─ 实时显示当前处理的日期
```

#### 数据库模型
```
Stock                    - 股票基本信息
Concept                  - 概念信息
StockConcept             - 股票-概念关联
DailyStockData           - 每日交易数据 (合并)
DataImportRecord         - 导入记录元数据
ImportBatch              - 导入批次信息
RawImportData            - 原始导入数据行
StockConceptRawData      - 原始概念关联 (双写)
{FileType}DailyTrading   - 动态表 (TTV, EEE等)
```

## 关键配置

### 数据库连接池
```python
DATABASE_POOL_SIZE: int = 10           # 基础连接数
DATABASE_MAX_OVERFLOW: int = 20        # 最大溢出连接
DATABASE_POOL_TIMEOUT: int = 30        # 等待超时(秒)
DATABASE_POOL_RECYCLE: int = 3600      # 连接回收(秒)
```

### 文件大小限制
```
CSV: ≤100MB
TXT: ≤50MB
历史数据: ≤500MB
```

### 超时设置
```
默认: 30秒
大文件导入: 120秒 (2分钟)
建议: 异步处理超过10MB的文件
```

## 导入流程速查

### CSV导入流程
```
1. 解析日期 (文件名 → 今天)
2. 检查重复 (存在 && 不覆盖 → 拒绝)
3. 标准化列 (中英文自动转换)
4. 第一遍: 收集股票/概念信息
5. 第二遍: 
   - 插入Stock (新增或更新)
   - 插入Concept (新增)
   - 关联StockConcept
   - 插入DailyStockData (仅一次)
   - 保存RawImportData (所有)
   - 双写StockConceptRawData
6. 批量保存 (bulk_save_objects)
7. 提交事务 (db.commit)
8. 返回统计
```

### TXT导入流程
```
1. 预解析文件 (收集日期)
2. 确定目标日期 (参数 → 文件内容 → 最常见 → 文件名)
3. 删除旧数据 (覆盖模式)
   - DELETE daily_stock_data WHERE trade_date=target AND stock_id IN (...)
4. 逐行处理:
   - 验证: 股票代码 (6位数字), 热度值 (float)
   - 创建Stock (不存在)
   - 创建DailyStockData
   - 保存RawImportData
5. 批量保存
6. 提交事务
7. 返回统计
```

### 大文件导入流程
```
文件大小判断:
├─ <50MB: 直接上传
│  ├─ <10MB: POST /import-sync (同步)
│  │  └─ 直接返回结果
│  └─ 10-50MB: POST /import-async (异步)
│     ├─ 返回 task_id
│     └─ 轮询 GET /progress/{taskId}
│
├─ 50-100MB: 优化上传
│  ├─ POST /import-async
│  └─ 轮询进度 (显示当前日期)
│
└─ >100MB: 分块上传
   ├─ POST /large-file-upload/direct-large-upload
   │  └─ 显示上传进度条
   └─ 轮询 GET /large-file-upload/progress/{uploadId}
      └─ 流式处理 + 显示进度
```

## 性能数据

### 批量插入
```
方式: SQLAlchemy bulk_save_objects()
效率: 远快于逐条 add() + flush()
示例: 10000条记录 → <1秒 (vs 1-2分钟逐条插入)
```

### 内存优化
```
两遍遍历: 第一遍收集统计，第二遍插入数据
跟踪字典: processed_stock_dates 避免重复插入
分批处理: 1000条一批的batch_size
```

### 数据库性能
```
索引:
- idx_import_date (import_date)
- idx_import_type (import_type)
- idx_import_status (import_status)
- uk_date_type_file (import_date, import_type, file_name) UNIQUE

建议添加:
- stock_id + trade_date 复合索引 (daily_stock_data)
- file_type + trading_date (动态表)
```

## 错误处理

### 前端验证
```
✓ 文件类型检查 (.csv/.txt/.ttv/.eee)
✓ 文件大小检查 (≤500MB)
✓ 日期格式检查 (YYYY-MM-DD 或 YYYYMMDD)
✓ 股票代码验证 (6位数字)
✓ 编码检查 (UTF-8/GBK)
```

### 后端验证
```
✓ 必需列检查 (stock_code, stock_name, concept)
✓ 数据类型检查 (数字、日期、浮点数)
✓ 股票代码规范化 (SH600000 → 600000)
✓ 转债检测 (1开头的6位代码)
✓ 错误日志 (仅保存前5个错误)
```

### 错误恢复
```
- 单行错误不影响其他行 (continue处理)
- 事务回滚机制 (db.rollback)
- 部分导入支持 (import_status='partial')
- 覆盖模式对已删除数据的处理
```

## 关键优化

### 1. 两遍处理 (CSV)
```python
# 第一遍: 收集统计信息
for index, row in df.iterrows():
    csv_stocks_info[code] = {name, industry}
    csv_stock_concepts[code].add(concept)

# 第二遍: 插入数据
for index, row in df.iterrows():
    stock = get_or_create(Stock)
    concept = get_or_create(Concept)
    create_or_update(StockConcept)
    create(DailyStockData)  # 仅一次
    save_to_raw(RawImportData)
```

### 2. 覆盖模式 (TXT)
```python
if allow_overwrite or existing_record:
    # 删除该日期的旧数据
    DELETE FROM daily_stock_data 
    WHERE trade_date = target_date 
    AND stock_id IN (collected_stock_ids)
    
    # 插入新数据
    INSERT INTO daily_stock_data (...)
    
    # 单个事务完成
    db.commit()
```

### 3. 大文件异步处理
```typescript
// 前端
if (fileSizeMB > 10) {
    task_id = await POST /import-async
    // 每2秒轮询一次
    GET /progress/{task_id}
} else {
    result = await POST /import-sync
}

// 后端
# 异步导入
asyncio.create_task(background_import(task_id, content))
return {task_id: ...}

# 轮询进度
GET /progress/{task_id} → {status, current, total, ...}
```

## 故障排查

### 导入超时
```
问题: 文件太大，超过120秒超时
解决: 
1. 使用异步导入 (POST /import-async)
2. 增加server超时配置
3. 分割文件为多个较小的文件
```

### 重复记录
```
问题: DailyStockData出现重复 (同一stock_id+trade_date)
原因: CSV中同一股票出现多行
解决: 已通过 processed_stock_dates 跟踪避免
```

### 内存溢出
```
问题: 处理超大文件时内存不足
解决:
1. 使用分块上传 (>100MB)
2. 分批处理 (batch_size=1000)
3. 及时释放旧数据 (db.flush)
```

### 日期检测失败
```
问题: 无法从文件检测日期
原因: 日期格式不标准
解决: 
1. 检查文件格式 (YYYY-MM-DD 或 YYYYMMDD)
2. 使用文件名解析日期 (_extract_date_from_filename)
3. 指定 trade_date 参数
```

## 扩展指南

### 添加新的文件类型 (如XYZ格式)
```python
# 1. 在FileTypeRegistry中注册配置
registry.config_manager.register({
    'file_type': 'xyz',
    'display_name': 'XYZ格式',
    'file_extensions': ['.xyz'],
    'max_file_size': 100*1024*1024,
    'enabled': True
})

# 2. 创建动态表 (自动执行)
# 表名: xyz_daily_trading, xyz_concept_summary等

# 3. 通过通用API使用
POST /api/v1/universal-import/import
{
    "file_type": "xyz",
    "trading_date": "2024-01-01",
    "mode": "overwrite"
}
```

### 性能优化建议
```
1. 缓存Stock/Concept对象 (避免重复查询)
2. 使用Redis缓存热数据
3. 异步触发后续计算 (RankingCalculatorService)
4. 实现导入队列 (Celery)
5. 定期清理过期原始数据 (RawImportData)
```

## 常用命令

### 检查导入记录
```python
# 查询最近的导入
db.query(DataImportRecord)\
  .order_by(DataImportRecord.created_at.desc())\
  .limit(10)

# 按日期查询
db.query(DataImportRecord)\
  .filter(DataImportRecord.import_date == date(2025, 1, 15))\
  .all()
```

### 手动重新计算
```python
# 触发重新计算
POST /api/v1/universal-import/{file_type}/recalculate
{
    "trading_date": "2025-01-15"
}
```

### 检查数据导入状态
```python
# 导入完整性检查
service.check_daily_import_completeness(date(2025, 1, 15))
# 返回: {csv_imported, txt_imported, complete, ...}
```

---

**最后更新**: 2025-11-11
**系统版本**: dev/20251023
**状态**: 完全可用
