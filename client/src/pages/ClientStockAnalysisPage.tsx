/**
 * Stock Analysis Page
 * Query individual stocks and view associated concepts
 */

import React, { useState } from 'react';
import {
  Card, Input, Button, Spin, Table, Empty, Alert, Tag, Row, Col,
  Statistic, Space, Divider, Typography, message, Select
} from 'antd';
import {
  SearchOutlined, LoadingOutlined, CheckCircleOutlined,
  HomeOutlined, ArrowRightOutlined
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import { ConceptAnalysisApi, conceptUtils, Concept, Stock } from '../services/conceptApi';
import { designTokens } from '../styles/designTokens';

const { Title, Text, Paragraph } = Typography;

interface ClientStockAnalysisPageProps {
  user?: any;
}

const ClientStockAnalysisPage: React.FC<ClientStockAnalysisPageProps> = ({ user }) => {
  const [searchInput, setSearchInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bond, setBond] = useState<Stock | null>(null);
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (value?: string) => {
    const stockCode = value || searchInput;

    if (!stockCode.trim()) {
      message.warning('请输入股票代码');
      return;
    }

    // 验证股票代码格式
    if (!conceptUtils.validateStockCode(stockCode)) {
      message.warning('请输入正确的股票代码格式 (如: 000001 或 SZ000001)');
      return;
    }

    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const response = await ConceptAnalysisApi.getStockConcepts(stockCode);
      setBond(response.stock);
      setConcepts(response.concepts);
    } catch (err: any) {
      const errorMessage = err.message || '查询失败，请稍后重试';
      setError(errorMessage);

      // 处理特定错误
      if (err.response?.status === 404) {
        setError(`股票不存在: ${stockCode}`);
      } else if (err.response?.status === 403) {
        setError('查询次数不足，请升级会员或购买查询包');
      } else if (err.response?.status === 401) {
        setError('认证失效，请重新登录');
      }

      setBond(null);
      setConcepts([]);
    } finally {
      setLoading(false);
    }
  };

  const conceptColumns = [
    {
      title: '概念名称',
      dataIndex: 'concept_name',
      key: 'concept_name',
      width: '30%',
      render: (text: string) => (
        <Tag color="blue" style={{ fontSize: '13px' }}>{text}</Tag>
      ),
    },
    {
      title: '概念描述',
      dataIndex: 'description',
      key: 'description',
      width: '50%',
      render: (text: string) => (
        <Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: 0, fontSize: '13px' }}>
          {text || '-'}
        </Paragraph>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: '20%',
      render: (date: string) => (
        <Text type="secondary" style={{ fontSize: '12px' }}>
          {conceptUtils.formatDate(date)}
        </Text>
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
        background: `linear-gradient(135deg, #f0f4ff 0%, #f8e8ff 100%)`,
      }}
    >
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <Card
          bordered={false}
          style={{
            marginBottom: designTokens.spacing.md,
            boxShadow: '0 2px 8px rgba(102, 126, 234, 0.1)',
          }}
        >
          <Row align="middle" gutter={[16, 0]}>
            <Col span={24}>
              <Title level={2} style={{ marginBottom: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <HomeOutlined style={{ fontSize: '24px', color: designTokens.colors.primary[500] }} />
                股票概念查询
              </Title>
            </Col>
          </Row>

          <Paragraph style={{ color: designTokens.colors.text.secondary, marginTop: '12px', marginBottom: 0 }}>
            输入股票代码（如：000001 或 SZ000001）查询该股票所属的所有概念
          </Paragraph>
        </Card>

        {/* Search Card */}
        <Card bordered={false} style={{ marginBottom: designTokens.spacing.md }}>
          <Space.Compact style={{ width: '100%', maxWidth: '500px' }}>
            <Input
              placeholder="请输入股票代码（如: 000001 或 SZ000001）"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onPressEnter={() => handleSearch()}
              size="large"
              disabled={loading}
              prefix={<SearchOutlined style={{ color: designTokens.colors.primary[500] }} />}
            />
            <Button
              type="primary"
              size="large"
              icon={<SearchOutlined />}
              onClick={() => handleSearch()}
              loading={loading}
              style={{
                background: `linear-gradient(135deg, ${designTokens.colors.primary[500]} 0%, #764ba2 100%)`,
              }}
            >
              查询
            </Button>
          </Space.Compact>
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
              <Spin indicator={<LoadingOutlined style={{ fontSize: 48, color: designTokens.colors.primary[500] }} />} />
              <p style={{ marginTop: '16px', color: designTokens.colors.text.secondary }}>正在查询股票信息...</p>
            </Card>
          </motion.div>
        )}

        {/* Results */}
        {!loading && searched && !error && bond && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {/* Stock Info */}
            <Card
              bordered={false}
              style={{
                marginBottom: designTokens.spacing.md,
                boxShadow: '0 2px 8px rgba(102, 126, 234, 0.1)',
              }}
            >
              <Title level={3} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px' }}>
                <HomeOutlined style={{ fontSize: '20px', color: designTokens.colors.primary[500] }} />
                股票信息
              </Title>

              <Row gutter={[24, 24]}>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="股票代码"
                    value={bond.stock_code}
                    valueStyle={{ color: designTokens.colors.primary[500], fontWeight: 'bold' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="股票名称"
                    value={bond.stock_name}
                    valueStyle={{ color: designTokens.colors.primary[400], fontWeight: 'bold', fontSize: '16px' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="所属行业"
                    value={bond.industry || '未分类'}
                    valueStyle={{ color: designTokens.colors.success[500], fontWeight: 'bold', fontSize: '16px' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="证券类型"
                    value="普通股"
                    valueStyle={{ color: designTokens.colors.primary[500], fontWeight: 'bold', fontSize: '16px' }}
                  />
                </Col>
              </Row>
            </Card>

            <Divider style={{ margin: `${designTokens.spacing.md} 0` }} />

            {/* Concepts */}
            <Card bordered={false}>
              <Title level={3} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px' }}>
                <CheckCircleOutlined style={{ fontSize: '20px', color: designTokens.colors.primary[500] }} />
                所属概念
                <Tag color="blue" style={{ marginLeft: '8px' }}>
                  {concepts.length} 个
                </Tag>
              </Title>

              {concepts.length > 0 ? (
                <div>
                  {/* Concept Tags Summary */}
                  <div style={{ marginBottom: '24px' }}>
                    <Text type="secondary" style={{ display: 'block', marginBottom: '12px' }}>
                      <strong>概念汇总：</strong>
                    </Text>
                    <Space wrap size="middle" style={{ width: '100%' }}>
                      {concepts.map((concept) => (
                        <motion.div
                          key={concept.id}
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                        >
                          <Tag color="blue" style={{ padding: '6px 12px', fontSize: '14px', cursor: 'pointer' }}>
                            {concept.concept_name}
                          </Tag>
                        </motion.div>
                      ))}
                    </Space>
                  </div>

                  <Divider />

                  {/* Detailed Table */}
                  <div style={{ marginTop: '24px' }}>
                    <Text type="secondary" style={{ display: 'block', marginBottom: '16px' }}>
                      <strong>详细信息：</strong>
                    </Text>
                    <Table
                      columns={conceptColumns}
                      dataSource={concepts}
                      rowKey="id"
                      pagination={{
                        pageSize: 10,
                        showSizeChanger: true,
                        pageSizeOptions: ['10', '20', '50'],
                        showTotal: (total) => `共 ${total} 个概念`,
                      }}
                      bordered
                      size="small"
                    />
                  </div>
                </div>
              ) : (
                <Empty description="该股票暂无相关概念" />
              )}
            </Card>
          </motion.div>
        )}

        {/* Empty State */}
        {!loading && (!searched || (searched && !bond && error)) && !error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <Card
              style={{
                textAlign: 'center',
                background: `linear-gradient(135deg, ${designTokens.colors.primary[50]} 0%, #f8e8ff 100%)`,
                border: 'none',
              }}
            >
              <Empty
                description={searched ? '未找到相关数据' : '输入股票代码开始查询'}
                style={{ padding: '40px 0' }}
              />
            </Card>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default ClientStockAnalysisPage;
