import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Table, Button, DatePicker, message, Spin, 
  Typography, Tag, Space, Modal, Empty, Input, Tooltip
} from 'antd';
import { 
  SearchOutlined, EyeOutlined, CalendarOutlined, 
  BarChartOutlined, ReloadOutlined, StockOutlined,
  TrophyOutlined, FireOutlined, RiseOutlined
} from '@ant-design/icons';
import { adminApiClient } from '../../../shared/admin-auth';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

interface ConceptSummary {
  concept_name: string;
  total_volume: number;
  stock_count: number;
  avg_volume: number;
  max_volume: number;
  trading_date: string;
  volume_percentage: number;
}

interface StockInfo {
  stock_code: string;
  stock_name: string;
  trading_volume: number;
  concept_rank: number;
  volume_percentage: number;
}

interface ConceptStocksResponse {
  concept_name: string;
  trading_date: string;
  total_volume: number;
  stock_count: number;
  total_stocks: number;
  stocks: StockInfo[];
  pagination: {
    offset: number;
    limit: number;
    total: number;
    has_more: boolean;
  };
}

const NewStockAnalysisPage: React.FC = () => {
  const [conceptSummaries, setConceptSummaries] = useState<ConceptSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [tradingDate, setTradingDate] = useState<string>('2025-09-02'); // 使用最新有数据的日期
  const [searchText, setSearchText] = useState('');
  
  // 股票列表弹窗相关状态
  const [stockModalVisible, setStockModalVisible] = useState(false);
  const [selectedConceptName, setSelectedConceptName] = useState<string>('');
  const [stockList, setStockList] = useState<StockInfo[]>([]);
  const [stockLoading, setStockLoading] = useState(false);
  const [conceptStockInfo, setConceptStockInfo] = useState<ConceptStocksResponse | null>(null);

  // 获取概念汇总列表
  const fetchConceptSummaries = async () => {
    setLoading(true);
    try {
      const response = await adminApiClient.get(
        `/api/v1/stock-analysis/concepts/daily-summary?trading_date=${tradingDate}&sort_by=total_volume&sort_order=desc&size=500`
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

  // 获取概念下的股票列表
  const fetchConceptStocks = async (conceptName: string) => {
    setStockLoading(true);
    try {
      const response = await adminApiClient.get(
        `/api/v1/stock-analysis/concept/${encodeURIComponent(conceptName)}/stocks?trading_date=${tradingDate}&limit=100`
      );
      
      if (response.data) {
        setConceptStockInfo(response.data);
        setStockList(response.data.stocks || []);
      } else {
        setStockList([]);
        setConceptStockInfo(null);
      }
    } catch (error) {
      console.error('获取概念股票失败:', error);
      message.error('获取概念股票失败');
      setStockList([]);
      setConceptStockInfo(null);
    } finally {
      setStockLoading(false);
    }
  };

  // 处理查看股票操作
  const handleViewStocks = async (conceptName: string) => {
    setSelectedConceptName(conceptName);
    setStockModalVisible(true);
    await fetchConceptStocks(conceptName);
  };

  // 处理日期变化
  const handleDateChange = (date: any, dateString: string) => {
    setTradingDate(dateString);
  };

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchText(value);
  };

  // 页面加载时获取数据
  useEffect(() => {
    fetchConceptSummaries();
  }, [tradingDate]);

  // 当搜索条件变化时重新过滤
  useEffect(() => {
    fetchConceptSummaries();
  }, [searchText]);

  // 概念汇总表格列定义
  const conceptColumns = [
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
      width: 200,
      render: (name: string) => (
        <div style={{ fontWeight: 'bold', color: '#1890ff' }}>
          <StockOutlined style={{ marginRight: 8 }} />
          {name}
        </div>
      ),
    },
    {
      title: '总交易量',
      dataIndex: 'total_volume',
      key: 'total_volume',
      width: 150,
      render: (volume: number) => (
        <Text strong style={{ color: '#f50' }}>
          {volume?.toLocaleString() || 'N/A'}
        </Text>
      ),
      sorter: (a: ConceptSummary, b: ConceptSummary) => a.total_volume - b.total_volume,
    },
    {
      title: '股票数量',
      dataIndex: 'stock_count',
      key: 'stock_count',
      width: 100,
      render: (count: number) => (
        <Tag color="green">{count || 0} 只</Tag>
      ),
      sorter: (a: ConceptSummary, b: ConceptSummary) => a.stock_count - b.stock_count,
    },
    {
      title: '平均交易量',
      dataIndex: 'avg_volume',
      key: 'avg_volume',
      width: 120,
      render: (avg: number) => (
        <Text>{avg?.toLocaleString() || 'N/A'}</Text>
      ),
    },
    {
      title: '市场占比',
      dataIndex: 'volume_percentage',
      key: 'volume_percentage',
      width: 100,
      render: (percentage: number) => (
        <Text style={{ color: '#1890ff' }}>
          {percentage ? `${percentage.toFixed(2)}%` : 'N/A'}
        </Text>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: ConceptSummary) => (
        <Space size="small">
          <Button 
            type="primary" 
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewStocks(record.concept_name)}
          >
            查看股票
          </Button>
        </Space>
      ),
    },
  ];

  // 股票列表表格列定义
  const stockColumns = [
    {
      title: '排名',
      dataIndex: 'concept_rank',
      key: 'concept_rank',
      width: 80,
      render: (rank: number) => (
        <div style={{ textAlign: 'center' }}>
          <Tag color={rank <= 3 ? 'red' : rank <= 10 ? 'orange' : 'blue'}>
            #{rank}
          </Tag>
        </div>
      ),
    },
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 120,
      render: (code: string) => (
        <Text code style={{ fontWeight: 'bold' }}>{code}</Text>
      ),
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      width: 150,
      render: (name: string) => (
        <Text strong style={{ color: '#1890ff' }}>{name || '未知'}</Text>
      ),
    },
    {
      title: '交易量',
      dataIndex: 'trading_volume',
      key: 'trading_volume',
      width: 150,
      render: (volume: number) => (
        <Text strong style={{ color: '#f50' }}>
          {volume?.toLocaleString() || 'N/A'}
        </Text>
      ),
      sorter: (a: StockInfo, b: StockInfo) => a.trading_volume - b.trading_volume,
    },
    {
      title: '概念占比',
      dataIndex: 'volume_percentage',
      key: 'volume_percentage',
      width: 100,
      render: (percentage: number) => (
        <Text style={{ color: '#52c41a' }}>
          {percentage ? `${percentage.toFixed(2)}%` : 'N/A'}
        </Text>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        <Card
          title={
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Space>
                <BarChartOutlined style={{ fontSize: '20px', color: '#1890ff' }} />
                <Title level={3} style={{ margin: 0 }}>股票分析 - 概念驱动视图</Title>
                <Tag color="blue">{tradingDate}</Tag>
              </Space>
              <Space>
                <Input.Search
                  placeholder="搜索概念名称..."
                  allowClear
                  style={{ width: 200 }}
                  onSearch={handleSearch}
                />
                <DatePicker
                  value={dayjs(tradingDate)}
                  onChange={handleDateChange}
                  format="YYYY-MM-DD"
                  allowClear={false}
                />
                <Button 
                  icon={<ReloadOutlined />} 
                  onClick={() => fetchConceptSummaries()}
                  loading={loading}
                >
                  刷新
                </Button>
              </Space>
            </div>
          }
          style={{ marginBottom: '24px' }}
        >
          <div style={{ marginBottom: '16px' }}>
            <Text type="secondary">
              显示 {tradingDate} 交易日的所有概念汇总信息，点击"查看股票"可查看概念下的具体股票排名
            </Text>
          </div>
          
          <Table
            columns={conceptColumns}
            dataSource={conceptSummaries}
            rowKey="concept_name"
            loading={loading}
            pagination={{
              total: conceptSummaries.length,
              pageSize: 20,
              showTotal: (total) => `共 ${total} 个概念`,
              showSizeChanger: true,
              showQuickJumper: true,
            }}
            scroll={{ x: 1000 }}
            locale={{
              emptyText: <Empty description="暂无概念数据" />
            }}
          />
        </Card>

        {/* 股票列表弹窗 */}
        <Modal
          title={
            <Space>
              <StockOutlined style={{ color: '#1890ff' }} />
              <span>概念股票列表 - {selectedConceptName}</span>
              {conceptStockInfo && (
                <Tag color="green">{conceptStockInfo.total_stocks} 只股票</Tag>
              )}
            </Space>
          }
          open={stockModalVisible}
          onCancel={() => setStockModalVisible(false)}
          width={1000}
          footer={null}
        >
          {conceptStockInfo && (
            <Card size="small" style={{ marginBottom: '16px' }}>
              <Row gutter={24}>
                <Col span={6}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '14px', color: '#666' }}>总交易量</div>
                    <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#f50' }}>
                      {conceptStockInfo.total_volume?.toLocaleString()}
                    </div>
                  </div>
                </Col>
                <Col span={6}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '14px', color: '#666' }}>股票数量</div>
                    <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#1890ff' }}>
                      {conceptStockInfo.stock_count} 只
                    </div>
                  </div>
                </Col>
                <Col span={6}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '14px', color: '#666' }}>平均交易量</div>
                    <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                      {((conceptStockInfo.total_volume || 0) / (conceptStockInfo.stock_count || 1)).toLocaleString()}
                    </div>
                  </div>
                </Col>
                <Col span={6}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '14px', color: '#666' }}>交易日期</div>
                    <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#52c41a' }}>
                      {conceptStockInfo.trading_date}
                    </div>
                  </div>
                </Col>
              </Row>
            </Card>
          )}
          
          <Table
            columns={stockColumns}
            dataSource={stockList}
            rowKey="stock_code"
            loading={stockLoading}
            pagination={{
              total: stockList.length,
              pageSize: 20,
              showTotal: (total) => `共 ${total} 只股票`,
              showSizeChanger: true,
            }}
            scroll={{ x: 800 }}
            locale={{
              emptyText: <Empty description="暂无股票数据" />
            }}
          />
        </Modal>
      </div>
    </div>
  );
};

export default NewStockAnalysisPage;