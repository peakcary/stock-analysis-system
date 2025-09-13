import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Table, Button, DatePicker, message, Spin, 
  Typography, Tag, Space, Empty, Input, Modal
} from 'antd';
import { 
  SearchOutlined, EyeOutlined, CalendarOutlined, 
  StockOutlined, ReloadOutlined, InfoCircleOutlined
} from '@ant-design/icons';
import { adminApiClient } from '../../../shared/admin-auth';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

interface StockSummary {
  stock_code: string;
  stock_name: string;
  trading_volume: number;
  concept_count: number;
  trading_date: string;
}

interface ConceptInfo {
  concept_name: string;
  trading_volume: number;
  concept_rank: number;
  concept_total_volume: number;
  volume_percentage: number;
  trading_date: string;
}

interface StockConceptsResponse {
  stock_code: string;
  stock_name: string;
  trading_date: string;
  total_trading_volume: number;
  concepts: ConceptInfo[];
}

const NewStockAnalysisPage: React.FC = () => {
  const [stockSummaries, setStockSummaries] = useState<StockSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [tradingDate, setTradingDate] = useState<string>(dayjs().format('YYYY-MM-DD'));
  const [searchText, setSearchText] = useState('');
  
  // 分页状态
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 50,
    total: 0
  });
  
  // 弹窗相关状态
  const [conceptModalVisible, setConceptModalVisible] = useState(false);
  const [selectedStockCode, setSelectedStockCode] = useState<string>('');
  const [selectedStockName, setSelectedStockName] = useState<string>('');
  const [conceptList, setConceptList] = useState<ConceptInfo[]>([]);
  const [conceptLoading, setConceptLoading] = useState(false);

  // 获取股票每日汇总 - 性能优化版
  const fetchStockSummaries = async (page: number = 1, pageSize: number = 50) => {
    setLoading(true);
    try {
      const searchParam = searchText.trim() ? `&search=${encodeURIComponent(searchText.trim())}` : '';
      const response = await adminApiClient.get(
        `/api/v1/stock-analysis/stocks/daily-summary?trading_date=${tradingDate}&page=${page}&size=${pageSize}&sort_by=trading_volume&sort_order=desc${searchParam}`
      );
      
      if (response.data?.summaries) {
        // 后端已经处理了搜索、排序和分页，直接使用返回的数据
        setStockSummaries(response.data.summaries);
        
        // 更新分页信息
        if (response.data.pagination) {
          setPagination({
            current: response.data.pagination.page,
            pageSize: response.data.pagination.size,
            total: response.data.pagination.total
          });
        }
      } else {
        setStockSummaries([]);
        setPagination({ current: 1, pageSize: 50, total: 0 });
      }
    } catch (error) {
      console.error('获取股票汇总失败:', error);
      message.error('获取股票汇总失败');
      setStockSummaries([]);
    } finally {
      setLoading(false);
    }
  };

  // 获取指定股票的概念信息
  const fetchConceptInfo = async (stockCode: string) => {
    if (!stockCode) return;
    
    setConceptLoading(true);
    try {
      const response = await adminApiClient.get(
        `/api/v1/stock-analysis/stock/${encodeURIComponent(stockCode)}/concepts?trading_date=${tradingDate}`
      );
      
      if (response.data?.concepts) {
        // 按概念总交易量排序（从高到低）
        const sortedConcepts = response.data.concepts.sort((a: ConceptInfo, b: ConceptInfo) => 
          b.concept_total_volume - a.concept_total_volume
        );
        setConceptList(sortedConcepts);
      } else {
        setConceptList([]);
        message.info('该股票暂无概念数据');
      }
    } catch (error) {
      console.error('获取概念信息失败:', error);
      message.error('获取概念信息失败');
      setConceptList([]);
    } finally {
      setConceptLoading(false);
    }
  };

  // 处理查看概念信息
  const handleViewConcepts = async (stockCode: string, stockName: string) => {
    setSelectedStockCode(stockCode);
    setSelectedStockName(stockName);
    setConceptModalVisible(true);
    await fetchConceptInfo(stockCode);
  };

  // 关闭弹窗
  const handleCloseModal = () => {
    setConceptModalVisible(false);
    setSelectedStockCode('');
    setSelectedStockName('');
    setConceptList([]);
  };

  // 数字格式化函数
  const formatNumber = (num: number): string => {
    if (num >= 100000000) {
      return `${(num / 100000000).toFixed(2)}亿`;
    } else if (num >= 10000) {
      return `${(num / 10000).toFixed(1)}万`;
    } else {
      return num.toLocaleString();
    }
  };

  // 处理分页变化
  const handlePageChange = (page: number, pageSize?: number) => {
    fetchStockSummaries(page, pageSize || pagination.pageSize);
  };

  // 处理搜索
  const handleSearch = () => {
    // 搜索时重置到第一页
    setPagination(prev => ({ ...prev, current: 1 }));
    fetchStockSummaries(1, pagination.pageSize);
  };

  // 页面加载时获取数据
  useEffect(() => {
    fetchStockSummaries(1, pagination.pageSize);
  }, [tradingDate]);

  // 搜索防抖处理
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchText !== '') {
        handleSearch();
      } else if (searchText === '') {
        // 清空搜索时重新加载
        fetchStockSummaries(1, pagination.pageSize);
      }
    }, 500); // 500ms防抖

    return () => clearTimeout(timer);
  }, [searchText]);

  // 股票汇总表格列定义
  const summaryColumns = [
    {
      title: '排名',
      key: 'index',
      width: 80,
      render: (_: any, __: any, index: number) => (
        <div style={{ textAlign: 'center' }}>
          <Tag color={index < 3 ? 'red' : index < 10 ? 'orange' : 'blue'}>
            #{index + 1}
          </Tag>
        </div>
      ),
    },
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
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      render: (name: string) => (
        <Text strong>{name}</Text>
      ),
    },
    {
      title: '交易日期',
      dataIndex: 'trading_date',
      key: 'trading_date',
      width: 120,
      render: (date: string) => (
        <Text>{date}</Text>
      ),
    },
    {
      title: '交易量',
      dataIndex: 'trading_volume',
      key: 'trading_volume',
      width: 140,
      sorter: (a: StockSummary, b: StockSummary) => a.trading_volume - b.trading_volume,
      render: (volume: number) => (
        <Text strong style={{ color: '#52c41a' }}>
          {formatNumber(volume)}
        </Text>
      ),
    },
    {
      title: '概念数量',
      dataIndex: 'concept_count',
      key: 'concept_count',
      width: 100,
      render: (count: number) => (
        <Tag color="blue">{count}个</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: StockSummary) => (
        <Button
          type="primary"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => handleViewConcepts(record.stock_code, record.stock_name)}
        >
          查看概念
        </Button>
      ),
    },
  ];

  // 概念信息表格列定义
  const conceptColumns = [
    {
      title: '排名',
      dataIndex: 'concept_rank',
      key: 'concept_rank',
      width: 80,
      render: (rank: number) => (
        <Tag color={rank <= 3 ? 'red' : rank <= 10 ? 'orange' : 'blue'}>
          #{rank}
        </Tag>
      ),
    },
    {
      title: '概念名称',
      dataIndex: 'concept_name',
      key: 'concept_name',
      render: (name: string) => (
        <Text strong style={{ color: '#1890ff' }}>{name}</Text>
      ),
    },
    {
      title: '交易量',
      dataIndex: 'trading_volume',
      key: 'trading_volume',
      sorter: (a: ConceptInfo, b: ConceptInfo) => a.trading_volume - b.trading_volume,
      render: (volume: number) => (
        <Text strong style={{ color: '#52c41a' }}>
          {formatNumber(volume)}
        </Text>
      ),
    },
    {
      title: '概念总量',
      dataIndex: 'concept_total_volume',
      key: 'concept_total_volume',
      render: (volume: number) => (
        <Text style={{ color: '#8c8c8c' }}>
          {formatNumber(volume)}
        </Text>
      ),
    },
    {
      title: '占比',
      dataIndex: 'volume_percentage',
      key: 'volume_percentage',
      width: 100,
      render: (percentage: number) => (
        <Text>{percentage ? `${percentage.toFixed(2)}%` : '0%'}</Text>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题 */}
      <Card style={{ marginBottom: '24px', borderRadius: '12px' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <Title level={2} style={{ margin: '0 0 8px 0', color: '#1f2937' }}>
            <StockOutlined style={{ marginRight: '8px', color: '#3b82f6' }} />
            个股列表分析
          </Title>
          <Text type="secondary">
            展示选择日期的所有股票及其交易量和概念信息
          </Text>
        </div>

        {/* 控制面板 */}
        <Row gutter={16} align="middle" justify="center">
          <Col xs={24} sm={8} md={6}>
            <div style={{ marginBottom: '8px' }}>
              <Text strong>交易日期:</Text>
            </div>
            <DatePicker
              value={dayjs(tradingDate)}
              onChange={(date) => setTradingDate(date ? date.format('YYYY-MM-DD') : dayjs().format('YYYY-MM-DD'))}
              format="YYYY-MM-DD"
              placeholder="选择日期"
              style={{ width: '100%' }}
              suffixIcon={<CalendarOutlined />}
            />
          </Col>
          <Col xs={24} sm={8} md={6}>
            <div style={{ marginBottom: '8px' }}>
              <Text strong>股票搜索:</Text>
            </div>
            <Input
              placeholder="输入股票代码或名称"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              prefix={<SearchOutlined />}
              allowClear
            />
          </Col>
          <Col xs={24} sm={4} md={3}>
            <div style={{ marginBottom: '8px' }}>
              <Text strong>&nbsp;</Text>
            </div>
            <Button 
              type="primary" 
              icon={<ReloadOutlined />}
              onClick={() => fetchStockSummaries(pagination.current, pagination.pageSize)}
              loading={loading}
              style={{ width: '100%' }}
            >
              刷新数据
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 股票列表 */}
      <Card 
        title={
          <Space>
            <StockOutlined style={{ color: '#1890ff' }} />
            <span>股票每日汇总</span>
            <Tag color="blue">{stockSummaries.length}只股票</Tag>
            <Tag color="green">{tradingDate}</Tag>
          </Space>
        }
        style={{ borderRadius: '12px' }}
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px' }}>
            <Spin size="large" tip="正在加载股票数据..." />
          </div>
        ) : stockSummaries.length > 0 ? (
          <Table
            columns={summaryColumns}
            dataSource={stockSummaries}
            rowKey="stock_code"
            loading={loading}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: pagination.total,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 只股票`,
              pageSizeOptions: ['20', '50', '100'],
              onChange: handlePageChange,
              onShowSizeChange: handlePageChange,
            }}
            scroll={{ x: 800 }}
            size="middle"
          />
        ) : (
          <Empty
            description={
              <div>
                <Text type="secondary">
                  {tradingDate} 暂无股票汇总数据
                </Text>
                <br />
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  请确保已导入TXT文件数据，或尝试选择其他日期
                </Text>
              </div>
            }
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Card>

      {/* 概念信息弹窗 */}
      <Modal
        title={
          <Space>
            <EyeOutlined style={{ color: '#1890ff' }} />
            <span>{selectedStockName} ({selectedStockCode}) - 概念信息</span>
            <Tag color="blue">{conceptList.length}个概念</Tag>
          </Space>
        }
        open={conceptModalVisible}
        onCancel={handleCloseModal}
        footer={[
          <Button key="close" onClick={handleCloseModal}>
            关闭
          </Button>
        ]}
        width={900}
        style={{ top: 20 }}
      >
        {conceptLoading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" tip="正在加载概念信息..." />
          </div>
        ) : conceptList.length > 0 ? (
          <Table
            columns={conceptColumns}
            dataSource={conceptList}
            rowKey="concept_name"
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 个概念`,
            }}
            scroll={{ x: 700 }}
            size="small"
          />
        ) : (
          <Empty
            description={`${selectedStockName} 暂无概念数据`}
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Modal>
    </div>
  );
};

export default NewStockAnalysisPage;