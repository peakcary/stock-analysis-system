import React, { useState, useEffect } from 'react';
import { 
  Card, Row, Col, Table, Tag, Space, Tooltip, Alert, Empty, 
  Spin, Typography, Progress, Select, Button, DatePicker, 
  Statistic, List, Avatar, Badge
} from 'antd';
import { 
  FireOutlined, TrophyOutlined, RiseOutlined, 
  ThunderboltOutlined, StarOutlined, CrownOutlined,
  ReloadOutlined, CalendarOutlined
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import ReactECharts from 'echarts-for-react';
import dayjs from 'dayjs';
import { ConceptAnalysisApi, ChartDataApi, conceptAnalysisUtils } from '../services/conceptAnalysisApi';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

interface InnovationAnalysisPageProps {
  user: any;
  tradeDate?: string;
}

export const InnovationAnalysisPage: React.FC<InnovationAnalysisPageProps> = ({ 
  user, 
  tradeDate: initialTradeDate 
}) => {
  const [loading, setLoading] = useState(false);
  const [innovationConcepts, setInnovationConcepts] = useState<any[]>([]);
  const [timelineData, setTimelineData] = useState<any>(null);
  const [selectedDate, setSelectedDate] = useState(initialTradeDate || dayjs().format('YYYY-MM-DD'));
  const [daysBack, setDaysBack] = useState(10);
  const [selectedConcept, setSelectedConcept] = useState<any>(null);

  // 加载创新高概念数据
  const loadInnovationData = async (date: string, days: number) => {
    setLoading(true);
    try {
      // 并行加载创新高概念和时间线数据
      const [innovationRes, timelineRes] = await Promise.all([
        ConceptAnalysisApi.getInnovationConcepts(date, days, 1, 50),
        ChartDataApi.getInnovationTimeline(30)
      ]);

      setInnovationConcepts(innovationRes.innovation_concepts || []);
      setTimelineData(timelineRes);
    } catch (error) {
      console.error('Load innovation data error:', error);
      setInnovationConcepts([]);
      setTimelineData(null);
    } finally {
      setLoading(false);
    }
  };

  // 处理概念点击
  const handleConceptClick = async (concept: any) => {
    setSelectedConcept(concept);
    
    // 加载概念详细数据
    try {
      const detailRes = await ConceptAnalysisApi.getConceptRanking(
        concept.concept_id, 
        selectedDate, 
        1, 
        10
      );
      setSelectedConcept({
        ...concept,
        details: detailRes
      });
    } catch (error) {
      console.error('Load concept detail error:', error);
    }
  };

  // 初始加载
  useEffect(() => {
    loadInnovationData(selectedDate, daysBack);
  }, [selectedDate, daysBack]);

  // 创新高概念表格列
  const conceptColumns = [
    {
      title: '排名',
      key: 'rank',
      width: 70,
      render: (text: any, record: any, index: number) => (
        <div style={{ textAlign: 'center' }}>
          <Avatar 
            style={{ 
              backgroundColor: index < 3 ? '#f59e0b' : index < 10 ? '#10b981' : '#6b7280',
              color: 'white',
              fontSize: '12px',
              fontWeight: '600'
            }}
            size="small"
          >
            {index + 1}
          </Avatar>
        </div>
      )
    },
    {
      title: '概念名称',
      dataIndex: 'concept_name',
      key: 'concept_name',
      render: (name: string, record: any) => (
        <div>
          <Button 
            type="link" 
            style={{ padding: 0, fontWeight: '600' }}
            onClick={() => handleConceptClick(record)}
          >
            {name}
          </Button>
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.stock_count}只股票
          </Text>
        </div>
      )
    },
    {
      title: '总热度值',
      dataIndex: 'total_heat_value',
      key: 'total_heat_value',
      render: (value: number) => (
        <div>
          <Text style={{ 
            fontSize: '16px',
            fontWeight: '600',
            color: conceptAnalysisUtils.getHeatColor(value / 10000) // 假设热度值需要缩放
          }}>
            {conceptAnalysisUtils.formatHeatValue(value)}
          </Text>
          <div style={{ marginTop: '4px' }}>
            <Progress
              percent={Math.min((value / 100000) * 100, 100)}
              size="small"
              strokeColor="#ef4444"
              showInfo={false}
            />
          </div>
        </div>
      )
    },
    {
      title: '平均热度',
      dataIndex: 'avg_heat_value',
      key: 'avg_heat_value',
      render: (value: number) => (
        <Text style={{ fontWeight: '500' }}>
          {conceptAnalysisUtils.formatHeatValue(value)}
        </Text>
      )
    },
    {
      title: '创新高天数',
      dataIndex: 'new_high_days',
      key: 'new_high_days',
      render: (days: number) => (
        <Tag color={days >= 20 ? 'red' : days >= 10 ? 'orange' : 'green'}>
          <CrownOutlined /> {days}天新高
        </Tag>
      )
    },
    {
      title: '热门个股',
      dataIndex: 'top_stocks',
      key: 'top_stocks',
      render: (stocks: any[]) => (
        <div>
          {stocks?.slice(0, 2).map((stock, index) => (
            <div key={index} style={{ marginBottom: '4px' }}>
              <Tag color="blue" style={{ fontSize: '12px' }}>
                {stock.stock_name}
              </Tag>
              <Text type="secondary" style={{ fontSize: '10px', marginLeft: '4px' }}>
                {conceptAnalysisUtils.formatHeatValue(stock.heat_value)}
              </Text>
            </div>
          ))}
          {stocks?.length > 2 && (
            <Text type="secondary" style={{ fontSize: '12px' }}>
              +{stocks.length - 2}只...
            </Text>
          )}
        </div>
      )
    }
  ];

  // 时间线图表配置
  const getTimelineChartOptions = () => {
    if (!timelineData?.chart_data) return {};

    return {
      title: {
        text: '创新高概念时间线',
        textStyle: { fontSize: 16, fontWeight: 'normal' }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        formatter: (params: any) => {
          return params.map((item: any) => 
            `${item.seriesName}: ${item.value}<br/>`
          ).join('');
        }
      },
      legend: {
        data: timelineData.chart_data.series?.map((s: any) => s.name) || []
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: timelineData.chart_data.dates || []
      },
      yAxis: [
        {
          type: 'value',
          name: '创新高概念数量',
          axisLabel: { formatter: '{value}个' }
        },
        {
          type: 'value',
          name: '总热度值'
        }
      ],
      series: timelineData.chart_data.series || []
    };
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题和控制区域 */}
      <Card style={{ marginBottom: '24px', borderRadius: '12px' }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={2} style={{ margin: '0 0 8px 0', color: '#1f2937' }}>
              <ThunderboltOutlined style={{ marginRight: '8px', color: '#ef4444' }} />
              创新高概念分析
            </Title>
            <Text type="secondary">
              发现市场热点，捕捉创新高概念投资机会
            </Text>
          </Col>
          
          <Col>
            <Space size="middle">
              <div>
                <Text type="secondary" style={{ fontSize: '12px' }}>分析日期: </Text>
                <DatePicker
                  value={dayjs(selectedDate)}
                  onChange={(date) => {
                    if (date) {
                      setSelectedDate(date.format('YYYY-MM-DD'));
                    }
                  }}
                  format="YYYY-MM-DD"
                />
              </div>
              
              <div>
                <Text type="secondary" style={{ fontSize: '12px' }}>回望天数: </Text>
                <Select
                  value={daysBack}
                  onChange={setDaysBack}
                  style={{ width: 100 }}
                >
                  <Option value={5}>5天</Option>
                  <Option value={10}>10天</Option>
                  <Option value={20}>20天</Option>
                  <Option value={30}>30天</Option>
                </Select>
              </div>
              
              <Button 
                icon={<ReloadOutlined />}
                onClick={() => loadInnovationData(selectedDate, daysBack)}
                loading={loading}
              >
                刷新数据
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 用户权限提示 */}
      {user?.memberType === 'free' && (
        <Alert
          message="创新分析功能"
          description="升级为专业版会员，解锁完整的创新高概念分析功能"
          type="warning"
          showIcon
          style={{ marginBottom: '24px' }}
          action={<Button type="primary" size="small">升级会员</Button>}
        />
      )}

      <Row gutter={[24, 24]}>
        {/* 左侧：创新高概念列表 */}
        <Col xs={24} lg={16}>
          <Card 
            title={
              <Space>
                <FireOutlined style={{ color: '#ef4444' }} />
                <span>创新高概念排行</span>
                <Badge count={innovationConcepts.length} style={{ backgroundColor: '#ef4444' }} />
              </Space>
            }
            style={{ borderRadius: '12px' }}
          >
            {loading ? (
              <div style={{ textAlign: 'center', padding: '60px' }}>
                <Spin size="large" tip="正在分析创新高概念..."/>
              </div>
            ) : innovationConcepts.length > 0 ? (
              <Table
                columns={conceptColumns}
                dataSource={innovationConcepts}
                rowKey="concept_id"
                pagination={{
                  pageSize: 20,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `共发现 ${total} 个创新高概念`
                }}
                scroll={{ x: 1000 }}
              />
            ) : (
              <Empty 
                description="当前日期暂无创新高概念"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            )}
          </Card>
        </Col>

        {/* 右侧：统计信息和图表 */}
        <Col xs={24} lg={8}>
          {/* 统计卡片 */}
          <Card style={{ marginBottom: '24px', borderRadius: '12px' }}>
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Statistic
                  title="创新高概念"
                  value={innovationConcepts.length}
                  suffix="个"
                  prefix={<TrophyOutlined style={{ color: '#f59e0b' }} />}
                  valueStyle={{ color: '#f59e0b' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="涉及个股"
                  value={innovationConcepts.reduce((sum, c) => sum + c.stock_count, 0)}
                  suffix="只"
                  prefix={<RiseOutlined style={{ color: '#10b981' }} />}
                  valueStyle={{ color: '#10b981' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="平均新高天数"
                  value={innovationConcepts.length > 0 
                    ? (innovationConcepts.reduce((sum, c) => sum + c.new_high_days, 0) / innovationConcepts.length).toFixed(1)
                    : 0
                  }
                  suffix="天"
                  prefix={<StarOutlined style={{ color: '#3b82f6' }} />}
                  valueStyle={{ color: '#3b82f6' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="分析日期"
                  value={conceptAnalysisUtils.formatDate(selectedDate)}
                  prefix={<CalendarOutlined style={{ color: '#6b7280' }} />}
                  valueStyle={{ color: '#6b7280', fontSize: '16px' }}
                />
              </Col>
            </Row>
          </Card>

          {/* 创新高时间线图表 */}
          {timelineData && (
            <Card 
              title="创新高时间线"
              style={{ borderRadius: '12px' }}
            >
              <ReactECharts
                option={getTimelineChartOptions()}
                style={{ height: '300px' }}
                opts={{ renderer: 'svg' }}
              />
            </Card>
          )}
        </Col>
      </Row>

      {/* 概念详情抽屉式显示 */}
      <AnimatePresence>
        {selectedConcept && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            style={{ 
              position: 'fixed',
              bottom: '20px',
              right: '20px',
              width: '400px',
              zIndex: 1000
            }}
          >
            <Card 
              title={
                <Space>
                  <CrownOutlined style={{ color: '#f59e0b' }} />
                  <span>{selectedConcept.concept_name}</span>
                </Space>
              }
              extra={
                <Button 
                  type="text" 
                  onClick={() => setSelectedConcept(null)}
                >
                  ×
                </Button>
              }
              style={{ 
                borderRadius: '12px',
                boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
              }}
            >
              <div style={{ marginBottom: '16px' }}>
                <Progress
                  percent={Math.min((selectedConcept.total_heat_value / 100000) * 100, 100)}
                  strokeColor="#ef4444"
                  format={(percent) => `热度 ${percent}%`}
                />
              </div>

              <Row gutter={[8, 8]} style={{ marginBottom: '16px' }}>
                <Col span={12}>
                  <Text type="secondary">创新高天数:</Text>
                  <br />
                  <Text strong>{selectedConcept.new_high_days}天</Text>
                </Col>
                <Col span={12}>
                  <Text type="secondary">股票数量:</Text>
                  <br />
                  <Text strong>{selectedConcept.stock_count}只</Text>
                </Col>
              </Row>

              <div>
                <Text type="secondary">热门个股:</Text>
                <List
                  size="small"
                  dataSource={selectedConcept.top_stocks?.slice(0, 3) || []}
                  renderItem={(stock: any) => (
                    <List.Item style={{ padding: '4px 0' }}>
                      <Space>
                        <Tag color="blue" style={{ fontSize: '12px' }}>{stock.stock_name}</Tag>
                        <Text style={{ fontSize: '12px', color: '#f59e0b' }}>
                          {conceptAnalysisUtils.formatHeatValue(stock.heat_value)}
                        </Text>
                      </Space>
                    </List.Item>
                  )}
                />
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 空状态说明 */}
      {!loading && innovationConcepts.length === 0 && (
        <Card style={{ textAlign: 'center', marginTop: '24px', borderRadius: '12px' }}>
          <div style={{ padding: '40px' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📈</div>
            <Title level={3} style={{ color: '#6b7280' }}>暂无创新高概念</Title>
            <Paragraph style={{ color: '#9ca3af', maxWidth: '500px', margin: '0 auto' }}>
              在{conceptAnalysisUtils.formatDate(selectedDate)}这一天，
              没有发现创新{daysBack}天新高的概念。
              您可以尝试调整分析日期或回望天数来查看其他时期的创新高概念。
            </Paragraph>
          </div>
        </Card>
      )}
    </div>
  );
};

export default InnovationAnalysisPage;