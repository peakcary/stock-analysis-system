# Frontend Raw Data Table Viewer - Planning & Architecture Summary

## Executive Summary
This document provides a comprehensive analysis of the frontend architecture and recommendations for building a new raw data table viewer page.

---

## 1. FRONTEND STRUCTURE & ORGANIZATION

### Project Setup
- **Framework**: React 18.2.0 with TypeScript
- **Build Tool**: Vite 7.1.2
- **UI Framework**: Ant Design (antd) 5.27.1
- **HTTP Client**: Axios 1.11.0
- **Routing**: React Router DOM 6.8.1
- **Dev Server Port**: 8006

### Directory Structure
```
frontend/
├── src/
│   ├── main.tsx                 # Entry point
│   ├── App.tsx                  # Main app with routing & state
│   ├── api/
│   │   └── endpoints.ts        # Centralized API endpoint constants
│   ├── components/              # Page components
│   │   ├── AdminLayout.tsx      # Main layout wrapper
│   │   ├── Dashboard.tsx
│   │   ├── StockListPage.tsx    # Example data display page
│   │   ├── ConceptAnalysisPage.tsx
│   │   ├── DataImportPage.tsx
│   │   ├── UserManagement.tsx
│   │   ├── AdminManagement.tsx
│   │   ├── PackageManagement.tsx
│   │   ├── PaymentPage.tsx
│   │   └── [other analysis pages]
│   ├── contexts/
│   │   └── AuthContext.tsx      # Auth state management
│   └── assets/
├── index.html
├── vite.config.ts
└── package.json
```

---

## 2. PAGES & ROUTING STRUCTURE

### Current Pages (Tab-Based Routing)
All pages are managed through `App.tsx` using an `activeTab` state rather than traditional routing:

```typescript
// Main menu items (from AdminLayout.tsx)
const menuItems = [
  { key: 'dashboard', icon: <DashboardOutlined />, label: '控制台' },
  { key: 'simple-import', icon: <CloudUploadOutlined />, label: '数据导入' },
  { key: 'concepts', icon: <ApiOutlined />, label: '概念分析' },
  { key: 'stock-analysis', icon: <SearchOutlined />, label: '个股分析' },
  { key: 'innovation-analysis', icon: <FireOutlined />, label: '创新高分析' },
  { key: 'convertible-bonds', icon: <DatabaseOutlined />, label: '转债分析' },
  { key: 'client-users', icon: <TeamOutlined />, label: '客户端用户' },
  { key: 'admin-users', icon: <CrownOutlined />, label: '管理员账户' },
  { key: 'packages', icon: <GiftOutlined />, label: '套餐管理' },
];
```

### Navigation Flow
1. User logs in via `LoginPage`
2. Authenticated users see `AdminLayout` wrapper
3. `AdminLayout` renders navigation sidebar + active page content
4. Page selection via menu click → calls `onTabChange(key)` → updates `activeTab` state in `App.tsx`
5. App renders corresponding component based on `activeTab`

---

## 3. EXISTING DATA VIEW PAGES ANALYSIS

### Key Example: StockListPage.tsx
**Purpose**: Display stocks with trading volumes and concept information

**Data Flow**:
```
Component State → API Call → Ant Design Table → Optional Modal Detail View
```

**Key Pattern**:
```typescript
// 1. State management
const [stockSummaries, setStockSummaries] = useState<StockSummary[]>([]);
const [loading, setLoading] = useState(false);
const [tradingDate, setTradingDate] = useState<string>(dayjs().format('YYYY-MM-DD'));

// 2. Data fetching
const fetchStockSummaries = async () => {
  setLoading(true);
  try {
    const response = await adminApiClient.get(
      `/stock-analysis/stocks/daily-summary?trading_date=${tradingDate}&size=10000`
    );
    // Process and filter data
    setStockSummaries(summaries);
  } catch (error) {
    message.error('获取股票汇总失败');
  } finally {
    setLoading(false);
  }
};

// 3. Table rendering
<Table
  columns={summaryColumns}
  dataSource={stockSummaries}
  rowKey="stock_code"
  pagination={{ pageSize: 15, showSizeChanger: true, showQuickJumper: true }}
  scroll={{ x: 800 }}
  loading={loading}
/>
```

### Key Example: ConceptAnalysisPage.tsx
**Pattern**: Concept data with drill-down modal
- Main table: Concept summaries with totals
- Modal view: Stock list within concept with rankings
- Date selector: DatePicker for filtering by trading_date

### Key Example: UserManagement.tsx
**Pattern**: User list with pagination and filters
```typescript
// Pagination state
const [pagination, setPagination] = useState({
  current: 1,
  pageSize: 10,
  total: 0
});

// Fetch with pagination
const response = await adminApiClient.get('/admin/client-users/users', {
  params: {
    skip: (page - 1) * pageSize,
    limit: pageSize,
    search: searchText,
    membership_type: selectedMembership
  }
});
```

