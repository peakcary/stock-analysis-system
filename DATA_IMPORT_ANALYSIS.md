# 数据导入系统完整分析报告

## 项目概况
- **分支**: dev/20251023
- **系统**: 股票分析系统
- **分析时间**: 2025-11-11
- **核心功能**: 多格式数据导入（CSV、TXT、TTV、EEE等）

---

## 一、前端数据导入架构

### 1.1 核心组件层级
```
DataImportPage (主页面)
├── CSV导入区域
│   ├── 选择文件按钮
│   └── 导入结果显示
├── TXT导入区域
│   ├── 选择文件按钮
│   ├── HistoricalDataImport (历史数据导入)
│   └── TxtImportRecords (导入记录)
├── TTV导入区域
│   ├── 文件选择器
│   ├── 日期检查 (checkDateExists)
│   ├── 覆盖确认Modal
│   └── TtvImportRecords (导入记录)
└── EEE导入区域
    ├── 文件选择器
    ├── 日期检查 (checkDateExists)
    ├── 覆盖确认Modal
    └── EeeImportRecords (导入记录)
```

### 1.2 主组件: DataImportPage.tsx

**位置**: `/Users/peakom/work/stock-analysis-system/frontend/src/components/DataImportPage.tsx`

**关键功能**:
- CSV基础数据导入（股票代码、名称、概念、行业）
- TXT热度数据导入（每日交易量）
- TTV视频数据导入（新增）
- EEE能源数据导入（新增）
- 股票列表查询和过滤

**文件处理流程**:

```typescript
1. 用户选择文件
   ↓
2. parseFileDate() - 解析文件中的交易日期
   ├─ 支持格式: YYYY-MM-DD 或 YYYYMMDD
   ├─ 从文件内容第一行的第二字段提取
   └─ 回退到文件名或今天的日期

3. checkDateExists() - 验证日期是否已有数据
   └─ POST /api/v1/universal-import/{fileType}/check-date
   ├─ 返回: { exists: boolean, count: number }
   └─ 如果存在，显示覆盖确认Modal

4. executeFileImport() - 执行导入
   └─ POST /api/v1/universal-import/import
   ├─ FormData: {file, file_type, trading_date}
   ├─ timeout: 120000ms (2分钟)
   └─ 监听导入结果事件
```

**关键状态管理**:
```typescript
interface DataImportPageProps {
  stocks: any[];                          // 股票列表
  loading: boolean;                       // 加载中
  csvImportLoading: boolean;              // CSV导入中
  txtImportLoading: boolean;              // TXT导入中
  ttvImportLoading?: boolean;             // TTV导入中
  eeeImportLoading?: boolean;             // EEE导入中
  importStats: any;                       // 导入统计
  importResult?: any;                     // 导入结果
  onGetAllStocks: () => void;
  onCsvImport: () => void;
  onTxtImport: () => void;
  onTtvImport?: () => void;
  onEeeImport?: () => void;
  onGetStockList: (searchText?: string) => void;
  searchText: string;
  onSearchTextChange: (value: string) => void;
  onUpdateStock?: (stockCode: string, updatedData: any) => void;
  onTxtImportSuccess?: () => void;
}
```

**覆盖确认逻辑**:
```typescript
// 显示覆盖确认Modal
if (checkResult.exists) {
  setOverwriteData({
    file,
    fileType: 'ttv' | 'eee',
    tradingDate,
    count: checkResult.count
  });
  setOverwriteModalVisible(true);
}

// 确认覆盖后
await executeFileImport(fileType, file, true, tradingDate);
```

### 1.3 历史数据导入: HistoricalDataImport.tsx

**位置**: `/Users/peakom/work/stock-analysis-system/frontend/src/components/HistoricalDataImport.tsx`

**特点**: 支持大文件导入和流式处理

