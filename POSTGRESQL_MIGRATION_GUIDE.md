# PostgreSQL Migration Guide

## Pre-Migration Checklist

- [ ] PostgreSQL 14+ installed (or cloud instance created)
- [ ] psycopg2-binary installed: `pip install psycopg2-binary`
- [ ] Staging environment ready
- [ ] Backup of current MySQL database taken
- [ ] Team familiar with PostgreSQL basics
- [ ] Performance testing environment prepared

## Step 1: Database Setup

### 1.1 Create PostgreSQL Database

```sql
-- Connect to PostgreSQL as superuser
CREATE DATABASE stock_analysis_dev WITH 
  ENCODING = 'UTF8' 
  LC_COLLATE = 'en_US.UTF-8' 
  LC_CTYPE = 'en_US.UTF-8';

-- Optional: Create role
CREATE ROLE stock_user WITH LOGIN PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE stock_analysis_dev TO stock_user;
```

### 1.2 Update Dependencies

```bash
# Remove MySQL drivers
pip uninstall pymysql mysql-connector-python -y

# Install PostgreSQL driver
pip install psycopg2-binary==2.9.9

# Update requirements.txt
cat > requirements.txt << 'REQS'
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
pandas==2.0.3
numpy==1.24.4
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
argon2-cffi==23.1.0
bcrypt>=4.0.0
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.0.3
email-validator==2.1.0
python-dotenv==1.0.0
httpx==0.25.2
requests==2.31.0
python-dateutil==2.8.2
pytz==2023.3
redis==6.1.1
pycryptodome==3.23.0
REQS
pip install -r requirements.txt
```

## Step 2: Update Configuration

### 2.1 Database URL in `.env`

```bash
# Before (MySQL)
DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/stock_analysis_dev

# After (PostgreSQL)
DATABASE_URL=postgresql+psycopg2://stock_user:password@127.0.0.1:5432/stock_analysis_dev
```

### 2.2 Update `backend/app/core/config.py`

```python
# Change default port
DATABASE_PORT: int = int(os.getenv("DATABASE_PORT", "5432"))  # Was 3306

# Update DATABASE_URL property
@property
def DATABASE_URL(self) -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # Use PostgreSQL instead of MySQL
    return f"postgresql+psycopg2://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
```

## Step 3: Schema Migration

### 3.1 Migrate Existing Alembic Migrations

```bash
cd backend

# Initialize/upgrade database schema
alembic upgrade head
```

**Note:** Most migrations will work automatically. Check for any MySQL-specific syntax:

- `CURRENT_TIMESTAMP` → Works in PostgreSQL ✓
- `DATETIME` → `TIMESTAMP` (SQLAlchemy handles conversion) ✓
- Window functions → Same syntax ✓

### 3.2 Manual Fixes (if needed)

Some ENUM columns may need adjustment if they were created with MySQL ENUM type:

```python
# In models, ENUM columns should be:
from sqlalchemy import String  # NOT Enum

# Good (portable)
status = Column(String(20), default='pending')

# Avoid (MySQL specific)
status = Column(Enum('pending', 'paid', 'failed'))
```

## Step 4: Code Updates

### 4.1 Update `bulk_insert_optimizer.py`

**Original MySQL version:**
```python
def bulk_insert_daily_trading(self, trading_data: List[Dict]) -> int:
    if not trading_data:
        return 0

    total_inserted = 0
    
    with self.optimized_session():
        for i in range(0, len(trading_data), self.batch_size):
            batch = trading_data[i:i + self.batch_size]
            values = []
            for item in batch:
                values.append(f"('{item['code']}', '{item['date']}', ...)")
            
            sql = f"INSERT INTO daily_trading VALUES {','.join(values)}"
            self.db.execute(text(sql))
            total_inserted += len(batch)
    
    return total_inserted
```

