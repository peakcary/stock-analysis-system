import React, { useState, useEffect } from 'react';
import {
  Card,
  Input,
  Button,
  List,
  Typography,
  Space,
  message,
  Spin,
  Row,
  Col,
  Collapse,
  Table,
  Tag,
  DatePicker,
  InputNumber,
  Divider,
  Empty,
  Tooltip,
  Progress
} from 'antd';
import { 
  SearchOutlined, 
  FireOutlined, 
  TrophyOutlined, 
  RocketOutlined,
  InfoCircleOutlined,
  AreaChartOutlined,
  DownOutlined,
  UpOutlined
} from '@ant-design/icons';
import type { ColumnType } from 'antd/es/table';
import dayjs from 'dayjs';

// 移除可能不存在的依赖
// import { motion, AnimatePresence } from 'framer-motion';
// import ReactECharts from 'echarts-for-react';

const { Title, Text } = Typography;
const { Panel } = Collapse;

interface NewHighConcept {
  concept_name: string;
  total_volume: number;
  days_period: number;
  trading_date: string;
  stocks: ConceptStock[];
}

interface ConceptStock {
  stock_code: string;
  stock_name: string;
  trading_volume: number;
  concept_rank: number;
  volume_percentage: number;
}

interface ChartData {
  date: string;
  volume: number;
  ranking: number;
  concept_total: number;
}

