# Quick Reference: Frontend Architecture

## File Locations (Absolute Paths)

```
/Users/peakom/work/stock-analysis-system/frontend/
├── src/
│   ├── App.tsx                           # Main app with tab-based routing
│   ├── main.tsx                          # Entry point
│   ├── api/endpoints.ts                  # API endpoint constants
│   ├── components/
│   │   ├── AdminLayout.tsx               # Navigation sidebar + header
│   │   ├── Dashboard.tsx                 # Home page
│   │   ├── StockListPage.tsx             # Example data table page
│   │   ├── ConceptAnalysisPage.tsx       # Concept data table
│   │   ├── UserManagement.tsx            # User table with filters
│   │   ├── DataImportPage.tsx            # Data import interface
│   │   ├── LoginPage.tsx                 # Authentication
│   │   └── [other pages...]
│   ├── contexts/
│   │   └── AuthContext.tsx               # Auth state & functions
│   └── assets/                           # Images, fonts, etc.
├── package.json
├── vite.config.ts
└── index.html

/Users/peakom/work/stock-analysis-system/shared/
└── admin-auth.ts                         # API client + auth manager

/Users/peakom/work/stock-analysis-system/backend/
├── app/models/
│   ├── daily_trading.py                  # DailyTrading, ConceptDailySummary, etc.
│   ├── stock.py                          # Stock master data
│   └── [other models...]
└── app/api/api_v1/endpoints/
    ├── stocks.py
    ├── stock_analysis.py
    └── [other endpoints...]
```

## Common Patterns

### 1. Fetching Data
```typescript
import { adminApiClient } from '../../../shared/admin-auth';

const fetchData = async () => {
  try {
    const response = await adminApiClient.get('/endpoint', {
      params: { skip: 0, limit: 20, filters: {...} }
    });
    setData(response.data);
  } catch (error) {
    message.error('Error message');
  }
};
```

### 2. Creating a Page Component
```typescript
import React, { useState, useEffect } from 'react';
import { Card, Table, Spin, message, Button } from 'antd';
import { adminApiClient } from '../../../shared/admin-auth';

const MyPage: React.FC = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    fetchData();
  }, []);
  
  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await adminApiClient.get('/api/endpoint');
      setData(response.data);
    } catch (error) {
      message.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Card>
      <Table dataSource={data} loading={loading} columns={columns} />
    </Card>
  );
};

export default MyPage;
```

### 3. Adding a Menu Item
**File**: `frontend/src/components/AdminLayout.tsx`
```typescript
const menuItems = [
  {
    key: 'my-page-key',
    icon: <DatabaseOutlined />,
    label: 'My Page Label',
  },
  // ...
];
```

**File**: `frontend/src/App.tsx`
```typescript
import MyPage from './components/MyPage';

// In render section:
{activeTab === 'my-page-key' && <MyPage />}
```

### 4. Ant Design Table Columns
```typescript
const columns = [
  {
    title: 'Code',
    dataIndex: 'stock_code',
    key: 'stock_code',
    width: 100,
    sorter: (a, b) => a.stock_code.localeCompare(b.stock_code),
    render: (text) => <Text strong style={{ color: '#1890ff' }}>{text}</Text>,
  },
  {
    title: 'Date',
    dataIndex: 'trading_date',
    key: 'trading_date',
    render: (date) => dayjs(date).format('YYYY-MM-DD'),
  },
  {
    title: 'Volume',
    dataIndex: 'trading_volume',
    key: 'trading_volume',
    sorter: (a, b) => a.trading_volume - b.trading_volume,
    render: (volume) => <Text style={{ color: '#52c41a' }}>{volume.toLocaleString()}</Text>,
  },
];
```

### 5. Pagination Pattern
```typescript
const [pagination, setPagination] = useState({
  current: 1,
  pageSize: 10,
  total: 0
});

// Fetch with pagination
const fetchData = async (page: number, pageSize: number) => {
  const response = await adminApiClient.get('/endpoint', {
    params: {
      skip: (page - 1) * pageSize,
      limit: pageSize
    }
  });
  setPagination({ current: page, pageSize, total: response.data.total });
  setData(response.data.items);
};

// Table props
<Table
  pagination={{
    current: pagination.current,
    pageSize: pagination.pageSize,
    total: pagination.total,
    onChange: (page, pageSize) => fetchData(page, pageSize),
  }}
/>
```

