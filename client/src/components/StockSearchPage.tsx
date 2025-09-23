import React, { useState, useCallback } from 'react';
import {
  Card, Input, Button, List, Tag, Typography, Space, Alert, Spin,
  Collapse, Badge, Empty, message, Row, Col
} from 'antd';
import {
  SearchOutlined, StockOutlined, BulbOutlined,
  DownOutlined, UpOutlined, InfoCircleOutlined
} from '@ant-design/icons';
// API配置
const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? 'https://your-domain.com/api/v1'
  : 'http://localhost:3007/api/v1';
import './StockSearchPage.css';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface Stock {
  id: number;
  stock_code: string;
  stock_name: string;
  industry?: string;
  is_convertible_bond?: boolean;
}

interface Concept {
  id: number;
  concept_name: string;
  description?: string;
}

interface StockDetail {
  stock: Stock;
  concepts: Concept[];
}

interface ConceptStocks {
  concept: Concept;
  stocks: Stock[];
}

const StockSearchPage: React.FC = () => {
  // 状态管理
  const [searchValue, setSearchValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [stockDetail, setStockDetail] = useState<StockDetail | null>(null);
  const [conceptStocksMap, setConceptStocksMap] = useState<Map<string, ConceptStocks>>(new Map());
  const [loadingConcepts, setLoadingConcepts] = useState<Set<string>>(new Set());
  const [expandedConcepts, setExpandedConcepts] = useState<Set<string>>(new Set());

  // 搜索股票
  const handleSearch = useCallback(async () => {
    if (!searchValue.trim()) {
      message.warning('请输入股票代码');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/stocks/${searchValue.trim().toUpperCase()}`);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('STOCK_NOT_FOUND');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data) {
        setStockDetail(data);
        // 清空之前的概念股票数据
        setConceptStocksMap(new Map());
        setExpandedConcepts(new Set());
        message.success('查询成功');
      }
    } catch (error: any) {
      console.error('搜索失败:', error);
      if (error.message === 'STOCK_NOT_FOUND') {
        message.error('未找到该股票，请检查股票代码');
      } else {
        message.error('搜索失败，请稍后重试');
      }
      setStockDetail(null);
    } finally {
      setLoading(false);
    }
  }, [searchValue]);

  // 获取概念下的股票
  const fetchConceptStocks = useCallback(async (conceptName: string) => {
    if (conceptStocksMap.has(conceptName)) {
      return; // 已经获取过了
    }

    setLoadingConcepts(prev => new Set(prev).add(conceptName));

    try {
      const response = await fetch(`${API_BASE_URL}/concepts/${encodeURIComponent(conceptName)}/stocks`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data) {
        setConceptStocksMap(prev => new Map(prev).set(conceptName, data));
      }
    } catch (error) {
      console.error('获取概念股票失败:', error);
      message.error(`获取 ${conceptName} 相关股票失败`);
    } finally {
      setLoadingConcepts(prev => {
        const newSet = new Set(prev);
        newSet.delete(conceptName);
        return newSet;
      });
    }
  }, [conceptStocksMap]);

  // 处理概念点击
  const handleConceptClick = useCallback(async (conceptName: string) => {
    // 切换展开状态
    const newExpanded = new Set(expandedConcepts);
    if (newExpanded.has(conceptName)) {
      newExpanded.delete(conceptName);
    } else {
      newExpanded.add(conceptName);
      // 如果是展开且还没有获取数据，则获取数据
      if (!conceptStocksMap.has(conceptName)) {
        await fetchConceptStocks(conceptName);
      }
    }
    setExpandedConcepts(newExpanded);
  }, [expandedConcepts, conceptStocksMap, fetchConceptStocks]);

  // 渲染概念下的股票列表
  const renderConceptStocks = useCallback((conceptName: string, conceptStocks: ConceptStocks) => {
    const { stocks } = conceptStocks;
    const isLoading = loadingConcepts.has(conceptName);

    if (isLoading) {
      return (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Spin size="small" />
          <Text style={{ marginLeft: '8px', color: '#666' }}>正在加载相关股票...</Text>
        </div>
      );
    }

    if (!stocks || stocks.length === 0) {
      return (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="暂无相关股票"
          style={{ margin: '20px 0' }}
        />
      );
    }

    // 显示前10个，其余隐藏
    const visibleStocks = stocks.slice(0, 10);
    const hiddenStocks = stocks.slice(10);

    return (
      <div className="concept-stocks-container">
        <div className="stocks-grid">
          {visibleStocks.map((stock) => (
            <div key={stock.id} className="stock-item">
              <div className="stock-code">
                <StockOutlined />
                <Text strong>{stock.stock_code}</Text>
              </div>
              <div className="stock-name">
                <Text ellipsis={{ tooltip: stock.stock_name }}>{stock.stock_name}</Text>
              </div>
              {stock.industry && (
                <div className="stock-industry">
                  <Text type="secondary" style={{ fontSize: '12px' }}>{stock.industry}</Text>
                </div>
              )}
            </div>
          ))}
        </div>

        {hiddenStocks.length > 0 && (
          <div style={{ textAlign: 'center', marginTop: '16px' }}>
            <Button
              type="link"
              size="small"
              onClick={() => {
                // 这里可以展开显示更多股票
                message.info(`还有 ${hiddenStocks.length} 只相关股票，功能开发中`);
              }}
            >
              查看更多 {hiddenStocks.length} 只股票 <DownOutlined />
            </Button>
          </div>
        )}

        <div className="stocks-summary">
          <Text type="secondary">
            <InfoCircleOutlined /> 共 {stocks.length} 只相关股票
            {stocks.length > 10 && `，显示前 10 只`}
          </Text>
        </div>
      </div>
    );
  }, [loadingConcepts]);

  // 处理回车键搜索
  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  }, [handleSearch]);

  return (
    <div className="stock-search-page">
        <div className="search-header">
          <Title level={2}>
            <StockOutlined /> 个股查询
          </Title>
          <Paragraph type="secondary">
            输入股票代码查询该股票的所有相关概念，点击概念可查看概念下的其他股票
          </Paragraph>
        </div>

        {/* 搜索区域 */}
        <div className="search-section">
          <Row gutter={16} align="middle">
            <Col flex="auto">
              <Input
                size="large"
                placeholder="请输入股票代码，如：000001、600000、300001"
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                onKeyPress={handleKeyPress}
                prefix={<SearchOutlined />}
                allowClear
              />
            </Col>
            <Col>
              <Button
                type="primary"
                size="large"
                icon={<SearchOutlined />}
                loading={loading}
                onClick={handleSearch}
              >
                查询
              </Button>
            </Col>
          </Row>
        </div>

        {/* 搜索结果区域 */}
        {stockDetail && (
          <div className="result-section">
            {/* 股票基本信息 */}
            <Card
              title={
                <Space>
                  <StockOutlined />
                  <span>股票信息</span>
                </Space>
              }
              size="small"
              className="stock-info-card"
            >
              <Row gutter={16}>
                <Col span={8}>
                  <div className="info-item">
                    <Text type="secondary">股票代码</Text>
                    <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
                      {stockDetail.stock.stock_code}
                    </Title>
                  </div>
                </Col>
                <Col span={8}>
                  <div className="info-item">
                    <Text type="secondary">股票名称</Text>
                    <Title level={4} style={{ margin: 0 }}>
                      {stockDetail.stock.stock_name}
                    </Title>
                  </div>
                </Col>
                <Col span={8}>
                  <div className="info-item">
                    <Text type="secondary">所属行业</Text>
                    <Text strong>{stockDetail.stock.industry || '未知'}</Text>
                  </div>
                </Col>
              </Row>
              {stockDetail.stock.is_convertible_bond && (
                <div style={{ marginTop: '8px' }}>
                  <Tag color="purple">可转换债券</Tag>
                </div>
              )}
            </Card>

            {/* 相关概念 */}
            <Card
              title={
                <Space>
                  <BulbOutlined />
                  <span>相关概念</span>
                  <Badge count={stockDetail.concepts.length} />
                </Space>
              }
              size="small"
              className="concepts-card"
            >
              {stockDetail.concepts.length === 0 ? (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description="该股票暂无相关概念"
                />
              ) : (
                <div className="concepts-section">
                  {stockDetail.concepts.map((concept) => {
                    const isExpanded = expandedConcepts.has(concept.concept_name);
                    const conceptStocks = conceptStocksMap.get(concept.concept_name);

                    return (
                      <Card
                        key={concept.id}
                        size="small"
                        className={`concept-card ${isExpanded ? 'expanded' : ''}`}
                        title={
                          <div
                            className="concept-header"
                            onClick={() => handleConceptClick(concept.concept_name)}
                          >
                            <Space>
                              <BulbOutlined />
                              <Text strong>{concept.concept_name}</Text>
                              {isExpanded ? <UpOutlined /> : <DownOutlined />}
                            </Space>
                          </div>
                        }
                        extra={
                          conceptStocks && (
                            <Badge
                              count={conceptStocks.stocks.length}
                              style={{ backgroundColor: '#52c41a' }}
                            />
                          )
                        }
                      >
                        {concept.description && (
                          <Paragraph
                            type="secondary"
                            style={{ marginBottom: isExpanded ? '16px' : '0' }}
                            ellipsis={!isExpanded ? { rows: 1 } : false}
                          >
                            {concept.description}
                          </Paragraph>
                        )}

                        {isExpanded && conceptStocks && renderConceptStocks(concept.concept_name, conceptStocks)}
                      </Card>
                    );
                  })}
                </div>
              )}
            </Card>
          </div>
        )}

        {/* 使用说明 */}
        {!stockDetail && !loading && (
          <Alert
            message="使用说明"
            description={
              <ul style={{ margin: 0, paddingLeft: '20px' }}>
                <li>输入股票代码（如：000001、600000、300001）进行查询</li>
                <li>查询结果将显示该股票的基本信息和所有相关概念</li>
                <li>点击概念标签可以展开查看该概念下的其他股票</li>
                <li>每个概念最多显示前10只股票，点击"查看更多"可查看完整列表</li>
              </ul>
            }
            type="info"
            showIcon
            style={{ marginTop: '24px' }}
          />
        )}
    </div>
  );
};

export default StockSearchPage;