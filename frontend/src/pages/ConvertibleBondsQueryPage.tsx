import React, { useState } from 'react';
import {
  Card, Input, Button, Spin, Table, Empty, Alert, Tag, Row, Col,
  Statistic, Space, Divider, Form, message
} from 'antd';
import {
  SearchOutlined, LoadingOutlined, CheckCircleOutlined,
  GiftOutlined, HomeOutlined
} from '@ant-design/icons';
import { API_BASE_URL } from '../config/api';
import './ConvertibleBondsQueryPage.css';

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

interface BondConceptResponse {
  stock: Stock;
  concepts: Concept[];
}

const ConvertibleBondsQueryPage: React.FC = () => {
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
    const bondCodeRegex = /^(1\d{3}|SZ1\d{3}|SH1\d{3})$/i;
    if (!bondCodeRegex.test(bondCode.trim())) {
      message.warning('请输入正确的可转债代码格式 (如: 1001, SZ1001)');
      return;
    }

    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/concepts/bonds/${encodeURIComponent(bondCode)}/concepts`,
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
          setError(`可转债不存在: ${bondCode}`);
        } else if (response.status === 403) {
          setError('查询次数不足，请升级会员或购买查询包');
        } else if (response.status === 401) {
          setError('认证失效，请重新登录');
        } else {
          setError(errorData.detail || '查询失败，请稍后重试');
        }

        setBond(null);
        setConcepts([]);
        setLoading(false);
        return;
      }

      const data: BondConceptResponse = await response.json();

      // 验证返回的是可转债
      if (!data.stock.is_convertible_bond) {
        setError('该证券不是可转债，请输入正确的可转债代码');
        setBond(null);
        setConcepts([]);
        setLoading(false);
        return;
      }

      setBond(data.stock);
      setConcepts(data.concepts);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '网络错误';
      setError(`网络错误: ${errorMessage}`);
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
        <Tag color="orange">{text}</Tag>
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
    <div className="convertible-bonds-query-page">
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <GiftOutlined style={{ fontSize: '20px', color: '#fa8c16' }} />
            <span>可转债概念查询</span>
          </div>
        }
        bordered={false}
        style={{ marginBottom: '24px' }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <p style={{ color: '#666', marginBottom: '16px' }}>
            输入可转债代码（如：1001 或 SZ1001）查询该可转债所属的所有概念
          </p>

          <Space.Compact style={{ width: '100%', maxWidth: '500px' }}>
            <Input
              placeholder="请输入可转债代码（如: 1001 或 SZ1001）"
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
          <Spin indicator={<LoadingOutlined style={{ fontSize: 48, color: '#fa8c16' }} />} />
          <p style={{ marginTop: '16px', color: '#999' }}>正在查询可转债信息...</p>
        </Card>
      )}

      {/* 查询结果 */}
      {!loading && searched && !error && bond && (
        <div style={{ animation: 'fadeIn 0.3s ease-in' }}>
          {/* 可转债信息卡片 */}
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <HomeOutlined style={{ fontSize: '18px', color: '#fa8c16' }} />
                <span>可转债信息</span>
              </div>
            }
            bordered={false}
            style={{ marginBottom: '24px' }}
          >
            <Row gutter={[24, 24]}>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="可转债代码"
                  value={bond.stock_code}
                  valueStyle={{ color: '#fa8c16', fontWeight: 'bold', fontSize: '18px' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="可转债名称"
                  value={bond.stock_name}
                  valueStyle={{ color: '#ff7a45', fontWeight: 'bold', fontSize: '18px' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="所属行业"
                  value={bond.industry || '未分类'}
                  valueStyle={{ color: '#52c41a', fontWeight: 'bold', fontSize: '18px' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="类型"
                  value="可转债"
                  valueStyle={{ color: '#fa8c16', fontWeight: 'bold', fontSize: '18px' }}
                />
              </Col>
            </Row>
          </Card>

          <Divider style={{ margin: '24px 0' }} />

          {/* 概念列表 */}
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircleOutlined style={{ fontSize: '18px', color: '#fa8c16' }} />
                <span>所属概念</span>
                <Tag color="orange" style={{ marginLeft: '8px' }}>
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
                        color="orange"
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
              <Empty description="该可转债暂无相关概念" />
            )}
          </Card>
        </div>
      )}

      {/* 初始状态或查询失败 */}
      {!loading && (!searched || (searched && !bond && error)) && (
        !error && (
          <Card
            style={{
              textAlign: 'center',
              background: 'linear-gradient(135deg, #fff7e6 0%, #ffe7ba 100%)',
              border: 'none',
            }}
          >
            <Empty
              description={searched ? '未找到相关数据' : '输入可转债代码开始查询'}
              style={{ padding: '40px 0' }}
            />
          </Card>
        )
      )}
    </div>
  );
};

export default ConvertibleBondsQueryPage;
