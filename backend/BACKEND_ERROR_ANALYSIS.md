# Backend Error Handling and Validation Analysis - TXT, TTV, and EEE File Imports

## Executive Summary

The backend has three main import systems with varying levels of robustness:
1. **data_import.py** - Original CSV/TXT service (mature but hardcoded)
2. **universal_import_service.py** - Dynamic file type service (flexible but lacks validation)
3. **API endpoints** - Express handler layer (good error catching but inconsistent)

The analysis reveals **critical validation gaps**, **date parsing vulnerabilities**, and **encoding issues** that could cause silent failures or data corruption.

---

## 1. data_import.py - TXT Import Analysis

### Location
`/Users/peakom/work/stock-analysis-system/backend/app/services/data_import.py`

### 1.1 import_txt_data() Method (Lines 453-770)

#### Critical Issues

**Issue #1: Inflexible Date Parsing - Multiple Silent Failures**
```python
# Lines 480, 484-490: Date parsing with poor error handling
parts = line.split('\t') if '\t' in line else line.split()
if len(parts) >= 3:
    try:
        date_str = parts[1].strip()
        parsed_date = self._parse_date_from_string(date_str)
        if parsed_date:
            detected_dates.add(parsed_date)
```

**Failure Points:**
- Line 481: `split('\t')` may have trailing spaces causing `>=3` to pass but fields misaligned
- If date parsing returns `None`, line is silently skipped with no error logged
- Lines 499-504: Falls back to "most common date" if multiple detected - can miss outliers
- No validation that dates are reasonable (e.g., not from year 1900 or 2099)

**Risk:** File with 50% malformed dates could import without warning

---

**Issue #2: Stock Code Validation is Incomplete**
```python
# Lines 634-641
stock_code = self._normalize_stock_code(stock_code_with_prefix)

# Validation ONLY happens here:
if not stock_code or not stock_code.isdigit() or len(stock_code) != 6:
    skipped_records += 1
    errors.append(f"第{line_num}行: 股票代码格式无效 {stock_code_with_prefix} -> {stock_code}")
    stats['error_records'] += 1
    continue
```

**Problems:**
- `isdigit()` check happens AFTER normalization
- No check for valid prefixes before normalization
- Stock code "1" after normalization would pass `len()` check if prefix stripped wrongly
- No validation of actual Chinese stock code ranges (000001-899999, 600000-699999, etc.)

**Risk:** Malformed codes like "SH1" → "1" won't be caught

---

**Issue #3: Heat Value Parsing Has No Range Validation**
```python
# Lines 624-631
try:
    heat_value = float(heat_value_str)
except ValueError:
    skipped_records += 1
    errors.append(f"第{line_num}行: 无法解析热度值 '{heat_value_str}'")
    continue
```

**Problems:**
- No check for negative values
- No check for unrealistic values (e.g., heat_value > 1,000,000)
- Accepts scientific notation ("1e10") as valid
- Float precision issues not addressed (e.g., 0.1 + 0.2 != 0.3)

**Risk:** Garbage data like "-999999" or "NaN" parsed as float could corrupt data

---

**Issue #4: Encoding Assumption**
```python
# Line 468
text_content = content.decode('utf-8')
```

**Problems:**
- No fallback encoding (GBK, GB2312)
- No try-except for UnicodeDecodeError
- Will crash entire import if file uses different encoding

**Risk:** Non-UTF-8 files fail completely instead of graceful degradation

---

### 1.2 import_csv_data() Method (Lines 54-451)

#### Critical Issues

**Issue #5: CSV Column Normalization is Order-Dependent**
```python
# Lines 806-843: _normalize_csv_columns()
chinese_to_english = {
    '股票代码': 'stock_code',
    '股票名称': 'stock_name',
    # ... 7 more mappings
}

columns = df.columns.tolist()
is_chinese_format = any(col in chinese_to_english for col in columns)
```