### Common Table Features Used
1. **Columns with custom rendering**: Tags, formatted numbers, color-coded values
2. **Pagination**: Both client-side and server-side (with skip/limit)
3. **Sorting**: Column sorter functions
4. **Search/Filter**: Input fields + API query parameters
5. **Date Picker**: For filtering by date
6. **Row Actions**: Detail modals, edit forms
7. **Empty State**: Empty component with helpful messages
8. **Loading State**: Spin component with loading message

---

## 4. API INTEGRATION PATTERN

### API Client Setup
**File**: `/Users/peakom/work/stock-analysis-system/shared/admin-auth.ts`

```typescript
// Singleton pattern
export const adminApiClient = adminAuthManager.getApiClient();

// Usage in components
import { adminApiClient } from '../../../shared/admin-auth';

// Making requests
const response = await adminApiClient.get('/stocks/simple?limit=10000');
const response = await adminApiClient.post('/data/import-csv', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});
```

### API Client Features
- **Automatic Authorization**: Bearer token automatically added to headers
- **Token Refresh**: Auto-refresh if token expiring
- **Error Handling**: 401 redirects to login, unified error handling
- **Interceptors**: Request & response middleware for auth logic
- **Timeout**: 30 seconds default (configurable per request)

### API Endpoints (from `endpoints.ts`)
```typescript
export const API_ENDPOINTS = {
  STOCKS: {
    LIST: '/stocks',
    COUNT: '/stocks/count',
    SIMPLE: '/stocks/simple',
    DETAIL: (stockCode: string) => `/stocks/${stockCode}`,
    DELETE: (stockId: number) => `/stocks/${stockId}`,
    BATCH_DELETE: '/stocks/batch',
  },
  CONCEPTS: {
    LIST: '/concepts',
    COUNT: '/concepts/count',
  },
  DATA_IMPORT: {
    STATUS: (date: string) => `/data/import-status/${date}`,
    IMPORT_CSV: '/data/import-csv',
    IMPORT_TXT: '/data/import-txt',
  },
  TXT_IMPORT: {
    CHECK_DATE: '/txt-import/check-date',
    IMPORT: '/txt-import/import',
  },
  DAILY_ANALYSIS: {
    LIST: '/daily-analysis',
  },
  CONCEPT_ANALYSIS: {
    LIST: '/concept-analysis',
  },
  // ... more endpoints
};
```

---

## 5. UI/COMPONENTS FRAMEWORK

### Ant Design Components Used
- **Table**: Primary data display component
- **Card**: Container for content sections
- **DatePicker**: Date filtering (dayjs integration)
- **Input**: Text search
- **Select**: Dropdown filtering
- **Button**: Actions (with loading states)
- **Modal**: Detail views, confirmations
- **Tag**: Status indicators, badges
- **Spin**: Loading indicator
- **Empty**: No data state
- **Message**: Toast notifications
- **Typography**: Text styling (Title, Text, etc.)
- **Space**: Component spacing
- **Row/Col**: Grid layout

### Styling Approach
- Inline styles for quick adjustments
- Ant Design theme colors (e.g., `#1890ff` blue)
- Custom CSS for specific needs (where needed)
- Responsive design via Ant Grid (xs, sm, md breakpoints)

### Table Customization Examples
```typescript
const columns = [
  {
    title: '股票代码',
    dataIndex: 'stock_code',
    key: 'stock_code',
    width: 100,
    render: (code: string) => (
      <Text strong style={{ color: '#1890ff' }}>{code}</Text>
    ),
  },
  {
    title: '交易量',
    dataIndex: 'trading_volume',
    key: 'trading_volume',
    width: 140,
    sorter: (a, b) => a.trading_volume - b.trading_volume,
    render: (volume: number) => (
      <Text strong style={{ color: '#52c41a' }}>
        {formatNumber(volume)}
      </Text>
    ),
  },
  {
    title: '操作',
    key: 'action',
    width: 120,
    render: (_: any, record: StockSummary) => (
      <Button type="primary" size="small" onClick={() => handleAction(record)}>
        查看详情
      </Button>
    ),
  },
];
```

---

## 6. AVAILABLE DATA SOURCES & TABLES

### Backend Data Models
From `/backend/app/models/daily_trading.py`:

**DailyTrading** - Raw daily trading data
- `id`, `original_stock_code`, `normalized_stock_code`, `stock_code`
- `trading_date`, `trading_volume`
- Indexes: `(stock_code, trading_date)`, `(trading_date, trading_volume)`

