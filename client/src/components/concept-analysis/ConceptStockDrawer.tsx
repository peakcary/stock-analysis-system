import React, { useState, useEffect } from 'react';
import {
  Drawer,
  Table,
  Button,
  Space,
  Spin,
  Card,
  Row,
  Col,
  Statistic,
  Empty,
  message,
  Tag,
  Typography,
} from 'antd';
import {
  FireOutlined,
  LoadingOutlined,
  LineChartOutlined,
} from '@ant-design/icons';
import { motion } from 'framer-motion';
import {
  getConceptStockRanking,
  ConceptRanking,
  StockRanking,
} from '../../utils/conceptAnalysisApi';
import StockChartModal from './StockChartModal';

const { Text, Title, Paragraph } = Typography;

interface ConceptStockDrawerProps {
  open: boolean;
  onClose: () => void;
  concept: ConceptRanking | null;
}

const ConceptStockDrawer: React.FC<ConceptStockDrawerProps> = ({
  open,
  onClose,
  concept,
}) => {
  const [loading, setLoading] = useState(false);
  const [stocks, setStocks] = useState<StockRanking[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize] = useState(10);
  const [summary, setSummary] = useState<any>(null);
  const [selectedStock, setSelectedStock] = useState<string | null>(null);
  const [chartModalOpen, setChartModalOpen] = useState(false);

  // 当概念改变时，重置状态
  useEffect(() => {
    if (open && concept) {
      setCurrentPage(1);
      setStocks([]);
      loadConceptStocks(1);
    }
  }, [open, concept]);

  const loadConceptStocks = async (page: number) => {
    if (!concept) return;

    setLoading(true);
    try {
      const response = await getConceptStockRanking(
        concept.concept_id,
        page,
        pageSize
      );

      if (page === 1) {
        setStocks(response.rankings);
      } else {
        // 追加新数据
        setStocks([...stocks, ...response.rankings]);
      }

      setTotalCount(response.pagination.total);
      setSummary(response.summary);
      setCurrentPage(page);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || '加载失败';
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadMore = () => {
    loadConceptStocks(currentPage + 1);
  };

  const handleStockClick = (stockCode: string) => {
    setSelectedStock(stockCode);
    setChartModalOpen(true);
  };

  const columns = [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_: any, record: StockRanking, index: number) => (
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
          #{record.rank}
        </Tag>
      ),
    },
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 100,
      render: (text: string) => (
        <Button
          type="link"
          onClick={() => handleStockClick(text)}
          style={{ padding: 0, height: 'auto', fontSize: '14px', fontWeight: '600' }}
        >
          {text}
        </Button>
      ),
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      width: 100,
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
      sorter: (a: StockRanking, b: StockRanking) => b.heat_value - a.heat_value,
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: StockRanking) => (
        <Button
          type="primary"
          size="small"
          icon={<LineChartOutlined />}
          onClick={() => handleStockClick(record.stock_code)}
        >
          查看图表
        </Button>
      ),
    },
  ];

  const displayedCount = stocks.length;
  const hasMore = displayedCount < totalCount;

  return (
    <>
      <Drawer
        title={
          concept ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <FireOutlined style={{ color: '#ff4d4f', fontSize: '20px' }} />
              <span>{concept.concept_name} - 概念内股票</span>
            </div>
          ) : (
            '概念详情'
          )
        }
        placement="right"
        onClose={onClose}
        open={open}
        width={1000}
        bodyStyle={{ padding: '24px' }}
      >
        {concept && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            {/* 概念统计信息 */}
            <Card
              style={{
                marginBottom: '24px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                borderRadius: '12px',
              }}
            >
              <Row gutter={[24, 24]}>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title={
                      <Text style={{ color: 'rgba(255,255,255,0.8)' }}>
                        概念总热度
                      </Text>
                    }
                    value={summary?.total_heat_value?.toFixed(2) || 0}
                    valueStyle={{ color: '#fff23b', fontSize: '24px' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title={
                      <Text style={{ color: 'rgba(255,255,255,0.8)' }}>
                        概念股票数
                      </Text>
                    }
                    value={summary?.stock_count || 0}
                    suffix="只"
                    valueStyle={{ color: '#52c41a', fontSize: '24px' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title={
                      <Text style={{ color: 'rgba(255,255,255,0.8)' }}>
                        平均热度
                      </Text>
                    }
                    value={summary?.avg_heat_value?.toFixed(2) || 0}
                    valueStyle={{ color: '#1890ff', fontSize: '24px' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  {summary?.is_new_high && (
                    <Statistic
                      title={
                        <Text style={{ color: 'rgba(255,255,255,0.8)' }}>
                          创新高天数
                        </Text>
                      }
                      value={summary?.new_high_days || 0}
                      suffix="天"
                      valueStyle={{ color: '#fadb14', fontSize: '24px' }}
                      prefix="🔥 "
                    />
                  )}
                </Col>
              </Row>
            </Card>

            {/* 股票列表 */}
            <Card style={{ marginBottom: '24px', borderRadius: '12px' }}>
              <Title level={4} style={{ marginBottom: '16px' }}>
                概念股票排名（已显示 {displayedCount} / {totalCount}）
              </Title>

              {stocks.length > 0 ? (
                <Spin spinning={loading && currentPage > 1} indicator={<LoadingOutlined />}>
                  <Table
                    columns={columns}
                    dataSource={stocks}
                    rowKey={(record) => record.stock_id}
                    pagination={false}
                    bordered
                    size="small"
                  />

                  {/* 加载更多按钮 */}
                  {hasMore && (
                    <div style={{ textAlign: 'center', marginTop: '16px' }}>
                      <Button
                        type="primary"
                        onClick={handleLoadMore}
                        loading={loading}
                        style={{ minWidth: '200px' }}
                      >
                        加载更多 10 只 ({displayedCount + 10 > totalCount ? totalCount : displayedCount + 10}/
                        {totalCount})
                      </Button>
                    </div>
                  )}

                  {!hasMore && stocks.length > 0 && (
                    <div style={{ textAlign: 'center', marginTop: '16px', color: '#999' }}>
                      已加载全部 {totalCount} 只股票
                    </div>
                  )}
                </Spin>
              ) : loading ? (
                <Spin indicator={<LoadingOutlined />} />
              ) : (
                <Empty description="暂无股票数据" />
              )}
            </Card>

            {/* 提示信息 */}
            <Card style={{ background: '#f0f5ff', borderRadius: '12px', border: 'none' }}>
              <Paragraph style={{ margin: 0, color: '#1890ff' }}>
                <strong>💡 提示：</strong>点击股票代码或"查看图表"按钮可以查看该股票的详细图表分析。
              </Paragraph>
            </Card>
          </motion.div>
        )}
      </Drawer>

      {/* 股票图表模态框 */}
      <StockChartModal
        open={chartModalOpen}
        onClose={() => setChartModalOpen(false)}
        stockCode={selectedStock}
      />
    </>
  );
};

export default ConceptStockDrawer;