**Problems:**
- Detection is fragile: if ONLY ONE Chinese column exists, entire CSV treated as Chinese
- Assumes all columns present, but code continues if missing
- Line 104-107: Missing column check happens AFTER normalization
  ```python
  required_columns = ['stock_code', 'stock_name', 'concept']
  missing_columns = [col for col in required_columns if col not in df.columns]
  if missing_columns:
      raise Exception(f"CSV文件缺少必需的列: ...")
  ```

**Risk:** CSV with Chinese headers but English data fails silently during normalization

---

**Issue #6: Date Handling Falls Back Without Warning**
```python
# Lines 62-67
if not trade_date:
    import_date = self._extract_date_from_filename(filename)
    if not import_date:
        import_date = date.today()  # SILENT FALLBACK!
else:
    import_date = trade_date
```

**Problems:**
- If filename has no date, defaults to TODAY without warning
- User assumes file dated 2025-01-15 but system uses 2025-11-11
- No log message or response indication of fallback

**Risk:** Historical data imported with wrong date, breaking analysis

---

**Issue #7: Stock Code Prefix Extraction Has Edge Cases**
```python
# Lines 203-207
stock_code_raw = str(row['stock_code']).strip()
stock_code = self._normalize_stock_code(stock_code_raw)
```

And in _normalize_stock_code (lines 869-888):
```python
if stock_code.startswith('SH'):
    return stock_code[2:]
elif stock_code.startswith('SZ'):
    return stock_code[2:]
```

**Problems:**
- "SHANGHAI123" would become "NGHAI123" (not "123")
- Whitespace not stripped before checking startswith()
- No validation that remaining code is numeric

**Risk:** Incorrectly formatted codes create wrong database entries

---

### 1.3 Date Parsing Helper (Lines 846-867)

```python
def _parse_date_from_string(self, date_str: str) -> date:
    formats = [
        '%Y-%m-%d',    # 2025-08-28
        '%Y/%m/%d',    # 2025/08/28
        '%Y%m%d',      # 20250828
        '%m/%d/%Y',    # 08/28/2025
        '%d/%m/%Y',    # 28/08/2025
        '%m-%d-%Y',    # 08-28-2025
        '%d-%m-%Y',    # 28-08-2025
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    return None
```

**Problems:**
- Ambiguous dates like "01-02-2025" could match multiple formats (Jan 2 or Feb 1)
- No logging of which format was attempted
- Returns None silently
- Only tries 7 specific formats - edge cases like "2025/8/28" (no padding) fail

**Risk:** Same string parses differently depending on format list order

---

---

## 2. universal_import_service.py - TTV & EEE Support Analysis

### Location
`/Users/peakom/work/stock-analysis-system/backend/app/services/universal_import_service.py`

### 2.1 parse_file_content() Method (Lines 69-170)

#### Critical Issues

**Issue #8: Strict Column Count Validation**
```python
# Lines 90-98
parts = line.split('\t')
if len(parts) != 3:  # STRICT EQUALITY CHECK
    self.last_parse_errors.append({
        'line_number': line_num,
        'reason': '格式不正确，应为3列：股票代码\t交易日期\t交易量',
        'content': line
    })
    continue
```

**Problems:**
- Requires EXACTLY 3 columns - rejects valid data with extra columns
- No support for space-delimited files
- Trailing tabs create empty 4th element, rejected silently
- No warning if entire file is rejected

**Risk:** TTV/EEE files with 4+ columns fail completely

**Suggested Fix:**
```python
if len(parts) < 3:  # Minimum 3 columns required
    self.last_parse_errors.append(...)
    continue

# Use only first 3 columns
stock_code = parts[0].strip()
date_str = parts[1].strip()
volume_str = parts[2].strip()
```

---

