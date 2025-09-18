import React, { useState, useEffect } from 'react';
import {
  Table, Card, Button, message, Space, Tag, Tooltip,
  DatePicker, Row, Col, Input, Alert, Statistic, Typography
} from 'antd';
import {
  ReloadOutlined, SearchOutlined, ClearOutlined,
  CheckCircleOutlined, CloseCircleOutlined, SyncOutlined,
  FileTextOutlined, CalendarOutlined, ClockCircleOutlined
} from '@ant-design/icons';
import { adminApiClient } from '../../../shared/admin-auth';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;
const { Text } = Typography;

interface HistoricalImportRecord {
  id: number;
  filename: string;
  total_dates: number;
  date_range: string;
  total_records: number;
  imported_records: number;
  error_records: number;
  import_status: string;
  imported_by: string;
  import_started_at: string;
  import_completed_at: string;
  duration: string;
  error_message?: string;
}

interface HistoricalImportRecordsProps {
  refreshTrigger?: number;
}

const HistoricalImportRecords: React.FC<HistoricalImportRecordsProps> = ({
  refreshTrigger = 0
}) => {
  const [records, setRecords] = useState<HistoricalImportRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });

  // 过滤条件
  const [filters, setFilters] = useState({
    filename: '',
    imported_by: '',
    status: '',
    date_range: null as any
  });

  // 统计信息
  const [stats, setStats] = useState({
    total_imports: 0,
    success_imports: 0,
    failed_imports: 0,
    total_records: 0
  });

  // 获取历史导入记录
  const fetchRecords = async () => {
    setLoading(true);
    try {
      const params = {
        page: pagination.current,
        size: pagination.pageSize,
        ...filters,
        start_date: filters.date_range?.[0]?.format('YYYY-MM-DD'),
        end_date: filters.date_range?.[1]?.format('YYYY-MM-DD')
      };

      // 移除空值
      Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === null || params[key] === undefined) {
          delete params[key];
        }
      });

      const response = await adminApiClient.get('/api/v1/historical-import/records', { params });

      if (response.data.success) {
        setRecords(response.data.data.records);
        setPagination(prev => ({
          ...prev,
          total: response.data.data.total
        }));
        setStats(response.data.data.stats);
      } else {
        message.error(response.data.message || '获取记录失败');
      }
    } catch (error: any) {
      console.error('获取历史导入记录失败:', error);
      message.error(`获取记录失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 初始加载和刷新触发
  useEffect(() => {
    fetchRecords();
  }, [pagination.current, pagination.pageSize, refreshTrigger]);

  // 搜索
  const handleSearch = () => {
    setPagination(prev => ({ ...prev, current: 1 }));
    fetchRecords();
  };

  // 清空搜索条件
  const handleClearFilters = () => {
    setFilters({
      filename: '',
      imported_by: '',
      status: '',
      date_range: null
    });
    setPagination(prev => ({ ...prev, current: 1 }));
    setTimeout(() => fetchRecords(), 100);
  };

  // 重新导入
  const handleReimport = async (record: HistoricalImportRecord) => {
    try {
      const response = await adminApiClient.post(`/api/v1/historical-import/reimport/${record.id}`);

      if (response.data.success) {
        message.success('重新导入成功');
        fetchRecords();
      } else {
        message.error(response.data.message || '重新导入失败');
      }
    } catch (error: any) {
      console.error('重新导入失败:', error);
      message.error(`重新导入失败: ${error.response?.data?.detail || error.message}`);
    }
  };

  // 状态渲染
  const renderStatus = (status: string, record: HistoricalImportRecord) => {
    const statusConfig = {
      'success': { color: 'success', icon: <CheckCircleOutlined />, text: '成功' },
      'failed': { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
      'processing': { color: 'processing', icon: <SyncOutlined spin />, text: '处理中' }
    };

    const config = statusConfig[status] || { color: 'default', icon: null, text: status };

    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  // 表格列定义
  const columns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      width: 200,
      ellipsis: true,
      render: (filename: string) => (
        <Tooltip title={filename}>
          <Space>
            <FileTextOutlined />
            <span>{filename}</span>
          </Space>
        </Tooltip>
      )
    },
    {
      title: '日期范围',
      dataIndex: 'date_range',
      key: 'date_range',
      width: 150,
      render: (date_range: string, record: HistoricalImportRecord) => (
        <Space direction="vertical" size="small">
          <Text style={{ fontSize: '12px' }}>{date_range}</Text>
          <Tag color="blue">{record.total_dates} 个交易日</Tag>
        </Space>
      )
    },
    {
      title: '导入统计',
      key: 'import_stats',
      width: 120,
      render: (_, record: HistoricalImportRecord) => (
        <Space direction="vertical" size="small">
          <Text style={{ fontSize: '12px', color: '#52c41a' }}>
            成功: {record.imported_records}
          </Text>
          {record.error_records > 0 && (
            <Text style={{ fontSize: '12px', color: '#ff4d4f' }}>
              失败: {record.error_records}
            </Text>
          )}
        </Space>
      )
    },
    {
      title: '状态',
      dataIndex: 'import_status',
      key: 'import_status',
      width: 100,
      render: (status: string, record: HistoricalImportRecord) => renderStatus(status, record)
    },
    {
      title: '导入时间',
      key: 'import_time',
      width: 180,
      render: (_, record: HistoricalImportRecord) => (
        <Space direction="vertical" size="small">
          <Text style={{ fontSize: '12px' }}>
            <CalendarOutlined /> {dayjs(record.import_started_at).format('YYYY-MM-DD HH:mm')}
          </Text>
          {record.duration && (
            <Text style={{ fontSize: '12px', color: '#8c8c8c' }}>
              <ClockCircleOutlined /> 用时: {record.duration}
            </Text>
          )}
        </Space>
      )
    },
    {
      title: '导入人',
      dataIndex: 'imported_by',
      key: 'imported_by',
      width: 100
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_, record: HistoricalImportRecord) => (
        <Space>
          {record.import_status === 'failed' && (
            <Button
              type="link"
              size="small"
              onClick={() => handleReimport(record)}
              style={{ padding: 0 }}
            >
              重新导入
            </Button>
          )}
          {record.error_message && (
            <Tooltip title={record.error_message}>
              <Button type="link" size="small" danger style={{ padding: 0 }}>
                查看错误
              </Button>
            </Tooltip>
          )}
        </Space>
      )
    }
  ];

  return (
    <div>
      {/* 统计信息 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="总导入次数"
              value={stats.total_imports}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="成功导入"
              value={stats.success_imports}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="失败导入"
              value={stats.failed_imports}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="总记录数"
              value={stats.total_records}
              prefix={<CalendarOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 搜索条件 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[8, 8]} align="middle">
          <Col flex="100px">
            <span style={{ fontWeight: 'bold' }}>筛选条件:</span>
          </Col>
          <Col flex="150px">
            <Input
              placeholder="文件名"
              value={filters.filename}
              onChange={(e) => setFilters(prev => ({ ...prev, filename: e.target.value }))}
              allowClear
              size="small"
            />
          </Col>
          <Col flex="120px">
            <Input
              placeholder="导入人"
              value={filters.imported_by}
              onChange={(e) => setFilters(prev => ({ ...prev, imported_by: e.target.value }))}
              allowClear
              size="small"
            />
          </Col>
          <Col flex="200px">
            <RangePicker
              size="small"
              value={filters.date_range}
              onChange={(dates) => setFilters(prev => ({ ...prev, date_range: dates }))}
              style={{ width: '100%' }}
            />
          </Col>
          <Col flex="80px">
            <Button
              type="primary"
              icon={<SearchOutlined />}
              onClick={handleSearch}
              size="small"
              block
            >
              搜索
            </Button>
          </Col>
          <Col flex="60px">
            <Button
              icon={<ClearOutlined />}
              onClick={handleClearFilters}
              size="small"
              block
            >
              清空
            </Button>
          </Col>
          <Col flex="60px">
            <Button
              icon={<ReloadOutlined />}
              onClick={() => fetchRecords()}
              loading={loading}
              size="small"
              block
            >
              刷新
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 数据表格 */}
      <Table
        columns={columns}
        dataSource={records}
        rowKey="id"
        loading={loading}
        pagination={{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: pagination.total,
          showSizeChanger: true,
          showQuickJumper: true,
          pageSizeOptions: ['10', '20', '50', '100'],
          showTotal: (total, range) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 条记录`,
          onChange: (page, size) => {
            setPagination({ current: page, pageSize: size || 10, total: pagination.total });
          }
        }}
        scroll={{ x: 'max-content' }}
        size="small"
      />
    </div>
  );
};

export default HistoricalImportRecords;