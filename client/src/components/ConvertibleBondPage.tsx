import React, { useState, useEffect } from 'react';
import { 
  Card, Row, Col, Table, Tag, Space, Tooltip, Alert, Empty, 
  Spin, Typography, Progress, Button, DatePicker, Statistic,
  Select, Input, Badge
} from 'antd';
import { 
  DollarOutlined, LineChartOutlined, SearchOutlined,
  InfoCircleOutlined, FilterOutlined, ReloadOutlined,
  RiseOutlined, FallOutlined, TrophyOutlined
} from '@ant-design/icons';
import { motion } from 'framer-motion';
import ReactECharts from 'echarts-for-react';
import dayjs from 'dayjs';
import { ConceptAnalysisApi, ChartDataApi, conceptAnalysisUtils } from '../services/conceptAnalysisApi';

const { Title, Text, Paragraph } = Typography;
const { Search } = Input;
const { Option } = Select;

interface ConvertibleBondPageProps {
  user: any;
  tradeDate?: string;
}

export const ConvertibleBondPage: React.FC<ConvertibleBondPageProps> = ({ 
  user, 
  tradeDate: initialTradeDate 
}) => {
  const [loading, setLoading] = useState(false);
  const [bondData, setBondData] = useState<any>(null);
  const [chartData, setChartData] = useState<any>(null);
  const [selectedDate, setSelectedDate] = useState(initialTradeDate || dayjs().format('YYYY-MM-DD'));
  const [sortBy, setSortBy] = useState<'heat' | 'name'>('heat');
  const [filterText, setFilterText] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // 加载可转债数据
  const loadBondData = async (date: string, page: number, size: number) => {
    setLoading(true);
    try {
      // 并行加载可转债数据和图表数据
      const [bondRes, chartRes] = await Promise.all([
        ConceptAnalysisApi.getConvertibleBonds(date, page, size),
        ChartDataApi.getConvertibleBondsChart(date)
      ]);

      setBondData(bondRes);
      setChartData(chartRes);
    } catch (error) {
      console.error('Load bond data error:', error);
      setBondData(null);
      setChartData(null);
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    loadBondData(selectedDate, currentPage, pageSize);
  }, [selectedDate, currentPage, pageSize]);

  // 过滤和排序后的数据
  const filteredBonds = React.useMemo(() => {
    let bonds = bondData?.convertible_bonds || [];
    
    // 文本过滤
    if (filterText) {
      bonds = bonds.filter((bond: any) => 
        bond.stock_name.includes(filterText) || 
        bond.stock_code.includes(filterText) ||
        bond.concepts?.some((concept: string) => concept.includes(filterText))
      );
    }

    // 排序
    bonds.sort((a: any, b: any) => {
      if (sortBy === 'heat') {
        return b.heat_value - a.heat_value;
      } else {
        return a.stock_name.localeCompare(b.stock_name, 'zh-CN');
      }
    });

    return bonds;
  }, [bondData, filterText, sortBy]);

  // 可转债表格列定义
  const bondColumns = [
    {
      title: '排名',
      key: 'rank',
      width: 70,
      render: (text: any, record: any, index: number) => (
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            background: index < 3 ? '#f59e0b' : index < 10 ? '#10b981' : '#6b7280',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '12px',
            fontWeight: '600',
            margin: '0 auto'
          }}>
            {index + 1}
          </div>
        </div>
      )
    },
    {
      title: '债券代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 100,
      render: (code: string) => (
        <Text code style={{ fontSize: '12px', color: '#3b82f6' }}>
          {code}
        </Text>
      )
    },
    {
      title: '债券名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      render: (name: string, record: any) => (
        <div>
          <Text strong style={{ fontSize: '14px' }}>{name}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: '11px' }}>
            ID: {record.stock_id}
          </Text>
        </div>
      )
    },
    {
      title: '热度值',
      dataIndex: 'heat_value',
      key: 'heat_value',
      sorter: (a: any, b: any) => a.heat_value - b.heat_value,
      render: (value: number) => (
        <div>
          <div style={{ 
            fontSize: '16px',
            fontWeight: '600',
            color: conceptAnalysisUtils.getHeatColor(value / 1000) 
          }}>
            {conceptAnalysisUtils.formatHeatValue(value)}
          </div>
          <Progress
            percent={Math.min((value / 10000) * 100, 100)}
            size="small"
            strokeColor={conceptAnalysisUtils.getHeatColor(value / 1000)}
            showInfo={false}
            style={{ marginTop: '4px' }}
          />
          <Text style={{ fontSize: '10px', color: '#9ca3af' }}>
            {conceptAnalysisUtils.getHeatLevel(value / 1000)}
          </Text>
        </div>
      )
    },
    {
      title: '相关概念',
      dataIndex: 'concepts',
      key: 'concepts',
      render: (concepts: string[]) => (
        <div>
          {concepts?.slice(0, 2).map((concept, index) => (
            <Tag 
              key={index} 
              color="blue"
              style={{ marginBottom: '2px', fontSize: '12px' }}
            >
              {concept}
            </Tag>
          ))}
          {concepts?.length > 2 && (
            <Tooltip 
              title={concepts.slice(2).join(', ')}
              placement="topLeft"
            >
              <Tag color="default" style={{ fontSize: '12px' }}>
                +{concepts.length - 2}
              </Tag>
            </Tooltip>
          )}
          {!concepts?.length && (
            <Text type="secondary" style={{ fontSize: '12px' }}>
              暂无概念
            </Text>
          )}
        </div>
      )
    }
  ];

  // 热度分布图表配置
  const getDistributionChartOptions = () => {
    if (!chartData?.distribution_chart) return {};

    return {
      title: {
        text: '可转债热度分布',
        textStyle: { fontSize: 14, fontWeight: 'normal' }
      },
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c}只 ({d}%)'
      },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          data: chartData.distribution_chart.categories?.map((cat: string, index: number) => ({
            name: cat,
            value: chartData.distribution_chart.data[index]
          })) || [],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    };
  };

  // 热度排行图表配置
  const getTopBondsChartOptions = () => {
    if (!chartData?.top_bonds_chart) return {};

    return {
      title: {
        text: '热度Top20',
        textStyle: { fontSize: 14, fontWeight: 'normal' }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'value',
        axisLabel: { formatter: '{value}' }
      },
      yAxis: {
        type: 'category',
        data: chartData.top_bonds_chart.categories?.reverse() || [],
        axisLabel: { fontSize: 10 }
      },
      series: [
        {
          type: 'bar',
          data: chartData.top_bonds_chart.data?.reverse() || [],
          itemStyle: {
            color: (params: any) => {
              const colors = ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6'];
              return colors[params.dataIndex % colors.length];
            }
          }
        }
      ]
    };
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题和控制区域 */}
      <Card style={{ marginBottom: '24px', borderRadius: '12px' }}>
        <Row justify="space-between" align="middle">
          <Col xs={24} md={12}>
            <Title level={2} style={{ margin: '0 0 8px 0', color: '#1f2937' }}>
              <DollarOutlined style={{ marginRight: '8px', color: '#f59e0b' }} />
              可转债分析
            </Title>
            <Text type="secondary">
              专注1开头代码的可转债市场热度分析
            </Text>
          </Col>
          
          <Col xs={24} md={12}>
            <Space size="middle" style={{ float: 'right' }}>
              <DatePicker
                value={dayjs(selectedDate)}
                onChange={(date) => {
                  if (date) {
                    setSelectedDate(date.format('YYYY-MM-DD'));
                  }
                }}
                format="YYYY-MM-DD"
                placeholder="选择日期"
              />
              
              <Button 
                icon={<ReloadOutlined />}
                onClick={() => loadBondData(selectedDate, currentPage, pageSize)}
                loading={loading}
              >
                刷新
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 用户权限提示 */}
      {user?.memberType === 'free' && (
        <Alert
          message="可转债分析功能"
          description="升级会员解锁完整的可转债市场分析功能"
          type="warning"
          showIcon
          style={{ marginBottom: '24px' }}
          action={<Button type="primary" size="small">升级会员</Button>}
        />
      )}

      <Row gutter={[24, 24]}>
        {/* 左侧：统计概览 */}
        <Col xs={24} lg={8}>
          {/* 市场统计 */}
          <Card 
            title={
              <Space>
                <TrophyOutlined style={{ color: '#f59e0b' }} />
                <span>市场概况</span>
              </Space>
            }
            style={{ marginBottom: '24px', borderRadius: '12px' }}
          >
            {bondData?.statistics ? (
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Statistic
                    title="总数量"
                    value={bondData.statistics.total_bonds}
                    suffix="只"
                    valueStyle={{ color: '#3b82f6' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="平均热度"
                    value={bondData.statistics.avg_heat_value}
                    valueStyle={{ color: '#10b981' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="最高热度"
                    value={bondData.statistics.max_heat_value}
                    valueStyle={{ color: '#ef4444' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="分析日期"
                    value={conceptAnalysisUtils.formatDate(selectedDate)}
                    valueStyle={{ fontSize: '16px', color: '#6b7280' }}
                  />
                </Col>
              </Row>
            ) : (
              <div style={{ textAlign: 'center', padding: '20px' }}>
                {loading ? (
                  <Spin tip="加载统计数据..." />
                ) : (
                  <Text type="secondary">暂无统计数据</Text>
                )}
              </div>
            )}
          </Card>

          {/* 热度分布图 */}
          {chartData && (
            <Card 
              title="热度分布"
              style={{ marginBottom: '24px', borderRadius: '12px' }}
            >
              <ReactECharts
                option={getDistributionChartOptions()}
                style={{ height: '300px' }}
                opts={{ renderer: 'svg' }}
              />
            </Card>
          )}

          {/* 热度排行图 */}
          {chartData && (
            <Card 
              title="热度排行"
              style={{ borderRadius: '12px' }}
            >
              <ReactECharts
                option={getTopBondsChartOptions()}
                style={{ height: '400px' }}
                opts={{ renderer: 'svg' }}
              />
            </Card>
          )}
        </Col>

        {/* 右侧：可转债列表 */}
        <Col xs={24} lg={16}>
          <Card 
            title={
              <Space>
                <LineChartOutlined style={{ color: '#3b82f6' }} />
                <span>可转债列表</span>
                <Badge 
                  count={filteredBonds.length} 
                  style={{ backgroundColor: '#3b82f6' }} 
                />
              </Space>
            }
            extra={
              <Space>
                <Search
                  placeholder="搜索债券名称、代码或概念"
                  style={{ width: 200 }}
                  value={filterText}
                  onChange={(e) => setFilterText(e.target.value)}
                  prefix={<SearchOutlined />}
                  allowClear
                />
                
                <Select
                  value={sortBy}
                  onChange={setSortBy}
                  style={{ width: 100 }}
                  suffixIcon={<FilterOutlined />}
                >
                  <Option value="heat">按热度</Option>
                  <Option value="name">按名称</Option>
                </Select>
              </Space>
            }
            style={{ borderRadius: '12px' }}
          >
            {loading ? (
              <div style={{ textAlign: 'center', padding: '60px' }}>
                <Spin size="large" tip="正在加载可转债数据..."/>
              </div>
            ) : filteredBonds.length > 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                <Table
                  columns={bondColumns}
                  dataSource={filteredBonds}
                  rowKey="stock_id"
                  pagination={{
                    current: currentPage,
                    pageSize: pageSize,
                    total: bondData?.pagination?.total || filteredBonds.length,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total) => `共 ${total} 只可转债`,
                    onChange: (page, size) => {
                      setCurrentPage(page);
                      if (size !== pageSize) {
                        setPageSize(size);
                      }
                    }
                  }}
                  scroll={{ x: 800 }}
                  size="middle"
                />
              </motion.div>
            ) : (
              <Empty 
                description="暂无可转债数据或未找到匹配结果"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            )}
          </Card>
        </Col>
      </Row>

      {/* 功能说明 */}
      {!loading && !bondData && (
        <Card style={{ textAlign: 'center', marginTop: '24px', borderRadius: '12px' }}>
          <div style={{ padding: '40px' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>💰</div>
            <Title level={3} style={{ color: '#6b7280' }}>可转债市场分析</Title>
            <Paragraph style={{ color: '#9ca3af', maxWidth: '600px', margin: '0 auto' }}>
              专门分析1开头代码的可转债品种，提供热度排名、概念关联和市场分布等维度的深度分析。
              帮助投资者发现可转债市场的投资机会。
            </Paragraph>
            
            <Row gutter={[24, 16]} style={{ marginTop: '32px', maxWidth: '600px', margin: '32px auto 0' }}>
              <Col span={8}>
                <div>
                  <div style={{ fontSize: '24px', marginBottom: '8px' }}>📊</div>
                  <Text strong>热度分析</Text>
                  <div style={{ marginTop: '8px' }}>
                    <Text type="secondary">多维度热度评估</Text>
                  </div>
                </div>
              </Col>
              <Col span={8}>
                <div>
                  <div style={{ fontSize: '24px', marginBottom: '8px' }}>🏷️</div>
                  <Text strong>概念关联</Text>
                  <div style={{ marginTop: '8px' }}>
                    <Text type="secondary">概念标签分析</Text>
                  </div>
                </div>
              </Col>
              <Col span={8}>
                <div>
                  <div style={{ fontSize: '24px', marginBottom: '8px' }}>📈</div>
                  <Text strong>市场分布</Text>
                  <div style={{ marginTop: '8px' }}>
                    <Text type="secondary">可视化市场结构</Text>
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

export default ConvertibleBondPage;