import React, { useState } from 'react';
import {
  Card,
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
  Pagination,
} from 'antd';
import {
  LoadingOutlined,
  FireOutlined,
  BankOutlined,
  SortAscendingOutlined,
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import { getConvertibleBonds, ConvertibleBond } from '../../utils/conceptAnalysisApi';

const { Title, Text, Paragraph } = Typography;

interface ConvertibleBondDisplayData extends ConvertibleBond {
  rank: number;
}

const ConvertibleBondsTab: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ConvertibleBondDisplayData[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalCount, setTotalCount] = useState(0);
  const [statistics, setStatistics] = useState<any>(null);
  const [tradeDate, setTradeDate] = useState<string>('');

  const handleQuery = async (page: number = 1) => {
    setLoading(true);
    setError(null);

    try {
      const response = await getConvertibleBonds(page, pageSize, tradeDate || undefined);

      const bondsWithRank = (response.convertible_bonds || []).map(
        (bond: ConvertibleBond, index: number) => ({
          ...bond,
          rank: (page - 1) * pageSize + index + 1,
        })
      );

      setData(bondsWithRank);
      setTotalCount(response.pagination?.total || 0);
      setStatistics(response.statistics || {});
      setCurrentPage(page);
      setSearched(true);
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.detail || err.message || '查询失败';
      setError(errorMsg);
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    // 自动加载初始数据
    if (!searched) {
      handleQuery(1);
    }
  }, []);

  const columns = [
    {
      title: '排名',
      key: 'rank',
      width: 70,
      render: (_: any, record: ConvertibleBondDisplayData) => (
        <Tag
          color={
            record.rank === 1
              ? 'gold'
              : record.rank === 2
                ? 'silver'
                : record.rank === 3
                  ? '#2db7f5'
                  : 'default'
          }
        >
          #{record.rank}
        </Tag>
      ),
    },
    {
      title: '转债代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 110,
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '转债名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      width: 140,
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
      sorter: (a: ConvertibleBondDisplayData, b: ConvertibleBondDisplayData) =>
        b.heat_value - a.heat_value,
    },
    {
      title: '所属概念',
      dataIndex: 'concepts',
      key: 'concepts',
      width: '30%',
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
          <div>
            <Text strong style={{ display: 'block', marginBottom: '12px', fontSize: '16px' }}>
              交易日期 (可选)
            </Text>
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} md={8}>
                <input
                  type="date"
                  value={tradeDate}
                  onChange={(e) => setTradeDate(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    border: '1px solid #d9d9d9',
                    fontSize: '14px',
                  }}
                />
              </Col>
            </Row>
          </div>

          <Button
            type="primary"
            size="large"
            icon={<SortAscendingOutlined />}
            onClick={() => handleQuery(1)}
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
            查询可转债热度排行
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
              正在查询可转债热度数据...
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
          {statistics && (
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
                    title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>转债总数</Text>}
                    value={statistics.total_bonds || 0}
                    suffix="只"
                    valueStyle={{ color: 'white', fontSize: '28px', fontWeight: 'bold' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>总热度值</Text>}
                    value={statistics.total_heat_value?.toFixed(2) || 0}
                    valueStyle={{ color: '#fff23b', fontSize: '28px', fontWeight: 'bold' }}
                    prefix={<FireOutlined style={{ marginRight: '8px' }} />}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>平均热度</Text>}
                    value={statistics.avg_heat_value?.toFixed(2) || 0}
                    valueStyle={{ color: '#1890ff', fontSize: '28px', fontWeight: 'bold' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>最高热度</Text>}
                    value={statistics.max_heat_value?.toFixed(2) || 0}
                    valueStyle={{ color: '#52c41a', fontSize: '28px', fontWeight: 'bold' }}
                  />
                </Col>
              </Row>
            </Card>
          )}

          {/* 转债列表 */}
          <Card
            bordered={false}
            style={{
              boxShadow: '0 20px 60px rgba(0,0,0,0.1)',
              borderRadius: '16px',
            }}
          >
            <Title level={3} style={{ marginBottom: '24px' }}>
              <BankOutlined style={{ marginRight: '8px', color: '#667eea' }} />
              可转债热度排行表
            </Title>
            <Table
              columns={columns}
              dataSource={data}
              rowKey={(record) => record.stock_id}
              pagination={false}
              bordered
              size="middle"
              rowClassName={(record, index) => {
                if (record.rank === 1) return 'rank-1';
                if (record.rank === 2) return 'rank-2';
                if (record.rank === 3) return 'rank-3';
                return '';
              }}
            />

            {/* 分页控件 */}
            <div style={{ marginTop: '24px', textAlign: 'center' }}>
              <Pagination
                current={currentPage}
                pageSize={pageSize}
                total={totalCount}
                onChange={(page) => handleQuery(page)}
                onShowSizeChange={(_, size) => {
                  setPageSize(size);
                  handleQuery(1);
                }}
                showSizeChanger
                pageSizeOptions={['10', '20', '50']}
                showTotal={(total) => `共 ${total} 只转债`}
                style={{ paddingTop: '16px' }}
              />
            </div>
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
              可转债是指用代码1开头的债券。此表显示所有可转债按热度值从高到低排列。点击表头可按热度值排序。
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
              description="暂无可转债数据"
              style={{ padding: '40px 0' }}
            />
          </Card>
        </motion.div>
      )}

      {/* 初始加载提示 */}
      {!searched && !loading && (
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
              description="正在加载可转债数据..."
              style={{ padding: '60px 0' }}
            />
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

export default ConvertibleBondsTab;