const InnovationAnalysisPage: React.FC = () => {
  const [days, setDays] = useState<number>(10);
  const [newHighConcepts, setNewHighConcepts] = useState<NewHighConcept[]>([]);
  const [loading, setLoading] = useState(false);
  const [tradingDate, setTradingDate] = useState<string>(dayjs().format('YYYY-MM-DD'));
  const [expandedConcepts, setExpandedConcepts] = useState<Record<string, boolean>>({});
  const [visibleStocks, setVisibleStocks] = useState<Record<string, number>>({});
  const [chartData, setChartData] = useState<ChartData[]>([]);
  const [selectedStock, setSelectedStock] = useState<string>('');

  // 查询创新高概念
  const searchNewHighConcepts = async () => {
    if (days <= 0 || days > 365) {
      message.warning('请输入有效的天数（1-365）');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('admin_token') || localStorage.getItem('token');
      const response = await fetch(`/api/stock-analysis/concepts/new-highs?days=${days}&trading_date=${tradingDate}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error('查询失败');
      }
      
      const data = await response.json();
      setNewHighConcepts(data.new_high_concepts || []);
      
      // 初始化显示状态
      const initialVisible: Record<string, number> = {};
      const concepts = data.new_high_concepts || [];
      concepts.forEach((concept: NewHighConcept) => {
        initialVisible[concept.concept_name] = 10;
      });
      setVisibleStocks(initialVisible);
      
      const conceptCount = concepts.length;
      message.success(`查询成功，找到${conceptCount}个创新高概念`);
    } catch (error) {
      message.error('查询失败，请检查网络连接');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // 查看股票图表
  const viewStockChart = async (stockCode: string, conceptName: string) => {
    try {
      const token = localStorage.getItem('admin_token') || localStorage.getItem('token');
      const response = await fetch(`/api/stock-analysis/stock/${stockCode}/chart-data?concept_name=${conceptName}&days=30`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error('获取图表数据失败');
      }
      
      const data = await response.json();
      setChartData(data.chart_data || []);
      setSelectedStock(`${stockCode} - ${conceptName}`);
      message.success('图表数据加载成功');
    } catch (error) {
      message.error('获取图表数据失败');
      console.error(error);
    }
  };

  // 展开更多股票
  const showMoreStocks = (conceptName: string) => {
    setVisibleStocks(prev => ({
      ...prev,
      [conceptName]: (prev[conceptName] || 10) + 10
    }));
  };

  // 切换概念展开状态
  const toggleConcept = (conceptName: string) => {
    setExpandedConcepts(prev => ({
      ...prev,
      [conceptName]: !prev[conceptName]
    }));
  };

  // 概念股票表格列定义
  const stockColumns: ColumnType<ConceptStock>[] = [
    {
      title: '排名',
      dataIndex: 'concept_rank',
      key: 'rank',
      width: 70,
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
      render: (code: string, record: ConceptStock) => (
        <Button 
          type="link" 
          size="small"
          onClick={() => viewStockChart(code, newHighConcepts.find(c => c.stocks.includes(record))?.concept_name || '')}
        >
          {code}
        </Button>
      ),
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      ellipsis: true,
    },
    {
      title: '交易量',
      dataIndex: 'trading_volume',
      key: 'trading_volume',
      render: (volume: number) => (
        <Text>{volume ? volume.toLocaleString() : 0}</Text>
      ),
    },
    {
      title: '占比',
      dataIndex: 'volume_percentage',
      key: 'volume_percentage',
      width: 80,
      render: (percentage: number) => (
        <div>
          <Text>{percentage ? percentage.toFixed(2) : 0}%</Text>
          <Progress
            percent={percentage || 0}
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
      <Title level={2}>
        <RocketOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />
        创新高概念分析
      </Title>
      
      {/* 搜索区域 */}
      <Card style={{ marginBottom: 24, borderRadius: '12px' }}>
        <Row gutter={16} align="middle">
          <Col span={3}>
            <Text strong>统计周期:</Text>
          </Col>
          <Col span={4}>
            <InputNumber
              min={1}
              max={365}
              value={days}
              onChange={(value) => setDays(value || 10)}
              addonAfter="天"
              placeholder="天数"
            />
          </Col>
          <Col span={4}>
            <DatePicker
              value={dayjs(tradingDate)}
              onChange={(date) => setTradingDate(date ? date.format('YYYY-MM-DD') : dayjs().format('YYYY-MM-DD'))}
              format="YYYY-MM-DD"
              placeholder="交易日期"
            />
          </Col>
          <Col span={4}>
            <Button 
              type="primary" 
              icon={<SearchOutlined />}
              loading={loading}
              onClick={searchNewHighConcepts}
              block
            >
              查询创新高
            </Button>
          </Col>
          <Col span={9}>
            <Text type="secondary">
              <InfoCircleOutlined style={{ marginRight: 4 }} />
              查询指定天数内创新高的概念及其股票排名情况
            </Text>
          </Col>
        </Row>
      </Card>

      {/* 结果展示区域 */}
      {loading && (
        <Card style={{ textAlign: 'center', borderRadius: '12px' }}>
          <Spin size="large" tip="正在查询创新高概念数据..." />
        </Card>
      )}

      {!loading && newHighConcepts.length > 0 && (
        <Row gutter={16}>
          <Col span={16}>
            <Card 
              title={
                <Space>
                  <FireOutlined style={{ color: '#ff4d4f' }} />
                  <span>创新高概念列表 ({newHighConcepts.length}个)</span>
                  <Tag color="red">{days}天新高</Tag>
                </Space>
              }
              style={{ marginBottom: 24, borderRadius: '12px' }}
            >
              <List
                dataSource={newHighConcepts}
                renderItem={(concept, index) => (
                  <List.Item style={{ padding: '16px 0' }}>
                    <div style={{ width: '100%' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                        <Space size="large">
                          <div>
                            <Tag color="red" style={{ fontSize: '14px', padding: '4px 8px' }}>
                              #{index + 1}
                            </Tag>
                            <Text strong style={{ fontSize: '16px' }}>{concept.concept_name}</Text>
                          </div>
                          <div>
                            <Text type="secondary">总交易量: </Text>
                            <Text strong style={{ color: '#ff4d4f' }}>
                              {concept.total_volume.toLocaleString()}
                            </Text>
                          </div>
                          <div>
                            <Text type="secondary">股票数: </Text>
                            <Text strong>{concept.stocks.length}</Text>
                          </div>
                        </Space>
                        <Space>
                          <Button 
                            size="small"
                            icon={expandedConcepts[concept.concept_name] ? <UpOutlined /> : <DownOutlined />}
                            onClick={() => toggleConcept(concept.concept_name)}
                          >
                            {expandedConcepts[concept.concept_name] ? '收起' : '展开'}股票列表
                          </Button>
                        </Space>
                      </div>
                      
                      {/* 概念股票列表 */}
                      {expandedConcepts[concept.concept_name] && (
                        <div>
                          <Divider style={{ margin: '12px 0' }} />
                          <Title level={5} style={{ marginBottom: 16 }}>
                            概念股排名 (前{Math.min(visibleStocks[concept.concept_name] || 10, concept.stocks.length)}名)
                          </Title>
                          <Table
                            dataSource={concept.stocks ? concept.stocks.slice(0, visibleStocks[concept.concept_name] || 10) : []}
                            columns={stockColumns}
                            size="small"
                            pagination={false}
                            rowKey="stock_code"
                          />
                          
                          {concept.stocks && concept.stocks.length > (visibleStocks[concept.concept_name] || 10) && (
                            <div style={{ textAlign: 'center', marginTop: 16 }}>
                              <Button 
                                type="dashed"
                                onClick={() => showMoreStocks(concept.concept_name)}
                              >
                                显示更多 (+10) - 还有{concept.stocks.length - (visibleStocks[concept.concept_name] || 10)}只股票
                              </Button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </List.Item>
                )}
              />
            </Card>
          </Col>
          
          <Col span={8}>
            <Card 
              title={
                <Space>
                  <AreaChartOutlined />
                  <span>股票图表分析</span>
                </Space>
              }
              style={{ marginBottom: 24, borderRadius: '12px' }}
            >
              {chartData.length > 0 ? (
                <div>
                  <Title level={5}>{selectedStock} 趋势图</Title>
                  
                  {/* 这里可以集成真实的图表库 */}
                  <div style={{ height: 300, border: '1px solid #d9d9d9', borderRadius: 6, padding: 16 }}>
                    <Text type="secondary">📈 图表数据 ({chartData.length} 个数据点)</Text>
                    <div style={{ marginTop: 16, maxHeight: 240, overflowY: 'auto' }}>
                      {chartData.slice(0, 10).map((point, index) => (
                        <div key={index} style={{ marginBottom: 8, fontSize: '12px' }}>
                          <Text>{point.date}:</Text>
                          <br />
                          <Text type="secondary">
                            量: {point.volume ? point.volume.toLocaleString() : 0}
                            {point.ranking && `, 排名: ${point.ranking}`}
                          </Text>
                        </div>
                      ))}
                      {chartData.length > 10 && (
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          ... 还有 {chartData.length - 10} 个数据点
                        </Text>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: 40 }}>
                  <div style={{ fontSize: '48px', marginBottom: 16 }}>📊</div>
                  <Text type="secondary">点击股票代码查看图表</Text>
                </div>
              )}
            </Card>

            {/* 统计信息卡片 */}
            <Card title="数据统计" style={{ borderRadius: '12px' }}>
              <Row gutter={[0, 16]}>
                <Col span={24}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '24px', fontWeight: '600', color: '#ff4d4f' }}>
                      {newHighConcepts.length}
                    </div>
                    <Text type="secondary">创新高概念数</Text>
                  </div>
                </Col>
                <Col span={24}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '24px', fontWeight: '600', color: '#1890ff' }}>
                      {newHighConcepts.reduce((sum, concept) => sum + concept.stocks.length, 0)}
                    </div>
                    <Text type="secondary">涉及股票总数</Text>
                  </div>
                </Col>
                <Col span={24}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '20px', fontWeight: '600', color: '#52c41a' }}>
                      {days}天
                    </div>
                    <Text type="secondary">统计周期</Text>
                  </div>
                </Col>
                <Col span={24}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '14px', color: '#666' }}>
                      {tradingDate}
                    </div>
                    <Text type="secondary">分析日期</Text>
                  </div>
                </Col>
              </Row>
            </Card>
          </Col>
        </Row>
      )}
      
      {!loading && newHighConcepts.length === 0 && days > 0 && (
        <Card style={{ textAlign: 'center', padding: 40, borderRadius: '12px' }}>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <div>
                <Text type="secondary" style={{ fontSize: '16px' }}>
                  在{tradingDate}这一天，过去{days}天内没有发现创新高的概念
                </Text>
                <br />
                <Text type="secondary">
                  可以尝试调整查询日期或减少统计天数
                </Text>
              </div>
            }
          >
            <Button type="primary" onClick={() => setDays(5)}>
              试试5天周期
            </Button>
          </Empty>
        </Card>
      )}

      {!loading && days === 0 && (
        <Card style={{ borderRadius: '12px' }}>
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>🚀</div>
            <Title level={3} style={{ color: '#6b7280' }}>创新高概念分析工具</Title>
            <div style={{ maxWidth: '600px', margin: '0 auto' }}>
              <Text type="secondary" style={{ fontSize: '16px', lineHeight: '1.6' }}>
                输入统计天数查询概念总和创新高的概念股，分析市场热点板块和个股表现。
                支持1-365天的灵活周期设置。
              </Text>
            </div>
            
            <Row gutter={[24, 16]} style={{ marginTop: '32px' }}>
              <Col xs={24} md={8}>
                <div style={{ padding: '16px' }}>
                  <div style={{ fontSize: '24px', marginBottom: '8px' }}>📊</div>
                  <Text strong>精准识别</Text>
                  <div style={{ marginTop: '8px' }}>
                    <Text type="secondary">准确识别指定周期内的创新高概念</Text>
                  </div>
                </div>
              </Col>
              <Col xs={24} md={8}>
                <div style={{ padding: '16px' }}>
                  <div style={{ fontSize: '24px', marginBottom: '8px' }}>🏆</div>
                  <Text strong>排名分析</Text>
                  <div style={{ marginTop: '8px' }}>
                    <Text type="secondary">详细展示概念内股票排名情况</Text>
                  </div>
                </div>
              </Col>
              <Col xs={24} md={8}>
                <div style={{ padding: '16px' }}>
                  <div style={{ fontSize: '24px', marginBottom: '8px' }}>📈</div>
                  <Text strong>图表展示</Text>
                  <div style={{ marginTop: '8px' }}>
                    <Text type="secondary">可视化股票走势和排名变化</Text>
                  </div>
                </div>
              </Col>
            </Row>
          </div>
        </Card>
      )}
    </div>
  );
};

export default InnovationAnalysisPage;
