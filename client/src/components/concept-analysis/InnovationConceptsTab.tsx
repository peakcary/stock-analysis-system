import React, { useState } from 'react';
import {
  Card,
  Input,
  Button,
  Table,
  Spin,
  Empty,
  Alert,
  Row,
  Col,
  Statistic,
  Space,
  Tag,
  Typography,
  message,
  Collapse,
} from 'antd';
import {
  SearchOutlined,
  LoadingOutlined,
  FireOutlined,
  TrophyOutlined,
  RiseOutlined,
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import { getInnovationConcepts, InnovationConcept } from '../../utils/conceptAnalysisApi';

const { Title, Text, Paragraph } = Typography;

const InnovationConceptsTab: React.FC = () => {
  const [daysBack, setDaysBack] = useState<number>(10);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<InnovationConcept[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [tradeDate, setTradeDate] = useState<string>('');

  const handleQuery = async () => {
    if (!daysBack || daysBack < 1) {
      message.warning('请输入有效的天数（1以上）');
      return;
    }

    setLoading(true);
    setError(null);
    setData([]);
    setSearched(true);

    try {
      const response = await getInnovationConcepts(daysBack, 1, 50, tradeDate || undefined);

      // 按新高天数和总热度排序
      const sortedConcepts = (response.innovation_concepts || []).sort((a, b) => {
        if (b.new_high_days !== a.new_high_days) {
          return b.new_high_days - a.new_high_days;
        }
        return b.total_heat_value - a.total_heat_value;
      });

      setData(sortedConcepts);
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.detail || err.message || '查询失败';
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

  // 股票列表的列定义
  const stockColumns = [
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 100,
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      width: 120,
    },
    {
      title: '热度值',
      dataIndex: 'heat_value',
      key: 'heat_value',
      width: 120,
      render: (value: number) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <FireOutlined style={{ color: '#ff4d4f' }} />
          <Text strong style={{ color: '#ff4d4f' }}>
            {value.toFixed(2)}
          </Text>
        </div>
      ),
    },
  ];

  const conceptColumns = [
    {
      title: '排名',
      key: 'rank',
      width: 70,
      render: (_: any, _record: InnovationConcept, index: number) => (
        <Tag
          color={
            index === 0
              ? 'gold'
              : index === 1
                ? 'silver'
                : index === 2
                  ? '#2db7f5'
                  : 'default'
          }
        >
          #{index + 1}
        </Tag>
      ),
    },
    {
      title: '概念名称',
      dataIndex: 'concept_name',
      key: 'concept_name',
      width: '25%',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '总热度值',
      dataIndex: 'total_heat_value',
      key: 'total_heat_value',
      width: 120,
      render: (value: number) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <FireOutlined style={{ color: '#faad14' }} />
          <Text strong style={{ color: '#faad14' }}>
            {value.toFixed(2)}
          </Text>
        </div>
      ),
      sorter: (a: InnovationConcept, b: InnovationConcept) =>
        b.total_heat_value - a.total_heat_value,
    },
    {
      title: '概念股票数',
      dataIndex: 'stock_count',
      key: 'stock_count',
      width: 100,
      render: (value: number) => <Tag color="cyan">{value} 只</Tag>,
    },
    {
      title: '平均热度',
      dataIndex: 'avg_heat_value',
      key: 'avg_heat_value',
      width: 100,
      render: (value: number) => <Text>{value.toFixed(2)}</Text>,
    },
    {
      title: '创新高天数',
      dataIndex: 'new_high_days',
      key: 'new_high_days',
      width: 100,
      render: (value: number) => (
        <Tag color="red">
          <FireOutlined style={{ marginRight: '4px' }} />
          {value} 天
        </Tag>
      ),
      sorter: (a: InnovationConcept, b: InnovationConcept) =>
        b.new_high_days - a.new_high_days,
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
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12}>
              <div>
                <Text strong style={{ display: 'block', marginBottom: '12px', fontSize: '16px' }}>
                  创新高时间范围（天数）
                </Text>
                <Input
                  size="large"
                  type="number"
                  min="1"
                  max="365"
                  placeholder="输入天数，如：10, 20, 30"
                  value={daysBack}
                  onChange={(e) => setDaysBack(parseInt(e.target.value) || 1)}
                  onKeyPress={handleKeyPress}
                  style={{ borderRadius: '8px' }}
                />
              </div>
            </Col>
            <Col xs={24} sm={12}>
              <div>
                <Text strong style={{ display: 'block', marginBottom: '12px', fontSize: '16px' }}>
                  交易日期 (可选)
                </Text>
                <Input
                  size="large"
                  type="date"
                  value={tradeDate}
                  onChange={(e) => setTradeDate(e.target.value)}
                  onKeyPress={handleKeyPress}
                  style={{ borderRadius: '8px' }}
                />
              </div>
            </Col>
          </Row>

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
            查询最近 {daysBack} 天创新高的概念
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
              正在查询最近 {daysBack} 天创新高的概念...
            </p>
          </Card>
        </motion.div>
      )}

      {/* 结果显示 */}
      {!loading && searched && data.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {/* 统计信息 */}
          <Card
            bordered={false}
            style={{
              marginBottom: '24px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              boxShadow: '0 20px 60px rgba(0,0,0,0.1)',
              borderRadius: '16px',
            }}
          >
            <Row gutter={[32, 32]} align="middle">
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>时间范围</Text>}
                  value={daysBack}
                  suffix="天"
                  valueStyle={{ color: 'white', fontSize: '28px', fontWeight: 'bold' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>创新高概念数</Text>}
                  value={data.length}
                  suffix="个"
                  valueStyle={{ color: '#52c41a', fontSize: '28px', fontWeight: 'bold' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>最高热度和</Text>}
                  value={data.length > 0 ? data[0].total_heat_value.toFixed(2) : 0}
                  valueStyle={{ color: '#fff23b', fontSize: '28px', fontWeight: 'bold' }}
                  prefix={<FireOutlined style={{ marginRight: '8px' }} />}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>最多创新高天数</Text>}
                  value={data.length > 0 ? data[0].new_high_days : 0}
                  suffix="天"
                  valueStyle={{ color: '#ff7a45', fontSize: '28px', fontWeight: 'bold' }}
                />
              </Col>
            </Row>
          </Card>

          {/* 概念列表 */}
          <Card
            bordered={false}
            style={{
              boxShadow: '0 20px 60px rgba(0,0,0,0.1)',
              borderRadius: '16px',
              marginBottom: '24px',
            }}
          >
            <Title level={3} style={{ marginBottom: '24px' }}>
              <TrophyOutlined style={{ marginRight: '8px', color: '#667eea' }} />
              创新高概念详情列表
            </Title>
            <Table
              columns={conceptColumns}
              dataSource={data}
              rowKey={(record) => record.concept_id}
              pagination={{
                pageSize: 15,
                showSizeChanger: true,
                pageSizeOptions: ['10', '15', '20'],
                showTotal: (total) => `共 ${total} 个创新高概念`,
              }}
              bordered
              size="middle"
              expandable={{
                expandedRowRender: (record: InnovationConcept) => (
                  <Card
                    style={{
                      background: '#f8f9fa',
                      border: 'none',
                      marginBottom: '16px',
                    }}
                  >
                    <div style={{ marginBottom: '16px' }}>
                      <Title level={5} style={{ marginTop: 0 }}>
                        概念前 {Math.min(5, record.top_stocks.length)} 高热度股票
                      </Title>
                      <Table
                        columns={stockColumns}
                        dataSource={record.top_stocks}
                        rowKey={(record) => record.stock_code}
                        pagination={false}
                        bordered
                        size="small"
                      />
                    </div>
                  </Card>
                ),
                expandIcon: ({ expanded, onExpand, record }) => (
                  <Button
                    type="link"
                    size="small"
                    onClick={(e) => onExpand(record, e)}
                  >
                    {expanded ? '隐藏股票' : '查看股票'}
                  </Button>
                ),
              }}
              rowClassName={(record, index) => {
                if (index === 0) return 'rank-1';
                if (index === 1) return 'rank-2';
                if (index === 2) return 'rank-3';
                return '';
              }}
            />
          </Card>

          {/* 提示信息 */}
          <Card
            style={{
              background: '#f0f5ff',
              borderRadius: '12px',
              border: 'none',
            }}
          >
            <Paragraph style={{ margin: 0, color: '#1890ff' }}>
              <strong>💡 提示：</strong>
              显示最近 {daysBack}
              天内，日热度总和达到创新高的所有概念。点击"查看股票"可以展开查看每个概念的前 5 只高热度股票。
            </Paragraph>
          </Card>
        </motion.div>
      )}

      {/* 空状态 */}
      {!loading && searched && data.length === 0 && !error && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <Card
            style={{
              textAlign: 'center',
              borderRadius: '16px',
            }}
          >
            <Empty
              description={`最近 ${daysBack} 天未发现创新高概念`}
              style={{ padding: '40px 0' }}
            />
          </Card>
        </motion.div>
      )}

      {/* 初始状态提示 */}
      {!searched && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <Card
            style={{
              textAlign: 'center',
              borderRadius: '16px',
              background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
              border: 'none',
            }}
          >
            <Empty
              description="输入天数开始查询"
              style={{ padding: '60px 0' }}
            />
            <Paragraph style={{ color: '#666', marginTop: '16px' }}>
              查询指定天数内日热度总和达到创新高的所有概念
            </Paragraph>
          </Card>
        </motion.div>
      )}

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

export default InnovationConceptsTab;
