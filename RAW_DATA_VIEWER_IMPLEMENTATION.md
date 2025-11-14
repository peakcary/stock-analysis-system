# Raw Data Viewer Implementation Guide

## Overview
This guide provides step-by-step instructions for building the new raw data table viewer page.

## Phase 1: Backend API Development (Dependencies)

### 1.1 Create Raw Data Endpoints

Location: `/backend/app/api/api_v1/endpoints/raw_data.py`

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.admin_auth import get_current_admin_user

router = APIRouter(prefix="/raw-data", tags=["raw-data"])

# List available tables
@router.get("/tables")
async def get_available_tables(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """Return list of available raw data tables with metadata"""
    return {
        "tables": [
            {
                "id": "daily_trading",
                "label": "Daily Trading Data",
                "description": "Raw daily trading volume data",
                "recordCount": 500000,  # Approximate
                "columns": [
                    {"name": "stock_code", "type": "string"},
                    {"name": "trading_date", "type": "date"},
                    {"name": "trading_volume", "type": "integer"},
                ]
            },
            {
                "id": "concept_summary",
                "label": "Concept Daily Summary",
                "recordCount": 10000,
                "columns": [...]
            },
            # ... more tables
        ]
    }

# Get raw data for a table
@router.get("/{table_name}")
async def get_table_data(
    table_name: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """
    Fetch raw data from specified table
    
    Query params:
    - skip: Number of records to skip (for pagination)
    - limit: Number of records to fetch
    - [table_specific filters]
    """
    
    if table_name == "daily_trading":
        query = db.query(DailyTrading)
        # Apply filters
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        
        return {
            "table": "daily_trading",
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    # Handle other tables...
    
    raise HTTPException(status_code=404, detail="Table not found")

# Export data
@router.post("/export/{table_name}")
async def export_table_data(
    table_name: str,
    format: str = Query("csv", regex="^(csv|xlsx)$"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """Export table data in specified format"""
    # Implementation: Generate and return file
    pass
```

### 1.2 Register Router
Add to `/backend/app/api/api_v1/api.py`:
```python
from app.api.api_v1.endpoints import raw_data

api_router.include_router(raw_data.router)
```

## Phase 2: Frontend Page Development

### 2.1 Create Main Page Component

Location: `/frontend/src/components/RawDataViewerPage.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Select, Table, Spin, message, Button,
  Space, Empty, Input, DatePicker, Tag, Typography
} from 'antd';
import {
  DatabaseOutlined, DownloadOutlined, ReloadOutlined, SearchOutlined
} from '@ant-design/icons';
import { adminApiClient } from '../../../shared/admin-auth';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

interface TableMetadata {
  id: string;
  label: string;
  description: string;
  recordCount: number;
  columns: Array<{
    name: string;
    type: string;
  }>;
}

interface RawDataViewerPageProps {}

const RawDataViewerPage: React.FC<RawDataViewerPageProps> = () => {
  // State
  const [tables, setTables] = useState<TableMetadata[]>([]);
  const [selectedTable, setSelectedTable] = useState<string>('daily_trading');
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [tablesLoading, setTablesLoading] = useState(true);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  });
  const [filters, setFilters] = useState<Record<string, any>>({});

  // Load available tables on mount
  useEffect(() => {
    fetchTables();
  }, []);

  // Load data when table or pagination changes
  useEffect(() => {
    if (selectedTable) {
      fetchData(1, pagination.pageSize);
    }
  }, [selectedTable]);

  // Fetch available tables
  const fetchTables = async () => {
    setTablesLoading(true);
    try {
      const response = await adminApiClient.get('/raw-data/tables');
      setTables(response.data.tables || []);
      if (response.data.tables.length > 0) {
        setSelectedTable(response.data.tables[0].id);
      }
    } catch (error) {
      console.error('Failed to load tables:', error);
      message.error('Failed to load available tables');
    } finally {
      setTablesLoading(false);
    }
  };

  // Fetch data for selected table
  const fetchData = async (page: number, pageSize: number) => {
    setLoading(true);
    try {
      const params: any = {
        skip: (page - 1) * pageSize,
        limit: pageSize,
        ...filters,
      };

      const response = await adminApiClient.get(
        `/raw-data/${selectedTable}`,
        { params }
      );

      setData(response.data.items || []);
      setPagination({
        current: page,
        pageSize,
        total: response.data.total || 0
      });
    } catch (error) {
      console.error('Failed to load data:', error);
      message.error('Failed to load table data');
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  // Get columns for selected table
  const getTableColumns = () => {
    const table = tables.find(t => t.id === selectedTable);
    if (!table) return [];

    return table.columns.map(col => ({
      title: col.name,
      dataIndex: col.name,
      key: col.name,
      width: 120,
      ellipsis: true,
      render: (value: any) => renderValue(value, col.type),
    }));
  };

  // Render values based on type
  const renderValue = (value: any, type: string) => {
    if (value === null || value === undefined) {
      return <Text type="secondary">-</Text>;
    }

    switch (type) {
      case 'date':
        return dayjs(value).format('YYYY-MM-DD');
      case 'integer':
        return value.toLocaleString();
      case 'float':
        return typeof value === 'number' 
          ? value.toFixed(2)
          : value;
      default:
        return value;
    }
  };

  // Export data
  const handleExport = async (format: 'csv' | 'xlsx') => {
    try {
      const response = await adminApiClient.get(
        `/raw-data/export/${selectedTable}`,
        {
          params: { format, ...filters },
          responseType: 'blob'
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${selectedTable}_${dayjs().format('YYYYMMDD_HHmmss')}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (error) {
      message.error('Export failed');
    }
  };

  const selectedTableMetadata = tables.find(t => t.id === selectedTable);

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <Card style={{ marginBottom: '24px' }}>
        <Row align="middle" justify="space-between">
          <Col>
            <Title level={2} style={{ margin: 0 }}>
              <DatabaseOutlined style={{ marginRight: '8px' }} />
              Raw Data Viewer
            </Title>
          </Col>
          <Col>
            <Button icon={<ReloadOutlined />} onClick={() => fetchData(1, pagination.pageSize)}>
              Refresh
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Table Selector */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={16} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Text strong style={{ display: 'block', marginBottom: '8px' }}>
              Select Table
            </Text>
            <Select
              loading={tablesLoading}
              value={selectedTable}
              onChange={setSelectedTable}
              style={{ width: '100%' }}
              disabled={tablesLoading}
            >
              {tables.map(table => (
                <Select.Option key={table.id} value={table.id}>
                  {table.label}
                </Select.Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={16}>
            {selectedTableMetadata && (
              <div>
                <Text type="secondary">
                  {selectedTableMetadata.description}
                </Text>
                <br />
                <Tag color="blue" style={{ marginTop: '8px' }}>
                  {selectedTableMetadata.recordCount.toLocaleString()} records
                </Tag>
              </div>
            )}
          </Col>
        </Row>
      </Card>

      {/* Data Table */}
      <Card
        title={
          <Space>
            <DatabaseOutlined style={{ color: '#1890ff' }} />
            <span>{selectedTableMetadata?.label}</span>
            <Tag color="blue">{data.length} rows</Tag>
          </Space>
        }
        extra={
          <Space>
            <Button 
              size="small" 
              icon={<DownloadOutlined />}
              onClick={() => handleExport('csv')}
            >
              CSV
            </Button>
            <Button 
              size="small" 
              icon={<DownloadOutlined />}
              onClick={() => handleExport('xlsx')}
            >
              Excel
            </Button>
          </Space>
        }
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px' }}>
            <Spin size="large" tip="Loading data..." />
          </div>
        ) : data.length > 0 ? (
          <Table
            columns={getTableColumns()}
            dataSource={data}
            rowKey={(record, index) => index}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: pagination.total,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `Total ${total.toLocaleString()} records`,
              onChange: (page, pageSize) => fetchData(page, pageSize),
            }}
            scroll={{ x: 1200 }}
            size="small"
          />
        ) : (
          <Empty description="No data" />
        )}
      </Card>
    </div>
  );
};

export default RawDataViewerPage;
```

### 2.2 Update App.tsx

Add import:
```typescript
import RawDataViewerPage from './components/RawDataViewerPage';
```

Add menu item in `AdminApp` component's menu:
```typescript
{
  key: 'raw-data-viewer',
  icon: <DatabaseOutlined />,
  label: 'Raw Data Viewer',
}
```

Add render condition:
```typescript
{activeTab === 'raw-data-viewer' && <RawDataViewerPage />}
```

### 2.3 Update AdminLayout.tsx

Add menu item to the menuItems array:
```typescript
{
  key: 'raw-data-viewer',
  icon: <DatabaseOutlined />,
  label: 'Raw Data Viewer',
}
```

## Phase 3: Enhanced Features (Optional)

### 3.1 Advanced Filtering Component

Location: `/frontend/src/components/RawDataViewer/FilterPanel.tsx`

```typescript
import React from 'react';
import { Row, Col, Input, DatePicker, Button, Space, Form } from 'antd';
import { SearchOutlined, ClearOutlined } from '@ant-design/icons';

interface FilterPanelProps {
  filters: Record<string, any>;
  onFiltersChange: (filters: Record<string, any>) => void;
  onClear: () => void;
}

const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  onFiltersChange,
  onClear
}) => {
  const handleFilterChange = (key: string, value: any) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  return (
    <Form layout="vertical">
      <Row gutter={16}>
        <Col xs={24} sm={12} md={6}>
          <Form.Item label="Stock Code">
            <Input
              placeholder="e.g., 000001"
              value={filters.stock_code || ''}
              onChange={(e) => handleFilterChange('stock_code', e.target.value)}
              prefix={<SearchOutlined />}
            />
          </Form.Item>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Form.Item label="Trading Date">
            <DatePicker
              style={{ width: '100%' }}
              onChange={(date) => handleFilterChange('trading_date', date?.format('YYYY-MM-DD'))}
            />
          </Form.Item>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Form.Item label="Min Volume">
            <Input
              type="number"
              placeholder="Minimum volume"
              onChange={(e) => handleFilterChange('min_volume', parseInt(e.target.value))}
            />
          </Form.Item>
        </Col>
        <Col xs={24} sm={12} md={6} style={{ paddingTop: '32px' }}>
          <Space>
            <Button type="primary" icon={<SearchOutlined />}>
              Search
            </Button>
            <Button icon={<ClearOutlined />} onClick={onClear}>
              Clear
            </Button>
          </Space>
        </Col>
      </Row>
    </Form>
  );
};

export default FilterPanel;
```

### 3.2 Column Selector Component

Location: `/frontend/src/components/RawDataViewer/ColumnSelector.tsx`

```typescript
import React from 'react';
import { Modal, Checkbox, Button, Space } from 'antd';
import { SettingOutlined } from '@ant-design/icons';

interface ColumnSelectorProps {
  allColumns: string[];
  visibleColumns: string[];
  onColumnsChange: (columns: string[]) => void;
}

const ColumnSelector: React.FC<ColumnSelectorProps> = ({
  allColumns,
  visibleColumns,
  onColumnsChange
}) => {
  const [modalVisible, setModalVisible] = React.useState(false);
  const [selected, setSelected] = React.useState<string[]>(visibleColumns);

  const handleOk = () => {
    onColumnsChange(selected);
    setModalVisible(false);
  };

  const handleSelectAll = () => {
    setSelected(allColumns);
  };

  const handleClearAll = () => {
    setSelected([]);
  };

  return (
    <>
      <Button 
        icon={<SettingOutlined />} 
        onClick={() => setModalVisible(true)}
      >
        Columns
      </Button>

      <Modal
        title="Select Columns"
        open={modalVisible}
        onOk={handleOk}
        onCancel={() => setModalVisible(false)}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space>
            <Button size="small" onClick={handleSelectAll}>Select All</Button>
            <Button size="small" onClick={handleClearAll}>Clear All</Button>
          </Space>
          
          {allColumns.map(col => (
            <Checkbox
              key={col}
              checked={selected.includes(col)}
              onChange={(e) => {
                if (e.target.checked) {
                  setSelected([...selected, col]);
                } else {
                  setSelected(selected.filter(c => c !== col));
                }
              }}
            >
              {col}
            </Checkbox>
          ))}
        </Space>
      </Modal>
    </>
  );
};

export default ColumnSelector;
```

## Implementation Checklist

### Backend
- [ ] Create `/raw-data` endpoints
- [ ] Implement table metadata endpoint
- [ ] Implement data fetching with pagination
- [ ] Implement export functionality
- [ ] Add authentication/authorization checks
- [ ] Test endpoints with curl/Postman
- [ ] Handle edge cases (empty tables, missing columns)

### Frontend
- [ ] Create `RawDataViewerPage.tsx`
- [ ] Add menu item to `AdminLayout.tsx`
- [ ] Update `App.tsx` with new page
- [ ] Test data loading and pagination
- [ ] Test table rendering
- [ ] Test export functionality
- [ ] Test with various data volumes

### Optional Features
- [ ] Add `FilterPanel` component
- [ ] Add `ColumnSelector` component
- [ ] Add column sorting
- [ ] Add search highlighting
- [ ] Add data caching
- [ ] Add CSV/Excel exports

### Testing
- [ ] Test with small datasets (< 1000 rows)
- [ ] Test with medium datasets (10K rows)
- [ ] Test with large datasets (100K+ rows)
- [ ] Test pagination with different page sizes
- [ ] Test filter combinations
- [ ] Test export with various formats
- [ ] Test on different screen sizes (responsive)
- [ ] Test error handling (API failures, empty tables)

## Common Pitfalls to Avoid

1. **Pagination**: Always use server-side pagination for large datasets
2. **Column Rendering**: Don't forget to handle null/undefined values
3. **Loading States**: Show loading indicators for all async operations
4. **Error Handling**: Provide clear error messages to users
5. **Performance**: Limit columns displayed if table is too wide (use scroll)
6. **Responsiveness**: Test on mobile devices
7. **Auth**: Always check authentication on protected endpoints
8. **Data Validation**: Validate API responses before rendering

## API Response Format Expected

```json
{
  "table": "daily_trading",
  "items": [
    {
      "stock_code": "000001",
      "trading_date": "2025-09-02",
      "trading_volume": 1000000
    }
  ],
  "total": 1000000,
  "skip": 0,
  "limit": 20
}
```

## Future Enhancements

1. **Real-time Updates**: WebSocket integration for live data
2. **Bookmarks**: Save favorite table views
3. **Query Builder**: UI for building complex queries
4. **Visualization**: Charts for data analysis
5. **Comparison View**: Compare tables side-by-side
6. **Change History**: Track data changes over time
7. **Alerts**: Set up alerts for data changes
8. **Scheduled Reports**: Generate reports automatically

---

**Next Steps**: Start with Phase 1 (Backend), then Phase 2 (Frontend), then optionally add Phase 3 features based on requirements.