**五步流程**:
```
Step 1: 选择文件 → Upload.Dragger
   ↓ (beforeUpload={false} 防止自动上传)
   ├─ 验证文件大小 (≤500MB)
   └─ 根据大小选择处理策略
      ├─ <50MB: 小文件，直接上传
      ├─ 50-100MB: 大文件，优化上传
      └─ >100MB: 超大文件，分块上传

Step 2: 预览文件
   └─ POST /api/v1/historical-txt-import/preview
   ├─ 上传进度: 显示0-90%
   ├─ 返回: 
   │  ├─ total_lines: 总行数
   │  ├─ preview_lines: 预览行数
   │  ├─ estimated_dates: 发现日期数
   │  └─ date_preview: 日期分布
   └─ 显示表格预览

Step 3: 确认导入
   └─ 选择合适的导入模式
      ├─ 同步导入 (<10MB)
      │  └─ POST /api/v1/historical-txt-import/import-sync
      │     └─ 进度: 0-100%，单次返回结果
      │
      ├─ 异步导入 (10-100MB)
      │  ├─ POST /api/v1/historical-txt-import/import-async
      │  │  └─ 返回: task_id
      │  └─ 轮询进度 (每2秒)
      │     └─ GET /api/v1/historical-txt-import/progress/{taskId}
      │
      └─ 大文件分块上传 (>100MB)
         ├─ POST /api/v1/large-file-upload/direct-large-upload
         │  └─ 显示上传进度
         └─ 轮询导入进度
            └─ GET /api/v1/large-file-upload/progress/{uploadId}

Step 4: 导入进度
   └─ 实时显示:
      ├─ 上传/处理进度条
      ├─ 整体进度统计
      ├─ 成功日期列表
      └─ 失败日期列表

Step 5: 完成
   └─ 显示导入统计:
      ├─ 总日期数
      ├─ 成功/失败日期数
      ├─ 总记录数
      └─ 耗时
```

**文件大小策略**:
- 小文件 (<10MB): 标准同步处理，快速完成
- 中型文件 (10-50MB): 异步处理，实时显示进度
- 大文件 (50-100MB): 直接上传 + 流式处理，内存优化
- 超大文件 (>100MB): 分块上传 + 流式处理，确保稳定性

### 1.4 API客户端: admin-auth.ts

**位置**: `/Users/peakom/work/stock-analysis-system/shared/admin-auth.ts`

**超时设置**:
```typescript
const apiClient = axios.create({
  baseURL: config.apiBaseUrl,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000 // 默认30秒超时
});

// 导入API中单独设置超时
timeout: 120000 // 2分钟，用于大文件导入
```

**重试机制**:
```typescript
withRetry(request, {
  maxAttempts: config.maxRetryAttempts,
  delay: 1000,        // 初始延迟1秒
  backoff: 2          // 指数退避，每次翻倍
})
```

**Token管理**:
```typescript
// 请求拦截器
├─ 检查token是否即将过期
├─ 自动刷新token (if config.autoRefresh)
└─ 添加Authorization header

// 响应拦截器
├─ 捕获401错误
├─ 尝试刷新token
├─ 重试原请求
└─ 失败则跳转到登录页
```

---

## 二、后端数据导入架构

### 2.1 API端点总览

**基础导入API** (`/api/v1/`):
```
POST /import-csv
├─ 参数: file (CSV), allow_overwrite (bool)
├─ 验证: 文件类型、大小 (≤100MB)
├─ 返回: {message, filename, imported_records, skipped_records, ...}
└─ 处理: DataImportService.import_csv_data()

POST /import-txt
├─ 参数: file (TXT), allow_overwrite (bool)
├─ 验证: 文件类型、大小 (≤50MB)
├─ 返回: {message, filename, imported_records, ...}
└─ 处理: DataImportService.import_txt_data()
```

**通用导入API** (`/api/v1/universal-import/`):
```
POST /import
├─ 参数: file, file_type (ttv/eee/...), trading_date, mode
├─ 验证: 支持的文件类型
├─ 动态: 根据file_type使用不同表和模型
└─ 处理: UniversalImportService.import_file()

POST /{fileType}/check-date
├─ 参数: trading_date
├─ 返回: {exists: bool, count: int}
└─ 用途: 检查日期是否已有数据

GET /{fileType}/records
├─ 参数: limit, offset, trading_date
├─ 返回: 导入记录列表
└─ 分页支持

POST /{fileType}/recalculate
├─ 参数: trading_date
├─ 返回: 重新计算结果
└─ 用途: 重新执行汇总计算
```

**历史数据API** (`/api/v1/historical-txt-import/`):
```
POST /preview
├─ 参数: file, preview_lines (默认2000)
├─ 返回: 文件预览信息
└─ 流程: 解析文件格式和日期分布

POST /import-sync
├─ 参数: file (≤10MB)
├─ 返回: 导入结果
└─ 特点: 同步阻塞，单次返回

POST /import-async
├─ 参数: file (10-100MB)
├─ 返回: {task_id, ...}
└─ 后续: 轮询GET /progress/{task_id}

GET /progress/{taskId}
├─ 返回: {status, current, total, current_date, ...}
├─ 轮询间隔: 2秒
└─ 超时: 无特定限制（长连接）
```

