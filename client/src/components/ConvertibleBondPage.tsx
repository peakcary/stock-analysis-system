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
  Table,
  Tag,
  DatePicker,
  Divider,
  Empty,
  Tooltip,
  Progress,
  Select,
  Statistic
} from 'antd';
import { 
  SearchOutlined, 
  FireOutlined, 
  TrophyOutlined, 
  ExperimentOutlined,
  InfoCircleOutlined,
  AreaChartOutlined,
  DownOutlined,
  UpOutlined,
  BankOutlined
} from '@ant-design/icons';
import type { ColumnType } from 'antd/es/table';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

interface ConvertibleBondConcept {
  concept_name: string;
  convertible_bond_count: number;
  total_convertible_volume: number;
  concept_total_volume: number;
  convertible_percentage: number;
  bonds: ConvertibleBond[];
}

interface ConvertibleBond {
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

const ConvertibleBondPage: React.FC = () => {
  const [bondConcepts, setBondConcepts] = useState<ConvertibleBondConcept[]>([]);
  const [loading, setLoading] = useState(false);
  const [tradingDate, setTradingDate] = useState<string>(dayjs().format('YYYY-MM-DD'));
  const [expandedConcepts, setExpandedConcepts] = useState<Record<string, boolean>>({});
  const [visibleBonds, setVisibleBonds] = useState<Record<string, number>>({});
  const [chartData, setChartData] = useState<ChartData[]>([]);
  const [selectedBond, setSelectedBond] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('volume'); // volume, percentage, count
  const [limit, setLimit] = useState<number>(50);

  // 查询转债概念排行
  const searchConvertibleBonds = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('admin_token') || localStorage.getItem('token');
      const response = await fetch(`/api/v1/stock-analysis/convertible-bonds/concepts?trading_date=${tradingDate}&limit=${limit}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error('查询失败');
      }
      
      const data = await response.json();
      let concepts = data.concepts || [];
      
      // 排序
      switch (sortBy) {
        case 'volume':
          concepts.sort((a: ConvertibleBondConcept, b: ConvertibleBondConcept) => 
            b.total_convertible_volume - a.total_convertible_volume);
          break;
        case 'percentage':
          concepts.sort((a: ConvertibleBondConcept, b: ConvertibleBondConcept) => 
            b.convertible_percentage - a.convertible_percentage);
          break;
        case 'count':
          concepts.sort((a: ConvertibleBondConcept, b: ConvertibleBondConcept) => 
            b.convertible_bond_count - a.convertible_bond_count);
          break;
      }
      
      setBondConcepts(concepts);
      
      // 初始化显示状态
      const initialVisible: Record<string, number> = {};
      concepts.forEach((concept: ConvertibleBondConcept) => {
        initialVisible[concept.concept_name] = 10;
      });
      setVisibleBonds(initialVisible);
      
      const conceptCount = concepts.length;
      const totalBonds = concepts.reduce((sum, concept) => sum + concept.convertible_bond_count, 0);
      message.success(`查询成功，找到${conceptCount}个概念，共${totalBonds}只转债`);
    } catch (error) {
      message.error('查询失败，请检查网络连接');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // 页面加载时自动查询
  useEffect(() => {
    searchConvertibleBonds();
  }, [sortBy]);

  // 查看转债图表
  const viewBondChart = async (bondCode: string, conceptName: string) => {
    try {
      const token = localStorage.getItem('admin_token') || localStorage.getItem('token');
      const response = await fetch(`/api/v1/stock-analysis/stock/${bondCode}/chart-data?concept_name=${conceptName}&days=30`, {
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
      setSelectedBond(`${bondCode} - ${conceptName}`);
      message.success('图表数据加载成功');
    } catch (error) {
      message.error('获取图表数据失败');
      console.error(error);
    }
  };

  // 展开更多转债
  const showMoreBonds = (conceptName: string) => {
    setVisibleBonds(prev => ({
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

  // 转债表格列定义
  const bondColumns: ColumnType<ConvertibleBond>[] = [
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
      title: '转债代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 100,
      render: (code: string, record: ConvertibleBond) => (
        <Button 
          type="link" 
          size="small"
          style={{ color: '#722ed1' }}
          onClick={() => viewBondChart(code, bondConcepts.find(c => c.bonds.includes(record))?.concept_name || '')}
        >
          {code}
        </Button>
      ),
    },
    {
      title: '转债名称',
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
      width: 100,
      render: (percentage: number) => (
        <div>
          <Text>{percentage ? percentage.toFixed(2) : 0}%</Text>
          <Progress
            percent={Math.min(percentage || 0, 100)}
            size="small"
            showInfo={false}
            strokeColor={percentage > 20 ? '#722ed1' : percentage > 10 ? '#faad14' : '#52c41a'}
          />
        </div>
      ),
    },
  ];

  // 概念列表的列定义
  const conceptColumns: ColumnType<ConvertibleBondConcept>[] = [
    {
      title: '排名',
      key: 'index',
      width: 70,
      render: (_, __, index) => (
        <Tag color="purple" style={{ fontSize: '12px' }}>
          #{index + 1}
        </Tag>
      ),
    },
    {
      title: '概念名称',
      dataIndex: 'concept_name',
      key: 'concept_name',
      render: (name: string) => <Text strong>{name}</Text>,
    },
    {
      title: '转债数量',
      dataIndex: 'convertible_bond_count',
      key: 'convertible_bond_count',
      width: 100,
      render: (count: number) => (
        <Text style={{ color: '#722ed1', fontWeight: '600' }}>
          {count}只
        </Text>
      ),
    },
    {
      title: '转债总量',
      dataIndex: 'total_convertible_volume',
      key: 'total_convertible_volume',
      render: (volume: number) => (
        <Text>{volume ? volume.toLocaleString() : 0}</Text>
      ),
    },
    {
      title: '转债占比',
      dataIndex: 'convertible_percentage',
      key: 'convertible_percentage',
      width: 120,
      render: (percentage: number) => (
        <div>
          <Text style={{ color: percentage > 50 ? '#722ed1' : '#666' }}>
            {percentage ? percentage.toFixed(1) : 0}%
          </Text>
          <Progress
            percent={Math.min(percentage || 0, 100)}
            size="small"
            showInfo={false}
            strokeColor={percentage > 50 ? '#722ed1' : '#1890ff'}
          />
        </div>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_, record) => (
        <Button 
          size="small"
          onClick={() => toggleConcept(record.concept_name)}
        >
          {expandedConcepts[record.concept_name] ? '收起' : '展开'}
        </Button>
      ),
    },
  ];

  const totalStats = {
    totalConcepts: bondConcepts.length,
    totalBonds: bondConcepts.reduce((sum, concept) => sum + concept.convertible_bond_count, 0),
    totalVolume: bondConcepts.reduce((sum, concept) => sum + concept.total_convertible_volume, 0),
    avgPercentage: bondConcepts.length > 0 
      ? bondConcepts.reduce((sum, concept) => sum + concept.convertible_percentage, 0) / bondConcepts.length 
      : 0
  };

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>
        <ExperimentOutlined style={{ color: '#722ed1', marginRight: 8 }} />
        转债概念分析
      </Title>
      
      {/* 控制面板 */}
      <Card style={{ marginBottom: 24, borderRadius: '12px' }}>
        <Row gutter={16} align="middle">
          <Col span={3}>
            <Text strong>交易日期:</Text>
          </Col>
          <Col span={4}>
            <DatePicker
              value={dayjs(tradingDate)}
              onChange={(date) => setTradingDate(date ? date.format('YYYY-MM-DD') : dayjs().format('YYYY-MM-DD'))}
              format="YYYY-MM-DD"
              placeholder="交易日期"
            />
          </Col>
          <Col span={3}>
            <Text strong>排序方式:</Text>
          </Col>
          <Col span={4}>
            <Select
              value={sortBy}
              onChange={(value) => setSortBy(value)}
              style={{ width: '100%' }}
            >
              <Option value="volume">按交易量</Option>
              <Option value="percentage">按转债占比</Option>
              <Option value="count">按转债数量</Option>
            </Select>
          </Col>
          <Col span={3}>
            <Button 
              type="primary" 
              icon={<SearchOutlined />}
              loading={loading}
              onClick={searchConvertibleBonds}
            >
              刷新数据
            </Button>
          </Col>
          <Col span={7}>
            <Text type="secondary">
              <InfoCircleOutlined style={{ marginRight: 4 }} />
              分析转债在各概念中的排名和交易情况
            </Text>
          </Col>
        </Row>
      </Card>

      {/* 统计概览 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card style={{ borderRadius: '8px' }}>
            <Statistic
              title="涉及概念数"
              value={totalStats.totalConcepts}
              prefix={<BankOutlined style={{ color: '#722ed1' }} />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card style={{ borderRadius: '8px' }}>
            <Statistic
              title="转债总数"
              value={totalStats.totalBonds}
              suffix="只"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card style={{ borderRadius: '8px' }}>
            <Statistic
              title="总交易量"
              value={totalStats.totalVolume}
              formatter={(value) => value ? Number(value).toLocaleString() : '0'}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card style={{ borderRadius: '8px' }}>
            <Statistic
              title="平均转债占比"
              value={totalStats.avgPercentage}
              precision={1}
              suffix="%"
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 结果展示区域 */}
      {loading && (
        <Card style={{ textAlign: 'center', borderRadius: '12px' }}>
          <Spin size="large" tip="正在查询转债概念数据..." />
        </Card>
      )}

      {!loading && bondConcepts.length > 0 && (
        <Row gutter={16}>
          <Col span={16}>
            <Card 
              title={
                <Space>
                  <FireOutlined style={{ color: '#722ed1' }} />
                  <span>转债概念排行榜</span>
                  <Tag color="purple">共{bondConcepts.length}个概念</Tag>
                </Space>
              }
              style={{ marginBottom: 24, borderRadius: '12px' }}
            >
              {/* 概念列表表格 */}
              <Table
                dataSource={bondConcepts}
                columns={conceptColumns}
                rowKey="concept_name"
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `共 ${total} 个概念`
                }}
                expandable={{
                  expandedRowKeys: Object.keys(expandedConcepts).filter(key => expandedConcepts[key]),
                  expandedRowRender: (record) => (
                    <div style={{ padding: '16px', backgroundColor: '#fafafa', borderRadius: '8px' }}>
                      <Title level={5} style={{ marginBottom: 16 }}>
                        {record.concept_name} - 转债明细 
                        (前{Math.min(visibleBonds[record.concept_name] || 10, record.bonds.length)}只)
                      </Title>
                      <Table
                        dataSource={record.bonds ? record.bonds.slice(0, visibleBonds[record.concept_name] || 10) : []}
                        columns={bondColumns}
                        size="small"
                        pagination={false}
                        rowKey="stock_code"
                      />
                      
                      {record.bonds && record.bonds.length > (visibleBonds[record.concept_name] || 10) && (
                        <div style={{ textAlign: 'center', marginTop: 16 }}>
                          <Button 
                            type="dashed"
                            onClick={() => showMoreBonds(record.concept_name)}
                          >
                            显示更多 (+10) - 还有{record.bonds.length - (visibleBonds[record.concept_name] || 10)}只转债
                          </Button>
                        </div>
                      )}
                    </div>
                  ),
                  onExpand: (expanded, record) => {
                    setExpandedConcepts(prev => ({
                      ...prev,
                      [record.concept_name]: expanded
                    }));
                  }
                }}
              />
            </Card>
          </Col>
          
          <Col span={8}>
            <Card 
              title={
                <Space>
                  <AreaChartOutlined />
                  <span>转债图表分析</span>
                </Space>
              }
              style={{ marginBottom: 24, borderRadius: '12px' }}
            >
              {chartData.length > 0 ? (
                <div>
                  <Title level={5}>{selectedBond} 趋势图</Title>
                  
                  {/* 这里可以集成真实的图表库 */}
                  <div style={{ height: 300, border: '1px solid #d9d9d9', borderRadius: 6, padding: 16 }}>
                    <Text type="secondary">📈 转债数据 ({chartData.length} 个数据点)</Text>
                    <div style={{ marginTop: 16, maxHeight: 240, overflowY: 'auto' }}>
                      {chartData.slice(0, 10).map((point, index) => (
                        <div key={index} style={{ marginBottom: 8, fontSize: '12px' }}>
                          <Text>{point.date}:</Text>
                          <br />
                          <Text type="secondary">
                            交易量: {point.volume ? point.volume.toLocaleString() : 0}
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
                  <div style={{ fontSize: '48px', marginBottom: 16 }}>💎</div>
                  <Text type="secondary">点击转债代码查看图表</Text>
                </div>
              )}
            </Card>

            {/* 转债特色说明 */}
            <Card title="转债特色" style={{ borderRadius: '12px' }}>
              <div style={{ lineHeight: '1.8' }}>
                <div style={{ marginBottom: 12 }}>
                  <Text strong style={{ color: '#722ed1' }}>💎 转债特点:</Text>
                </div>
                <div style={{ marginBottom: 8 }}>
                  <Text type="secondary">• 代码以"1"开头</Text>
                </div>
                <div style={{ marginBottom: 8 }}>
                  <Text type="secondary">• 股债双重属性</Text>
                </div>
                <div style={{ marginBottom: 8 }}>
                  <Text type="secondary">• 下有保底上不封顶</Text>
                </div>
                <div style={{ marginBottom: 8 }}>
                  <Text type="secondary">• 流动性较好</Text>
                </div>
                <Divider style={{ margin: '16px 0' }} />
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    点击转债代码可查看详细走势
                  </Text>
                </div>
              </div>
            </Card>
          </Col>
        </Row>
      )}
      
      {!loading && bondConcepts.length === 0 && (
        <Card style={{ textAlign: 'center', padding: 40, borderRadius: '12px' }}>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <div>
                <Text type="secondary" style={{ fontSize: '16px' }}>
                  {tradingDate} 暂无转债概念数据
                </Text>
                <br />
                <Text type="secondary">
                  可以尝试选择其他交易日期
                </Text>
              </div>
            }
          >
            <Button type="primary" onClick={() => setTradingDate(dayjs().subtract(1, 'day').format('YYYY-MM-DD'))}>
              查看昨日数据
            </Button>
          </Empty>
        </Card>
      )}
    </div>
  );
};

export default ConvertibleBondPage;