**Issue #9: Date Format Configuration Not Validated**
```python
# Lines 102-121
trading_date = None
preferred_formats = []
if getattr(self.config, 'date_format', None):
    preferred_formats.append(self.config.date_format)
preferred_formats.extend(['%Y-%m-%d', '%Y%m%d'])

for fmt in preferred_formats:
    try:
        trading_date = datetime.strptime(date_str.strip(), fmt).date()
        break
    except Exception:
        pass

if trading_date is None:
    self.last_parse_errors.append({...})
    continue
```

**Problems:**
- Config might specify invalid format string (e.g., "%Z" for timezone)
- No validation that date_format is actually used
- If config format fails, falls back silently to hardcoded formats
- No indication which format succeeded

**Risk:** TTV/EEE with custom date_format never imported if format incorrect

---

**Issue #10: Trading Volume Parsing Lacks Validation**
```python
# Lines 123-142
volume_str = volume_str.strip()
if not volume_str:
    self.last_parse_errors.append(...)
    continue
try:
    trading_volume = int(float(volume_str))
except Exception:
    self.last_parse_errors.append(...)
    continue
```

**Problems:**
- `int(float(...))` allows ".5" → 0, losing precision
- No check for negative volumes
- No check for extremely large values (> 1 billion)
- Scientific notation "1e6" converts to 1000000 silently
- Decimal input "123.456" truncates to 123 without warning

**Risk:** Volume data corrupted through conversion (e.g., 123.9 → 123)

---

**Issue #11: Stock Code Normalization Can Produce Invalid Codes**
```python
# Lines 145-154
try:
    stock_info = self._normalize_stock_code(stock_code)
except Exception as e:
    self.last_parse_errors.append(...)
    continue

# In _normalize_stock_code (lines 209-251):
if original.startswith('SH'):
    return {
        'original': original,
        'normalized': original[2:],  # Blind slicing!
        'prefix': 'SH'
    }
```

**Problems:**
- Slicing without length check: "SH1" → normalized to "1"
- No validation that normalized code is 6 digits
- No check for codes starting with invalid digits

**Risk:** "SH123" normalized to "123" (3 digits) passes through

---

### 2.2 import_file() Method (Lines 697-879)

#### Critical Issues

**Issue #12: Date Mismatch Detection Doesn't Prevent Data Loss**
```python
# Lines 737-766
trading_dates = list(set(item['trading_date'] for item in trading_data))
if len(trading_dates) > 1:
    raise ValueError("数据包含多个交易日期，请分别导入")

final_trading_date = trading_dates[0]

if trading_date != final_trading_date:
    logger.warning(f"用户指定日期 {trading_date} 与文件数据日期 {final_trading_date} 不一致...")
    trading_date = final_trading_date
    # Updates import_record with new date
```

**Problems:**
- If user uploads TTV for 2025-11-05 but file contains 2025-11-04 data, **silently switches**
- Old import records for 2025-11-05 are deleted (line 760-766)
- If upload fails, user sees 404 (record deleted but data not saved)
- No confirmation prompt to user

**Risk:** Data loss or date mismatch if file header incorrect

---

**Issue #13: Parse Errors Truncated Without Indication**
```python
# Lines 803-819
preview_limit = 50
errors_preview = []
for e in self.last_parse_errors[:preview_limit]:
    errors_preview.append({
        'line_number': e.get('line_number'),
        'reason': e.get('reason'),
        'content': (e.get('content') or '')[:200]
    })
notes_json = json.dumps({
    'file_internal_duplicates': import_result.get('file_internal_duplicates', 0),
    'parse_error_count': parse_error_count,
    'parse_errors': errors_preview,
    'parse_errors_truncated': parse_error_count > preview_limit  # Flag but no detail
}, ensure_ascii=False)
```

**Problems:**
- Only first 50 errors shown, rest hidden
- If file has 1000 parse errors, user sees "truncated=true" but can't debug
- Error content truncated to 200 chars (line with 500 char stock code cut off)
- No way to request full error list

**Risk:** Users can't debug malformed TTV files

---

### 2.3 Data Aggregation Issues (Lines 318-339)