### 2.2 核心服务: DataImportService

**位置**: `/Users/peakom/work/stock-analysis-system/backend/app/services/data_import.py`

**主要方法**:

#### 2.2.1 import_csv_data() - CSV导入

```python
async def import_csv_data(
    self, 
    content: bytes, 
    filename: str, 
    allow_overwrite: bool = False, 
    trade_date: date = None
) -> Dict[str, Any]:
```

**流程**:
```
1. 日期解析
   └─ _extract_date_from_filename(filename)
      ├─ 支持: YYYY-MM-DD, YYYY_MM_DD, YYYYMMDD等
      └─ 回退: 今天的日期

2. 检查重复导入
   └─ check_existing_import(import_date, 'csv', filename)
      └─ 如果存在且不覆盖，返回已存在提示

3. CSV解析与列标准化
   └─ _normalize_csv_columns(df)
      ├─ 支持中文列名: 股票代码, 股票名称, 概念, 行业等
      ├─ 映射到: stock_code, stock_name, concept, industry
      └─ 设置默认date列

4. 两遍循环处理
   第一遍 - 收集信息:
   └─ 扫描所有行，提取:
      ├─ csv_stocks_info: {stock_code: {name, industry}}
      └─ csv_stock_concepts: {stock_code: [concepts]}
   
   第二遍 - 插入数据:
   ├─ 创建ImportBatch记录
   ├─ 处理每一行:
   │  ├─ 股票代码规范化: SH600000 → 600000
   │  ├─ 检测转债: 以1开头的6位代码
   │  ├─ 获取或创建Stock记录
   │  ├─ 获取或创建Concept记录
   │  ├─ 创建StockConcept关联
   │  ├─ 创建DailyStockData (仅一次)
   │  ├─ 保存RawImportData (每行)
   │  └─ 保存StockConceptRawData (双写)
   └─ 批量保存raw数据: bulk_save_objects()

5. 性能优化
   ├─ 跟踪processed_stock_dates: 避免DailyStockData重复插入
   ├─ 支持覆盖模式: 先删除旧数据
   │  └─ DELETE FROM daily_stock_data 
   │     WHERE trade_date = import_date AND stock_id IN (...)
   └─ 事务管理: db.commit()

6. 统计信息返回
   └─ stats:
      ├─ new_stocks: 新增股票数
      ├─ updated_stocks: 更新股票数
      ├─ new_concepts: 新增概念数
      ├─ new_relations: 新增关联数
      ├─ new_daily_data: 新增日数据
      ├─ updated_daily_data: 更新日数据
      └─ raw_import_records: 原始数据行数
```

**关键优化点**:
- 使用bulk_save_objects()进行批量插入
- 跟踪stock_date_key避免重复插入
- 两遍遍历：第一遍收集统计信息，第二遍插入数据
- 支持中文和英文列名自动转换
- 双写原始数据表用于审计

#### 2.2.2 import_txt_data() - TXT导入

```python
async def import_txt_data(
    self, 
    content: bytes, 
    filename: str, 
    allow_overwrite: bool = False, 
    trade_date: date = None
) -> Dict[str, Any]:
```

**特点**:
- 支持多日期文件，根据日期分组处理
- 完全覆盖模式：重新导入会覆盖同日期数据
- 用于数据纠正

**流程**:
```
1. 预解析文件 (第一遍)
   ├─ 扫描所有行，提取日期
   ├─ 检测多个日期: 使用最常见的日期
   └─ detected_dates: 文件中的所有日期集合

2. 确定目标日期
   └─ 优先级:
      ├─ 1. 参数trade_date
      ├─ 2. 文件内容检测到的单一日期
      ├─ 3. 最常见的日期
      └─ 4. 文件名解析的日期

3. 核心覆盖逻辑
   └─ 如果allow_overwrite或existing_record:
      ├─ 收集TXT中的股票代码
      ├─ DELETE FROM daily_stock_data
      │  WHERE trade_date = target_date AND stock_id IN (...)
      └─ 记录deleted_records数

4. 数据处理 (第二遍)
   └─ 逐行处理:
      ├─ 解析: 股票代码、日期、热度值
      ├─ 验证: 股票代码6位数字，热度值为浮点数
      ├─ 处理:
      │  ├─ 若股票不存在，创建基础Stock记录
      │  ├─ 创建DailyStockData (新记录)
      │  ├─ 保存RawImportData
      │  └─ 每100条打印进度
      └─ 错误处理: 记录错误行，继续处理

5. 批量保存
   └─ self.db.bulk_save_objects(raw_import_records)

6. 返回统计
   └─ stats:
      ├─ deleted_records: 删除的旧数据
      ├─ new_records: 新增记录数
      ├─ error_records: 错误记录数
      └─ raw_import_records: 原始数据行数
```

