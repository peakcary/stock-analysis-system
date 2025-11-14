/**
 * Top Concepts Stock Page
 * Display all concepts with their top N performing stocks
 */

import React, { useState } from 'react';
import {
  Card, Button, Spin, Table, Empty, Alert, Tag, Row, Col,
  Statistic, Space, Typography, message, InputNumber, DatePicker, Collapse
} from 'antd';
import {
  CrownOutlined, LoadingOutlined, ArrowUpOutlined
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import dayjs from 'dayjs';
import { ConceptAnalysisApi, conceptUtils, TopConceptData } from '../services/conceptApi';
import { designTokens } from '../styles/designTokens';

const { Title, Text, Paragraph } = Typography;

interface ClientTopConceptsStockPageProps {
  user?: any;
}

const ClientTopConceptsStockPage: React.FC<ClientTopConceptsStockPageProps> = ({ user }) => {
  const [n, setN] = useState(10);
  const [tradeDate, setTradeDate] = useState<any>(dayjs());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conceptsData, setConceptsData] = useState<TopConceptData[]>([]);
  const [stats, setStats] = useState({ totalConcepts: 0, totalStocks: 0 });
  const [searched, setSearched] = useState(false);

  const handleQuery = async () => {
    if (!n || n < 1 || n > 50) {
      message.warning('请输入1-50之间的数值');
      return;
    }

    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const tradeDateStr = tradeDate ? tradeDate.format('YYYY-MM-DD') : undefined;
      const response = await ConceptAnalysisApi.getTopStocksForConcepts(n, tradeDateStr);

      setConceptsData(response.concepts_with_top_stocks);
      setStats({
        totalConcepts: response.total_concepts,
        totalStocks: response.total_unique_stocks,
      });
    } catch (err: any) {
      const errorMessage = err.message || '查询失败，请稍后重试';
      setError(errorMessage);
      setConceptsData([]);
      setStats({ totalConcepts: 0, totalStocks: 0 });
    } finally {
      setLoading(false);
    }
  };

  const stockColumns = [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_, __: any, index: number) => (
        <Tag color={conceptUtils.getRankColor(index + 1)} style={{ fontWeight: 'bold' }}>
          #{index + 1}
        </Tag>
      ),
    },
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: '20%',
      render: (text: string) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      width: '30%',
    },
    {
      title: '热度值',
      dataIndex: 'heat_value',
      key: 'heat_value',
      width: '20%',
      render: (value: number) => (
        <Text style={{
          color: conceptUtils.getHeatColor(value),
          fontWeight: 'bold',
          fontSize: '14px'
        }}>
          {value.toFixed(2)}
        </Text>
      ),
      sorter: (a: any, b: any) => a.heat_value - b.heat_value,
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
        background: `linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)`,
      }}
    >
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {/* Header */}
        <Card
          bordered={false}
          style={{
            marginBottom: designTokens.spacing.md,
            boxShadow: '0 2px 8px rgba(251, 191, 36, 0.1)',
          }}
        >
          <Title level={2} style={{ marginBottom: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CrownOutlined style={{ fontSize: '24px', color: '#fbbf24' }} />
            热门概念股票
          </Title>
          <Paragraph style={{ color: designTokens.colors.text.secondary, marginTop: '12px', marginBottom: 0 }}>
            展示各个概念的最热门股票，帮助您快速了解每个概念的核心标的
          </Paragraph>
        </Card>

        {/* Filter Card */}
        <Card bordered={false} style={{ marginBottom: designTokens.spacing.md }}>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Row gutter={[16, 16]} align="middle">
              <Col xs={24} sm={12} md={6}>
                <Text strong style={{ display: 'block', marginBottom: '8px' }}>Top N 股票数</Text>
                <InputNumber
                  min={1}
                  max={50}
                  value={n}
                  onChange={(value) => setN(value || 10)}
                  style={{ width: '100%' }}
                  size="large"
                  placeholder="1-50"
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
                    background: `linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)`,
                    flex: 1
                  }}
                >
                  <CrownOutlined /> 查询
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
              <Spin indicator={<LoadingOutlined style={{ fontSize: 48, color: '#fbbf24' }} />} />
              <p style={{ marginTop: '16px', color: designTokens.colors.text.secondary }}>正在查询热门概念股票...</p>
            </Card>
          </motion.div>
        )}

        {/* Results */}
        {!loading && searched && !error && conceptsData.length > 0 && (
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
                    title="热门概念数"
                    value={stats.totalConcepts}
                    prefix={<CrownOutlined />}
                    valueStyle={{ color: '#fbbf24', fontSize: '28px', fontWeight: 'bold' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card style={{ textAlign: 'center' }}>
                  <Statistic
                    title="涵盖股票数"
                    value={stats.totalStocks}
                    prefix={<ArrowUpOutlined />}
                    valueStyle={{ color: '#10b981', fontSize: '28px', fontWeight: 'bold' }}
                  />
                </Card>
              </Col>
            </Row>

            {/* Concepts */}
            <Collapse
              items={conceptsData.map((item, index) => ({
                key: item.concept.id,
                label: (
                  <Row gutter={16} style={{ width: '100%', paddingRight: '16px' }}>
                    <Col flex="auto">
                      <Tag color="orange" style={{ marginRight: '8px' }}>
                        #{index + 1}
                      </Tag>
                      <Text strong>{item.concept.concept_name}</Text>
                    </Col>
                    <Col>
                      <Tag color="blue">{item.top_stocks.length}股</Tag>
                    </Col>
                  </Row>
                ),
                children: (
                  <Table
                    columns={stockColumns}
                    dataSource={item.top_stocks}
                    rowKey={(record) => record.stock_code}
                    pagination={false}
                    bordered
                    size="small"
                  />
                ),
              }))}
              style={{ marginBottom: designTokens.spacing.md }}
            />
          </motion.div>
        )}

        {/* Empty State */}
        {!loading && searched && (conceptsData.length === 0 || error) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <Card style={{
              textAlign: 'center',
              background: `linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)`,
              border: 'none',
            }}>
              <Empty
                description={conceptsData.length === 0 ? '未找到相关数据' : error}
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
              background: `linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)`,
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

export default ClientTopConceptsStockPage;