```python
# Lines 318-339: Aggregating duplicate stock codes
aggregated_map = {}
for row in trading_data:
    key = (row['stock_code'], trading_date)
    if key in aggregated_map:
        try:
            aggregated_map[key]['trading_volume'] += int(row['trading_volume'])
        except Exception:
            # Silently ignore aggregation errors!
            pass
    else:
        aggregated_map[key] = {
            'original_stock_code': row.get('original_stock_code'),
            'normalized_stock_code': row.get('normalized_stock_code'),
            'stock_code': row.get('stock_code'),
            'trading_date': trading_date,
            'trading_volume': int(row.get('trading_volume', 0)),
            'market_prefix': row.get('market_prefix')
        }
```

**Issues:**
- Line 323: Exception silently ignored when adding volumes
- If one row has non-numeric volume from earlier parsing error, aggregation fails silently
- Duplicates in file don't trigger warnings (just silently sums)
- No max aggregation limit

**Risk:** Duplicate rows summed without notification

---

---

## 3. API Endpoints (data_import.py) - Validation Layer

### Location
`/Users/peakom/work/stock-analysis-system/backend/app/api/api_v1/endpoints/data_import.py`

### Issues Found

**Issue #14: File Size Validation Has Double-Check Problem**
```python
# Lines 33-34, 44-46 (import_csv_data)
if file.size and file.size > 100 * 1024 * 1024:
    raise HTTPException(status_code=400, detail="文件大小不能超过100MB")

# Then after reading:
if len(content) > 100 * 1024 * 1024:
    raise HTTPException(status_code=400, detail="文件内容超过100MB限制")
```

**Problems:**
- First check uses `file.size` (may be None or wrong)
- Second check is redundant but necessary (file.size unreliable)
- No check for empty files between upload and processing
- Different error messages for same condition

**Risk:** Confusing error messages, inconsistent behavior

---

**Issue #15: No Encoding Fallback in API Layer**
```python
# Lines 36-52 (import_csv_data)
try:
    content = await file.read()
    
    # Uses pandas default encoding
    df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
except HTTPException:
    raise
except Exception as e:
    print(f"❌ CSV导入异常: {str(e)}")
    error_detail = str(e)
    if "CSV解析失败" in error_detail:
        raise HTTPException(status_code=400, detail=error_detail)
    else:
        raise HTTPException(status_code=500, detail=f"导入失败: {error_detail}")
```

**Problems:**
- No encoding detection or fallback
- UnicodeDecodeError becomes 500 error instead of 400
- Pandas errors not specifically handled

**Risk:** User can't import CSV with GBK encoding

---

**Issue #16: Async/Await Pattern Inconsistency**
```python
# import_csv_data is async but calls sync DataImportService:
async def import_csv_data(...):
    import_service = DataImportService(db)
    result = await import_service.import_csv_data(...)  # Proper await
    
# But in import_daily_batch:
async def import_daily_batch(...):
    import_service = DataImportService(db)
    result = await import_service.import_daily_batch(...)  # Both methods are async
```

**Problems:**
- import_csv_data is marked async (returns coroutine)
- If called without await, returns coroutine object, not result
- No type hints to catch this

**Risk:** Subtle bugs if method signature changes

---

---

## 4. File Type Configuration - TTV and EEE Support

### Location
`/Users/peakom/work/stock-analysis-system/backend/app/services/schema/file_type_config.py`

### Issues Found

**Issue #17: TTV/EEE Configuration Not Validated at Startup**
```python
# Lines 161-191: TTV and EEE configs defined
ttv_config = FileTypeConfig(
    file_type="ttv",
    display_name="TTV数据",
    description="TTV格式股票交易数据",
    file_extensions=[".txt", ".ttv"],
    table_prefix="ttv_",
    # ... other fields
)

eee_config = FileTypeConfig(
    file_type="eee",
    display_name="EEE数据",
    # ... other fields
)
```

