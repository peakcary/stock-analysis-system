/**
 * New High Concepts Page
 * Query concepts that reached new highs within N days
 */

import React, { useState } from 'react';
import {
  Card, Button, Spin, Table, Empty, Alert, Tag, Row, Col,
  Statistic, Space, Typography, message, InputNumber, DatePicker
} from 'antd';
import {
  FireOutlined, LoadingOutlined, ArrowUpOutlined, ThunderboltOutlined
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import dayjs from 'dayjs';
import { ConceptAnalysisApi, conceptUtils, NewHighConcept } from '../services/conceptApi';
import { designTokens } from '../styles/designTokens';

const { Title, Text, Paragraph } = Typography;

interface ClientNewHighConceptPageProps {
  user?: any;
}

const ClientNewHighConceptPage: React.FC<ClientNewHighConceptPageProps> = ({ user }) => {
  const [days, setDays] = useState(1);
  const [tradeDate, setTradeDate] = useState<any>(dayjs());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [concepts, setConcepts] = useState<NewHighConcept[]>([]);
  const [stats, setStats] = useState({ conceptCount: 0, stockCount: 0 });
  const [searched, setSearched] = useState(false);

  const handleQuery = async () => {
    if (!days || days < 1 || days > 30) {
      message.warning('请输入1-30之间的天数');
      return;
    }

    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const tradeDateStr = tradeDate ? tradeDate.format('YYYY-MM-DD') : undefined;
      const response = await ConceptAnalysisApi.getNewHighConcepts(days, tradeDateStr);

      setConcepts(response.concepts);
      setStats({
        conceptCount: response.total_concepts,
        stockCount: response.total_stocks,
      });
    } catch (err: any) {
      const errorMessage = err.message || '查询失败，请稍后重试';
      setError(errorMessage);
      setConcepts([]);
      setStats({ conceptCount: 0, stockCount: 0 });
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_, record: NewHighConcept, index: number) => (
        <Tag color={conceptUtils.getRankColor(index + 1)} style={{ fontWeight: 'bold' }}>
          #{index + 1}
        </Tag>
      ),
    },
    {
      title: '概念名称',
      dataIndex: ['concept', 'concept_name'],
      key: 'concept_name',
      width: '25%',
      render: (text: string) => (
        <Tag color="orange" style={{ fontSize: '13px', fontWeight: '500' }}>
          {text}
        </Tag>
      ),
    },
    {
      title: '热度值',
      dataIndex: 'total_heat_value',
      key: 'total_heat_value',
      width: '15%',
      render: (value: number) => (
        <Text style={{
          color: conceptUtils.getHeatColor(value),
          fontWeight: 'bold',
          fontSize: '14px'
        }}>
          {conceptUtils.formatNumber(value)}
        </Text>
      ),
      sorter: (a: NewHighConcept, b: NewHighConcept) => a.total_heat_value - b.total_heat_value,
    },
    {
      title: '股票数',
      dataIndex: 'stock_count',
      key: 'stock_count',
      width: '15%',
      render: (value: number) => (
        <Statistic value={value} valueStyle={{ color: designTokens.colors.primary[500], fontSize: '14px', fontWeight: 'bold' }} />
      ),
      sorter: (a: NewHighConcept, b: NewHighConcept) => a.stock_count - b.stock_count,
    },
    {
      title: '平均热度',
      dataIndex: 'average_heat_value',
      key: 'average_heat_value',
      width: '15%',
      render: (value: number) => (
        <Text style={{
          color: conceptUtils.getHeatColor(value),
          fontWeight: '600',
          fontSize: '13px'
        }}>
          {value.toFixed(2)}
        </Text>
      ),
      sorter: (a: NewHighConcept, b: NewHighConcept) => a.average_heat_value - b.average_heat_value,
    },
    {
      title: '检查天数',
      dataIndex: 'days_checked',
      key: 'days_checked',
      width: '15%',
      render: (value: number) => (
        <Tag color="blue">{value}天</Tag>
      ),
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      style={{
        minHeight: '100vh',
        padding: designTokens.spacing.md,
        background: `linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%)`,
      }}
    >
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {/* Header */}
        <Card
          bordered={false}
          style={{
            marginBottom: designTokens.spacing.md,
            boxShadow: '0 2px 8px rgba(245, 158, 11, 0.1)',
          }}
        >
          <Title level={2} style={{ marginBottom: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FireOutlined style={{ fontSize: '24px', color: '#f59e0b' }} />
            新高概念查询
          </Title>
          <Paragraph style={{ color: designTokens.colors.text.secondary, marginTop: '12px', marginBottom: 0 }}>
            查询在指定天数内达到新高的概念及其对应的股票信息
          </Paragraph>
        </Card>

        {/* Filter Card */}
        <Card bordered={false} style={{ marginBottom: designTokens.spacing.md }}>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Row gutter={[16, 16]} align="middle">
              <Col xs={24} sm={12} md={6}>
                <Text strong style={{ display: 'block', marginBottom: '8px' }}>天数范围</Text>
                <InputNumber
                  min={1}
                  max={30}
                  value={days}
                  onChange={(value) => setDays(value || 1)}
                  style={{ width: '100%' }}
                  size="large"
                  placeholder="1-30"
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Text strong style={{ display: 'block', marginBottom: '8px' }}>交易日期</Text>
                <DatePicker
                  value={tradeDate}
                  onChange={(date) => setTradeDate(date)}
                  style={{ width: '100%' }}
                  size="large"
                />
              </Col>
              <Col xs={24} md={12} style={{ display: 'flex', gap: '8px' }}>
                <Button
                  type="primary"
                  size="large"
                  onClick={handleQuery}
                  loading={loading}
                  style={{
                    background: `linear-gradient(135deg, #f59e0b 0%, #d97706 100%)`,
                    flex: 1
                  }}
                >
                  <ThunderboltOutlined /> 查询
                </Button>
              </Col>
            </Row>
          </Space>
        </Card>

        {/* Error Alert */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              style={{ marginBottom: designTokens.spacing.md }}
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

        {/* Loading State */}
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{ marginBottom: designTokens.spacing.md }}
          >
            <Card style={{ textAlign: 'center', padding: '40px' }}>
              <Spin indicator={<LoadingOutlined style={{ fontSize: 48, color: '#f59e0b' }} />} />
              <p style={{ marginTop: '16px', color: designTokens.colors.text.secondary }}>正在查询新高概念...</p>
            </Card>
          </motion.div>
        )}

        {/* Results */}
        {!loading && searched && !error && concepts.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {/* Statistics */}
            <Row gutter={[16, 16]} style={{ marginBottom: designTokens.spacing.md }}>
              <Col xs={24} sm={12} md={6}>
                <Card style={{ textAlign: 'center' }}>
                  <Statistic
                    title="新高概念数"
                    value={stats.conceptCount}
                    prefix={<FireOutlined />}
                    valueStyle={{ color: '#f59e0b', fontSize: '28px', fontWeight: 'bold' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card style={{ textAlign: 'center' }}>
                  <Statistic
                    title="相关股票数"
                    value={stats.stockCount}
                    prefix={<ArrowUpOutlined />}
                    valueStyle={{ color: '#10b981', fontSize: '28px', fontWeight: 'bold' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card style={{ textAlign: 'center' }}>
                  <Statistic
                    title="检查天数"
                    value={days}
                    suffix="天"
                    valueStyle={{ color: designTokens.colors.primary[500], fontSize: '28px', fontWeight: 'bold' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card style={{ textAlign: 'center' }}>
                  <Statistic
                    title="交易日期"
                    value={tradeDate?.format('YYYY-MM-DD')}
                    valueStyle={{ color: designTokens.colors.primary[400], fontSize: '16px', fontWeight: 'bold' }}
                  />
                </Card>
              </Col>
            </Row>

            {/* Table */}
            <Card bordered={false}>
              <Table
                columns={columns}
                dataSource={concepts}
                rowKey={(record) => record.concept.id}
                pagination={{
                  pageSize: 20,
                  showSizeChanger: true,
                  pageSizeOptions: ['10', '20', '50'],
                  showTotal: (total) => `共 ${total} 个概念`,
                }}
                bordered
                size="middle"
              />
            </Card>
          </motion.div>
        )}

        {/* Empty State */}
        {!loading && searched && (concepts.length === 0 || error) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <Card style={{
              textAlign: 'center',
              background: `linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%)`,
              border: 'none',
            }}>
              <Empty
                description={concepts.length === 0 ? '未找到相关数据' : error}
                style={{ padding: '40px 0' }}
              />
            </Card>
          </motion.div>
        )}

        {!searched && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <Card style={{
              textAlign: 'center',
              background: `linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%)`,
              border: 'none',
            }}>
              <Empty
                description="设置查询条件开始搜索"
                style={{ padding: '40px 0' }}
              />
            </Card>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default ClientNewHighConceptPage;
