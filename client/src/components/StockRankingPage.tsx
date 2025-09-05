/**
 * 个股排名页面组件
 */

import React, { useState, useEffect } from 'react';
import {
  Card, Table, Typography, Space, Tag, Button, Statistic,
  Row, Col, Progress, Alert, Empty, Spin, Tooltip,
  Input, Select, Pagination, Tabs, message, Switch,
  Radio, Slider, Divider
} from 'antd';
import {
  ArrowUpOutlined, ArrowDownOutlined, DollarOutlined,
  StockOutlined, FireOutlined, EyeOutlined, SearchOutlined,
  BarChartOutlined, LineChartOutlined, CaretUpOutlined,
  CaretDownOutlined, TrophyOutlined, CrownOutlined,
  ThunderboltOutlined, FundOutlined, FilterOutlined
} from '@ant-design/icons';
import { motion } from 'framer-motion';
import dayjs from 'dayjs';
import { DailyAnalysisApi, ConceptRanking, analysisUtils } from '../services/dailyAnalysisApi';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { Search } = Input;
const { TabPane } = Tabs;

interface StockRankingPageProps {
  analysisDate?: string;
  user?: any;
}

type RankingType = 'net_inflow_rank' | 'price_rank' | 'turnover_rate_rank' | 'total_reads_rank';

interface RankingFilter {
  concept?: string;
  industry?: string;
  priceRange?: [number, number];
  netInflowRange?: [number, number];
}

