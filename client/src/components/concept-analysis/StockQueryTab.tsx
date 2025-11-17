import React, { useState } from 'react';
import {
  Input,
  Button,
  Card,
  Table,
  Space,
  Spin,
  Empty,
  Alert,
  Tag,
  Row,
  Col,
  Statistic,
  Typography,
  message,
} from 'antd';
import {
  SearchOutlined,
  LoadingOutlined,
  FireOutlined,
  StockOutlined,
  BankOutlined,
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import {
  getStockConceptRanking,
  ConceptRanking,
  StockConceptData,
} from '../../utils/conceptAnalysisApi';
import ConceptStockDrawer from './ConceptStockDrawer';

const { Title, Text, Paragraph } = Typography;

const StockQueryTab: React.FC = () => {
  const [stockCode, setStockCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<StockConceptData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [selectedConcept, setSelectedConcept] = useState<ConceptRanking | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

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
      const response = await getStockConceptRanking(stockCode);

      // 按热度值从高到低排序概念
      const sortedConcepts = [...response.concept_rankings].sort(
        (a, b) => b.heat_value - a.heat_value
      );

      setData({
        ...response,
        concept_rankings: sortedConcepts,
      });
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.detail || err.message || '查询失败，请检查股票代码';
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

  const handleConceptClick = (concept: ConceptRanking) => {
    setSelectedConcept(concept);
    setDrawerOpen(true);
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
      render: (text: string, record: ConceptRanking) => (
        <Button
          type="link"
          onClick={() => handleConceptClick(record)}
          style={{
            fontSize: '14px',
            fontWeight: '600',
            padding: 0,
            height: 'auto',
          }}
        >
          {text}
        </Button>
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
      render: (value: number) => <Tag color="cyan">{value} 只</Tag>,
      sorter: (a: ConceptRanking, b: ConceptRanking) => b.total_stocks - a.total_stocks,
    },
    {
      title: '操作',
      key: 'action',
      width: '10%',
      render: (_: any, record: ConceptRanking) => (
        <Button
          type="primary"
          size="small"
          onClick={() => handleConceptClick(record)}
        >
          查看股票
        </Button>
      ),
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      style={{ width: '100%' }}
    >
      {/* 查询框 */}
      <Card
        style={{
          marginBottom: '24px',
          borderRadius: '12px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
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
            <div
              style={{ marginTop: '16px', fontSize: '12px', color: 'rgba(255,255,255,0.6)' }}
            >
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

      {/* 概念内股票查看抽屉 */}
      <ConceptStockDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        concept={selectedConcept}
      />

      {/* CSS样式 */}
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

export default StockQueryTab;