## Key React Hooks Used

| Hook | Usage | Example |
|------|-------|---------|
| `useState` | Component state | `const [data, setData] = useState([])` |
| `useEffect` | Side effects, data fetching | `useEffect(() => { fetchData(); }, [])` |
| `useContext` | Global state (auth) | `const { isAuthenticated } = useAuth()` |

## Ant Design Components Cheat Sheet

| Component | Usage | Import |
|-----------|-------|--------|
| Table | Data display | `<Table columns={cols} dataSource={data} />` |
| Card | Content container | `<Card title="Title"><content></Card>` |
| Button | Actions | `<Button type="primary" onClick={handler}>Text</Button>` |
| Input | Text input | `<Input placeholder="Search..." />` |
| Select | Dropdown | `<Select><Select.Option value="1">Option 1</Select.Option></Select>` |
| DatePicker | Date selection | `<DatePicker onChange={setDate} />` |
| Modal | Dialog | `<Modal visible={show} onOk={ok} onCancel={cancel}><content/></Modal>` |
| Tag | Label/badge | `<Tag color="blue">Label</Tag>` |
| Spin | Loading | `<Spin size="large" tip="Loading..." />` |
| Empty | No data state | `<Empty description="No data" />` |
| Message | Toast notification | `message.success('Done'); message.error('Error');` |

## TypeScript Interfaces Pattern

```typescript
interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
}

interface ApiResponse<T> {
  data: T[];
  total: number;
  skip: number;
  limit: number;
}

// Usage
const response = await adminApiClient.get('/users');
const users: User[] = response.data;
```

## API Request Examples

```typescript
// GET with query params
adminApiClient.get('/stocks', {
  params: { skip: 0, limit: 20, search: 'AAPL' }
});

// POST with data
adminApiClient.post('/stocks', { stock_code: '000001', stock_name: 'Test' });

// PUT to update
adminApiClient.put('/stocks/1', { stock_name: 'Updated' });

// DELETE
adminApiClient.delete('/stocks/1');

// POST with file (multipart)
const formData = new FormData();
formData.append('file', file);
adminApiClient.post('/import', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});
```

## Common Colors Used

- Primary Blue: `#1890ff`
- Success Green: `#52c41a`
- Danger Red: `#ff4d4f`
- Warning Orange: `#faad14`
- Text Dark: `#262626`
- Text Light: `#8c8c8c`
- Background: `#fafafa`

## Dev Commands

```bash
# Start dev server (port 8006)
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check

# Linting
npm run lint
npm run lint:fix
```

## Data Models Available (Backend)

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| `stocks` | Master stock data | `stock_code`, `stock_name`, `industry`, `is_convertible_bond` |
| `daily_trading` | Raw daily trading | `stock_code`, `trading_date`, `trading_volume` |
| `concept_daily_summary` | Concept daily stats | `concept_name`, `trading_date`, `total_volume`, `stock_count` |
| `stock_concept_ranking` | Stock rank in concept | `stock_code`, `concept_name`, `concept_rank`, `trading_volume` |
| `daily_stock_data` | Technical data | `stock_id`, `trade_date`, `heat_value`, `turnover_rate` |

## Error Handling Pattern

```typescript
try {
  const response = await adminApiClient.get('/endpoint');
  setData(response.data);
} catch (error: any) {
  if (error.response?.status === 404) {
    message.error('Not found');
  } else if (error.response?.status === 401) {
    // Auto-redirects to login via interceptor
  } else {
    message.error(error.response?.data?.detail || 'Error occurred');
  }
} finally {
  setLoading(false);
}
```

## Component Naming Convention

- Page components (full pages): `*Page.tsx` (e.g., `RawDataViewerPage.tsx`)
- Sub-components: `*Component.tsx` or `*Panel.tsx` (e.g., `FilterPanel.tsx`)
- Context/Hooks: `*Context.tsx` or use `*Hook.ts`
- Utilities: `*Utils.ts` or `*Helper.ts`

