import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Table, Button, DatePicker, message, Spin, 
  Typography, Tag, Space, Empty, Statistic, Progress, Input, Select, Divider
} from 'antd';
import { 
  SearchOutlined, FireOutlined, TrophyOutlined, 
  CalendarOutlined, InfoCircleOutlined, BarChartOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { adminApiClient } from '../../../shared/admin-auth';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

interface ConceptSummary {
  concept_name: string;
  total_volume: number;
  stock_count: number;
  trading_date: string;
  avg_volume: number;
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
  const [conceptRankings, setConceptRankings] = useState<ConceptRanking[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedConcept, setSelectedConcept] = useState<string>('');
  const [tradingDate, setTradingDate] = useState<string>(dayjs().format('YYYY-MM-DD'));
  const [searchText, setSearchText] = useState('');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');
  const [recalculating, setRecalculating] = useState(false);

  // 获取概念每日汇总
  const fetchConceptSummaries = async () => {
    setLoading(true);
    try {
      const response = await adminApiClient.get(`/api/v1/stock-analysis/concepts/daily-summary?trading_date=${tradingDate}`);
      
      if (response.data?.summaries) {
        let summaries = response.data.summaries;
        
        // 按总交易量排序
        summaries = summaries.sort((a: ConceptSummary, b: ConceptSummary) => {
          return sortOrder === 'desc' 
            ? b.total_volume - a.total_volume
            : a.total_volume - b.total_volume;
        });
        
        // 搜索过滤
        if (searchText.trim()) {
          summaries = summaries.filter((item: ConceptSummary) =>
            item.concept_name.toLowerCase().includes(searchText.toLowerCase())
          );
        }
        
        setConceptSummaries(summaries);
        message.success(`获取到 ${summaries.length} 个概念的每日汇总数据`);
      } else {
        setConceptSummaries([]);
        message.info('该日期暂无概念汇总数据');
      }
    } catch (error) {
      console.error('获取概念汇总失败:', error);
      message.error('获取概念汇总失败，请检查网络连接');
      setConceptSummaries([]);
    } finally {
      setLoading(false);
    }
  };

  // 获取指定概念的个股排名
  const fetchConceptRankings = async (conceptName: string) => {
    if (!conceptName) return;
    
    setLoading(true);
    try {
      const response = await adminApiClient.get(
        `/api/v1/stock-analysis/concepts/${encodeURIComponent(conceptName)}/rankings?trading_date=${tradingDate}`
      );
      
      if (response.data?.rankings) {
        setConceptRankings(response.data.rankings);
        message.success(`获取到 ${response.data.rankings.length} 只股票的排名数据`);
      } else {
        setConceptRankings([]);
        message.info('该概念暂无股票排名数据');
      }
    } catch (error) {
      console.error('获取概念排名失败:', error);
      message.error('获取概念排名失败，请检查网络连接');
      setConceptRankings([]);
    } finally {
      setLoading(false);
    }
  };

  // 重新计算指定日期的数据
  const handleRecalculate = async () => {
    setRecalculating(true);
    try {
      const response = await adminApiClient.post(`/api/v1/txt-import/recalculate?trading_date=${tradingDate}`);
      
      if (response.data?.success) {
        const stats = response.data.stats;
        message.success(
          `重新计算完成！概念汇总: ${stats.concept_summary_count}个，个股排名: ${stats.ranking_count}条，创新高: ${stats.new_high_count}条`
        );
        
        // 重新获取数据
        await fetchConceptSummaries();
        if (selectedConcept) {
          await fetchConceptRankings(selectedConcept);
        }
      } else {
        message.error(response.data?.message || '重新计算失败');
      }
    } catch (error: any) {
      console.error('重新计算失败:', error);
      message.error(`重新计算失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setRecalculating(false);
    }
  };

  // 页面加载时获取数据
  useEffect(() => {
    fetchConceptSummaries();
  }, [tradingDate, searchText, sortOrder]);

  // 当选择概念时获取排名数据
  useEffect(() => {
    if (selectedConcept) {
      fetchConceptRankings(selectedConcept);
    } else {
      setConceptRankings([]);
    }
  }, [selectedConcept, tradingDate]);

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
        <Button 
          type="link" 
          onClick={() => setSelectedConcept(name)}
          style={{ padding: 0, fontWeight: 'bold' }}
        >
          {name}
        </Button>
      ),
    },
    {
      title: '总交易量',
      dataIndex: 'total_volume',
      key: 'total_volume',
      render: (volume: number) => (
        <Text strong style={{ color: '#1890ff' }}>
          {volume ? volume.toLocaleString() : 0}
        </Text>
      ),
    },
    {
      title: '股票数量',
      dataIndex: 'stock_count',
      key: 'stock_count',
      render: (count: number) => (
        <Text>{count}只</Text>
      ),
    },
    {
      title: '平均交易量',
      dataIndex: 'avg_volume',
      key: 'avg_volume',
      render: (avg: number) => (
        <Text type="secondary">
          {avg ? avg.toLocaleString() : 0}
        </Text>
      ),
    },
  ];

  // 个股排名表格列定义
  const rankingColumns = [
    {
      title: '排名',
      dataIndex: 'concept_rank',
      key: 'concept_rank',
      width: 80,
      render: (rank: number) => (
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            background: rank <= 3 ? '#f59e0b' : rank <= 10 ? '#10b981' : '#6b7280',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '12px',
            fontWeight: '600',
            margin: '0 auto'
          }}>
            {rank}
          </div>
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
      ellipsis: true,
      render: (name: string) => (
        <Text strong>{name}</Text>
      ),
    },
    {
      title: '交易量',
      dataIndex: 'trading_volume',
      key: 'trading_volume',
      render: (volume: number) => (
        <Text style={{ fontWeight: '600' }}>
          {volume ? volume.toLocaleString() : 0}
        </Text>
      ),
    },
    {
      title: '占比',
      dataIndex: 'volume_percentage',
      key: 'volume_percentage',
      width: 120,
      render: (percentage: number) => (
        <div>
          <Text>{percentage ? percentage.toFixed(2) : 0}%</Text>
          <Progress
            percent={Math.min(percentage || 0, 100)}
            size="small"
            showInfo={false}
            strokeColor={percentage > 10 ? '#ff4d4f' : percentage > 5 ? '#faad14' : '#52c41a'}
          />
        </div>
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
            展示TXT文件导入后的概念每日总和与个股排名数据
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
          <Col xs={24} sm={8} md={6}>
            <div style={{ marginBottom: '8px' }}>
              <Text strong>排序方式:</Text>
            </div>
            <Select
              value={sortOrder}
              onChange={(value) => setSortOrder(value)}
              style={{ width: '100%' }}
            >
              <Option value="desc">交易量 从高到低</Option>
              <Option value="asc">交易量 从低到高</Option>
            </Select>
          </Col>
          <Col xs={24} sm={4} md={3}>
            <div style={{ marginBottom: '8px' }}>
              <Text strong>&nbsp;</Text>
            </div>
            <Button 
              type="primary" 
              icon={<SearchOutlined />}
              onClick={fetchConceptSummaries}
              loading={loading}
              style={{ width: '100%' }}
            >
              刷新数据
            </Button>
          </Col>
          <Col xs={24} sm={4} md={3}>
            <div style={{ marginBottom: '8px' }}>
              <Text strong>&nbsp;</Text>
            </div>
            <Button 
              icon={<ReloadOutlined />}
              onClick={handleRecalculate}
              loading={recalculating}
              style={{ width: '100%' }}
              title="重新计算当前日期的概念汇总和排名数据"
            >
              重新计算
            </Button>
          </Col>
        </Row>
      </Card>

      <Row gutter={16}>
        {/* 概念每日汇总 */}
        <Col xs={24} lg={selectedConcept ? 12 : 24}>
          <Card 
            title={
              <Space>
                <FireOutlined style={{ color: '#ff4d4f' }} />
                <span>概念每日汇总</span>
                <Tag color="blue">{conceptSummaries.length}个概念</Tag>
                <Tag color="green">{tradingDate}</Tag>
              </Space>
            }
            extra={
              conceptSummaries.length > 0 && (
                <Space>
                  <Text type="secondary">
                    <InfoCircleOutlined style={{ marginRight: 4 }} />
                    点击概念名称查看个股排名
                  </Text>
                </Space>
              )
            }
            style={{ marginBottom: '24px', borderRadius: '12px' }}
          >
            {loading && !selectedConcept ? (
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
        </Col>

        {/* 个股排名详情 */}
        {selectedConcept && (
          <Col xs={24} lg={12}>
            <Card 
              title={
                <Space>
                  <TrophyOutlined style={{ color: '#f59e0b' }} />
                  <span>{selectedConcept} - 个股排名</span>
                  <Tag color="orange">{conceptRankings.length}只股票</Tag>
                </Space>
              }
              extra={
                <Button 
                  size="small" 
                  onClick={() => setSelectedConcept('')}
                  type="text"
                >
                  关闭
                </Button>
              }
              style={{ marginBottom: '24px', borderRadius: '12px' }}
            >
              {loading ? (
                <div style={{ textAlign: 'center', padding: '60px' }}>
                  <Spin size="large" tip="正在加载个股排名..." />
                </div>
              ) : conceptRankings.length > 0 ? (
                <Table
                  columns={rankingColumns}
                  dataSource={conceptRankings}
                  rowKey={(record) => `${record.stock_code}_${record.concept_name}`}
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
                  description={`${selectedConcept} 暂无个股排名数据`}
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              )}
            </Card>

            {/* 统计信息 */}
            {conceptRankings.length > 0 && (
              <Card title="排名统计" style={{ borderRadius: '12px' }}>
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="前三名数量"
                      value={conceptRankings.filter(item => item.concept_rank <= 3).length}
                      suffix="只"
                      valueStyle={{ color: '#f59e0b' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="前十名数量"
                      value={conceptRankings.filter(item => item.concept_rank <= 10).length}
                      suffix="只"
                      valueStyle={{ color: '#10b981' }}
                    />
                  </Col>
                </Row>
                <Divider />
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="总交易量"
                      value={conceptRankings.reduce((sum, item) => sum + item.trading_volume, 0)}
                      formatter={(value) => Number(value).toLocaleString()}
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="平均交易量"
                      value={conceptRankings.length > 0 
                        ? conceptRankings.reduce((sum, item) => sum + item.trading_volume, 0) / conceptRankings.length 
                        : 0
                      }
                      formatter={(value) => Number(value).toLocaleString()}
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Col>
                </Row>
              </Card>
            )}
          </Col>
        )}
      </Row>
    </div>
  );
};

export default ConceptAnalysisPage;