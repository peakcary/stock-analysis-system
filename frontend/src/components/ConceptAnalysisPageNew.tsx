import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Table, Button, DatePicker, message, Spin, 
  Typography, Tag, Space, Empty, Statistic, Input, Select, Divider,
  Collapse, Alert, Progress
} from 'antd';
import { 
  SearchOutlined, FireOutlined, TrophyOutlined, 
  CalendarOutlined, InfoCircleOutlined, BarChartOutlined,
  ReloadOutlined, CaretRightOutlined, CaretDownOutlined,
  StockOutlined, DollarOutlined
} from '@ant-design/icons';
import { adminApiClient } from '../../../shared/admin-auth';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;
const { Panel } = Collapse;

interface ConceptSummary {
  concept_name: string;
  total_volume: number;
  stock_count: number;
  trading_date: string;
  avg_volume: number;
  max_volume: number;
  volume_percentage: number;
}

interface ConceptRanking {
  stock_code: string;
  stock_name: string;
  concept_name: string;
  trading_volume: number;
  concept_rank: number;
  volume_percentage: number;
  trading_date: string;
  concept_total_volume: number;
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

const ConceptAnalysisPage: React.FC = () => {
  const [conceptSummaries, setConceptSummaries] = useState<ConceptSummary[]>([]);
  const [conceptRankings, setConceptRankings] = useState<{[key: string]: ConceptRankingResponse}>({});
  const [loading, setLoading] = useState(false);
  const [loadingRankings, setLoadingRankings] = useState<{[key: string]: boolean}>({});
  const [tradingDate, setTradingDate] = useState<string>(dayjs().format('YYYY-MM-DD'));
  const [searchText, setSearchText] = useState('');
  const [sortBy, setSortBy] = useState<string>('total_volume');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');
  const [pagination, setPagination] = useState({ page: 1, size: 50 });
  const [statistics, setStatistics] = useState<any>(null);

  // 获取概念每日汇总
  const fetchConceptSummaries = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        trading_date: tradingDate,
        page: pagination.page.toString(),
        size: pagination.size.toString(),
        sort_by: sortBy,
        sort_order: sortOrder,
        ...(searchText && { search: searchText })
      });
      
      const response = await adminApiClient.get(`/api/v1/stock-analysis/concepts/daily-summary?${params}`);
      
      if (response.data.summaries && response.data.summaries.length > 0) {
        setConceptSummaries(response.data.summaries);
        setStatistics(response.data.statistics);
      } else {
        setConceptSummaries([]);
        setStatistics(null);
        message.info('该日期暂无概念数据');
      }
    } catch (error: any) {
      message.error('获取概念汇总失败: ' + error.message);
      setConceptSummaries([]);
    } finally {
      setLoading(false);
    }
  };

  // 获取指定概念的股票排名
  const fetchConceptRankings = async (conceptName: string) => {
    setLoadingRankings(prev => ({ ...prev, [conceptName]: true }));
    try {
      const response = await adminApiClient.get(
        `/api/v1/stock-analysis/concepts/${encodeURIComponent(conceptName)}/rankings?trading_date=${tradingDate}&page=1&size=20`
      );
      
      if (response.data) {
        setConceptRankings(prev => ({ ...prev, [conceptName]: response.data }));
      }
    } catch (error: any) {
      message.error(`获取概念 ${conceptName} 股票排名失败: ` + error.message);
    } finally {
      setLoadingRankings(prev => ({ ...prev, [conceptName]: false }));
    }
  };

  useEffect(() => {
    fetchConceptSummaries();
  }, [tradingDate, sortBy, sortOrder, searchText, pagination]);

  // 格式化数字
  const formatNumber = (num: number) => {
    if (num >= 100000000) {
      return (num / 100000000).toFixed(1) + '亿';
    } else if (num >= 10000) {
      return (num / 10000).toFixed(1) + '万';
    }
    return num.toLocaleString();
  };

  // 概念卡片组件
  const ConceptCard: React.FC<{ concept: ConceptSummary }> = ({ concept }) => {
    const isExpanded = conceptRankings[concept.concept_name];
    const isLoading = loadingRankings[concept.concept_name];

    return (
      <Card 
        hoverable
        className="concept-card"
        style={{ marginBottom: 16 }}
        bodyStyle={{ padding: '16px' }}
        actions={[
          <Button 
            type="link" 
            loading={isLoading}
            onClick={() => fetchConceptRankings(concept.concept_name)}
            icon={<StockOutlined />}
          >
            查看股票排名
          </Button>
        ]}
      >
        <Row gutter={16} align="middle">
          <Col span={8}>
            <div>
              <Title level={5} style={{ margin: 0, color: '#1890ff' }}>
                {concept.concept_name}
              </Title>
              <Text type="secondary">{concept.trading_date}</Text>
            </div>
          </Col>
          
          <Col span={4}>
            <Statistic
              title="总交易量"
              value={concept.total_volume}
              formatter={(value) => formatNumber(Number(value))}
              valueStyle={{ color: '#cf1322' }}
              prefix={<DollarOutlined />}
            />
          </Col>
          
          <Col span={3}>
            <Statistic
              title="股票数量"
              value={concept.stock_count}
              suffix="只"
              valueStyle={{ color: '#722ed1' }}
            />
          </Col>
          
          <Col span={4}>
            <Statistic
              title="平均交易量"
              value={concept.avg_volume}
              formatter={(value) => formatNumber(Number(value))}
              valueStyle={{ color: '#13c2c2' }}
            />
          </Col>
          
          <Col span={4}>
            <div>
              <Text strong>占比</Text>
              <div>
                <Progress 
                  percent={concept.volume_percentage} 
                  size="small" 
                  showInfo={false} 
                  strokeColor="#52c41a"
                />
                <Text type="secondary">{concept.volume_percentage}%</Text>
              </div>
            </div>
          </Col>
        </Row>

        {/* 展开的股票排名 */}
        {isExpanded && (
          <div style={{ marginTop: 16, borderTop: '1px solid #f0f0f0', paddingTop: 16 }}>
            <Title level={5}>
              <TrophyOutlined style={{ color: '#faad14' }} /> 股票排名 TOP 20
            </Title>
            
            <Row gutter={[8, 8]} style={{ marginBottom: 12 }}>
              <Col span={6}>
                <Statistic size="small" title="概念总量" value={formatNumber(isExpanded.concept_info.total_volume)} />
              </Col>
              <Col span={6}>
                <Statistic size="small" title="股票总数" value={isExpanded.concept_info.stock_count} suffix="只" />
              </Col>
              <Col span={6}>
                <Statistic size="small" title="平均交易量" value={formatNumber(isExpanded.concept_info.avg_volume)} />
              </Col>
              <Col span={6}>
                <Statistic size="small" title="最大交易量" value={formatNumber(isExpanded.concept_info.max_volume)} />
              </Col>
            </Row>

            <Table
              dataSource={isExpanded.rankings}
              rowKey="stock_code"
              pagination={false}
              size="small"
              columns={[
                {
                  title: '排名',
                  dataIndex: 'concept_rank',
                  key: 'rank',
                  width: 60,
                  render: (rank: number) => (
                    <Tag color={rank <= 3 ? 'gold' : rank <= 10 ? 'blue' : 'default'}>
                      #{rank}
                    </Tag>
                  )
                },
                {
                  title: '股票代码',
                  dataIndex: 'stock_code',
                  key: 'code',
                  width: 100
                },
                {
                  title: '股票名称',
                  dataIndex: 'stock_name',
                  key: 'name',
                  ellipsis: true
                },
                {
                  title: '交易量',
                  dataIndex: 'trading_volume',
                  key: 'volume',
                  render: (volume: number) => formatNumber(volume),
                  sorter: (a, b) => a.trading_volume - b.trading_volume
                },
                {
                  title: '占概念比例',
                  dataIndex: 'volume_percentage',
                  key: 'percentage',
                  render: (percentage: number) => `${percentage}%`,
                  sorter: (a, b) => a.volume_percentage - b.volume_percentage
                }
              ]}
            />
          </div>
        )}
      </Card>
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
          <Col>
            <Title level={2} style={{ margin: 0 }}>
              <BarChartOutlined style={{ color: '#1890ff' }} /> 概念分析
            </Title>
            <Text type="secondary">按日期查看概念交易量汇总和股票排名</Text>
          </Col>
          <Col>
            <Space>
              <DatePicker
                value={dayjs(tradingDate)}
                onChange={(date) => date && setTradingDate(date.format('YYYY-MM-DD'))}
                format="YYYY-MM-DD"
                placeholder="选择交易日期"
              />
              <Button icon={<ReloadOutlined />} onClick={fetchConceptSummaries}>
                刷新
              </Button>
            </Space>
          </Col>
        </Row>

        {/* 统计信息 */}
        {statistics && (
          <Alert
            message={
              <Row gutter={32}>
                <Col span={6}>
                  <Statistic title="概念总数" value={statistics.total_concepts} suffix="个" />
                </Col>
                <Col span={6}>
                  <Statistic title="当前页交易量" value={formatNumber(statistics.current_page_volume)} />
                </Col>
                <Col span={6}>
                  <Statistic title="当前页股票数" value={statistics.current_page_stocks} suffix="只" />
                </Col>
                <Col span={6}>
                  <Statistic title="平均每概念" value={formatNumber(statistics.avg_volume_per_concept)} />
                </Col>
              </Row>
            }
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {/* 搜索和排序 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={8}>
            <Input
              placeholder="搜索概念名称..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear
            />
          </Col>
          <Col span={4}>
            <Select
              value={sortBy}
              onChange={setSortBy}
              style={{ width: '100%' }}
              placeholder="排序字段"
            >
              <Option value="total_volume">总交易量</Option>
              <Option value="stock_count">股票数量</Option>
              <Option value="avg_volume">平均交易量</Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select
              value={sortOrder}
              onChange={setSortOrder}
              style={{ width: '100%' }}
              placeholder="排序方向"
            >
              <Option value="desc">降序</Option>
              <Option value="asc">升序</Option>
            </Select>
          </Col>
        </Row>

        {/* 概念列表 */}
        <Spin spinning={loading}>
          {conceptSummaries.length > 0 ? (
            <div>
              {conceptSummaries.map((concept) => (
                <ConceptCard key={concept.concept_name} concept={concept} />
              ))}
            </div>
          ) : (
            <Empty description="暂无概念数据" />
          )}
        </Spin>
      </Card>
    </div>
  );
};

export default ConceptAnalysisPage;