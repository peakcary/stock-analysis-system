/**
 * 概念详情页面组件
 */

import React, { useState, useEffect } from 'react';
import {
  Card, Table, Typography, Space, Tag, Button, Statistic,
  Row, Col, Progress, Alert, Empty, Spin, Tooltip,
  Input, Select, Pagination, Divider, message
} from 'antd';
import {
  ArrowUpOutlined, ArrowDownOutlined, DollarOutlined,
  StockOutlined, FireOutlined, EyeOutlined, SearchOutlined,
  BarChartOutlined, LineChartOutlined, CaretUpOutlined,
  CaretDownOutlined, TrophyOutlined, CrownOutlined
} from '@ant-design/icons';
import { motion } from 'framer-motion';
import dayjs from 'dayjs';
import { DailyAnalysisApi, ConceptDetail, ConceptRanking, analysisUtils } from '../services/dailyAnalysisApi';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { Search } = Input;

interface ConceptDetailPageProps {
  conceptName: string;
  analysisDate?: string;
  onClose?: () => void;
  user?: any;
}

export const ConceptDetailPage: React.FC<ConceptDetailPageProps> = ({
  conceptName,
  analysisDate = dayjs().format('YYYY-MM-DD'),
  onClose,
  user
}) => {
  const [loading, setLoading] = useState(false);
  const [conceptDetail, setConceptDetail] = useState<ConceptDetail | null>(null);
  const [filteredRankings, setFilteredRankings] = useState<ConceptRanking[]>([]);
  const [sortBy, setSortBy] = useState<'net_inflow_rank' | 'price_rank' | 'turnover_rate_rank' | 'total_reads_rank'>('net_inflow_rank');
  const [searchText, setSearchText] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const isSuperAdmin = user?.memberType === 'premium' && user?.queries_remaining >= 999999;
  const isMember = user?.memberType !== 'free' || isSuperAdmin;
  const isPremium = user?.memberType === 'premium' || isSuperAdmin;

  // 加载概念详情数据
  const loadConceptDetail = async () => {
    setLoading(true);
    try {
      const response = await DailyAnalysisApi.getConceptDetail(conceptName, analysisDate);
      setConceptDetail(response.data);
      setFilteredRankings(response.data.stock_rankings);
    } catch (error) {
      message.error('加载概念详情失败');
      console.error('Load concept detail error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 处理搜索和过滤
  const handleSearch = (value: string) => {
    setSearchText(value);
    if (!conceptDetail) return;

    let filtered = conceptDetail.stock_rankings;
    if (value) {
      filtered = filtered.filter(ranking => 
        ranking.stock_name.includes(value) || 
        ranking.stock_code.includes(value) ||
        ranking.industry.includes(value)
      );
    }

    // 应用排序
    filtered.sort((a, b) => {
      return (a[sortBy] || 0) - (b[sortBy] || 0);
    });

    setFilteredRankings(filtered);
    setCurrentPage(1);
  };

  // 处理排序变化
  const handleSortChange = (value: any) => {
    setSortBy(value);
    const sorted = [...filteredRankings].sort((a, b) => {
      return (a[value] || 0) - (b[value] || 0);
    });
    setFilteredRankings(sorted);
    setCurrentPage(1);
  };

  useEffect(() => {
    loadConceptDetail();
  }, [conceptName, analysisDate]);

  useEffect(() => {
    handleSearch(searchText);
  }, [sortBy]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" tip="加载概念详情中..." />
      </div>
    );
  }

  if (!conceptDetail) {
    return (
      <Empty 
        description="未找到概念详情数据"
        style={{ padding: '100px' }}
      />
    );
  }

  const { concept_summary, stock_rankings } = conceptDetail;
  const currentData = filteredRankings.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  // 表格列定义
  const columns = [
    {
      title: '排名',
      dataIndex: sortBy,
      width: 80,
      render: (rank: number, record: ConceptRanking, index: number) => (
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '28px',
            height: '28px',
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
            {rank <= 3 && <TrophyOutlined />}
            {rank > 3 && rank}
          </div>
        </div>
      )
    },
    {
      title: '股票',
      dataIndex: 'stock_name',
      width: 150,
      render: (name: string, record: ConceptRanking) => (
        <div>
          <Text strong style={{ fontSize: '14px' }}>{name}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>{record.stock_code}</Text>
        </div>
      )
    },
    {
      title: '净流入',
      dataIndex: 'net_inflow',
      width: 120,
      render: (value: number, record: ConceptRanking) => (
        <div>
          <div style={{ 
            color: analysisUtils.getChangeColor(value),
            fontWeight: '600',
            fontSize: '14px'
          }}>
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
      width: 100,
      render: (price: number, record: ConceptRanking) => (
        <div>
          <div style={{ fontSize: '14px', fontWeight: '500' }}>
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
      width: 100,
      render: (rate: number, record: ConceptRanking) => (
        <div>
          <div style={{ fontSize: '14px' }}>
            {(rate * 100).toFixed(2)}%
          </div>
          <Text type="secondary" style={{ fontSize: '11px' }}>
            排名 #{record.turnover_rate_rank}
          </Text>
        </div>
      )
    },
    {
      title: '热度',
      dataIndex: 'total_reads',
      width: 120,
      render: (reads: number, record: ConceptRanking) => (
        <div>
          <Progress
            percent={Math.min(reads / 100000 * 100, 100)}
            size="small"
            strokeColor="#f59e0b"
            showInfo={false}
            style={{ marginBottom: '4px' }}
          />
          <div style={{ fontSize: '12px' }}>
            {reads.toLocaleString()} 
            <Text type="secondary" style={{ marginLeft: '4px', fontSize: '11px' }}>
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
        <Tag style={{ fontSize: '11px' }}>{industry}</Tag>
      )
    }
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}
    >
      {/* 页头 */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <Title level={2} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '12px' }}>
              <FireOutlined style={{ color: '#f59e0b' }} />
              {conceptName}
              <Tag color="blue" style={{ fontSize: '12px' }}>
                {analysisUtils.formatAnalysisDate(analysisDate)}
              </Tag>
            </Title>
            <Text type="secondary" style={{ fontSize: '14px' }}>
              概念详情分析 • 共 {stock_rankings.length} 只相关股票
            </Text>
          </div>
          {onClose && (
            <Button onClick={onClose}>返回</Button>
          )}
        </div>
      </div>

      {/* 概念汇总统计 */}
      <Card style={{ marginBottom: '24px', borderRadius: '12px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={6}>
            <Statistic
              title="个股数量"
              value={concept_summary.stock_count}
              suffix="只"
              prefix={<StockOutlined style={{ color: '#3b82f6' }} />}
              valueStyle={{ color: '#3b82f6' }}
            />
          </Col>
          <Col xs={24} sm={6}>
            <Statistic
              title="总净流入"
              value={analysisUtils.formatNetInflow(concept_summary.total_net_inflow)}
              prefix={<DollarOutlined style={{ color: analysisUtils.getChangeColor(concept_summary.total_net_inflow) }} />}
              valueStyle={{ color: analysisUtils.getChangeColor(concept_summary.total_net_inflow) }}
            />
          </Col>
          <Col xs={24} sm={6}>
            <Statistic
              title="平均价格"
              value={concept_summary.avg_price.toFixed(2)}
              suffix="元"
              prefix={<LineChartOutlined style={{ color: '#10b981' }} />}
              valueStyle={{ color: '#10b981' }}
            />
          </Col>
          <Col xs={24} sm={6}>
            <Statistic
              title="概念排名"
              value={`#${concept_summary.concept_rank}`}
              prefix={concept_summary.concept_rank <= 3 ? <CrownOutlined style={{ color: '#f59e0b' }} /> : <BarChartOutlined style={{ color: '#6b7280' }} />}
              valueStyle={{ 
                color: concept_summary.concept_rank <= 10 ? '#f59e0b' : '#6b7280',
                fontSize: '24px'
              }}
            />
          </Col>
        </Row>
      </Card>

      {/* 控制栏 */}
      <Card style={{ marginBottom: '16px', borderRadius: '12px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Search
              placeholder="搜索股票代码、名称或行业"
              allowClear
              onChange={e => handleSearch(e.target.value)}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Select
              value={sortBy}
              onChange={handleSortChange}
              style={{ width: '100%' }}
            >
              <Option value="net_inflow_rank">净流入排名</Option>
              <Option value="price_rank">价格排名</Option>
              <Option value="turnover_rate_rank">换手率排名</Option>
              <Option value="total_reads_rank">热度排名</Option>
            </Select>
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              显示 {filteredRankings.length} / {stock_rankings.length} 只股票
            </Text>
          </Col>
        </Row>
      </Card>

      {/* 个股排名表格 */}
      <Card style={{ borderRadius: '12px' }}>
        {!isMember && (
          <Alert
            message="会员功能限制"
            description="免费用户只能查看前5只股票，升级会员查看完整排名"
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
        
        <Table
          columns={columns}
          dataSource={isMember ? currentData : currentData.slice(0, 5)}
          rowKey="stock_code"
          pagination={false}
          scroll={{ x: 800 }}
          size="small"
          style={{
            filter: !isMember && currentData.length > 5 ? 'blur(0px)' : 'none'
          }}
        />

        {isMember && (
          <div style={{ marginTop: '16px', textAlign: 'right' }}>
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

        {!isMember && currentData.length > 5 && (
          <div style={{
            position: 'relative',
            marginTop: '16px',
            padding: '20px',
            background: 'linear-gradient(135deg, #fef3c7 0%, #fbbf24 100%)',
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <Text style={{ color: '#92400e', fontSize: '14px', fontWeight: '600' }}>
              🔐 升级会员查看完整的 {stock_rankings.length} 只股票排名
            </Text>
          </div>
        )}
      </Card>
    </motion.div>
  );
};

export default ConceptDetailPage;