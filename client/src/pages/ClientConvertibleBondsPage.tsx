/**
 * Convertible Bonds Query Page
 * Search convertible bonds and view associated concepts
 */

import React, { useState } from 'react';
import {
  Card, Input, Button, Spin, Table, Empty, Alert, Tag, Row, Col,
  Statistic, Space, Divider, Typography, message
} from 'antd';
import {
  SearchOutlined, LoadingOutlined, CheckCircleOutlined,
  GiftOutlined
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import { ConceptAnalysisApi, conceptUtils, Concept, Stock } from '../services/conceptApi';
import { designTokens } from '../styles/designTokens';

const { Title, Text, Paragraph } = Typography;

interface ClientConvertibleBondsPageProps {
  user?: any;
}

const ClientConvertibleBondsPage: React.FC<ClientConvertibleBondsPageProps> = ({ user }) => {
  const [searchInput, setSearchInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bond, setBond] = useState<Stock | null>(null);
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (value?: string) => {
    const bondCode = value || searchInput;

    if (!bondCode.trim()) {
      message.warning('请输入可转债代码');
      return;
    }

    // 验证可转债代码格式 (1开头的4位数)
    if (!conceptUtils.validateBondCode(bondCode)) {
      message.warning('请输入正确的可转债代码格式 (如: 1001, SZ1001)');
      return;
    }

    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const response = await ConceptAnalysisApi.getBondConcepts(bondCode);

      // 验证返回的是可转债
      if (!response.stock.is_convertible_bond) {
        setError('该证券不是可转债，请输入正确的可转债代码');
        setBond(null);
        setConcepts([]);
        setLoading(false);
        return;
      }

      setBond(response.stock);
      setConcepts(response.concepts);
    } catch (err: any) {
      const errorMessage = err.message || '查询失败，请稍后重试';
      setError(errorMessage);

      if (err.response?.status === 404) {
        setError(`可转债不存在: ${bondCode}`);
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
        <Tag color="orange" style={{ fontSize: '13px' }}>{text}</Tag>
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
        background: `linear-gradient(135deg, #fef08a 0%, #fef3c7 100%)`,
      }}
    >
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <Card
          bordered={false}
          style={{
            marginBottom: designTokens.spacing.md,
            boxShadow: '0 2px 8px rgba(251, 191, 36, 0.1)',
          }}
        >
          <Row align="middle" gutter={[16, 0]}>
            <Col span={24}>
              <Title level={2} style={{ marginBottom: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <GiftOutlined style={{ fontSize: '24px', color: '#f59e0b' }} />
                可转债概念查询
              </Title>
            </Col>
          </Row>

          <Paragraph style={{ color: designTokens.colors.text.secondary, marginTop: '12px', marginBottom: 0 }}>
            输入可转债代码（如：1001 或 SZ1001）查询该可转债所属的所有概念
          </Paragraph>
        </Card>

        {/* Search Card */}
        <Card bordered={false} style={{ marginBottom: designTokens.spacing.md }}>
          <Space.Compact style={{ width: '100%', maxWidth: '500px' }}>
            <Input
              placeholder="请输入可转债代码（如: 1001 或 SZ1001）"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onPressEnter={() => handleSearch()}
              size="large"
              disabled={loading}
              prefix={<SearchOutlined style={{ color: '#f59e0b' }} />}
            />
            <Button
              type="primary"
              size="large"
              icon={<SearchOutlined />}
              onClick={() => handleSearch()}
              loading={loading}
              style={{
                background: `linear-gradient(135deg, #f59e0b 0%, #d97706 100%)`,
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
              <Spin indicator={<LoadingOutlined style={{ fontSize: 48, color: '#f59e0b' }} />} />
              <p style={{ marginTop: '16px', color: designTokens.colors.text.secondary }}>正在查询可转债信息...</p>
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
            {/* Bond Info */}
            <Card
              bordered={false}
              style={{
                marginBottom: designTokens.spacing.md,
                boxShadow: '0 2px 8px rgba(251, 191, 36, 0.1)',
              }}
            >
              <Title level={3} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px' }}>
                <GiftOutlined style={{ fontSize: '20px', color: '#f59e0b' }} />
                可转债信息
              </Title>

              <Row gutter={[24, 24]}>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="可转债代码"
                    value={bond.stock_code}
                    valueStyle={{ color: '#f59e0b', fontWeight: 'bold' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="可转债名称"
                    value={bond.stock_name}
                    valueStyle={{ color: '#f59e0b', fontWeight: 'bold', fontSize: '16px' }}
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
                    value="可转债"
                    valueStyle={{ color: '#f59e0b', fontWeight: 'bold', fontSize: '16px' }}
                  />
                </Col>
              </Row>
            </Card>

            <Divider style={{ margin: `${designTokens.spacing.md} 0` }} />

            {/* Concepts */}
            <Card bordered={false}>
              <Title level={3} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px' }}>
                <CheckCircleOutlined style={{ fontSize: '20px', color: '#f59e0b' }} />
                所属概念
                <Tag color="orange" style={{ marginLeft: '8px' }}>
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
                          <Tag color="orange" style={{ padding: '6px 12px', fontSize: '14px', cursor: 'pointer' }}>
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
                <Empty description="该可转债暂无相关概念" />
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
                background: `linear-gradient(135deg, #fef08a 0%, #fef3c7 100%)`,
                border: 'none',
              }}
            >
              <Empty
                description={searched ? '未找到相关数据' : '输入可转债代码开始查询'}
                style={{ padding: '40px 0' }}
              />
            </Card>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default ClientConvertibleBondsPage;
