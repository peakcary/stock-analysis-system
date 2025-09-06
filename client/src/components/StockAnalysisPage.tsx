import React, { useState, useEffect } from 'react';
import { 
  Card, Row, Col, Input, Button, Table, Tag, Space, Tooltip, 
  Alert, Empty, Spin, Typography, Progress, Divider, message
} from 'antd';
import { 
  SearchOutlined, StockOutlined, FireOutlined, 
  TrophyOutlined, InfoCircleOutlined
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import ReactECharts from 'echarts-for-react';
import { ConceptAnalysisApi, ChartDataApi, conceptAnalysisUtils } from '../services/conceptAnalysisApi';

const { Title, Text } = Typography;
const { Search } = Input;

interface StockAnalysisPageProps {
  user: any;
  tradeDate?: string;
}

export const StockAnalysisPage: React.FC<StockAnalysisPageProps> = ({ user, tradeDate }) => {
  const [loading, setLoading] = useState(false);
  const [searchResult, setSearchResult] = useState<any>(null);
  const [chartData, setChartData] = useState<any>(null);
  const [searchStock, setSearchStock] = useState('');

  // 处理股票搜索
  const handleStockSearch = async (stockCode: string) => {
    if (!stockCode.trim()) {
      message.warning('请输入股票代码');
      return;
    }

    setLoading(true);
    try {
      // 获取股票在各概念中的排名
      const rankingData = await ConceptAnalysisApi.getStockRanking(stockCode, tradeDate);
      setSearchResult(rankingData);

      // 获取股票概念表现图表数据
      if (rankingData.concept_rankings?.length > 0) {
        const stockId = rankingData.concept_rankings[0]?.stock_id;
        if (stockId) {
          const chartResponse = await ChartDataApi.getStockConceptPerformance(stockId, tradeDate);
          setChartData(chartResponse);
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
      setChartData(null);
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
      render: (rank: number, record: any) => (
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
      title: '热度值',
      dataIndex: 'heat_value',
      key: 'heat_value',
      render: (value: number) => (
        <div>
          <Text style={{ 
            color: conceptAnalysisUtils.getHeatColor(value),
            fontWeight: '600'
          }}>
            {conceptAnalysisUtils.formatHeatValue(value)}
          </Text>
          <div style={{ marginTop: '4px' }}>
            <Progress
              percent={Math.min((value / 1000) * 100, 100)}
              size="small"
              strokeColor={conceptAnalysisUtils.getHeatColor(value)}
              showInfo={false}
            />
          </div>
        </div>
      )
    },
    {
      title: '排名情况',
      key: 'ranking_info',
      render: (record: any) => (
        <div>
          <Text>{conceptAnalysisUtils.formatRank(record.rank, record.total_stocks)}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            共{record.total_stocks}只股票
          </Text>
        </div>
      )
    },
    {
      title: '热度等级',
      dataIndex: 'heat_value',
      key: 'heat_level',
      render: (value: number) => (
        <Tag color={conceptAnalysisUtils.getHeatColor(value)}>
          {conceptAnalysisUtils.getHeatLevel(value)}
        </Tag>
      )
    }
  ];

  // 生成概念表现图表选项
  const getChartOptions = () => {
    if (!chartData?.chart_data) return {};

    return {
      title: {
        text: `${searchResult?.stock_name} 概念表现分析`,
        textStyle: { fontSize: 16, fontWeight: 'normal' }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' }
      },
      legend: {
        data: ['概念排名', '热度值', '排名百分比']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: chartData.chart_data.categories,
        axisLabel: {
          rotate: 45,
          fontSize: 10
        }
      },
      yAxis: [
        {
          type: 'value',
          name: '排名',
          inverse: true,
          axisLabel: { formatter: '第{value}名' }
        },
        {
          type: 'value',
          name: '热度值'
        },
        {
          type: 'value',
          name: '排名百分比(%)',
          max: 100
        }
      ],
      series: chartData.chart_data.series?.map((series: any, index: number) => ({
        ...series,
        yAxisIndex: index
      })) || []
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
            查询个股在各概念中的排名表现和热度分析
          </Text>
        </div>

        <Row justify="center">
          <Col xs={24} sm={16} md={12} lg={8}>
            <Search
              placeholder="请输入股票代码（如：000001、600036）"
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
      <AnimatePresence>
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <Card style={{ textAlign: 'center', borderRadius: '12px' }}>
              <Spin size="large" tip="正在查询股票概念数据..."/>
            </Card>
          </motion.div>
        )}

        {searchResult && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            {/* 股票基本信息 */}
            <Card 
              title={
                <Space>
                  <TrophyOutlined style={{ color: '#f59e0b' }} />
                  <span>{searchResult.stock_name} ({searchResult.stock_code})</span>
                  <Tag color="blue">总热度: {conceptAnalysisUtils.formatHeatValue(searchResult.heat_value)}</Tag>
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
                      {conceptAnalysisUtils.formatDate(searchResult.trade_date)}
                    </div>
                    <Text type="secondary">分析日期</Text>
                  </div>
                </Col>
              </Row>
            </Card>

            {/* 概念排名表格 */}
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

            {/* 概念表现图表 */}
            {chartData && (
              <Card 
                title="概念表现可视化"
                style={{ borderRadius: '12px' }}
              >
                <ReactECharts
                  option={getChartOptions()}
                  style={{ height: '400px' }}
                  opts={{ renderer: 'svg' }}
                />
                
                {chartData.performance_summary && (
                  <div style={{ marginTop: '16px' }}>
                    <Divider orientation="left">表现总结</Divider>
                    <Row gutter={[16, 8]}>
                      <Col span={6}>
                        <Text type="secondary">平均排名: </Text>
                        <Text strong>{chartData.performance_summary.avg_rank}</Text>
                      </Col>
                      <Col span={6}>
                        <Text type="secondary">最佳排名: </Text>
                        <Text strong style={{ color: '#10b981' }}>
                          第{chartData.performance_summary.best_rank}名
                        </Text>
                      </Col>
                      <Col span={6}>
                        <Text type="secondary">最差排名: </Text>
                        <Text strong style={{ color: '#ef4444' }}>
                          第{chartData.performance_summary.worst_rank}名
                        </Text>
                      </Col>
                      <Col span={6}>
                        <Text type="secondary">平均热度: </Text>
                        <Text strong>{chartData.performance_summary.avg_heat}</Text>
                      </Col>
                    </Row>
                  </div>
                )}
              </Card>
            )}
          </motion.div>
        )}
      </AnimatePresence>

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
                  <Text strong>热度分析</Text>
                  <div style={{ marginTop: '8px' }}>
                    <Text type="secondary">多维度热度指标综合评估</Text>
                  </div>
                </div>
              </Col>
              <Col xs={24} md={8}>
                <div style={{ padding: '16px' }}>
                  <div style={{ fontSize: '24px', marginBottom: '8px' }}>📈</div>
                  <Text strong>可视化展示</Text>
                  <div style={{ marginTop: '8px' }}>
                    <Text type="secondary">直观的图表展示概念表现</Text>
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