**覆盖特性**:
```python
# TXT导入支持重复导入和覆盖（用于数据纠正）
if allow_overwrite or existing_record:
    # 1. 删除该日期的所有相关数据
    deleted_count = self.db.query(DailyStockData).filter(
        DailyStockData.trade_date == target_date,
        DailyStockData.stock_id.in_(stock_ids)
    ).delete(synchronize_session=False)
    
    # 2. 插入新数据
    self.db.add_all(new_daily_data)
    
    # 3. 提交事务
    self.db.commit()
```

#### 2.2.3 批量导入: import_daily_batch()

```python
async def import_daily_batch(
    self, 
    csv_content: bytes, 
    csv_filename: str,
    txt_content: bytes, 
    txt_filename: str,
    trade_date: date = None, 
    allow_overwrite: bool = False,
    import_mode: str = "smart"
) -> Dict[str, Any]:
```

**智能模式逻辑**:
```
检查CSV导入状态:
├─ 不存在: 导入CSV + TXT
├─ 存在:
│  ├─ TXT也存在: 都存在，返回提示
│  └─ TXT不存在: 仅导入TXT
└─ 导入失败: 返回失败信息

成功时:
└─ 触发每日分析计算:
   ├─ RankingCalculatorService.trigger_full_analysis(trade_date)
   └─ 异常处理: 不影响导入结果
```

### 2.3 通用导入服务: UniversalImportService

**位置**: `/Users/peakom/work/stock-analysis-system/backend/app/services/universal_import_service.py`

**特点**:
- 支持动态文件类型 (TTV, EEE等)
- 动态表和模型生成
- 与原TXT导入业务逻辑一致

**动态表生成**:
```python
self.registry = FileTypeRegistry(self.engine, db)
self.config = self.registry.get_file_type_config(file_type)
self.models = self.registry.model_generator.generate_models_for_file_type(file_type)

# 获取动态模型
self.DailyTrading = self.models['daily_trading']
self.ConceptDailySummary = self.models['concept_summary']
self.StockConceptRanking = self.models['ranking']
self.ConceptHighRecord = self.models['high_record']
self.ImportRecord = self.models['import_record']
```

**批量插入优化**:
```python
batch_size = 1000  # 固定批次大小

for i in range(0, total_rows, batch_size):
    batch_data = aggregated_data[i:i + batch_size]
    batch_records = []
    
    for row in batch_data:
        # 构建记录
        batch_records.append(record)
    
    if batch_records:
        try:
            self.db.add_all(batch_records)
            self.db.commit()
            success_count += len(batch_records)
            logger.info(f"成功插入批次: {len(batch_records)} 条记录")
        except Exception as e:
            self.db.rollback()
            error_count += len(batch_records)
```

### 2.4 数据库连接池配置

**位置**: `/Users/peakom/work/stock-analysis-system/backend/app/core/database.py`

```python
engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,           # 连接前检查连接是否有效
    pool_size=settings.DATABASE_POOL_SIZE,              # 10
    max_overflow=settings.DATABASE_MAX_OVERFLOW,        # 20
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,        # 30秒
    pool_recycle=settings.DATABASE_POOL_RECYCLE,        # 3600秒
    echo=settings.DEBUG                                 # 调试模式打印SQL
)
```

**配置说明**:
- `pool_size=10`: 连接池保持10个连接
- `max_overflow=20`: 超过10个连接后，最多允许20个溢出连接
- `pool_timeout=30`: 获取连接时最多等待30秒
- `pool_recycle=3600`: 连接回收时间为1小时（防止数据库断开）
- `pool_pre_ping=True`: 每次获取连接时检查连接有效性

