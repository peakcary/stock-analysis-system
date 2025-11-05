import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, DatePicker, message, Spin, Tag, Space, 
  Typography, Tooltip, Modal, Select, Row, Col, Statistic, Divider
} from 'antd';
import {
  HistoryOutlined, ReloadOutlined, CalendarOutlined, FileTextOutlined,
  CheckCircleOutlined, ExclamationCircleOutlined, ClockCircleOutlined,
  DownloadOutlined, SearchOutlined
} from '@ant-design/icons';
import { adminApiClient } from '../../../shared/admin-auth';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

interface ImportRecord {
  id: number;
  filename: string;
  trading_date: string;
  file_size: number;
  file_size_mb: number;
  import_status: string;
  imported_by: string;
  total_records: number;
  success_records: number;
  error_records: number;
  concept_count: number;
  ranking_count: number;
  new_high_count: number;
  import_started_at: string;
  import_completed_at: string | null;
  calculation_time: number | null;
  error_message: string | null;
  notes: string | null;
}

interface EeeImportRecordsProps {
  refreshTrigger?: number;
}

const EeeImportRecords: React.FC<EeeImportRecordsProps> = ({ refreshTrigger }) => {
  const [records, setRecords] = useState<ImportRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  });
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [recalculating, setRecalculating] = useState<Record<string, boolean>>({});
  const [isVisible, setIsVisible] = useState(false);
  const [errorModalVisible, setErrorModalVisible] = useState(false);
  const [errorModalData, setErrorModalData] = useState<{ tradingDate?: string; errors: any[]; truncated?: boolean }>({ errors: [] });

  const fetchRecords = async (page: number = 1, pageSize: number = 20, tradingDate?: string) => {
    setLoading(true);
    try {
      const limit = pageSize;
      const offset = (page - 1) * pageSize;
      const url = new URL(`/universal-import/eee/records`, window.location.origin);
      url.searchParams.set('limit', String(limit));
      url.searchParams.set('offset', String(offset));
      if (tradingDate) url.searchParams.set('trading_date', tradingDate);

      const response = await adminApiClient.get(url.pathname + url.search);

      if (response.data?.records) {
        const list = (response.data.records as any[]).map((r: any) => ({
          ...r,
          file_size_mb: r.file_size ? r.file_size / 1024 / 1024 : 0
        }));

        setRecords(list);
        setPagination({
          current: page,
          pageSize,
          total: response.data.total || list.length
        });
      } else {
        setRecords([]);
        setPagination(prev => ({ ...prev, total: 0 }));
      }
    } catch (error: any) {
      console.error('获取EEE导入记录失败:', error);
      message.error('获取EEE导入记录失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableDates = async () => {
    try {
      const response = await adminApiClient.get('/universal-import/eee/dates?limit=365');
      if (response.data?.success) {
        setAvailableDates(response.data.dates || []);
      }
    } catch (error) {
      console.error('获取EEE日期列表失败:', error);
    }
  };

  const handleRecalculate = async (tradingDate: string) => {
    setRecalculating(prev => ({ ...prev, [tradingDate]: true }));
    
    const hideLoading = message.loading(`正在重新计算 ${tradingDate} 的EEE数据，请耐心等待...`, 0);
    
    try {
      const response = await adminApiClient.post(`/universal-import/eee/recalculate?trading_date=${tradingDate}`, {}, {
        timeout: 180000
      });
      
      if (response.data?.success) {
        const stats = response.data.calculation_result || {};
        message.success(
          `${tradingDate} EEE重新计算完成！概念汇总: ${stats.concept_count || 0}个，个股排名: ${stats.ranking_count || 0}条，创新高: ${stats.new_high_count || 0}条`,
          5
        );
        
        await fetchRecords(pagination.current, pagination.pageSize, selectedDate);
      } else {
        message.error(response.data?.message || 'EEE重新计算失败');
      }
    } catch (error: any) {
      console.error('EEE重新计算失败:', error);
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        message.error('EEE重新计算超时，请检查后端服务状态或稍后重试');
      } else if (error.response?.status === 401) {
        message.error('认证失败，请重新登录');
      } else {
        message.error(`EEE重新计算失败: ${error.response?.data?.detail || error.message}`);
      }
    } finally {
      hideLoading();
      setRecalculating(prev => ({ ...prev, [tradingDate]: false }));
    }
  };

  useEffect(() => {
    fetchRecords();
    fetchAvailableDates();
  }, []);

  useEffect(() => {
    if (refreshTrigger && refreshTrigger > 0) {
      fetchRecords();
      fetchAvailableDates();
    }
  }, [refreshTrigger]);

  useEffect(() => {
    const handleEeeImportSuccess = (event: any) => {
      console.log('收到EEE导入成功事件，刷新记录列表', event.detail);
      setTimeout(() => {
        fetchRecords();
        fetchAvailableDates();
      }, 1000);
    };

    window.addEventListener('eeeImportSuccess', handleEeeImportSuccess);
    
    return () => {
      window.removeEventListener('eeeImportSuccess', handleEeeImportSuccess);
    };
  }, []);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsVisible(entry.isIntersecting);
      },
      { threshold: 0.1 }
    );

    const element = document.getElementById('eee-import-records-container');
    if (element) {
      observer.observe(element);
    }

    const interval = setInterval(() => {
      if (isVisible) {
        console.log('定期刷新EEE导入记录');
        fetchRecords(pagination.current, pagination.pageSize, selectedDate);
        fetchAvailableDates();
      }
    }, 30000);

    return () => {
      if (element) {
        observer.unobserve(element);
      }
      clearInterval(interval);
    };
  }, [isVisible, pagination.current, pagination.pageSize, selectedDate]);

  useEffect(() => {
    fetchRecords(1, pagination.pageSize, selectedDate);
  }, [selectedDate]);

  const renderStatus = (status: string) => {
    const statusMap = {
      success: { color: 'success', icon: <CheckCircleOutlined />, text: '成功' },
      failed: { color: 'error', icon: <ExclamationCircleOutlined />, text: '失败' },
      processing: { color: 'processing', icon: <ClockCircleOutlined />, text: '处理中' }
    };
    
    const config = statusMap[status as keyof typeof statusMap] || statusMap.processing;
    
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  const columns = [
    {
      title: '交易日期',
      dataIndex: 'trading_date',
      key: 'trading_date',
      width: 120,
      render: (date: string) => (
        <Tag color="gold" icon={<CalendarOutlined />}>
          {date}
        </Tag>
      )
    },
    {
      title: '状态',
      dataIndex: 'import_status',
      key: 'import_status',
      width: 100,
      render: renderStatus
    },
    {
      title: '文件大小',
      dataIndex: 'file_size_mb',
      key: 'file_size_mb',
      width: 100,
      render: (sizeMb: number) => `${sizeMb?.toFixed(1) || 0} MB`
    },
    {
      title: '导入记录',
      key: 'records',
      width: 120,
      render: (record: ImportRecord) => {
        let extras: any = {};
        try { extras = (record as any).notes ? JSON.parse((record as any).notes) : {}; } catch {}
        return (
          <div>
            <div style={{ fontSize: '12px', color: '#52c41a' }}>
              ✓ 成功: {record.success_records || 0}
            </div>
            {extras.parse_error_count > 0 && (
              <div style={{ fontSize: '12px', color: '#ff4d4f' }}>
                ✗ 解析失败: {extras.parse_error_count}
              </div>
            )}
            {(record as any).duplicate_records !== undefined && (
              <div style={{ fontSize: '12px', color: '#faad14' }}>
                ≈ 重复: {(record as any).duplicate_records || 0}
              </div>
            )}
            <div style={{ fontSize: '12px', color: '#666' }}>
              总计: {record.total_records || 0}
            </div>
          </div>
        );
      }
    },
    {
      title: '计算汇总结果',
      key: 'calculation',
      width: 150,
      render: (record: ImportRecord) => (
        <div style={{ fontSize: '12px' }}>
          <div style={{ color: '#722ed1' }}>
            概念汇总: <Text strong>{record.concept_count || 0}</Text>
          </div>
          <div style={{ color: '#fa541c' }}>
            排名记录: <Text strong>{record.ranking_count || 0}</Text>
          </div>
          <div style={{ color: '#52c41a' }}>
            创新高: <Text strong>{record.new_high_count || 0}</Text>
          </div>
        </div>
      )
    },
    {
      title: '导入信息',
      key: 'import_info',
      width: 180,
      render: (record: ImportRecord) => (
        <div style={{ fontSize: '12px' }}>
          <div>导入人: <Text strong>{record.imported_by}</Text></div>
          <div>开始时间: {record.import_started_at}</div>
          {record.import_completed_at && (
            <div>完成时间: {record.import_completed_at}</div>
          )}
          {record.calculation_time && (
            <div style={{ color: '#1890ff' }}>
              计算用时: <Text strong>{record.calculation_time}s</Text>
            </div>
          )}
        </div>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (record: ImportRecord) => {
        let extras: any = {};
        try { extras = (record as any).notes ? JSON.parse((record as any).notes) : {}; } catch {}
        const parseErrorCount = extras.parse_error_count || 0;
        const showErrorBtn = parseErrorCount > 0 || !!record.error_message;
        return (
          <Space size="small" direction="vertical">
            <Tooltip title="重新计算该日期的EEE汇总数据">
              <Button
                size="small"
                icon={<ReloadOutlined />}
                loading={recalculating[record.trading_date]}
                onClick={() => handleRecalculate(record.trading_date)}
                block
              >
                {recalculating[record.trading_date] ? '计算中...' : '重新计算'}
              </Button>
            </Tooltip>
            {showErrorBtn && (
              <Tooltip title={record.error_message ? record.error_message : `解析失败 ${parseErrorCount} 条，点击查看详情`}>
                <Button
                  size="small"
                  danger
                  type="text"
                  block
                  onClick={() => {
                    setErrorModalData({
                      tradingDate: record.trading_date,
                      errors: extras.parse_errors || [],
                      truncated: extras.parse_errors_truncated || false
                    });
                    setErrorModalVisible(true);
                  }}
                >
                  查看失败
                </Button>
              </Tooltip>
            )}
          </Space>
        );
      }
    }
  ];

  const handleTableChange = (page: number, pageSize?: number) => {
    fetchRecords(page, pageSize || pagination.pageSize, selectedDate);
  };

  return (
    <div id="eee-import-records-container" style={{ padding: '24px' }}>
      <Card style={{ marginBottom: '16px', borderRadius: '8px' }} bodyStyle={{ padding: '16px' }}>
        <Row gutter={[8, 8]} align="middle">
          <Col flex="auto" style={{ minWidth: '60px' }}>
            <Space>
              <HistoryOutlined />
              <Text strong>EEE导入记录筛选:</Text>
            </Space>
          </Col>
          
          <Col flex="200px">
            <Select
              value={selectedDate}
              onChange={setSelectedDate}
              placeholder="选择交易日期"
              style={{ width: '100%' }}
              allowClear
              size="small"
            >
              {availableDates.map(date => (
                <Option key={date} value={date}>{date}</Option>
              ))}
            </Select>
          </Col>
          
          <Col flex="60px">
            <Button 
              type="primary" 
              icon={<SearchOutlined />}
              onClick={() => fetchRecords(1, pagination.pageSize, selectedDate)}
              loading={loading}
              size="small"
              block
            >
              查询
            </Button>
          </Col>
          
          <Col flex="50px">
            <Button 
              icon={<ReloadOutlined />}
              onClick={() => {
                fetchRecords(pagination.current, pagination.pageSize, selectedDate);
                fetchAvailableDates();
              }}
              size="small"
              block
            >
              刷新
            </Button>
          </Col>
        </Row>
      </Card>

      <Card style={{ borderRadius: '8px' }}>
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
            showTotal: (total, range) => 
              `显示 ${range[0]}-${range[1]} 条，共 ${total} 条EEE记录`,
            onChange: handleTableChange,
            onShowSizeChange: handleTableChange
          }}
          scroll={{ x: 1200 }}
          size="middle"
        />
      </Card>

      <Modal
        title={`解析失败详情${errorModalData.tradingDate ? ' - ' + errorModalData.tradingDate : ''}`}
        open={errorModalVisible}
        onCancel={() => setErrorModalVisible(false)}
        footer={null}
        width={720}
      >
        {(!errorModalData.errors || errorModalData.errors.length === 0) ? (
          <Text type="secondary">暂无失败详情</Text>
        ) : (
          <div style={{ maxHeight: 400, overflowY: 'auto' }}>
            {errorModalData.errors.map((e: any, idx: number) => (
              <div key={idx} style={{ padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                <div style={{ color: '#fa541c' }}>第 {e.line_number} 行：{e.reason}</div>
                <div style={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', color: '#555' }}>{e.content}</div>
              </div>
            ))}
            {errorModalData.truncated && (
              <div style={{ marginTop: 8 }}>
                <Tag color="warning">仅显示前50条</Tag>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default EeeImportRecords;
