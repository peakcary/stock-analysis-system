import React, { useState, useEffect } from 'react';
import { 
  Card, Row, Col, Input, Button, Table, Tag, Space, Tooltip, 
  Alert, Empty, Spin, Typography, Progress, Divider, message,
  DatePicker, Select
} from 'antd';
import { 
  SearchOutlined, StockOutlined, FireOutlined, 
  TrophyOutlined, InfoCircleOutlined, AreaChartOutlined,
  LineChartOutlined, BarChartOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Line, DualAxes } from '@ant-design/charts';

const { Title, Text } = Typography;
const { Search } = Input;

interface StockAnalysisPageProps {
  user: any;
  tradeDate?: string;
}

interface ConceptInfo {
  concept_name: string;
  trading_volume: number;
  concept_rank: number;
  concept_total_volume: number;
  volume_percentage: number;
  trading_date: string;
}

interface ChartData {
  date: string;
  trading_volume: number;
  concept_rank?: number;
  volume_percentage?: number;
}

export const StockAnalysisPage: React.FC<StockAnalysisPageProps> = ({ user, tradeDate }) => {
  const [loading, setLoading] = useState(false);
  const [searchResult, setSearchResult] = useState<any>(null);
  const [chartData, setChartData] = useState<ChartData[]>([]);
  const [searchStock, setSearchStock] = useState('');
  const [currentTradeDate, setCurrentTradeDate] = useState(tradeDate || dayjs().format('YYYY-MM-DD'));
  const [selectedConcept, setSelectedConcept] = useState<string>('');
  const [chartLoading, setChartLoading] = useState(false);
  const [stockChartData, setStockChartData] = useState<any>(null);
  const [conceptSummaryData, setConceptSummaryData] = useState<any[]>([]);

  // 处理股票搜索
  const handleStockSearch = async (stockCode: string) => {
    if (!stockCode.trim()) {
      message.warning('请输入股票代码');
      return;
    }

    setLoading(true);
    try {
      // 获取股票概念信息
      const token = localStorage.getItem('admin_token') || localStorage.getItem('token');
      const response = await fetch(`/api/v1/stock-analysis/stock/${stockCode}/concepts?trading_date=${currentTradeDate}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('404');
        }
        throw new Error('查询失败');
      }

      const stockData = await response.json();
      setSearchResult({
        stock_code: stockData.stock_code,
        stock_name: stockData.stock_name,
        heat_value: stockData.total_trading_volume,
        total_concepts: stockData.concepts?.length || 0,
        trade_date: stockData.trading_date,
        concept_rankings: stockData.concepts?.map((concept: ConceptInfo, index: number) => ({
          concept_id: index + 1,
          concept_name: concept.concept_name,
          rank: concept.concept_rank,
          total_stocks: 100, // 默认值
          heat_value: concept.trading_volume,
          volume_percentage: concept.volume_percentage,
          concept_total_volume: concept.concept_total_volume
        })) || []
      });

      // 获取图表数据
      if (stockData.concepts?.length > 0) {
        const chartResponse = await fetch(`/api/v1/stock-analysis/stock/${stockCode}/chart-data?concept_name=${stockData.concepts[0].concept_name}&days=30`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (chartResponse.ok) {
          const chartData = await chartResponse.json();
          setChartData(chartData.chart_data || []);
        }
      }

      message.success('查询成功');
      
      // 如果有概念数据，默认选择第一个概念进行图表展示
      if (stockData.concepts?.length > 0) {
        setSelectedConcept(stockData.concepts[0].concept_name);
        await fetchChartData(stockCode, stockData.concepts[0].concept_name);
      }
    } catch (error: any) {
      console.error('Stock search error:', error);
      if (error.message.includes('404')) {
        message.error('未找到该股票或暂无相关数据');
      } else {
        message.error('查询失败，请稍后重试');
      }
      setSearchResult(null);
      setChartData([]);
      setStockChartData(null);
      setConceptSummaryData([]);
    } finally {
      setLoading(false);
    }
  };

  // 获取图表数据
  const fetchChartData = async (stockCode: string, conceptName?: string) => {
    if (!stockCode) return;
    
    setChartLoading(true);
    try {
      const token = localStorage.getItem('admin_token') || localStorage.getItem('token');
      let url = `/api/v1/stock-analysis/stock/${stockCode}/chart-data?days=30`;
      if (conceptName) {
        url += `&concept_name=${encodeURIComponent(conceptName)}`;
      }
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('获取图表数据失败');
      }

      const chartResult = await response.json();
      setStockChartData(chartResult.chart_data || []);
      setConceptSummaryData(chartResult.concept_summary_data || []);
      
    } catch (error: any) {
      console.error('Chart data error:', error);
      message.error('获取图表数据失败: ' + error.message);
      setStockChartData(null);
      setConceptSummaryData([]);
    } finally {
      setChartLoading(false);
    }
  };

  // 处理概念选择变化
  const handleConceptChange = async (conceptName: string) => {
    setSelectedConcept(conceptName);
    if (searchResult?.stock_code) {
      await fetchChartData(searchResult.stock_code, conceptName);
    }
  };

  // 格式化数字显示
  const formatNumber = (num: number) => {
    if (num >= 100000000) {
      return (num / 100000000).toFixed(1) + '亿';
    } else if (num >= 10000) {
      return (num / 10000).toFixed(1) + '万';
    }
    return num.toLocaleString();
  };

  // 概念排名表格列定义
  const conceptColumns = [
    {
      title: '概念名称',
      dataIndex: 'concept_name',
      key: 'concept_name',
      width: 120,
      render: (name: string) => (
        <Text strong style={{ color: '#1890ff' }}>{name}</Text>
      )
    },
    {
      title: '交易量',
      dataIndex: 'heat_value',
      key: 'heat_value',
      width: 120,
      sorter: (a: any, b: any) => a.heat_value - b.heat_value,
      render: (value: number) => (
        <Text style={{ fontWeight: '600', color: '#cf1322' }}>
          {formatNumber(value || 0)}
        </Text>
      )
    },
    {
      title: '概念内排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 100,
      render: (rank: number) => (
        <div style={{ textAlign: 'center' }}>
          <Tag color={rank <= 3 ? 'gold' : rank <= 10 ? 'blue' : 'default'}>
            #{rank}
          </Tag>
        </div>
      )
    },
    {
      title: '占概念比例',
      key: 'percentage',
      width: 120,
      render: (record: any) => (
        <div>
          <Text>{record.volume_percentage ? record.volume_percentage.toFixed(2) + '%' : '0%'}</Text>
        </div>
      )
    },
    {
      title: '概念总量',
      key: 'concept_total',
      width: 120,
      render: (record: any) => (
        <Text type="secondary">
          {formatNumber(record.concept_total_volume || 0)}
        </Text>
      )
    }
  ];

  // 生成图表数据
  const getChartData = () => {
    if (!stockChartData || stockChartData.length === 0) {
      return { leftData: [], rightData: [] };
    }

    // 左轴数据：个股交易量和概念总交易量
    const leftData: any[] = [];
    
    // 个股交易量数据
    stockChartData.forEach((item: any) => {
      leftData.push({
        date: item.date,
        type: '个股交易量',
        value: item.trading_volume || 0
      });
    });
    
    // 概念总交易量数据
    conceptSummaryData.forEach((item: any) => {
      leftData.push({
        date: item.date,
        type: '概念总交易量', 
        value: item.total_volume || 0
      });
    });

    // 右轴数据：概念内排名
    const rightData: any[] = [];
    stockChartData.forEach((item: any) => {
      if (item.concept_rank) {
        rightData.push({
          date: item.date,
          type: '概念内排名',
          value: item.concept_rank
        });
      }
    });

    return { leftData, rightData };
  };

  // 双轴图表配置
  const getDualAxesConfig = () => {
    const { leftData, rightData } = getChartData();
    
    if (leftData.length === 0 && rightData.length === 0) {
      return null;
    }

    return {
      data: [leftData, rightData],
      xField: 'date',
      yField: ['value', 'value'],
      height: 350,
      geometryOptions: [
        {
          geometry: 'line',
          seriesField: 'type',
          smooth: true,
          lineStyle: {
            lineWidth: 2,
          },
          point: {
            size: 4,
            shape: 'circle',
          },
          color: ['#1890ff', '#52c41a'],
        },
        {
          geometry: 'line', 
          seriesField: 'type',
          smooth: true,
          lineStyle: {
            lineWidth: 2,
            lineDash: [4, 4],
          },
          point: {
            size: 4,
            shape: 'square',
          },
          color: ['#f5222d'],
        },
      ],
      yAxis: {
        value: {
          min: 0,
          title: {
            text: '交易量',
            style: {
              fontSize: 12,
              fill: '#666',
            },
          },
          label: {
            formatter: (val: number) => formatNumber(val),
          },
        },
      },
      meta: {
        value: {
          alias: '交易量',
        },
        date: {
          alias: '日期',
        },
      },
      legend: {
        position: 'top-right',
        offsetY: -10,
      },
      tooltip: {
        shared: true,
        showCrosshairs: true,
        formatter: (datum: any) => {
          return {
            name: datum.type,
            value: datum.type === '概念内排名' ? `第${datum.value}名` : formatNumber(datum.value),
          };
        },
      },
    };
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题和搜索区域 */}
      <Card style={{ marginBottom: '24px', borderRadius: '12px' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <Title level={2} style={{ margin: '0 0 8px 0', color: '#1f2937' }}>
            <StockOutlined style={{ marginRight: '8px', color: '#3b82f6' }} />
            个股概念分析
          </Title>
          <Text type="secondary">
            输入股票代码查看该股票在所有概念中的表现，概念按交易量从高到低排列
          </Text>
        </div>

        <Row gutter={16} justify="center">
          <Col xs={24} sm={8}>
            <DatePicker
              value={dayjs(currentTradeDate)}
              onChange={(date) => setCurrentTradeDate(date ? date.format('YYYY-MM-DD') : dayjs().format('YYYY-MM-DD'))}
              format="YYYY-MM-DD"
              placeholder="选择交易日期"
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={12}>
            <Search
              placeholder="请输入股票代码（如：SH600000、SZ000001）"
              enterButton={
                <Button type="primary" icon={<SearchOutlined />}>
                  查询分析
                </Button>
              }
              size="large"
              value={searchStock}
              onChange={(e) => setSearchStock(e.target.value)}
              onSearch={handleStockSearch}
              loading={loading}
            />
          </Col>
        </Row>

        {/* 用户权限提示 */}
        {user?.memberType === 'free' && (
          <Alert
            message="功能限制提醒"
            description="免费用户每日查询次数有限，升级会员享受无限制查询"
            type="warning"
            showIcon
            style={{ marginTop: '16px' }}
            action={
              <Button size="small" type="primary">升级会员</Button>
            }
          />
        )}
      </Card>

      {/* 搜索结果区域 */}
      {loading && (
        <Card style={{ textAlign: 'center', borderRadius: '12px' }}>
          <Spin size="large" tip="正在查询股票概念数据..."/>
        </Card>
      )}

      {searchResult && !loading && (
        <div>
          {/* 股票基本信息 */}
          <Card 
            title={
              <Space>
                <TrophyOutlined style={{ color: '#f59e0b' }} />
                <span>{searchResult.stock_name} ({searchResult.stock_code})</span>
                <Tag color="blue">总交易量: {searchResult.heat_value ? searchResult.heat_value.toLocaleString() : 0}</Tag>
              </Space>
            }
            style={{ marginBottom: '24px', borderRadius: '12px' }}
          >
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={8} md={6}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: '600', color: '#3b82f6' }}>
                    {searchResult.total_concepts}
                  </div>
                  <Text type="secondary">涉及概念数</Text>
                </div>
              </Col>
              <Col xs={24} sm={8} md={6}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: '600', color: '#10b981' }}>
                    {searchResult.concept_rankings?.filter((c: any) => c.rank <= 10)?.length || 0}
                  </div>
                  <Text type="secondary">前十排名数</Text>
                </div>
              </Col>
              <Col xs={24} sm={8} md={6}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: '600', color: '#f59e0b' }}>
                    {Math.min(...(searchResult.concept_rankings?.map((c: any) => c.rank) || [0]))}
                  </div>
                  <Text type="secondary">最佳排名</Text>
                </div>
              </Col>
              <Col xs={24} sm={8} md={6}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: '600', color: '#ef4444' }}>
                    {currentTradeDate}
                  </div>
                  <Text type="secondary">分析日期</Text>
                </div>
              </Col>
            </Row>
          </Card>

          {/* 概念排名表格和图表 */}
          <Row gutter={16}>
            <Col xs={24} lg={14}>
              <Card 
                title={
                  <Space>
                    <FireOutlined style={{ color: '#ef4444' }} />
                    <span>概念排名详情</span>
                    <Tooltip title="显示该股票在各个概念中的排名情况">
                      <InfoCircleOutlined style={{ color: '#6b7280' }} />
                    </Tooltip>
                  </Space>
                }
                style={{ marginBottom: '24px', borderRadius: '12px' }}
              >
                {searchResult.concept_rankings?.length > 0 ? (
                  <Table
                    columns={conceptColumns}
                    dataSource={searchResult.concept_rankings}
                    rowKey="concept_id"
                    pagination={{
                      pageSize: 10,
                      showSizeChanger: true,
                      showQuickJumper: true,
                      showTotal: (total) => `共 ${total} 个概念`
                    }}
                    scroll={{ x: 600 }}
                    size="middle"
                  />
                ) : (
                  <Empty 
                    description="该股票暂无概念排名数据"
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                  />
                )}
              </Card>
            </Col>

            <Col xs={24} lg={10}>
              {/* 图表区域 */}
              <Card 
                title={
                  <Space>
                    <AreaChartOutlined />
                    <span>概念表现分析</span>
                  </Space>
                }
                extra={
                  searchResult?.concept_rankings?.length > 0 && (
                    <Select
                      style={{ width: 150 }}
                      placeholder="选择概念"
                      value={selectedConcept}
                      onChange={handleConceptChange}
                      size="small"
                    >
                      {searchResult.concept_rankings.map((concept: any) => (
                        <Select.Option key={concept.concept_name} value={concept.concept_name}>
                          {concept.concept_name}
                        </Select.Option>
                      ))}
                    </Select>
                  )
                }
                style={{ borderRadius: '12px' }}
              >
                <Spin spinning={chartLoading}>
                  {getDualAxesConfig() ? (
                    <div style={{ height: '400px' }}>
                      <DualAxes {...getDualAxesConfig()} />
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', padding: 40 }}>
                      <div style={{ fontSize: '48px', marginBottom: 16 }}>📊</div>
                      <Text type="secondary">
                        {selectedConcept ? '暂无该概念的图表数据' : '请选择概念查看图表'}
                      </Text>
                    </div>
                  )}
                </Spin>
                
                {/* 图表说明 */}
                {selectedConcept && (
                  <div style={{ marginTop: 16, padding: 12, backgroundColor: '#f6f6f6', borderRadius: 6 }}>
                    <Text strong style={{ color: '#1890ff' }}>图表说明：</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      • 蓝线：{searchResult?.stock_name}每日交易量趋势
                      <br />
                      • 红线：在"{selectedConcept}"概念中的排名变化（越低越好）
                      <br />
                      • 绿柱："{selectedConcept}"概念每日总交易量
                    </Text>
                  </div>
                )}
              </Card>
            </Col>
          </Row>
        </div>
      )}

      {/* 使用说明 */}
      {!searchResult && !loading && (
        <Card style={{ borderRadius: '12px' }}>
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
            <Title level={3} style={{ color: '#6b7280' }}>个股概念分析工具</Title>
            <div style={{ maxWidth: '600px', margin: '0 auto' }}>
              <Text type="secondary" style={{ fontSize: '16px', lineHeight: '1.6' }}>
                输入股票代码查询该股票所属的所有概念及其表现数据，概念按交易量从高到低排列，
                可查看股票在每个概念中的排名、交易量占比等详细信息。支持沪深A股所有股票代码查询。
              </Text>
            </div>
            
            <Row gutter={[24, 16]} style={{ marginTop: '32px' }}>
              <Col xs={24} md={8}>
                <div style={{ padding: '16px' }}>
                  <div style={{ fontSize: '24px', marginBottom: '8px' }}>🎯</div>
                  <Text strong>精准排名</Text>
                  <div style={{ marginTop: '8px' }}>
                    <Text type="secondary">实时计算股票在各概念中的准确排名</Text>
                  </div>
                </div>
              </Col>
              <Col xs={24} md={8}>
                <div style={{ padding: '16px' }}>
                  <div style={{ fontSize: '24px', marginBottom: '8px' }}>🔥</div>
                  <Text strong>交易量分析</Text>
                  <div style={{ marginTop: '8px' }}>
                    <Text type="secondary">多维度交易量指标综合评估</Text>
                  </div>
                </div>
              </Col>
              <Col xs={24} md={8}>
                <div style={{ padding: '16px' }}>
                  <div style={{ fontSize: '24px', marginBottom: '8px' }}>📈</div>
                  <Text strong>走势展示</Text>
                  <div style={{ marginTop: '8px' }}>
                    <Text type="secondary">直观的数据展示概念表现</Text>
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

export default StockAnalysisPage;