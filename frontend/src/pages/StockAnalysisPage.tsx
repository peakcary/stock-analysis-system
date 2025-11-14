import React, { useState } from 'react';
import {
  Card, Input, Button, Spin, Table, Empty, Alert, Tag, Row, Col,
  Statistic, Space, Divider, Form, message
} from 'antd';
import {
  SearchOutlined, LoadingOutlined, CheckCircleOutlined,
  ExclamationCircleOutlined, HomeOutlined
} from '@ant-design/icons';
import { API_BASE_URL } from '../config/api';
import './StockAnalysisPage.css';

interface Stock {
  id: number;
  stock_code: string;
  original_stock_code: string;
  stock_code_prefix: string;
  stock_name: string;
  industry: string;
  is_convertible_bond: boolean;
  created_at: string;
  updated_at: string;
}

interface Concept {
  id: number;
  concept_name: string;
  description: string;
  created_at: string;
}

interface StockConceptResponse {
  stock: Stock;
  concepts: Concept[];
}

const StockAnalysisPage: React.FC = () => {
  const [searchInput, setSearchInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stock, setStock] = useState<Stock | null>(null);
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (value?: string) => {
    const stockCode = value || searchInput;

    if (!stockCode.trim()) {
      message.warning('请输入股票代码');
      return;
    }

    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/concepts/stocks/${encodeURIComponent(stockCode)}/concepts`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include'
        }
      );

      if (!response.ok) {
        const errorData = await response.json();

        if (response.status === 404) {
          setError(`股票不存在: ${stockCode}`);
        } else if (response.status === 403) {
          setError('查询次数不足，请升级会员或购买查询包');
        } else if (response.status === 401) {
          setError('认证失效，请重新登录');
        } else {
          setError(errorData.detail || '查询失败，请稍后重试');
        }

        setStock(null);
        setConcepts([]);
        setLoading(false);
        return;
      }

      const data: StockConceptResponse = await response.json();
      setStock(data.stock);
      setConcepts(data.concepts);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '网络错误';
      setError(`网络错误: ${errorMessage}`);
      setStock(null);
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
        <Tag color="blue">{text}</Tag>
      ),
    },
    {
      title: '概念描述',
      dataIndex: 'description',
      key: 'description',
      width: '50%',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: '20%',
      render: (date: string) => new Date(date).toLocaleDateString('zh-CN'),
    },
  ];

  return (
    <div className="stock-analysis-page">
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <SearchOutlined style={{ fontSize: '20px', color: '#667eea' }} />
            <span>个股概念查询</span>
          </div>
        }
        bordered={false}
        style={{ marginBottom: '24px' }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <p style={{ color: '#666', marginBottom: '16px' }}>
            输入股票代码（如：000001 或 SZ000001）查询该股票所属的所有概念
          </p>

          <Space.Compact style={{ width: '100%', maxWidth: '500px' }}>
            <Input
              placeholder="请输入股票代码（如: 000001 或 SZ000001）"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onPressEnter={() => handleSearch()}
              size="large"
              disabled={loading}
            />
            <Button
              type="primary"
              size="large"
              icon={<SearchOutlined />}
              onClick={() => handleSearch()}
              loading={loading}
            >
              查询
            </Button>
          </Space.Compact>
        </Space>
      </Card>

      {/* 错误提示 */}
      {error && (
        <Alert
          message="查询失败"
          description={error}
          type="error"
          showIcon
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: '24px' }}
        />
      )}

      {/* 加载状态 */}
      {loading && (
        <Card style={{ textAlign: 'center', padding: '40px' }}>
          <Spin indicator={<LoadingOutlined style={{ fontSize: 48, color: '#667eea' }} />} />
          <p style={{ marginTop: '16px', color: '#999' }}>正在查询股票信息...</p>
        </Card>
      )}

      {/* 查询结果 */}
      {!loading && searched && !error && stock && (
        <div style={{ animation: 'fadeIn 0.3s ease-in' }}>
          {/* 股票信息卡片 */}
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <HomeOutlined style={{ fontSize: '18px', color: '#667eea' }} />
                <span>股票信息</span>
              </div>
            }
            bordered={false}
            style={{ marginBottom: '24px' }}
          >
            <Row gutter={[24, 24]}>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="股票代码"
                  value={stock.stock_code}
                  valueStyle={{ color: '#667eea', fontWeight: 'bold', fontSize: '18px' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="股票名称"
                  value={stock.stock_name}
                  valueStyle={{ color: '#764ba2', fontWeight: 'bold', fontSize: '18px' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="所属行业"
                  value={stock.industry || '未分类'}
                  valueStyle={{ color: '#52c41a', fontWeight: 'bold', fontSize: '18px' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="类型"
                  value={stock.is_convertible_bond ? '可转债' : '普通股票'}
                  valueStyle={{
                    color: stock.is_convertible_bond ? '#ff7a45' : '#1890ff',
                    fontWeight: 'bold',
                    fontSize: '18px'
                  }}
                />
              </Col>
            </Row>
          </Card>

          <Divider style={{ margin: '24px 0' }} />

          {/* 概念列表 */}
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircleOutlined style={{ fontSize: '18px', color: '#667eea' }} />
                <span>所属概念</span>
                <Tag color="blue" style={{ marginLeft: '8px' }}>
                  {concepts.length} 个
                </Tag>
              </div>
            }
            bordered={false}
          >
            {concepts.length > 0 ? (
              <div>
                {/* 概念标签展示 */}
                <div style={{ marginBottom: '24px' }}>
                  <p style={{ color: '#666', marginBottom: '12px' }}>
                    <strong>概念汇总：</strong>
                  </p>
                  <Space wrap size="middle" style={{ width: '100%' }}>
                    {concepts.map((concept) => (
                      <Tag
                        key={concept.id}
                        color="blue"
                        style={{
                          padding: '6px 12px',
                          fontSize: '14px',
                          cursor: 'pointer',
                          transition: 'all 0.3s ease'
                        }}
                      >
                        {concept.concept_name}
                      </Tag>
                    ))}
                  </Space>
                </div>

                <Divider />

                {/* 概念详细表格 */}
                <p style={{ color: '#666', marginBottom: '16px' }}>
                  <strong>详细信息：</strong>
                </p>
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
            ) : (
              <Empty description="该股票暂无相关概念" />
            )}
          </Card>
        </div>
      )}

      {/* 初始状态或查询失败 */}
      {!loading && (!searched || (searched && !stock && error)) && (
        !error && (
          <Card
            style={{
              textAlign: 'center',
              background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
              border: 'none',
            }}
          >
            <Empty
              description={searched ? '未找到相关数据' : '输入股票代码开始查询'}
              style={{ padding: '40px 0' }}
            />
          </Card>
        )
      )}
    </div>
  );
};

export default StockAnalysisPage;
