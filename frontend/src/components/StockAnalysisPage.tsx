import React, { useState, useEffect } from 'react';
import { 
  Card, Row, Col, Input, Button, Table, Tag, Space, Tooltip, 
  Alert, Empty, Spin, Typography, Progress, Divider, message,
  DatePicker
} from 'antd';
import { 
  SearchOutlined, StockOutlined, FireOutlined, 
  TrophyOutlined, InfoCircleOutlined, AreaChartOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';

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
          heat_value: concept.trading_volume
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
    } catch (error: any) {
      console.error('Stock search error:', error);
      if (error.message.includes('404')) {
        message.error('未找到该股票或暂无相关数据');
      } else {
        message.error('查询失败，请稍后重试');
      }
      setSearchResult(null);
      setChartData([]);
    } finally {
      setLoading(false);
    }
  };

  // 概念排名表格列定义
  const conceptColumns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
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
      )
    },
    {
      title: '概念名称',
      dataIndex: 'concept_name',
      key: 'concept_name',
      render: (name: string) => (
        <Text strong>{name}</Text>
      )
    },
    {
      title: '交易量',
      dataIndex: 'heat_value',
      key: 'heat_value',
      render: (value: number) => (
        <Text style={{ fontWeight: '600' }}>
          {value ? value.toLocaleString() : 0}
        </Text>
      )
    },
    {
      title: '排名情况',
      key: 'ranking_info',
      render: (record: any) => (
        <div>
          <Text>第{record.rank}名 / 共{record.total_stocks}只股票</Text>
        </div>
      )
    }
  ];

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
            查询个股在各概念中的排名表现和交易量分析
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

          {/* 概念排名表格 */}
          <Row gutter={16}>
            <Col span={16}>
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
                    scroll={{ x: 800 }}
                  />
                ) : (
                  <Empty 
                    description="该股票暂无概念排名数据"
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                  />
                )}
              </Card>
            </Col>

            <Col span={8}>
              {/* 图表区域 */}
              <Card 
                title={
                  <Space>
                    <AreaChartOutlined />
                    <span>概念表现分析</span>
                  </Space>
                }
                style={{ borderRadius: '12px' }}
              >
                {chartData.length > 0 ? (
                  <div>
                    <Title level={5}>{searchResult.stock_name} 走势图</Title>
                    <div style={{ height: '300px', border: '1px solid #d9d9d9', borderRadius: 6, padding: 16 }}>
                      <Text type="secondary">📈 图表数据 ({chartData.length} 个数据点)</Text>
                      <div style={{ marginTop: 16, maxHeight: 240, overflowY: 'auto' }}>
                        {chartData.slice(0, 10).map((point, index) => (
                          <div key={index} style={{ marginBottom: 8, fontSize: '12px' }}>
                            <Text>{point.date}:</Text>
                            <br />
                            <Text type="secondary">
                              交易量: {point.trading_volume ? point.trading_volume.toLocaleString() : 0}
                              {point.concept_rank && `, 排名: 第${point.concept_rank}名`}
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
                    <Text type="secondary">暂无图表数据</Text>
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
                输入股票代码查询该股票在各个概念中的排名表现，了解股票的概念属性和市场热度。
                支持沪深A股所有股票代码查询。
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