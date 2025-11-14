import React, { useState, useEffect } from 'react';
import {
  Card, Button, Spin, Empty, Alert, Tag, Row, Col, Statistic, Space, Divider,
  DatePicker, InputNumber, Table, message, Collapse, Progress
} from 'antd';
import {
  LoadingOutlined, TrophyOutlined, CheckCircleOutlined, RiseOutlined
} from '@ant-design/icons';
import { API_BASE_URL } from '../config/api';
import dayjs from 'dayjs';
import './TopConceptsStockPage.css';

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

interface TopStocksConcept {
  concept: Concept;
  top_stocks: Stock[];
  count: number;
}

const TopConceptsStockPage: React.FC = () => {
  const [topN, setTopN] = useState(10);
  const [tradeDate, setTradeDate] = useState(dayjs());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [concepts, setConcepts] = useState<TopStocksConcept[]>([]);

  const handleSearch = async () => {
    if (topN < 1 || topN > 50) {
      message.warning('请输入1-50之间的数字');
      return;
    }

    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const tradeDateStr = tradeDate.format('YYYY-MM-DD');
      const params = new URLSearchParams();
      params.append('trade_date', tradeDateStr);

      const response = await fetch(
        `${API_BASE_URL}/concepts/top-stocks/${topN}?${params.toString()}`,
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

        if (response.status === 401) {
          setError('认证失效，请重新登录');
        } else {
          setError(errorData.detail || '查询失败，请稍后重试');
        }

        setConcepts([]);
        setLoading(false);
        return;
      }

      const data: TopStocksConcept[] = await response.json();
      setConcepts(data);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '网络错误';
      setError(`网络错误: ${errorMessage}`);
      setConcepts([]);
    } finally {
      setLoading(false);
    }
  };

  const stockColumns = [
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: '15%',
      render: (text: string) => (
        <Tag color="green" style={{ padding: '4px 12px', fontSize: '13px' }}>
          {text}
        </Tag>
      ),
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      width: '20%',
      render: (text: string) => (
        <span style={{ fontWeight: 500 }}>{text}</span>
      ),
    },
    {
      title: '所属行业',
      dataIndex: 'industry',
      key: 'industry',
      width: '20%',
      render: (text: string) => (
        <span style={{ color: '#666' }}>{text || '未分类'}</span>
      ),
    },
    {
      title: '类型',
      dataIndex: 'is_convertible_bond',
      key: 'is_convertible_bond',
      width: '15%',
      render: (is_bond: boolean) => (
        <Tag color={is_bond ? 'orange' : 'blue'}>
          {is_bond ? '可转债' : '普通股票'}
        </Tag>
      ),
    },
  ];

  const renderConceptCards = () => {
    return concepts.map((item, index) => (
      <Card
        key={item.concept.id}
        className="concept-card"
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Tag color="blue" style={{ marginRight: '8px' }}>
              TOP {topN}
            </Tag>
            <span style={{ fontSize: '16px', fontWeight: 'bold' }}>
              {item.concept.concept_name}
            </span>
            <Tag color="red">{item.count} 只</Tag>
          </div>
        }
        bordered={false}
        style={{ marginBottom: '16px' }}
        extra={
          <span style={{ fontSize: '12px', color: '#999' }}>
            排名 #{index + 1}
          </span>
        }
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <p style={{ color: '#666', marginBottom: '0' }}>
            {item.concept.description}
          </p>

          <Table
            columns={stockColumns}
            dataSource={item.top_stocks}
            rowKey={(record) => record.id}
            pagination={false}
            bordered
            size="small"
            scroll={{ x: true }}
          />
        </Space>
      </Card>
    ));
  };

  return (
    <div className="top-concepts-stock-page">
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrophyOutlined style={{ fontSize: '20px', color: '#faad14' }} />
            <span>概念前N股票查询</span>
          </div>
        }
        bordered={false}
        style={{ marginBottom: '24px' }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <p style={{ color: '#666', marginBottom: '12px' }}>
            查询所有概念在指定日期内的前N只热度股票，展示概念最受欢迎的股票组合
          </p>

          <Row gutter={[16, 16]} style={{ alignItems: 'flex-end' }}>
            <Col xs={24} sm={12} md={6}>
              <div style={{ marginBottom: '8px' }}>
                <label style={{ color: '#333', fontWeight: 500 }}>前N只股票</label>
              </div>
              <InputNumber
                min={1}
                max={50}
                value={topN}
                onChange={(value) => setTopN(value || 10)}
                size="large"
                style={{ width: '100%' }}
                placeholder="输入N值(1-50)"
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <div style={{ marginBottom: '8px' }}>
                <label style={{ color: '#333', fontWeight: 500 }}>交易日期</label>
              </div>
              <DatePicker
                value={tradeDate}
                onChange={(date) => setTradeDate(date || dayjs())}
                format="YYYY-MM-DD"
                size="large"
                style={{ width: '100%' }}
              />
            </Col>
            <Col xs={24} sm={24} md={12}>
              <Button
                type="primary"
                size="large"
                icon={<RiseOutlined />}
                onClick={handleSearch}
                loading={loading}
                style={{ width: '100%' }}
              >
                查询前N股票
              </Button>
            </Col>
          </Row>
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
          <Spin indicator={<LoadingOutlined style={{ fontSize: 48, color: '#faad14' }} />} />
          <p style={{ marginTop: '16px', color: '#999' }}>正在查询前{topN}股票...</p>
        </Card>
      )}

      {/* 查询结果 */}
      {!loading && searched && !error && concepts.length > 0 && (
        <div style={{ animation: 'fadeIn 0.3s ease-in' }}>
          {/* 统计信息卡片 */}
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircleOutlined style={{ fontSize: '18px', color: '#faad14' }} />
                <span>查询统计</span>
              </div>
            }
            bordered={false}
            style={{ marginBottom: '24px' }}
          >
            <Row gutter={[24, 24]}>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="概念总数"
                  value={concepts.length}
                  suffix="个"
                  valueStyle={{ color: '#faad14', fontWeight: 'bold' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="每个概念前N股"
                  value={topN}
                  suffix="只"
                  valueStyle={{ color: '#52c41a', fontWeight: 'bold' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="总股票数"
                  value={concepts.reduce((sum, c) => sum + c.count, 0)}
                  suffix="只"
                  valueStyle={{ color: '#1890ff', fontWeight: 'bold' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="平均每个概念"
                  value={
                    concepts.length > 0
                      ? (concepts.reduce((sum, c) => sum + c.count, 0) / concepts.length).toFixed(2)
                      : 0
                  }
                  suffix="只"
                  valueStyle={{ color: '#722ed1', fontWeight: 'bold' }}
                />
              </Col>
            </Row>
          </Card>

          <Divider style={{ margin: '24px 0' }} />

          {/* 概念及其前N股票列表 */}
          <div>
            <div style={{ marginBottom: '16px' }}>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TrophyOutlined style={{ color: '#faad14' }} />
                <span>概念前N股票详情</span>
                <Tag color="orange" style={{ marginLeft: '8px' }}>
                  {concepts.length} 个概念
                </Tag>
              </h3>
            </div>

            {renderConceptCards()}
          </div>
        </div>
      )}

      {/* 无结果 */}
      {!loading && searched && !error && concepts.length === 0 && (
        <Card
          style={{
            textAlign: 'center',
            background: 'linear-gradient(135deg, #fffbe6 0%, #ffe58f 100%)',
            border: 'none',
          }}
        >
          <Empty
            description="未找到相关数据"
            style={{ padding: '40px 0' }}
          />
        </Card>
      )}

      {/* 初始状态 */}
      {!searched && (
        <Card
          style={{
            textAlign: 'center',
            background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
            border: 'none',
          }}
        >
          <Empty
            description="设置查询条件后开始查询"
            style={{ padding: '40px 0' }}
          />
        </Card>
      )}
    </div>
  );
};

export default TopConceptsStockPage;