**配置来源**: `/Users/peakom/work/stock-analysis-system/backend/app/core/config.py`
```python
DATABASE_POOL_SIZE: int = 10
DATABASE_MAX_OVERFLOW: int = 20
DATABASE_POOL_TIMEOUT: int = 30
DATABASE_POOL_RECYCLE: int = 3600
```

### 2.5 关键数据模型

**导入记录模型**:
```python
class DataImportRecord(Base):
    __tablename__ = "data_import_records"
    
    id: int                                  # 主键
    import_date: date                        # 导入日期
    import_type: str (csv|txt|both)         # 导入类型
    file_name: str                           # 文件名
    imported_records: int                    # 导入记录数
    skipped_records: int                     # 跳过记录数
    import_status: str (success|partial|failed)  # 导入状态
    error_message: str                       # 错误信息
    created_at: datetime
    updated_at: datetime
    
    __table_args__ = (
        Index('idx_import_date', 'import_date'),
        Index('idx_import_type', 'import_type'),
        Index('idx_import_status', 'import_status'),
        Index('uk_date_type_file', 'import_date', 'import_type', 'file_name', unique=True)
    )
```

**其他模型**:
- `ImportBatch`: 导入批次记录
- `RawImportData`: 原始导入数据（行级）
- `StockConceptRawData`: 股票概念原始数据（双写）

---

## 三、性能优化分析

### 3.1 批量插入优化

#### CSV导入:
```python
# 方式1: bulk_save_objects() - 快速批量插入
self.db.bulk_save_objects(raw_import_records)
print(f"📥 批量保存原始导入数据: {len(raw_import_records)} 条记录")

# 方式2: 分次提交
if raw_data_records:
    self.db.bulk_save_objects(raw_data_records)
    self.db.commit()
```

#### TXT导入:
```python
# 类似CSV的批量保存
self.db.bulk_save_objects(raw_import_records)
self.db.commit()
```

#### 通用导入:
```python
# 固定批次大小分批插入
batch_size = 1000

for i in range(0, total_rows, batch_size):
    batch_records = []
    for row in batch_data[i:i+batch_size]:
        batch_records.append(create_record(row))
    
    self.db.add_all(batch_records)
    self.db.commit()
    logger.info(f"成功插入批次: {len(batch_records)} 条")
```

### 3.2 超时配置

**前端**:
```typescript
// 默认超时
timeout: 30000  // 30秒

// 大文件导入超时
timeout: 120000  // 2分钟（导入API中设置）
```

**后端**:
- 无明确的请求级别超时设置
- FastAPI的默认超时可能导致大文件导入超时
- 建议: 对大文件导入实现异步处理和长连接支持

### 3.3 异步处理

**前端支持**:
```typescript
// 同步导入 (<10MB)
await adminApiClient.post(
    '/api/v1/historical-txt-import/import-sync',
    formData
);

// 异步导入 (10-100MB)
const response = await adminApiClient.post(
    '/api/v1/historical-txt-import/import-async',
    formData
);
// 获取task_id，轮询进度

// 分块上传 (>100MB)
await adminApiClient.post(
    '/api/v1/large-file-upload/direct-large-upload',
    formData,
    {
        onUploadProgress: (progressEvent) => {
            setUploadProgress(progressEvent.loaded / progressEvent.total * 100);
        }
    }
);
```

**后端支持**:
```python
# import_sync: 同步处理，直接返回结果
async def import_sync(...):
    result = await import_service.import_csv_data(...)
    return result

# import_async: 异步处理，返回task_id，后续轮询
async def import_async(...):
    task_id = create_task_id()
    asyncio.create_task(background_import(task_id, content))
    return {"task_id": task_id}

# progress/{taskId}: 获取进度
async def get_progress(task_id):
    return task_progress[task_id]
```

### 3.4 内存优化

**流式处理**:
```python
# 预解析优化（TXT导入）
lines = text_content.strip().split('\n')
valid_lines = []
detected_dates = set()

for line_num, line in enumerate(lines, 1):
    # 只保留有效行
    if validate_line(line):
        valid_lines.append((line_num, line, parsed_date))
        detected_dates.add(parsed_date)

# 分批处理
batch_size = 1000
for i in range(0, len(valid_lines), batch_size):
    batch = valid_lines[i:i+batch_size]
    process_batch(batch)
```

---

## 四、错误处理与验证

### 4.1 前端验证