**ConceptDailySummary** - Daily concept summaries
- `concept_name`, `trading_date`
- `total_volume`, `stock_count`, `average_volume`, `max_volume`

**StockConceptRanking** - Stock ranking within concepts
- `stock_code`, `concept_name`, `trading_date`
- `trading_volume`, `concept_rank`, `volume_percentage`

**ConceptHighRecord** - Concept high records
- `concept_name`, `trading_date`, `total_volume`, `days_period`, `is_active`

**TxtImportRecord** - Import metadata
- `filename`, `trading_date`, `file_size`, `import_status`
- `total_records`, `success_records`, `error_records`, `concept_count`

**Stock** - Stock master data
- `id`, `stock_code`, `original_stock_code`, `stock_name`
- `industry`, `is_convertible_bond`

**DailyStockData** - Daily stock technical data
- `stock_id`, `trade_date`, `pages_count`, `total_reads`
- `price`, `turnover_rate`, `net_inflow`, `heat_value`

---

## 7. RECOMMENDED ARCHITECTURE FOR RAW DATA VIEWER

### Proposed Page Name
`RawDataViewerPage.tsx`

### Feature Set
1. **Dynamic Table Viewer**
   - Select data table/entity to view
   - Configurable columns (show/hide)
   - Dynamic filtering and sorting
   - Pagination with adjustable page size

2. **Data Source Selection**
   - Dropdown to select from available tables
   - Display table metadata (record count, sample columns)

3. **Filtering & Search**
   - Quick search across key columns
   - Advanced filters (date range, numeric ranges, string matching)
   - Column-specific filters

4. **Export/Download**
   - Export filtered data as CSV
   - Excel download with formatting

5. **Performance Features**
   - Server-side pagination (for large datasets)
   - Column sorting delegated to backend
   - Lazy loading for large result sets

### Proposed File Structure
```
frontend/src/components/
├── RawDataViewerPage.tsx          # Main page component
├── RawDataViewer/
│   ├── DataSourceSelector.tsx     # Table selection dropdown
│   ├── DataTable.tsx              # Generic table display
│   ├── FilterPanel.tsx            # Advanced filters
│   ├── ColumnSelector.tsx         # Show/hide columns
│   └── ExportButton.tsx           # Export functionality
└── [other existing components]
```

### Key Implementation Patterns
```typescript
// 1. Data source configuration
const DATA_SOURCES = {
  daily_trading: {
    label: '每日交易数据',
    api: '/raw-data/daily-trading',
    columns: ['stock_code', 'trading_date', 'trading_volume', ...],
    filters: ['date_range', 'stock_code', 'volume_range'],
  },
  concept_summary: {
    label: '概念每日汇总',
    api: '/raw-data/concepts',
    columns: ['concept_name', 'trading_date', 'total_volume', ...],
    filters: ['date_range', 'concept_name'],
  },
  // ... more sources
};

// 2. Generic fetch with filters
const fetchRawData = async (
  source: string,
  page: number,
  pageSize: number,
  filters: Record<string, any>
) => {
  const params = {
    skip: (page - 1) * pageSize,
    limit: pageSize,
    ...filters,
  };
  const response = await adminApiClient.get(
    `/raw-data/${source}`,
    { params }
  );
  return response.data;
};

// 3. Dynamic table columns
const columns = selectedSource.columns.map(columnKey => ({
  title: columnLabels[columnKey],
  dataIndex: columnKey,
  key: columnKey,
  sorter: true,
  render: renderValue(columnKey),
}));
```

---

## 8. AUTHENTICATION & AUTHORIZATION

### Auth Flow
1. **Login Page**: `LoginPage.tsx` → `adminAuthManager.login()`
2. **Context Provider**: `AuthContext.tsx` wraps entire app
3. **Protected Pages**: Check `useAuth().isAuthenticated`
4. **API Authentication**: Auto-added Bearer token in requests
5. **Token Management**: Auto-refresh before expiry
6. **Logout**: Clear tokens + redirect to login

### Using Auth in Components
```typescript
import { useAuth } from '../contexts/AuthContext';

const MyComponent: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuth();
  
  if (!isAuthenticated) {
    return <Redirect to="/login" />;
  }
  
  return (
    <div>
      Welcome {user?.username}
      <button onClick={logout}>Logout</button>
    </div>
  );
};
```

---

## 9. BEST PRACTICES OBSERVED

### Component Organization
✓ State management at page level (not fragmented)
✓ Async operations in useEffect hooks
✓ Loading states for all async operations
✓ Error boundaries with user-friendly messages
✓ Proper TypeScript interfaces for data

### API Integration
✓ Centralized API client (`adminApiClient`)
✓ Consistent error handling
✓ Request cancellation on unmount (where needed)
✓ Pagination parameters standardized (skip/limit)
✓ Query parameters encoded properly