**Problems:**
- No validation that required columns exist
- date_format field not specified (defaults to "%Y%m%d")
- volume_column still set to "成交量" (Chinese) - might not match TTV/EEE actual format
- No test data included to verify format
- Concept mapping file path hardcoded for txt only

**Risk:** TTV files with English headers fail during import

---

**Issue #18: Configuration Defaults Don't Match File Formats**
```python
# Line 155-157 (txt config)
stock_code_column="股票代码",  # Chinese!
volume_column="成交量",        # Chinese!
concept_mapping_file="/Users/peakom/Desktop/..."
```

But TXT files likely have English columns or tab-delimited without headers.

**Risk:** Configuration misleading for actual file formats

---

---

## 5. Critical Validation Gaps

### Summary Table of Missing Validations

| Issue | Component | Severity | Impact |
|-------|-----------|----------|--------|
| No encoding fallback | data_import.py, universal_import.py | HIGH | Files with GBK/GB2312 fail completely |
| Stock code only validates length, not ranges | data_import.py, universal_import.py | HIGH | Invalid codes silently accepted (e.g., "1") |
| Date parsing returns None silently | data_import.py | HIGH | Invalid dates skip lines without indication |
| Volume validation has no range checks | universal_import.py | MEDIUM | Negative/extreme values corrupted data |
| Config date_format not validated | universal_import.py | MEDIUM | Invalid format strings cause silent failures |
| Parse errors truncated at 50 lines | universal_import.py | MEDIUM | Debugging impossible for large files |
| Column count strictly equals 3 | universal_import.py | MEDIUM | TTV/EEE with extra columns rejected |
| Date mismatch changes date silently | universal_import.py | CRITICAL | Data loss if file header wrong |
| No max limits on aggregation | universal_import.py | LOW | Memory issues with duplicate rows |

---

## 6. Suggested Fixes

### Fix #1: Add Encoding Fallback
```python
# In data_import.py, line 468
try:
    text_content = content.decode('utf-8')
except UnicodeDecodeError:
    try:
        text_content = content.decode('gbk')
        logger.warning(f"File {filename} decoded as GBK, not UTF-8")
    except UnicodeDecodeError:
        try:
            text_content = content.decode('gb2312')
            logger.warning(f"File {filename} decoded as GB2312")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File encoding not supported (UTF-8, GBK, GB2312 required)")
```

### Fix #2: Validate Stock Code Ranges
```python
# In universal_import_service.py, after normalization
VALID_PREFIXES = ['SH', 'SZ', 'BJ', 'HK']
VALID_RANGES = {
    'SH': range(600000, 688888),      # Shanghai A-shares
    'SZ': list(range(0, 200000)) + list(range(300000, 399999)),  # Shenzhen A-shares
    'BJ': range(800000, 890000),      # Beijing exchange
}

normalized_code = self._normalize_stock_code(stock_code)
if not normalized_code.isdigit() or len(normalized_code) != 6:
    raise ValueError(f"Invalid stock code format: {stock_code} -> {normalized_code}")

stock_num = int(normalized_code)
prefix = stock_info['prefix'] or 'SZ'  # Default to SZ if no prefix
if prefix in VALID_RANGES:
    if stock_num not in VALID_RANGES[prefix]:
        logger.warning(f"Stock code {normalized_code} outside expected range for {prefix}")
```

### Fix #3: Date Parsing with Logging
```python
def _parse_date_from_string(self, date_str: str) -> date:
    formats = [
        '%Y-%m-%d', '%Y/%m/%d', '%Y%m%d',
        '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%d-%m-%Y',
        '%Y-%m', '%Y/%m'  # Add month-only parsing
    ]
    
    original_str = date_str
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str.strip(), fmt).date()
            # Validate not too old or too new
            if 1990 <= parsed.year <= 2099:
                logger.debug(f"Parsed '{original_str}' as {parsed} using format '{fmt}'")
                return parsed
        except ValueError:
            continue
    
    logger.warning(f"Could not parse date string: {original_str}")
    return None
```