**New PostgreSQL version:**
```python
from io import StringIO
import csv

def bulk_insert_daily_trading(self, trading_data: List[Dict]) -> int:
    if not trading_data:
        return 0

    try:
        # Use PostgreSQL COPY command for 10-100x speed improvement
        buffer = StringIO()
        writer = csv.DictWriter(
            buffer, 
            fieldnames=['original_stock_code', 'normalized_stock_code', 
                       'stock_code', 'trading_date', 'trading_volume']
        )
        
        for item in trading_data:
            writer.writerow({
                'original_stock_code': item['original_stock_code'],
                'normalized_stock_code': item['normalized_stock_code'],
                'stock_code': item['stock_code'],
                'trading_date': item['trading_date'],
                'trading_volume': item['trading_volume']
            })
        
        buffer.seek(0)
        
        # Get raw connection and execute COPY
        from psycopg2 import sql
        conn = self.db.raw_connection()
        cursor = conn.cursor()
        cursor.copy_from(
            buffer,
            'daily_trading',
            columns=['original_stock_code', 'normalized_stock_code', 
                    'stock_code', 'trading_date', 'trading_volume'],
            sep=','
        )
        conn.commit()
        cursor.close()
        
        logger.info(f"Bulk inserted {len(trading_data)} records via COPY")
        return len(trading_data)
        
    except Exception as e:
        logger.error(f"Bulk insert failed: {e}")
        raise
```

### 4.2 Remove MySQL-Specific Optimizations

```python
# DELETE this entire context manager - PostgreSQL doesn't need it
@contextmanager
def optimized_session(self):
    """MySQL-specific optimizations - no longer needed"""
    try:
        # These MySQL-specific commands should be removed:
        # self.db.execute(text("SET unique_checks = 0"))
        # self.db.execute(text("SET foreign_key_checks = 0"))
        # self.db.execute(text("SET sql_log_bin = 0"))
        
        yield self.db
        self.db.commit()
    except Exception as e:
        self.db.rollback()
        raise
    finally:
        # PostgreSQL automatic optimization - nothing needed
        pass
```

### 4.3 Update Window Function Queries

PostgreSQL window functions use same syntax as MySQL 8.0+:

```python
# This stays the same - both databases support it
ranking_sql = text("""
    INSERT INTO daily_stock_concept_financial_rankings 
    SELECT 
        :analysis_date,
        concept,
        stock_code,
        stock_name,
        ROW_NUMBER() OVER (PARTITION BY concept ORDER BY net_inflow DESC) as net_inflow_rank,
        ROW_NUMBER() OVER (PARTITION BY concept ORDER BY price DESC) as price_rank,
        ...
    FROM stock_concept_data
    WHERE analysis_date = :analysis_date
""")
```

## Step 5: Performance Optimization

### 5.1 Create Optimized Indexes

```sql
-- Partial index for recent data (faster scans)
CREATE INDEX idx_recent_stock_data ON daily_stock_data 
WHERE trade_date > CURRENT_DATE - INTERVAL '1 year';

-- JSONB indexes for payment notifications
CREATE INDEX idx_payment_notifications_result ON payment_notifications 
USING GIN (notify_data);

-- Compound indexes (PostgreSQL can use partial)
CREATE INDEX idx_analysis_date_concept ON daily_concept_financial_summaries 
(analysis_date, concept) 
WHERE analysis_date > CURRENT_DATE - INTERVAL '2 years';

-- Unique constraints with partial index
CREATE UNIQUE INDEX idx_payment_orders_active ON payment_orders 
(out_trade_no) 
WHERE status != 'cancelled';
```

### 5.2 Analyze Query Plans

```python
# From API endpoint or service
from sqlalchemy import text

query = """
EXPLAIN ANALYZE
SELECT * FROM daily_stock_concept_financial_rankings 
WHERE analysis_date = CURRENT_DATE 
ORDER BY net_inflow_rank
LIMIT 20;
"""

result = self.db.execute(text(query))
for row in result:
    print(row[0])
```

### 5.3 Connection Pool Tuning

```python
# In backend/app/core/database.py
engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
    pool_size=15,           # Increased from 10
    max_overflow=25,        # Increased from 20
    pool_timeout=30,
    pool_recycle=3600,
    echo=settings.DEBUG,
    # PostgreSQL specific optimizations
    connect_args={
        "connect_timeout": 10,
        "application_name": "stock_analysis_app"
    }
)
```

