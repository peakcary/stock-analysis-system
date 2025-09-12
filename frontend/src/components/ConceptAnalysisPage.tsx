import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Table, Button, DatePicker, message, Spin, 
  Typography, Tag, Space, Empty, Input, Modal
} from 'antd';
import { 
  SearchOutlined, EyeOutlined, CalendarOutlined, 
  BarChartOutlined, ReloadOutlined, InfoCircleOutlined
} from '@ant-design/icons';
import { adminApiClient } from '../../../shared/admin-auth';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

interface ConceptSummary {
  concept_name: string;
  total_volume: number;
  stock_count: number;
  trading_date: string;
}

interface StockInfo {
  stock_code: string;
  stock_name: string;
  trading_volume: number;
  concept_rank: number;
  volume_percentage: number;
}

interface ConceptInfo {
  total_volume: number;
  stock_count: number;
  avg_volume: number;
  max_volume: number;
}

interface ConceptRankingResponse {
  concept_name: string;
  trading_date: string;
  concept_info: ConceptInfo;
  rankings: ConceptRanking[];
  pagination: {
    page: number;
    size: number;
    total: number;
    pages: number;
  };
}

interface ConceptRanking {
  stock_code: string;
  stock_name: string;
  concept_name: string;
  trading_volume: number;
  concept_rank: number;
  volume_percentage: number;
  trading_date: string;
}

