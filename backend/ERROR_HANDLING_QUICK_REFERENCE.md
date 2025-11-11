# Quick Reference - Error Handling Issues by Component

## Issue Quick Reference Table

| ID | Issue | File | Lines | Severity | Type | Workaround |
|----|-------|------|-------|----------|------|-----------|
| #1 | Date parsing silent failures | data_import.py | 480-490 | HIGH | Silent Skip | Add logging at line 487 |
| #2 | Stock code validation incomplete | data_import.py | 634-641 | HIGH | Bad Data | Add range validation |
| #3 | Heat value no bounds checking | data_import.py | 624-631 | MEDIUM | Data Corruption | Add min/max limits |
| #4 | UTF-8 encoding assumption | data_import.py | 468 | HIGH | Crash | Add GBK fallback |
| #5 | CSV column detection fragile | data_import.py | 820-821 | MEDIUM | Wrong Data | Require >=2 matching columns |
| #6 | Date falls back to today | data_import.py | 62-67 | HIGH | Wrong Date | Add warning/confirmation |
| #7 | Stock code prefix extraction | data_import.py | 203-207 | MEDIUM | Bad Data | Validate after normalization |
| #8 | Column count strictly 3 | universal_import.py | 91 | MEDIUM | Rejection | Change to minimum 3 |
| #9 | Date format config not validated | universal_import.py | 102-121 | MEDIUM | Silent Failure | Validate format string |
| #10 | Volume parsing no bounds | universal_import.py | 123-142 | MEDIUM | Data Corruption | Add validation |
| #11 | Stock code slicing no check | universal_import.py | 230 | HIGH | Bad Data | Add length validation |
| #12 | Date mismatch silent change | universal_import.py | 747-766 | CRITICAL | Data Loss | Add confirmation/error |
| #13 | Parse errors truncated | universal_import.py | 803-819 | MEDIUM | Debug Failure | Add pagination endpoint |
| #14 | File size double-check | data_import_api.py | 33-46 | LOW | Redundant | Keep only one check |
| #15 | No encoding fallback | data_import_api.py | 36-52 | HIGH | Crash | Add detection logic |
| #16 | Async/await inconsistent | data_import_api.py | 18-51 | LOW | Potential Bug | Add type hints |
| #17 | TTV/EEE config not validated | file_type_config.py | 161-191 | MEDIUM | Silent Failure | Add startup validation |
| #18 | Config defaults misleading | file_type_config.py | 155-157 | MEDIUM | Documentation | Update comments |

---

## Import Flow Error Points

### CSV Import Flow (data_import.py)
```
File Upload
    ↓
[File size check] ← Issue #14 (redundant)
    ↓
[UTF-8 decode] ← Issue #4 (no fallback encoding)
    ↓
[Pandas read_csv] ← Issue #15 (API layer)
    ↓
[Column normalization] ← Issue #5 (fragile detection)
    ↓
[Required columns check] ← Should come before normalization
    ↓
[Extract date from filename] ← Issue #6 (silent fallback)
    ↓
[For each row]:
    - Normalize stock code ← Issue #7 (prefix extraction)
    - Validate stock code ← Issue #2 (incomplete validation)
    - Parse date ← Issue #1 (silent failures)
    ↓
[Database insert]
```

### TXT Import Flow (data_import.py)
```
File Upload
    ↓
[UTF-8 decode] ← Issue #4 (CRITICAL - crashes on GBK)
    ↓
[Detect dates from file] ← Issue #1 (30% malformed = silent import)
    ↓
[Fallback to filename/today] ← Issue #6 (silent fallback)
    ↓
[For each line]:
    - Parse stock code ← Issue #2 (incomplete validation)
    - Parse date ← Issue #1 (returns None silently)
    - Parse heat value ← Issue #3 (no bounds check)
    ↓
[Database insert]
```

### Universal Import Flow (universal_import_service.py)
```
File Upload
    ↓
[Encoding: UTF-8 then GBK] ← Better than data_import.py
    ↓
[parse_file_content]:
    - Split by tab ← Issue #8 (must be exactly 3 parts)
    - Parse stock code ← Issue #11 (slicing without check)
    - Parse date ← Issue #9 (config format not validated)
    - Parse volume ← Issue #10 (no bounds check)
    ↓
[Check date consistency] ← Issue #12 (silently changes date)
    ↓
[Aggregate duplicate codes] ← Silent aggregation
    ↓
[Database insert]
    ↓
[Calculate rankings]
```

---

## Error Messages That Need Investigation

### In data_import.py

1. **"CSV文件缺少必需的列"** (Line 107)
   - Happens AFTER failed column normalization
   - May mask Issue #5

2. **"CSV解析失败"** (Line 451)
   - Generic catch-all, hides true error
   - Could be encoding, pandas error, or logic error

3. **"TXT解析失败"** (Line 770)
   - Generic catch-all for TXT
   - Could be Issue #4 (encoding) or others

4. **"股票代码格式无效"** (Line 639)
   - Comes too late - stock already normalized
   - Doesn't catch Issue #7

### In universal_import_service.py

1. **"格式不正确，应为3列"** (Line 94)
   - Triggered by Issue #8
   - True for files with >3 columns

2. **"日期格式错误"** (Line 117)
   - Triggered by Issue #9
   - Ambiguous if it's the data or the config

3. **"未解析到有效数据"** (Line 734)
   - Happens if ALL lines fail Issue #8
   - No indication why parsing failed

---

## Stock Code Validation Gaps

### Current Validation (data_import.py, Line 637)
```python
if not stock_code or not stock_code.isdigit() or len(stock_code) != 6:
    # Reject
```