```typescript
// 1. 文件类型验证
if (!file.filename.endsWith('.csv')) {
    throw new Error("文件必须是CSV格式");
}

// 2. 文件大小验证
if (fileSizeMB > 500) {
    throw new Error("文件过大，超过最大限制 500MB");
}

// 3. 日期验证
const dateRegex1 = /^\d{4}-\d{2}-\d{2}$/;
const dateRegex2 = /^\d{8}$/;
if (!dateRegex1.test(dateStr) && !dateRegex2.test(dateStr)) {
    throw new Error("日期格式无效");
}

// 4. 股票代码验证 (TXT)
if (!stockCode.isdigit() || len(stockCode) != 6) {
    throw new Error("股票代码格式无效");
}
```

### 4.2 后端验证

**CSV导入验证**:
```python
# 文件大小检查
if file.size > 100 * 1024 * 1024:
    raise HTTPException(status_code=400, detail="文件大小不能超过100MB")

# CSV列验证
required_columns = ['stock_code', 'stock_name', 'concept']
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    raise Exception(f"CSV文件缺少必需的列: {', '.join(missing_columns)}")

# 数据类型验证
if pd.isna(row.get('stock_code')) or pd.isna(row.get('stock_name')):
    skipped_records += 1
    continue

# 股票代码规范化
stock_code = self._normalize_stock_code(stock_code_raw)
is_convertible_bond = (len(stock_code) == 6 and 
                       stock_code.startswith('1') and 
                       stock_code.isdigit())
```

**TXT导入验证**:
```python
# 格式验证
if len(parts) < 3:
    errors.append(f"第{line_num}行: 数据格式不正确")
    continue

# 热度值验证
try:
    heat_value = float(heat_value_str)
except ValueError:
    errors.append(f"第{line_num}行: 无法解析热度值 '{heat_value_str}'")
    continue

# 股票代码验证
if not stock_code.isdigit() or len(stock_code) != 6:
    errors.append(f"第{line_num}行: 股票代码格式无效")
    continue
```

### 4.3 错误日志与统计

```python
# 错误收集
errors = []
errors.append(f"第{index+1}行: {str(e)}")

# 错误限制 (只保存前5个)
error_messages = '\n'.join(errors[:5])

# 错误计数
stats = {
    'error_records': len(errors),
    'skipped_records': skipped_records,
    'imported_records': imported_records
}

# 导入状态
import_status = 'success' if not errors else 'partial'
```

---

## 五、关键文件总结

### 核心文件路径

```
前端:
├─ /Users/peakom/work/stock-analysis-system/frontend/src/components/
│  ├─ DataImportPage.tsx          (主导入页面)
│  └─ HistoricalDataImport.tsx    (历史数据导入)
└─ /Users/peakom/work/stock-analysis-system/shared/
   └─ admin-auth.ts               (API客户端)

后端:
├─ /Users/peakom/work/stock-analysis-system/backend/app/
│  ├─ services/
│  │  ├─ data_import.py           (CSV/TXT导入服务)
│  │  ├─ txt_import.py            (TXT导入服务)
│  │  └─ universal_import_service.py  (通用导入服务)
│  ├─ api/api_v1/endpoints/
│  │  ├─ data_import.py           (导入API端点)
│  │  ├─ universal_import.py      (通用导入API)
│  │  └─ txt_import.py            (TXT导入API)
│  ├─ models/
│  │  └─ data_import.py           (导入记录模型)
│  └─ core/
│     ├─ database.py              (数据库连接池)
│     └─ config.py                (配置文件)
```

---

## 六、系统架构总结

### 数据流向

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 React                            │
│                                                              │
│  DataImportPage                  HistoricalDataImport      │
│  ├─ CSV导入 ──┬───→ adminApiClient  ← 大文件优化处理      │
│  ├─ TXT导入 ──┤                                           │
│  ├─ TTV导入 ──┼─→ checkDateExists() → POST /check-date   │
│  └─ EEE导入 ──┘    executeFileImport() → POST /import    │
│                                                              │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP/REST
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                    后端 FastAPI                             │
│                                                              │
│  API端点:                                                  │
│  ├─ POST /api/v1/import-csv ────→ DataImportService       │
│  ├─ POST /api/v1/import-txt ────→ DataImportService       │
│  ├─ POST /api/v1/universal-import/import → UniversalImportService
│  ├─ POST /api/v1/universal-import/{type}/check-date      │
│  └─ GET /api/v1/historical-txt-import/progress/{id}      │
│                                                              │
└────────────────┬──────────────────────────────────────────┘
                 │ SQLAlchemy ORM
                 ↓
