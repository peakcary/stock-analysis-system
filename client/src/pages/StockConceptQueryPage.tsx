import React, { useState } from 'react';
import {
  Card, Button, Input, Spin, Empty, Alert, Tag, Row, Col,
  Table, Typography, Space, Statistic, message, Modal
} from 'antd';
import {
  SearchOutlined, LoadingOutlined, FireOutlined,
  StockOutlined, BankOutlined
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import { apiClient } from '../utils/auth';

const { Title, Text, Paragraph } = Typography;

interface ConceptRanking {
  concept_id: number;
  concept_name: string;
  rank: number;
  total_stocks: number;
  heat_value: number;
}

interface StockConceptData {
  stock_code: string;
  stock_name: string;
  trade_date: string;
  heat_value: number;
  concept_rankings: ConceptRanking[];
  total_concepts: number;
}

const StockConceptQueryPage: React.FC = () => {
  const [stockCode, setStockCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<StockConceptData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const handleQuery = async () => {
    if (!stockCode.trim()) {
      message.warning('请输入股票代码');
      return;
    }

    setLoading(true);
    setError(null);
    setData(null);
    setSearched(true);

    try {
      const response = await apiClient.get(
        `/api/v1/stock-analysis/stocks/${stockCode}/ranking`
      );

      if (response.data) {
        // 按热度值从高到低排序概念
        const sortedConcepts = [...response.data.concept_rankings].sort(
          (a, b) => b.heat_value - a.heat_value
        );

        setData({
          ...response.data,
          concept_rankings: sortedConcepts
        });
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || '查询失败，请检查股票代码';
      setError(errorMsg);
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleQuery();
    }
  };

  const columns = [
    {
      title: '排名',
      key: 'rank',
      width: 80,
      render: (_: any, record: ConceptRanking, index: number) => (
        <Tag color={index === 0 ? 'gold' : index === 1 ? 'silver' : 'blue'}>
          #{record.rank}
        </Tag>
      ),
    },
    {
      title: '概念名称',
      dataIndex: 'concept_name',
      key: 'concept_name',
      width: '30%',
      render: (text: string) => (
        <Text strong style={{ fontSize: '14px' }}>
          {text}
        </Text>
      ),
    },
    {
      title: '热度值',
      dataIndex: 'heat_value',
      key: 'heat_value',
      width: '20%',
      render: (value: number) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FireOutlined style={{ color: '#ff4d4f', fontSize: '16px' }} />
          <Text strong style={{ color: '#ff4d4f', fontSize: '14px' }}>
            {value.toFixed(2)}
          </Text>
        </div>
      ),
      sorter: (a: ConceptRanking, b: ConceptRanking) => b.heat_value - a.heat_value,
    },
    {
      title: '概念股票总数',
      dataIndex: 'total_stocks',
      key: 'total_stocks',
      width: '20%',
      render: (value: number) => (
        <Tag color="cyan">{value} 只</Tag>
      ),
      sorter: (a: ConceptRanking, b: ConceptRanking) => b.total_stocks - a.total_stocks,
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      style={{
        minHeight: '100vh',
        padding: '40px 20px',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {/* 页面标题 */}
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          style={{ textAlign: 'center', marginBottom: '40px', color: 'white' }}
        >
          <Title level={1} style={{
            fontSize: '48px',
            margin: '0 0 16px 0',
            color: 'white'
          }}>
            <StockOutlined style={{ marginRight: '16px' }} />
            股票概念查询
          </Title>
          <Paragraph style={{
            fontSize: '18px',
            color: 'rgba(255,255,255,0.9)',
            maxWidth: '600px',
            margin: '0 auto'
          }}>
            输入股票代码，查看该股票所属的所有概念及热度排名
          </Paragraph>
        </motion.div>

        {/* 查询卡片 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <Card
            bordered={false}
            style={{
              marginBottom: '40px',
              boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
              borderRadius: '16px',
            }}
          >
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div>
                <Text strong style={{ display: 'block', marginBottom: '12px', fontSize: '16px' }}>
                  股票代码
                </Text>
                <Input
                  size="large"
                  placeholder="输入股票代码，如：000001, 600000"
                  prefix={<StockOutlined />}
                  value={stockCode}
                  onChange={(e) => setStockCode(e.target.value.toUpperCase())}
                  onKeyPress={handleKeyPress}
                  style={{ borderRadius: '8px' }}
                />
              </div>

              <Button
                type="primary"
                size="large"
                icon={<SearchOutlined />}
                onClick={handleQuery}
                loading={loading}
                style={{
                  width: '100%',
                  height: '48px',
                  fontSize: '16px',
                  fontWeight: '600',
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  borderColor: 'transparent',
                }}
              >
                查询
              </Button>
            </Space>
          </Card>
        </motion.div>

        {/* 错误提示 */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              style={{ marginBottom: '24px' }}
            >
              <Alert
                message="查询失败"
                description={error}
                type="error"
                showIcon
                closable
                onClose={() => setError(null)}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* 加载状态 */}
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{ marginBottom: '40px' }}
          >
            <Card style={{ textAlign: 'center', padding: '60px 20px' }}>
              <Spin
                indicator={<LoadingOutlined style={{ fontSize: 48, color: '#667eea' }} />}
              />
              <p style={{ marginTop: '16px', color: '#666', fontSize: '16px' }}>
                正在查询股票信息...
              </p>
            </Card>
          </motion.div>
        )}

        {/* 结果显示 */}
        {!loading && searched && data && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {/* 股票信息卡片 */}
            <Card
              bordered={false}
              style={{
                marginBottom: '40px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
                borderRadius: '16px',
              }}
            >
              <Row gutter={[32, 32]} align="middle">
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>股票代码</Text>}
                    value={data.stock_code}
                    valueStyle={{ color: 'white', fontSize: '32px', fontWeight: 'bold' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>股票名称</Text>}
                    value={data.stock_name}
                    valueStyle={{ color: 'white', fontSize: '24px', fontWeight: 'bold' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>股票热度</Text>}
                    value={data.heat_value.toFixed(2)}
                    suffix={<FireOutlined style={{ marginLeft: '8px' }} />}
                    valueStyle={{ color: '#fff23b', fontSize: '28px', fontWeight: 'bold' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>所属概念数</Text>}
                    value={data.total_concepts}
                    suffix="个"
                    valueStyle={{ color: '#52c41a', fontSize: '28px', fontWeight: 'bold' }}
                  />
                </Col>
              </Row>
              <div style={{ marginTop: '16px', fontSize: '12px', color: 'rgba(255,255,255,0.6)' }}>
                数据日期：{data.trade_date}
              </div>
            </Card>

            {/* 概念列表 */}
            {data.concept_rankings.length > 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.1 }}
              >
                <Card
                  bordered={false}
                  style={{
                    boxShadow: '0 20px 60px rgba(0,0,0,0.1)',
                    borderRadius: '16px',
                  }}
                >
                  <Title level={3} style={{ marginBottom: '24px' }}>
                    <BankOutlined style={{ marginRight: '8px', color: '#667eea' }} />
                    所属概念列表
                  </Title>
                  <Table
                    columns={columns}
                    dataSource={data.concept_rankings}
                    rowKey={(record) => record.concept_id}
                    pagination={{
                      pageSize: 20,
                      showSizeChanger: true,
                      pageSizeOptions: ['10', '20', '50'],
                      showTotal: (total) => `共 ${total} 个概念`,
                    }}
                    bordered
                    size="middle"
                    rowClassName={(record, index) => {
                      if (index === 0) return 'rank-1';
                      if (index === 1) return 'rank-2';
                      if (index === 2) return 'rank-3';
                      return '';
                    }}
                  />
                </Card>
              </motion.div>
            ) : (
              <Card
                style={{
                  textAlign: 'center',
                  borderRadius: '16px',
                }}
              >
                <Empty
                  description="暂无概念数据"
                  style={{ padding: '40px 0' }}
                />
              </Card>
            )}
          </motion.div>
        )}

        {/* 空状态 */}
        {!loading && searched && !data && !error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <Card
              style={{
                textAlign: 'center',
                borderRadius: '16px',
              }}
            >
              <Empty
                description="未找到相关数据"
                style={{ padding: '40px 0' }}
              />
            </Card>
          </motion.div>
        )}

        {/* 初始状态提示 */}
        {!searched && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <Card
              style={{
                textAlign: 'center',
                borderRadius: '16px',
                background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
                border: 'none',
              }}
            >
              <Empty
                description="输入股票代码开始查询"
                style={{ padding: '60px 0' }}
              />
              <Paragraph style={{ color: '#666', marginTop: '16px' }}>
                支持格式：000001、600000、SH000001、SZ000001 等
              </Paragraph>
            </Card>
          </motion.div>
        )}
      </div>

      <style>{`
        .rank-1 {
          background-color: #fffbe6 !important;
        }
        .rank-2 {
          background-color: #f6f6f6 !important;
        }
        .rank-3 {
          background-color: #fafafa !important;
        }
      `}</style>
    </motion.div>
  );
};

export default StockConceptQueryPage;