export const StockRankingPage: React.FC<StockRankingPageProps> = ({
  analysisDate = dayjs().format('YYYY-MM-DD'),
  user
}) => {
  const [loading, setLoading] = useState(false);
  const [allRankings, setAllRankings] = useState<ConceptRanking[]>([]);
  const [filteredRankings, setFilteredRankings] = useState<ConceptRanking[]>([]);
  const [activeTab, setActiveTab] = useState<RankingType>('net_inflow_rank');
  const [searchText, setSearchText] = useState('');
  const [selectedConcept, setSelectedConcept] = useState<string>('');
  const [filter, setFilter] = useState<RankingFilter>({});
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [showAdvancedFilter, setShowAdvancedFilter] = useState(false);

  const isMember = user?.memberType !== 'free';
  const isPremium = user?.memberType === 'premium';

  // 获取所有概念列表
  const [concepts, setConcepts] = useState<string[]>([]);
  const [industries, setIndustries] = useState<string[]>([]);

  // 加载个股排名数据
  const loadStockRankings = async () => {
    setLoading(true);
    try {
      const response = await DailyAnalysisApi.getConceptRankings(analysisDate, undefined, 1000);
      const rankings = response.data.rankings;
      setAllRankings(rankings);
      setFilteredRankings(rankings);
      
      // 提取唯一的概念和行业列表
      const uniqueConcepts = Array.from(new Set(rankings.map(r => r.concept)));
      const uniqueIndustries = Array.from(new Set(rankings.map(r => r.industry)));
      setConcepts(uniqueConcepts);
      setIndustries(uniqueIndustries);
    } catch (error) {
      message.error('加载个股排名数据失败');
      console.error('Load stock rankings error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 应用过滤和排序
  const applyFilters = () => {
    let filtered = [...allRankings];

    // 文本搜索过滤
    if (searchText) {
      filtered = filtered.filter(ranking =>
        ranking.stock_name.includes(searchText) ||
        ranking.stock_code.includes(searchText) ||
        ranking.concept.includes(searchText) ||
        ranking.industry.includes(searchText)
      );
    }

    // 概念过滤
    if (filter.concept) {
      filtered = filtered.filter(ranking => ranking.concept === filter.concept);
    }

    // 行业过滤
    if (filter.industry) {
      filtered = filtered.filter(ranking => ranking.industry === filter.industry);
    }

    // 价格范围过滤
    if (filter.priceRange) {
      filtered = filtered.filter(ranking =>
        ranking.price >= filter.priceRange![0] && ranking.price <= filter.priceRange![1]
      );
    }

    // 净流入范围过滤
    if (filter.netInflowRange) {
      filtered = filtered.filter(ranking =>
        ranking.net_inflow >= filter.netInflowRange![0] && ranking.net_inflow <= filter.netInflowRange![1]
      );
    }

    // 按当前选中的排名类型排序
    filtered.sort((a, b) => (a[activeTab] || 0) - (b[activeTab] || 0));

    setFilteredRankings(filtered);
    setCurrentPage(1);
  };

  // 重置过滤器
  const resetFilters = () => {
    setFilter({});
    setSearchText('');
    setSelectedConcept('');
    applyFilters();
  };

  useEffect(() => {
    loadStockRankings();
  }, [analysisDate]);

  useEffect(() => {
    applyFilters();
  }, [searchText, filter, activeTab, allRankings]);

  const currentData = filteredRankings.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  // 排名标签配置
  const rankingTabs = [
    { key: 'net_inflow_rank', label: '净流入排名', icon: <DollarOutlined />, color: '#10b981' },
    { key: 'price_rank', label: '价格排名', icon: <LineChartOutlined />, color: '#3b82f6' },
    { key: 'turnover_rate_rank', label: '换手率排名', icon: <BarChartOutlined />, color: '#f59e0b' },
    { key: 'total_reads_rank', label: '热度排名', icon: <FireOutlined />, color: '#ef4444' }
  ];

  // 表格列定义
  const columns = [
    {
      title: '排名',
      dataIndex: activeTab,
      width: 80,
      fixed: 'left' as const,
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
            fontSize: '14px',
            fontWeight: '600',
            margin: '0 auto'
          }}>
            {rank <= 3 ? <TrophyOutlined /> : rank}
          </div>
        </div>
      )
    },
    {
      title: '股票信息',
      dataIndex: 'stock_name',
      width: 180,
      fixed: 'left' as const,
      render: (name: string, record: ConceptRanking) => (
        <div>
          <Text strong style={{ fontSize: '16px' }}>{name}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>{record.stock_code}</Text>
          <br />
          <Tag size="small" style={{ fontSize: '10px' }}>{record.concept}</Tag>
        </div>
      )
    },
    {
      title: '净流入',
      dataIndex: 'net_inflow',
      width: 130,
      render: (value: number, record: ConceptRanking) => (
        <div>
          <div style={{
            color: analysisUtils.getChangeColor(value),
            fontWeight: '600',
            fontSize: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}>
            {value >= 0 ? <CaretUpOutlined /> : <CaretDownOutlined />}
            {analysisUtils.formatNetInflow(value)}
          </div>
          <Text type="secondary" style={{ fontSize: '11px' }}>
            排名 #{record.net_inflow_rank}
          </Text>
        </div>
      )
    },
    {
      title: '价格',
      dataIndex: 'price',
      width: 120,
      render: (price: number, record: ConceptRanking) => (
        <div>
          <div style={{ fontSize: '16px', fontWeight: '600' }}>
            ¥{price.toFixed(2)}
          </div>
          <Text type="secondary" style={{ fontSize: '11px' }}>
            排名 #{record.price_rank}
          </Text>
        </div>
      )
    },
    {
      title: '换手率',
      dataIndex: 'turnover_rate',
      width: 120,
      render: (rate: number, record: ConceptRanking) => (
        <div>
          <div style={{ fontSize: '16px', fontWeight: '500' }}>
            {(rate * 100).toFixed(2)}%
          </div>
          <Text type="secondary" style={{ fontSize: '11px' }}>
            排名 #{record.turnover_rate_rank}
          </Text>
        </div>
      )
    },
    {
      title: '市场热度',
      dataIndex: 'total_reads',
      width: 140,
      render: (reads: number, record: ConceptRanking) => (
        <div>
          <Progress
            percent={Math.min(reads / 100000 * 100, 100)}
            size="small"
            strokeColor="#ef4444"
            showInfo={false}
            style={{ marginBottom: '4px' }}
          />
          <div style={{ fontSize: '12px', display: 'flex', justifyContent: 'space-between' }}>
            <span>{reads.toLocaleString()}</span>
            <Text type="secondary" style={{ fontSize: '11px' }}>
              #{record.total_reads_rank}
            </Text>
          </div>
        </div>
      )
    },
    {
      title: '行业',
      dataIndex: 'industry',
      width: 100,
      render: (industry: string) => (
        <Tag color="blue" style={{ fontSize: '11px' }}>{industry}</Tag>
      )
    }
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" tip="加载个股排名数据中..." />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      style={{ padding: '20px' }}
    >
      {/* 页头 */}
      <div style={{ marginBottom: '24px' }}>
        <Title level={2} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '12px' }}>
          <TrophyOutlined style={{ color: '#f59e0b' }} />
          个股排名榜
          <Tag color="blue" style={{ fontSize: '12px' }}>
            {analysisUtils.formatAnalysisDate(analysisDate)}
          </Tag>
        </Title>
        <Text type="secondary" style={{ fontSize: '14px' }}>
          全市场个股多维度排名分析 • 共 {allRankings.length} 只股票
        </Text>
      </div>

      {/* 排名类型切换 */}
      <Card style={{ marginBottom: '16px', borderRadius: '12px' }}>
        <Tabs
          activeKey={activeTab}
          onChange={(key) => setActiveTab(key as RankingType)}
          size="large"
          style={{ margin: '-8px -12px' }}
        >
          {rankingTabs.map(tab => (
            <TabPane
              key={tab.key}
              tab={
                <Space>
                  <span style={{ color: tab.color }}>{tab.icon}</span>
                  <span>{tab.label}</span>
                  <Tag size="small" style={{ marginLeft: '4px' }}>
                    {filteredRankings.length}
                  </Tag>
                </Space>
              }
            />
          ))}
        </Tabs>
      </Card>

      {/* 搜索和过滤栏 */}
      <Card style={{ marginBottom: '16px', borderRadius: '12px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Search
              placeholder="搜索股票代码、名称、概念或行业"
              allowClear
              value={searchText}
              onChange={e => setSearchText(e.target.value)}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Select
              placeholder="选择概念"
              allowClear
              value={filter.concept}
              onChange={(value) => setFilter({ ...filter, concept: value })}
              style={{ width: '100%' }}
              showSearch
            >
              {concepts.map(concept => (
                <Option key={concept} value={concept}>{concept}</Option>
              ))}
            </Select>
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Select
              placeholder="选择行业"
              allowClear
              value={filter.industry}
              onChange={(value) => setFilter({ ...filter, industry: value })}
              style={{ width: '100%' }}
              showSearch
            >
              {industries.map(industry => (
                <Option key={industry} value={industry}>{industry}</Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} md={8}>
            <Space>
              <Button 
                icon={<FilterOutlined />}
                onClick={() => setShowAdvancedFilter(!showAdvancedFilter)}
              >
                高级筛选
              </Button>
              <Button onClick={resetFilters}>
                重置
              </Button>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                显示 {filteredRankings.length} / {allRankings.length}
              </Text>
            </Space>
          </Col>
        </Row>

        {/* 高级过滤选项 */}
        {showAdvancedFilter && (
          <div style={{ marginTop: '16px', padding: '16px', background: '#fafafa', borderRadius: '8px' }}>
            <Row gutter={[16, 16]}>
              <Col xs={24} md={12}>
                <Text strong style={{ fontSize: '12px', marginBottom: '8px', display: 'block' }}>
                  价格区间 (元)
                </Text>
                <Slider
                  range
                  min={0}
                  max={500}
                  value={filter.priceRange || [0, 500]}
                  onChange={(value) => setFilter({ ...filter, priceRange: value as [number, number] })}
                  marks={{ 0: '0', 100: '100', 200: '200', 500: '500+' }}
                />
              </Col>
              <Col xs={24} md={12}>
                <Text strong style={{ fontSize: '12px', marginBottom: '8px', display: 'block' }}>
                  净流入区间 (万元)
                </Text>
                <Slider
                  range
                  min={-100000}
                  max={100000}
                  value={filter.netInflowRange || [-100000, 100000]}
                  onChange={(value) => setFilter({ ...filter, netInflowRange: value as [number, number] })}
                  marks={{ 
                    [-100000]: '-10万', 
                    [-10000]: '-1万',
                    0: '0', 
                    10000: '1万',
                    100000: '10万+'
                  }}
                />
              </Col>
            </Row>
          </div>
        )}
      </Card>

      {/* 排名表格 */}
      <Card style={{ borderRadius: '12px' }}>
        {!isMember && (
          <Alert
            message="会员功能限制"
            description="免费用户只能查看前20名，升级会员查看完整排行榜"
            type="warning"
            showIcon
            style={{ marginBottom: '16px' }}
            action={
              <Button type="primary" size="small">
                立即升级
              </Button>
            }
          />
        )}

        {filteredRankings.length > 0 ? (
          <>
            <Table
              columns={columns}
              dataSource={isMember ? currentData : currentData.slice(0, 20)}
              rowKey="stock_code"
              pagination={false}
              scroll={{ x: 1000 }}
              size="small"
            />

            {isMember && (
              <div style={{ marginTop: '16px', textAlign: 'center' }}>
                <Pagination
                  current={currentPage}
                  total={filteredRankings.length}
                  pageSize={pageSize}
                  showSizeChanger
                  showQuickJumper
                  showTotal={(total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`}
                  onChange={(page, size) => {
                    setCurrentPage(page);
                    if (size) setPageSize(size);
                  }}
                />
              </div>
            )}

            {!isMember && currentData.length > 20 && (
              <div style={{
                position: 'relative',
                marginTop: '16px',
                padding: '20px',
                background: 'linear-gradient(135deg, #fef3c7 0%, #fbbf24 100%)',
                borderRadius: '8px',
                textAlign: 'center'
              }}>
                <Text style={{ color: '#92400e', fontSize: '14px', fontWeight: '600' }}>
                  🏆 升级会员查看完整的 {filteredRankings.length} 只股票排名
                </Text>
              </div>
            )}
          </>
        ) : (
          <Empty
            description="暂无符合条件的股票数据"
            style={{ padding: '40px' }}
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Card>
    </motion.div>
  );
};

export default StockRankingPage;