┌─────────────────────────────────────────────────────────────┐
│                    数据库 MySQL                             │
│                                                              │
│  表结构:                                                   │
│  ├─ stocks                 (股票基本信息)                  │
│  ├─ concepts              (概念信息)                       │
│  ├─ stock_concepts        (股票-概念关联)                 │
│  ├─ daily_stock_data      (每日交易数据)                  │
│  ├─ data_import_records   (导入记录)                      │
│  ├─ import_batches        (导入批次)                      │
│  ├─ raw_import_data       (原始导入数据)                  │
│  ├─ stock_concept_raw_data (原始概念关联数据)             │
│  ├─ ttv_daily_trading     (TTV文件动态表)                │
│  └─ eee_daily_trading     (EEE文件动态表)                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 导入流程对比

```
CSV导入流程:
File Select → Validate Size → Read Content → 
Normalize Columns → Two-Pass Process →
├─ Pass 1: Collect Stats
├─ Pass 2: Insert Data
│  ├─ Stock (Get or Create)
│  ├─ Concept (Get or Create)
│  ├─ StockConcept (Link)
│  ├─ DailyStockData (First Time Only)
│  ├─ RawImportData (Batch Insert)
│  └─ StockConceptRawData (Double Write)
└─ Commit & Return Stats

TXT导入流程:
File Select → Validate Size → Parse Content →
Detect Trading Dates → Determine Target Date →
Check & Delete Existing Data (if overwrite) →
Line-by-Line Processing →
├─ Validate Stock Code & Heat Value
├─ Get or Create Stock
├─ Create DailyStockData
└─ Save RawImportData (Batch)
Commit & Return Stats

历史数据导入流程 (Large File):
File Select → Validate Size →
├─ <50MB: Direct Upload
├─ 50-100MB: Optimized Upload
└─ >100MB: Chunked Upload
Preview & Confirm →
├─ <10MB: Sync Import
├─ 10-100MB: Async Import + Progress Poll
└─ >100MB: Chunked + Stream Processing
Real-time Progress → Completion Stats
```

---

## 七、性能建议

### 优化方向

1. **批量插入优化**:
   - 当前: bulk_save_objects() + single commit
   - 建议: 分批提交 (每1000条) 释放内存

2. **异步处理**:
   - 当前: 仅前端支持异步导入
   - 建议: 后端实现任务队列（Celery/RQ）处理大文件

3. **连接池**:
   - 当前: pool_size=10, max_overflow=20
   - 建议: 根据并发数调整，超大导入时增加到30-50

4. **数据库索引**:
   - 当前: 有基本索引
   - 建议: 在stock_id+trade_date上添加复合索引加快查询

5. **缓存机制**:
   - 建议: 缓存Stock和Concept对象，减少数据库查询

6. **超时处理**:
   - 建议: 后端对大文件导入设置更长超时（5-10分钟）

---

## 八、安全性分析

### 已实现

1. **文件验证**:
   - 文件类型检查 (.csv, .txt, .ttv, .eee)
   - 文件大小限制 (50-500MB)

2. **数据验证**:
   - 股票代码格式检查
   - 日期格式验证
   - 转债检测

3. **访问控制**:
   - JWT Token认证 (admin-auth)
   - Token自动刷新
   - 401错误自动重定向

4. **编码处理**:
   - UTF-8和GBK编码支持
   - 数据清理和规范化

### 建议增强

1. **文件安全**:
   - 添加病毒扫描
   - 实现文件内容哈希验证 (file_hash)

2. **速率限制**:
   - 实现按用户的导入速率限制
   - 防止恶意导入

3. **审计日志**:
   - 记录所有导入操作 (imported_by字段已预留)
   - 记录导入前后的数据变化

---

## 九、总结

此系统提供了完整的多格式数据导入解决方案：

**优势**:
- 支持多种文件格式 (CSV, TXT, TTV, EEE等动态扩展)
- 前端优化：大文件分块上传、异步处理、进度实时显示
- 后端优化：批量插入、两遍处理、事务管理
- 灵活的覆盖机制：支持数据纠正和更新
- 详细的错误处理和日志记录

**待优化**:
- 后端大文件异步处理可进一步完善
- 数据库连接池配置可根据负载调整
- 可添加更多的性能监控和告警
- 需要增强安全审计和日志追踪