### UI/UX
✓ Loading spinners during data fetch
✓ Empty states when no data
✓ Success/error toast messages
✓ Confirmation modals for destructive actions
✓ Responsive design with grid breakpoints
✓ Consistent color scheme

### Code Quality
✓ TypeScript for type safety
✓ Proper error logging
✓ Component reusability
✓ Clear naming conventions
✓ Comments for complex logic

---

## 10. KEY IMPLEMENTATION RECOMMENDATIONS

### For Raw Data Viewer Page

1. **Create API Endpoints (Backend)**
   ```
   GET /raw-data/tables                    # List available tables
   GET /raw-data/{table_name}              # Get table data with pagination
   POST /raw-data/export/{table_name}      # Export to CSV/Excel
   ```

2. **Implement Data Source Abstraction**
   - Create metadata about each available table
   - Define column types (string, number, date, boolean)
   - Pre-define common filters for each table

3. **Use Server-Side Pagination**
   - Always paginate large datasets
   - Implement skip/limit pattern
   - Return total count for pagination info

4. **Implement Smart Column Rendering**
   - Format dates with dayjs
   - Format large numbers (1M, 1K notation)
   - Color-code important values (percentages, volumes)
   - Show truncated strings with tooltip

5. **Add Advanced Filtering**
   - Date range picker
   - Numeric range sliders
   - Multi-select for categories
   - Text search with debounce

6. **Performance Optimization**
   - Lazy load data as user scrolls
   - Cache table metadata
   - Virtualize large tables if needed
   - Debounce filter inputs

7. **Export Functionality**
   - Use xlsx or papaparse for CSV generation
   - Include applied filters in export
   - Show export progress for large datasets

### Code Structure Template
```typescript
// RawDataViewerPage.tsx
import React, { useState, useEffect } from 'react';
import { Card, Select, Table, Spin, message, Row, Col, Button, Space } from 'antd';
import { adminApiClient } from '../../../shared/admin-auth';

interface RawDataViewerPageProps {}

const RawDataViewerPage: React.FC<RawDataViewerPageProps> = () => {
  // State
  const [selectedTable, setSelectedTable] = useState<string>('daily_trading');
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
  const [filters, setFilters] = useState({});
  
  // Fetch data
  const fetchData = async (page: number, pageSize: number) => {
    setLoading(true);
    try {
      const response = await adminApiClient.get(`/raw-data/${selectedTable}`, {
        params: {
          skip: (page - 1) * pageSize,
          limit: pageSize,
          ...filters,
        }
      });
      setData(response.data.items || []);
      setPagination({ current: page, pageSize, total: response.data.total || 0 });
    } catch (error) {
      message.error('获取数据失败');
    } finally {
      setLoading(false);
    }
  };
  
  // Load on mount or filter change
  useEffect(() => {
    fetchData(1, pagination.pageSize);
  }, [selectedTable, filters]);
  
  // Render
  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col span={24}>
            <Select
              value={selectedTable}
              onChange={setSelectedTable}
              style={{ width: '100%' }}
              placeholder="选择数据表"
            >
              <Select.Option value="daily_trading">每日交易数据</Select.Option>
              <Select.Option value="concept_summary">概念每日汇总</Select.Option>
            </Select>
          </Col>
        </Row>
        
        {loading ? (
          <Spin size="large" />
        ) : (
          <Table
            dataSource={data}
            columns={[/* dynamic columns */]}
            pagination={{
              ...pagination,
              onChange: (page, pageSize) => fetchData(page, pageSize),
            }}
            scroll={{ x: 1200 }}
          />
        )}
      </Card>
    </div>
  );
};

export default RawDataViewerPage;
```

---

## 11. NEXT STEPS

1. **Backend Preparation**
   - Create `/raw-data/*` endpoints
   - Implement flexible table metadata endpoint
   - Support dynamic column selection
   - Add filtering/sorting parameters

2. **Frontend Development**
   - Create `RawDataViewerPage.tsx`
   - Add menu item to `AdminLayout.tsx`
   - Connect to new endpoints
   - Implement UI features progressively

3. **Testing**
   - Test with various data volumes
   - Verify pagination and sorting
   - Test filter combinations
   - Performance testing with large datasets

4. **Documentation**
   - Document available tables and columns
   - Create user guide for filters
   - Document API endpoints

---

**Summary**: The frontend uses a tab-based routing system with centralized API client, Ant Design components for UI, and TypeScript for type safety. The recommended approach follows established patterns: state management at page level, async operations in useEffect, standardized pagination, and proper error handling. For raw data viewer, implement a flexible data source abstraction with server-side pagination, configurable columns, and advanced filtering.
