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

interface TxtImportRecordsProps {
  refreshTrigger?: number; // 用于触发刷新的计数器
}

const TxtImportRecords: React.FC<TxtImportRecordsProps> = ({ refreshTrigger }) => {
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

  // 获取导入记录
  const fetchRecords = async (page: number = 1, pageSize: number = 20, tradingDate?: string) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        size: pageSize.toString()
      });
      
      if (tradingDate) {
        params.append('trading_date', tradingDate);
      }
      
      const response = await adminApiClient.get(`/api/v1/txt-import/records?${params}`);
      
      if (response.data?.records) {
        setRecords(response.data.records);
        setPagination({
          current: response.data.pagination.page,
          pageSize: response.data.pagination.size,
          total: response.data.pagination.total
        });
      } else {
        setRecords([]);
        setPagination(prev => ({ ...prev, total: 0 }));
      }
    } catch (error: any) {
      console.error('获取导入记录失败:', error);
      message.error('获取导入记录失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取可用日期列表
  const fetchAvailableDates = async () => {
    try {
      const response = await adminApiClient.get('/api/v1/txt-import/dates');
      if (response.data?.dates) {
        setAvailableDates(response.data.dates);
      }
    } catch (error) {
      console.error('获取日期列表失败:', error);
    }
  };

  // 重新计算指定日期的数据
  const handleRecalculate = async (tradingDate: string) => {
    setRecalculating(prev => ({ ...prev, [tradingDate]: true }));
    
    try {
      const response = await adminApiClient.post(`/api/v1/txt-import/recalculate?trading_date=${tradingDate}`);
      
      if (response.data?.success) {
        const stats = response.data.stats;
        message.success(
          `${tradingDate} 重新计算完成！概念汇总: ${stats.concept_summary_count}个，个股排名: ${stats.ranking_count}条，创新高: ${stats.new_high_count}条`
        );
        
        // 重新获取记录
        await fetchRecords(pagination.current, pagination.pageSize, selectedDate);
      } else {
        message.error(response.data?.message || '重新计算失败');
      }
    } catch (error: any) {
      console.error('重新计算失败:', error);
      message.error(`重新计算失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setRecalculating(prev => ({ ...prev, [tradingDate]: false }));
    }
  };

  // 页面加载时获取数据
  useEffect(() => {
    fetchRecords();
    fetchAvailableDates();
  }, []);

  // 监听刷新触发器
  useEffect(() => {
    if (refreshTrigger && refreshTrigger > 0) {
      // 刷新记录和日期列表
      fetchRecords();
      fetchAvailableDates();
    }
  }, [refreshTrigger]);

  // 监听全局TXT导入成功事件
  useEffect(() => {
    const handleTxtImportSuccess = (event: any) => {
      console.log('收到TXT导入成功事件，刷新记录列表', event.detail);
      // 延迟一点时间确保后端已经完成数据写入
      setTimeout(() => {
        fetchRecords();
        fetchAvailableDates();
      }, 1000);
    };

    window.addEventListener('txtImportSuccess', handleTxtImportSuccess);
    
    // 清理事件监听器
    return () => {
      window.removeEventListener('txtImportSuccess', handleTxtImportSuccess);
    };
  }, []);

  // 组件可见性检测和定期刷新
  useEffect(() => {
    // 创建Intersection Observer来检测组件是否可见
    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsVisible(entry.isIntersecting);
      },
      { threshold: 0.1 }
    );

    // 获取组件的DOM元素
    const element = document.getElementById('txt-import-records-container');
    if (element) {
      observer.observe(element);
    }

    // 定期刷新数据（当组件可见时）
    const interval = setInterval(() => {
      if (isVisible) {
        console.log('定期刷新TXT导入记录');
        fetchRecords(pagination.current, pagination.pageSize, selectedDate);
        fetchAvailableDates();
      }
    }, 30000); // 每30秒刷新一次

    return () => {
      if (element) {
        observer.unobserve(element);
      }
      clearInterval(interval);
    };
  }, [isVisible, pagination.current, pagination.pageSize, selectedDate]);

  // 当日期过滤改变时重新获取数据
  useEffect(() => {
    fetchRecords(1, pagination.pageSize, selectedDate);
  }, [selectedDate]);

  // 状态标签渲染
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

  // 表格列定义 - 去掉文件名列，优化计算结果显示
  const columns = [
    {
      title: '交易日期',
      dataIndex: 'trading_date',
      key: 'trading_date',
      width: 120,
      render: (date: string) => (
        <Tag color="blue" icon={<CalendarOutlined />}>
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
      render: (record: ImportRecord) => (
        <div>
          <div style={{ fontSize: '12px', color: '#52c41a' }}>
            ✓ 成功: {record.success_records || 0}
          </div>
          {(record.error_records || 0) > 0 && (
            <div style={{ fontSize: '12px', color: '#ff4d4f' }}>
              ✗ 失败: {record.error_records}
            </div>
          )}
          <div style={{ fontSize: '12px', color: '#666' }}>
            总计: {record.total_records || 0}
          </div>
        </div>
      )
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
      render: (record: ImportRecord) => (
        <Space size="small" direction="vertical">
          <Tooltip title="重新计算该日期的汇总数据">
            <Button
              size="small"
              icon={<ReloadOutlined />}
              loading={recalculating[record.trading_date]}
              onClick={() => handleRecalculate(record.trading_date)}
              block
            >
              重新计算
            </Button>
          </Tooltip>
          {record.error_message && (
            <Tooltip title={record.error_message}>
              <Button size="small" danger type="text" block>
                查看错误
              </Button>
            </Tooltip>
          )}
        </Space>
      )
    }
  ];

  // 分页处理
  const handleTableChange = (page: number, pageSize?: number) => {
    fetchRecords(page, pageSize || pagination.pageSize, selectedDate);
  };

  return (
    <div id="txt-import-records-container" style={{ padding: '24px' }}>
      {/* 简化的查询区域 */}
      <Card style={{ marginBottom: '16px', borderRadius: '8px' }} bodyStyle={{ padding: '16px' }}>
        <Row gutter={[8, 8]} align="middle">
          <Col flex="auto" style={{ minWidth: '60px' }}>
            <Space>
              <HistoryOutlined />
              <Text strong>TXT导入记录筛选:</Text>
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

      {/* 导入记录表格 */}
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
              `显示 ${range[0]}-${range[1]} 条，共 ${total} 条记录`,
            onChange: handleTableChange,
            onShowSizeChange: handleTableChange
          }}
          scroll={{ x: 1200 }}
          size="middle"
        />
      </Card>
    </div>
  );
};

export default TxtImportRecords;