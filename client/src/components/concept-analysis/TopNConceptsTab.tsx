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
} from 'antd';
import {
  SearchOutlined,
  LoadingOutlined,
  FireOutlined,
  BankOutlined,
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import { getTopConceptsStocks } from '../../utils/conceptAnalysisApi';

const { Title, Text, Paragraph } = Typography;

interface StockData {
  stock_id: number;
  stock_code: string;
  stock_name: string;
  heat_value: number;
  concepts: string[];
  concept_count: number;
  rank: number;
}

const TopNConceptsTab: React.FC = () => {
  const [topN, setTopN] = useState<number>(5);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<StockData[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [tradeDate, setTradeDate] = useState<string>('');

  const handleQuery = async () => {
    if (!topN || topN < 1) {
      message.warning('请输入有效的数字（1以上）');
      return;
    }

    setLoading(true);
    setError(null);
    setData([]);
    setSearched(true);

    try {
      const response = await getTopConceptsStocks(topN, tradeDate || undefined);

      // 处理重复数据和排序
      const stockMap = new Map<string, StockData>();

      // 如果响应是对象，获取stocks字段；如果是数组，直接处理
      const stocks = Array.isArray(response) ? response : response.stocks || [];

      stocks.forEach((stock: any, index: number) => {
        if (stockMap.has(stock.stock_code)) {
          const existing = stockMap.get(stock.stock_code)!;
          // 合并concepts
          const allConcepts = [...new Set([...existing.concepts, ...(stock.concepts || [])])];
          existing.concepts = allConcepts;
          existing.concept_count = allConcepts.length;
          // 取最高热度值
          existing.heat_value = Math.max(existing.heat_value, stock.heat_value || 0);
        } else {
          stockMap.set(stock.stock_code, {
            stock_id: stock.stock_id || index,
            stock_code: stock.stock_code,
            stock_name: stock.stock_name || '',
            heat_value: stock.heat_value || 0,
            concepts: stock.concepts || [],
            concept_count: (stock.concepts || []).length,
            rank: index + 1,
          });
        }
      });

      // 转换为数组并按热度排序
      const sortedStocks = Array.from(stockMap.values())
        .sort((a, b) => b.heat_value - a.heat_value)
        .map((stock, index) => ({
          ...stock,
          rank: index + 1,
        }));

      setData(sortedStocks);
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

  const columns = [
    {
      title: '排名',
      key: 'rank',
      width: 70,
      render: (_: any, record: StockData) => (
        <Tag color={record.rank === 1 ? 'gold' : record.rank === 2 ? 'silver' : 'blue'}>
          #{record.rank}
        </Tag>
      ),
    },
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
      sorter: (a: StockData, b: StockData) => b.heat_value - a.heat_value,
    },
    {
      title: '所属概念数',
      dataIndex: 'concept_count',
      key: 'concept_count',
      width: 100,
      render: (value: number) => <Tag color="cyan">{value} 个</Tag>,
      sorter: (a: StockData, b: StockData) => b.concept_count - a.concept_count,
    },
    {
      title: '概念列表',
      dataIndex: 'concepts',
      key: 'concepts',
      render: (concepts: string[]) => (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
          {concepts.slice(0, 3).map((concept, idx) => (
            <Tag key={idx} color="blue" style={{ fontSize: '12px' }}>
              {concept}
            </Tag>
          ))}
          {concepts.length > 3 && (
            <Tag style={{ fontSize: '12px' }}>+{concepts.length - 3}</Tag>
          )}
        </div>
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
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12}>
              <div>
                <Text strong style={{ display: 'block', marginBottom: '12px', fontSize: '16px' }}>
                  概念数量 (Top N)
                </Text>
                <Input
                  size="large"
                  type="number"
                  min="1"
                  max="100"
                  placeholder="输入要查询的概念数量，如：5, 10"
                  value={topN}
                  onChange={(e) => setTopN(parseInt(e.target.value) || 1)}
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
            查询前 {topN} 个概念的股票
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
              正在查询前 {topN} 个概念的股票...
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
                  title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>查询概念数</Text>}
                  value={topN}
                  suffix="个"
                  valueStyle={{ color: 'white', fontSize: '28px', fontWeight: 'bold' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>去重后股票数</Text>}
                  value={data.length}
                  suffix="只"
                  valueStyle={{ color: '#52c41a', fontSize: '28px', fontWeight: 'bold' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>最高热度</Text>}
                  value={data.length > 0 ? data[0].heat_value.toFixed(2) : 0}
                  valueStyle={{ color: '#fff23b', fontSize: '28px', fontWeight: 'bold' }}
                  prefix={<FireOutlined style={{ marginRight: '8px' }} />}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>平均热度</Text>}
                  value={
                    data.length > 0
                      ? (data.reduce((sum, s) => sum + s.heat_value, 0) / data.length).toFixed(2)
                      : 0
                  }
                  valueStyle={{ color: '#1890ff', fontSize: '28px', fontWeight: 'bold' }}
                />
              </Col>
            </Row>
          </Card>

          {/* 股票列表 */}
          <Card
            bordered={false}
            style={{
              boxShadow: '0 20px 60px rgba(0,0,0,0.1)',
              borderRadius: '16px',
            }}
          >
            <Title level={3} style={{ marginBottom: '24px' }}>
              <BankOutlined style={{ marginRight: '8px', color: '#667eea' }} />
              前 {topN} 概念股票汇总列表
            </Title>
            <Table
              columns={columns}
              dataSource={data}
              rowKey={(record) => record.stock_code}
              pagination={{
                pageSize: 20,
                showSizeChanger: true,
                pageSizeOptions: ['10', '20', '50'],
                showTotal: (total) => `共 ${total} 只股票`,
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

          {/* 提示信息 */}
          <Card
            style={{
              marginTop: '24px',
              background: '#f0f5ff',
              borderRadius: '12px',
              border: 'none',
            }}
          >
            <Paragraph style={{ margin: 0, color: '#1890ff' }}>
              <strong>💡 提示：</strong>
              表格显示了前 {topN} 个概念中所有股票的汇总列表（去重显示）。每只股票可能同时属于多个概念，"所属概念数"表示该股票在查询的 {topN}
              个概念中出现的次数。
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
              description="未找到相关股票"
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
              description="输入概念数量开始查询"
              style={{ padding: '60px 0' }}
            />
            <Paragraph style={{ color: '#666', marginTop: '16px' }}>
              选择前 N 个热度最高的概念，查看这些概念中所有股票的汇总列表（去重显示）
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

export default TopNConceptsTab;