**What it catches:**
- Empty codes
- Non-digit characters
- Wrong length

**What it MISSES:**
- "000000" (all zeros) ✓ Passes but invalid
- "999999" (doesn't exist) ✓ Passes but invalid
- "SH1" → normalized to "1" → fails (correct)
- "SHANGHAI123" → normalized to "NGHAI123" → fails (correct)

### Recommended Validation
```python
VALID_SHANGHAI = range(600000, 688888)
VALID_SHENZHEN = list(range(0, 200000)) + list(range(300000, 399999))
VALID_BEIJING = range(800000, 890000)

code_num = int(normalized_code)
if prefix == 'SH' and code_num not in VALID_SHANGHAI:
    raise ValueError(...)
elif prefix == 'SZ' and code_num not in VALID_SHENZHEN:
    raise ValueError(...)
elif prefix == 'BJ' and code_num not in VALID_BEIJING:
    raise ValueError(...)
```

---

## Date Parsing Ambiguities

### Current _parse_date_from_string() Behavior

| Input | Format Tried | Result | Risk |
|-------|--------------|--------|------|
| "2025-11-11" | %Y-%m-%d | 2025-11-11 ✓ | None |
| "11-02-2025" | %m-%d-%Y | 2025-11-02 ✓ | Could also be %d-%m-%Y = 2025-02-11 |
| "2025-11" | Not in list | None (skipped) | Month-only dates fail |
| "25-11-11" | Not in list | None (skipped) | 2-digit year fails |
| "2025/8/28" | Not in list | None (skipped) | No-padding fails |
| "01-02-03" | Multiple match? | First match | Ambiguous |

### Issues
1. **Format list order matters** - "01-02-03" matches %m/%d/%Y first
2. **No way to know which format succeeded** - Silent parsing
3. **Missing common formats** - "25-11-11" (YY-MM-DD) common in Asia
4. **No validation** - "2099-12-31" parsed as valid

---

## TTV/EEE Configuration Gaps

### FileTypeConfig.py Lines 162-185

```python
ttv_config = FileTypeConfig(
    file_type="ttv",
    display_name="TTV数据",
    description="TTV格式股票交易数据",
    file_extensions=[".txt", ".ttv"],
    table_prefix="ttv_",
    stock_code_column="股票代码",      # Wrong: TTV likely has English
    volume_column="成交量",            # Wrong: TTV likely has English
    date_format="%Y%m%d",             # Assumed, not specified
    use_default_concept_mapping=True,
    created_by="system"
)
```

**Missing Information:**
- What do TTV files actually look like?
- What columns do they have?
- What delimiters (tab, comma, space)?
- What date formats?
- Sample file for testing

**Recommendation:** Create `TTV_FORMAT.md` documenting:
```
# TTV File Format Specification

## Expected Format
- Delimiter: TAB character (\t)
- Columns: stock_code, trading_date, trading_volume
- Stock codes: SH600000 or 600000 format
- Dates: YYYYMMDD format (e.g., 20251111)
- No headers

## Example
SH600000	20251111	123456
000001	20251111	987654

## Validation Rules
- Stock code: 6 digits or SH/SZ/BJ prefix + 6 digits
- Date: Must be valid date in YYYYMMDD format
- Volume: Positive integer, max 1 trillion
```

---

## Recommended Test Cases

### Test Issue #1 (Date Parsing)
```python
test_cases = [
    ("2025-11-11", "Valid ISO date"),
    ("11/11/2025", "US format"),
    ("11-11-2025", "Ambiguous - could be MM-DD or DD-MM"),
    ("2025/11", "Month only - should fail but might pass"),
    ("20251111", "YYYYMMDD"),
    ("25-11-11", "YY-MM-DD - currently fails"),
    ("11-02-03", "Ultra-ambiguous"),
    ("2099-12-31", "Far future - currently passes"),
    ("1900-01-01", "Far past - currently passes"),
]
```

### Test Issue #2 (Stock Code)
```python
test_cases = [
    ("600000", "Valid Shanghai"),
    ("000001", "Valid Shenzhen"),
    ("SH600000", "With prefix"),
    ("SZ000001", "With prefix"),
    ("1", "Too short"),
    ("123", "Too short"),
    ("123456789", "Too long"),
    ("ABCDEF", "Non-numeric"),
    ("600abc", "Mixed"),
    ("000000", "All zeros - passes validation but invalid stock"),
    ("999999", "Doesn't exist - passes validation"),
    ("SH1", "Prefix + short code"),
]
```

### Test Issue #4 (Encoding)
```python
test_files = [
    ("utf-8.txt", "Valid UTF-8"),
    ("gbk.txt", "GBK encoded"),
    ("gb2312.txt", "GB2312 encoded"),
    ("big5.txt", "Big5 (Traditional Chinese) - should fail"),
    ("utf-16.txt", "UTF-16 - should fail"),
    ("mixed_encoding.txt", "Starts UTF-8 then GBK"),
]
```

---

## Metrics to Monitor

After fixes applied, track:

1. **Parse Error Rate**
   - Target: <1% of rows fail parsing
   - Current: Unknown (errors silenced)

2. **Date Mismatch Rate**
   - Target: 0 silent changes
   - Current: Unknown

3. **Stock Code Rejection Rate**
   - Target: Should remain <5%
   - Ensure fixes don't over-reject valid codes

4. **Import Success Rate**
   - Target: >99% for valid files
   - Current: Unknown

5. **Data Quality**
   - Random sample audit of imported data
   - Check for garbage values (negative volumes, impossible dates)