## Step 6: Testing & Validation

### 6.1 Data Integrity Tests

```bash
# Run test suite
pytest backend/tests/ -v

# Key tests to verify:
# - Window function ranking generation
# - Bulk insert performance
# - JSON payload handling
# - Date-based filtering
# - Concurrent access patterns
```

### 6.2 Performance Benchmarks

```python
import time

# Compare ranking generation time
start = time.time()
# Run daily ranking analysis
end = time.time()
print(f"Ranking generation: {end-start:.2f}s")  # Should be 1-2s vs 3-5s

# Compare bulk inserts
start = time.time()
# Import 5000 records
end = time.time()
print(f"Bulk insert: {end-start:.2f}s")  # Should be <5s vs 20-30s
```

### 6.3 Data Verification

```sql
-- Verify row counts match
SELECT COUNT(*) FROM stocks;
SELECT COUNT(*) FROM daily_stock_data;
SELECT COUNT(*) FROM payment_orders;
SELECT COUNT(*) FROM membership_logs;

-- Verify constraints
SELECT constraint_name FROM information_schema.table_constraints 
WHERE table_name = 'payment_orders';

-- Verify indexes
SELECT schemaname, tablename, indexname FROM pg_indexes 
WHERE tablename = 'daily_stock_concept_financial_rankings';
```

## Step 7: Deployment

### 7.1 Blue-Green Deployment Strategy

1. **Blue Phase:** Run MySQL in production
2. **Green Phase:** Run PostgreSQL on staging with real traffic
3. **Monitor:** Compare performance metrics for 1-2 weeks
4. **Switch:** DNS/load balancer points to PostgreSQL
5. **Rollback:** Keep MySQL ready for quick rollback (24-48 hours)

### 7.2 Monitoring After Migration

```python
# Add to logging/monitoring
import logging

logger = logging.getLogger(__name__)

# Log slow queries
logging.basicConfig(level=logging.WARNING)

# Monitor in production
# - Query execution time
# - Connection pool usage
# - Memory consumption
# - Ranking generation time
```

### 7.3 Rollback Plan

If issues occur:
1. Stop writing to PostgreSQL
2. Switch application back to MySQL
3. Verify all queries run successfully
4. Investigate PostgreSQL issue offline
5. Retry migration after fixes

## Post-Migration Cleanup

### 8.1 Decommission MySQL

Once PostgreSQL is stable for 2-4 weeks:

```bash
# Backup final MySQL state
mysqldump -u root -p stock_analysis_dev > backup_final.sql

# Archive backups
# Keep for 3-6 months minimum

# Stop MySQL service
sudo systemctl stop mysql
sudo systemctl disable mysql
```

### 8.2 Optimize for PostgreSQL

```sql
-- Vacuum and analyze after migration
VACUUM FULL ANALYZE;

-- Update table statistics
ANALYZE stock_concept_data;
ANALYZE daily_stock_concept_financial_rankings;

-- Run EXPLAIN on critical queries for planning
```

### 8.3 Document Performance Improvements

Create performance report showing:
- Query execution time improvements
- Bulk import speed improvements
- Concurrent connection handling
- Resource utilization changes
- Cost/benefits analysis

## Troubleshooting

### Issue: Connection timeout
```python
# Increase timeout in connect_args
connect_args={"connect_timeout": 30}
```

### Issue: Slow COPY command
```python
# Check disk I/O and verify database isn't on slow storage
# Consider using UNLOGGED tables for staging
```

### Issue: Memory usage higher
```sql
-- Reduce work_mem if needed
ALTER SYSTEM SET work_mem = '256MB';
SELECT pg_reload_conf();
```

### Issue: Missing sequences
```sql
-- PostgreSQL uses sequences instead of AUTO_INCREMENT
-- Alembic should handle this automatically
-- Verify with: SELECT * FROM information_schema.sequences;
```

---

**Estimated Total Time:** 3-5 days (including testing and validation)
**Estimated Downtime:** 30-60 minutes (for cutover)
**Risk Level:** LOW (80% of code is portable)