const ConceptAnalysisPage: React.FC = () => {
  const [conceptSummaries, setConceptSummaries] = useState<ConceptSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [tradingDate, setTradingDate] = useState<string>(dayjs().format('YYYY-MM-DD'));
  const [searchText, setSearchText] = useState('');
  
  // 弹窗相关状态
  const [stockModalVisible, setStockModalVisible] = useState(false);
  const [selectedConceptName, setSelectedConceptName] = useState<string>('');
  const [stockList, setStockList] = useState<StockInfo[]>([]);
  const [stockLoading, setStockLoading] = useState(false);

  // 获取概念每日汇总
  const fetchConceptSummaries = async () => {
    setLoading(true);
    try {
      const response = await adminApiClient.get(
        `/api/v1/stock-analysis/concepts/daily-summary?trading_date=${tradingDate}&sort_by=total_volume&sort_order=desc&size=1000`
      );
      
      if (response.data?.summaries) {
        let summaries = response.data.summaries;
        
        // 搜索过滤
        if (searchText.trim()) {
          summaries = summaries.filter((item: ConceptSummary) =>
            item.concept_name.toLowerCase().includes(searchText.toLowerCase())
          );
        }
        
        // 按总交易量排序
        summaries = summaries.sort((a: ConceptSummary, b: ConceptSummary) => 
          b.total_volume - a.total_volume
        );
        
        setConceptSummaries(summaries);
      } else {
        setConceptSummaries([]);
      }
    } catch (error) {
      console.error('获取概念汇总失败:', error);
      message.error('获取概念汇总失败');
      setConceptSummaries([]);
    } finally {
      setLoading(false);
    }
  };

  // 获取指定概念的股票信息
  const fetchStockInfo = async (conceptName: string) => {
    if (!conceptName) return;
    
    setStockLoading(true);
    try {
      // 使用较大的页面大小来获取所有数据，避免分页问题
      const response = await adminApiClient.get(
        `/api/v1/stock-analysis/concepts/${encodeURIComponent(conceptName)}/rankings?trading_date=${tradingDate}&page=1&size=10000`
      );
      
      if (response.data?.rankings) {
        setStockList(response.data.rankings);
      } else {
        setStockList([]);
        message.info('该概念暂无股票数据');
      }
    } catch (error) {
      console.error('获取股票信息失败:', error);
      message.error('获取股票信息失败');
      setStockList([]);
    } finally {
      setStockLoading(false);
    }
  };

  // 处理查看股票信息
  const handleViewStocks = async (conceptName: string) => {
    setSelectedConceptName(conceptName);
    setStockModalVisible(true);
    await fetchStockInfo(conceptName);
  };

  // 关闭弹窗
  const handleCloseModal = () => {
    setStockModalVisible(false);
    setSelectedConceptName('');
    setStockList([]);
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

  // 页面加载时获取数据
  useEffect(() => {
    fetchConceptSummaries();
  }, [tradingDate]);

  // 概念汇总表格列定义
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
      title: '概念名称',
      dataIndex: 'concept_name',
      key: 'concept_name',
      render: (name: string) => (
        <Text strong style={{ color: '#1890ff' }}>{name}</Text>
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
      title: '概念总交易量',
      dataIndex: 'total_volume',
      key: 'total_volume',
      width: 140,
      sorter: (a: ConceptSummary, b: ConceptSummary) => a.total_volume - b.total_volume,
      render: (volume: number) => (
        <Text strong style={{ color: '#52c41a' }}>
          {formatNumber(volume)}
        </Text>
      ),
    },
    {
      title: '股票数量',
      dataIndex: 'stock_count',
      key: 'stock_count',
      width: 100,
      render: (count: number) => (
        <Tag color="blue">{count}只</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: ConceptSummary) => (
        <Button
          type="primary"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => handleViewStocks(record.concept_name)}
        >
          查看股票
        </Button>
      ),
    },
  ];

  // 股票信息表格列定义
  const stockColumns = [
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
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 100,
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
      title: '交易量',
      dataIndex: 'trading_volume',
      key: 'trading_volume',
      sorter: (a: StockInfo, b: StockInfo) => a.trading_volume - b.trading_volume,
      render: (volume: number) => (
        <Text strong style={{ color: '#1890ff' }}>
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
            <BarChartOutlined style={{ marginRight: '8px', color: '#3b82f6' }} />
            概念分析
          </Title>
          <Text type="secondary">
            展示选择日期的所有概念及其总交易量
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
              <Text strong>概念搜索:</Text>
            </div>
            <Input
              placeholder="输入概念名称"
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
              onClick={fetchConceptSummaries}
              loading={loading}
              style={{ width: '100%' }}
            >
              刷新数据
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 概念列表 */}
      <Card 
        title={
          <Space>
            <BarChartOutlined style={{ color: '#1890ff' }} />
            <span>概念每日汇总</span>
            <Tag color="blue">{conceptSummaries.length}个概念</Tag>
            <Tag color="green">{tradingDate}</Tag>
          </Space>
        }
        style={{ borderRadius: '12px' }}
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px' }}>
            <Spin size="large" tip="正在加载概念数据..." />
          </div>
        ) : conceptSummaries.length > 0 ? (
          <Table
            columns={summaryColumns}
            dataSource={conceptSummaries}
            rowKey="concept_name"
            pagination={{
              pageSize: 15,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 个概念`,
            }}
            scroll={{ x: 800 }}
            size="middle"
          />
        ) : (
          <Empty
            description={
              <div>
                <Text type="secondary">
                  {tradingDate} 暂无概念汇总数据
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

      {/* 股票信息弹窗 */}
      <Modal
        title={
          <Space>
            <EyeOutlined style={{ color: '#1890ff' }} />
            <span>{selectedConceptName} - 股票信息</span>
            <Tag color="blue">{stockList.length}只股票</Tag>
          </Space>
        }
        open={stockModalVisible}
        onCancel={handleCloseModal}
        footer={[
          <Button key="close" onClick={handleCloseModal}>
            关闭
          </Button>
        ]}
        width={800}
        style={{ top: 20 }}
      >
        {stockLoading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" tip="正在加载股票信息..." />
          </div>
        ) : stockList.length > 0 ? (
          <Table
            columns={stockColumns}
            dataSource={stockList}
            rowKey="stock_code"
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 只股票`,
            }}
            scroll={{ x: 600 }}
            size="small"
          />
        ) : (
          <Empty
            description={`${selectedConceptName} 暂无股票数据`}
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Modal>
    </div>
  );
};

export default ConceptAnalysisPage;