### Fix #4: Volume Range Validation
```python
# In universal_import_service.py, line 134
try:
    trading_volume = float(volume_str)
    if trading_volume < 0:
        raise ValueError("Volume cannot be negative")
    if trading_volume > 1_000_000_000_000:  # 1 trillion
        logger.warning(f"Suspiciously large volume: {trading_volume}")
    if '.' in volume_str:  # Preserve original for logging
        logger.warning(f"Volume '{volume_str}' contains decimals, truncating to {int(trading_volume)}")
    trading_volume = int(trading_volume)
except (ValueError, TypeError) as e:
    raise ValueError(f"Invalid volume format: {volume_str} ({str(e)})")
```

### Fix #5: Date Mismatch Confirmation
```python
# In universal_import_service.py, line 747
if trading_date != final_trading_date:
    logger.error(f"DATE MISMATCH: User specified {trading_date} but file contains {final_trading_date}")
    # Don't silently change - require explicit confirmation
    raise ValueError(
        f"File date mismatch: specified {trading_date} but file contains {final_trading_date}. "
        f"Please correct filename or specify correct date."
    )
```

### Fix #6: Parse Error Full Details
```python
# In universal_import_service.py, line 803-819
# Instead of truncating, provide endpoint to retrieve full errors
notes_json = json.dumps({
    'file_internal_duplicates': import_result.get('file_internal_duplicates', 0),
    'parse_error_count': parse_error_count,
    'parse_errors_stored': True,  # Flag that full errors are available
    'parse_errors_preview': errors_preview[:10],  # Only first 10
}, ensure_ascii=False)

# And add API endpoint:
@router.get("/import/{import_record_id}/errors")
def get_full_parse_errors(import_record_id: int):
    """Retrieve all parse errors for an import record"""
    # Return all stored errors, paginated
```

---

## 7. Recommendations

### Immediate (Critical)

1. **Add encoding detection with fallback**
   - Detect file encoding before parsing
   - Support UTF-8, GBK, GB2312
   - Return clear error if encoding unsupported

2. **Implement date mismatch prevention**
   - Reject imports where file date != specified date
   - Require explicit user confirmation to override
   - Log all date changes to audit trail

3. **Add stock code validation**
   - Check code is 6 digits
   - Validate against known ranges
   - Log warnings for suspicious codes

### Short-term (High Priority)

4. **Standardize error reporting**
   - Full error messages in response
   - Paginated error details endpoint
   - Consistent status codes (400 vs 500)

5. **Document file format expectations**
   - Update FileTypeConfig with actual TTV/EEE format specs
   - Provide sample files
   - Add format validation tests

6. **Fix volume parsing**
   - Validate ranges
   - Handle decimals consistently
   - Log any conversions

### Long-term (Maintenance)

7. **Add integration tests**
   - Test each format with real sample files
   - Test encoding edge cases
   - Test date parsing ambiguities

8. **Implement input validation framework**
   - Create reusable validators
   - Apply consistently across all imports
   - Make extensible for new formats

---

## 8. Files Requiring Changes

**High Priority:**
- `/Users/peakom/work/stock-analysis-system/backend/app/services/universal_import_service.py` (parse_file_content, import_file)
- `/Users/peakom/work/stock-analysis-system/backend/app/services/data_import.py` (import_txt_data, _parse_date_from_string)

**Medium Priority:**
- `/Users/peakom/work/stock-analysis-system/backend/app/api/api_v1/endpoints/universal_import.py` (encoding handling)
- `/Users/peakom/work/stock-analysis-system/backend/app/services/schema/file_type_config.py` (validation)

**Documentation:**
- Create FORMAT_SPECIFICATIONS.md describing TXT, TTV, EEE formats
- Create ERROR_HANDLING.md describing error codes and meanings

