import React, { useState, useEffect } from 'react';
import {
  Card, Button, Spin, Empty, Alert, Tag, Row, Col, Statistic, Space, Divider,
  DatePicker, InputNumber, Table, message, Progress
} from 'antd';
import {
  LoadingOutlined, FireOutlined, CheckCircleOutlined, BarChartOutlined
} from '@ant-design/icons';
import { API_BASE_URL } from '../config/api';
import dayjs from 'dayjs';
import './NewHighConceptPage.css';

interface Concept {
  id: number;
  concept_name: string;
  description: string;
  created_at: string;
}

interface NewHighConcept {
  concept: Concept;
  total_heat_value: number;
  stock_count: number;
  average_heat_value: number;
  days_checked: number;
  trade_date: string;
}

const NewHighConceptPage: React.FC = () => {
  const [concepts, setConcepts] = useState<NewHighConcept[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [days, setDays] = useState(10);
  const [tradeDate, setTradeDate] = useState(dayjs());

  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const tradeDateStr = tradeDate.format('YYYY-MM-DD');
      const params = new URLSearchParams();
      params.append('days', days.toString());
      params.append('trade_date', tradeDateStr);

      const response = await fetch(
        `${API_BASE_URL}/concepts/new-highs?${params.toString()}`,
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

      const data: NewHighConcept[] = await response.json();
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

  const conceptColumns = [
    {
      title: '概念名称',
      dataIndex: ['concept', 'concept_name'],
      key: 'concept_name',
      width: '20%',
      render: (text: string) => (
        <Tag color="red" style={{ padding: '4px 12px', fontSize: '13px' }}>
          {text}
        </Tag>
      ),
    },
    {
      title: '概念描述',
      dataIndex: ['concept', 'description'],
      key: 'description',
      width: '25%',
    },
    {
      title: '股票数量',
      dataIndex: 'stock_count',
      key: 'stock_count',
      width: '12%',
      render: (count: number) => (
        <span style={{ fontWeight: 'bold', color: '#ff7a45' }}>{count} 只</span>
      ),
    },
    {
      title: '总热度值',
      dataIndex: 'total_heat_value',
      key: 'total_heat_value',
      width: '15%',
      render: (value: number) => (
        <span style={{ fontWeight: 'bold', color: '#667eea' }}>
          {value.toFixed(2)}
        </span>
      ),
      sorter: (a: NewHighConcept, b: NewHighConcept) =>
        b.total_heat_value - a.total_heat_value,
    },
    {
      title: '平均热度',
      dataIndex: 'average_heat_value',
      key: 'average_heat_value',
      width: '13%',
      render: (value: number) => (
        <span style={{ color: '#764ba2' }}>{value.toFixed(2)}</span>
      ),
      sorter: (a: NewHighConcept, b: NewHighConcept) =>
        b.average_heat_value - a.average_heat_value,
    },
    {
      title: '检查周期',
      dataIndex: 'days_checked',
      key: 'days_checked',
      width: '10%',
      render: (value: number) => (
        <span>{value} 天</span>
      ),
    },
  ];

  return (
    <div className="new-high-concept-page">
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FireOutlined style={{ fontSize: '20px', color: '#ff7a45' }} />
            <span>创新高概念查询</span>
          </div>
        }
        bordered={false}
        style={{ marginBottom: '24px' }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <p style={{ color: '#666', marginBottom: '12px' }}>
            查询在指定交易日期内，过去N天创新高的所有概念及其热度数据
          </p>

          <Row gutter={[16, 16]} style={{ alignItems: 'flex-end' }}>
            <Col xs={24} sm={12} md={6}>
              <div style={{ marginBottom: '8px' }}>
                <label style={{ color: '#333', fontWeight: 500 }}>检查天数</label>
              </div>
              <InputNumber
                min={1}
                max={30}
                value={days}
                onChange={(value) => setDays(value || 10)}
                size="large"
                style={{ width: '100%' }}
                placeholder="输入天数"
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
                icon={<BarChartOutlined />}
                onClick={handleSearch}
                loading={loading}
                style={{ width: '100%' }}
              >
                查询创新高概念
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
          <Spin indicator={<LoadingOutlined style={{ fontSize: 48, color: '#ff7a45' }} />} />
          <p style={{ marginTop: '16px', color: '#999' }}>正在查询创新高概念...</p>
        </Card>
      )}

      {/* 查询结果 */}
      {!loading && searched && !error && concepts.length > 0 && (
        <div style={{ animation: 'fadeIn 0.3s ease-in' }}>
          {/* 统计信息卡片 */}
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircleOutlined style={{ fontSize: '18px', color: '#667eea' }} />
                <span>查询统计</span>
              </div>
            }
            bordered={false}
            style={{ marginBottom: '24px' }}
          >
            <Row gutter={[24, 24]}>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="创新高概念数"
                  value={concepts.length}
                  suffix="个"
                  valueStyle={{ color: '#ff7a45', fontWeight: 'bold' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="总股票数"
                  value={concepts.reduce((sum, c) => sum + c.stock_count, 0)}
                  suffix="只"
                  valueStyle={{ color: '#667eea', fontWeight: 'bold' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="平均热度值"
                  value={
                    concepts.length > 0
                      ? (
                          concepts.reduce((sum, c) => sum + c.total_heat_value, 0) /
                          concepts.length
                        ).toFixed(2)
                      : 0
                  }
                  valueStyle={{ color: '#764ba2', fontWeight: 'bold' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="检查周期"
                  value={concepts.length > 0 ? concepts[0].days_checked : 0}
                  suffix="天"
                  valueStyle={{ color: '#52c41a', fontWeight: 'bold' }}
                />
              </Col>
            </Row>
          </Card>

          <Divider style={{ margin: '24px 0' }} />

          {/* 创新高概念列表 */}
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FireOutlined style={{ fontSize: '18px', color: '#ff7a45' }} />
                <span>创新高概念详情</span>
                <Tag color="red" style={{ marginLeft: '8px' }}>
                  {concepts.length} 个
                </Tag>
              </div>
            }
            bordered={false}
          >
            <Table
              columns={conceptColumns}
              dataSource={concepts}
              rowKey={(record) => record.concept.id}
              pagination={{
                pageSize: 15,
                showSizeChanger: true,
                pageSizeOptions: ['10', '15', '20', '50'],
                showTotal: (total) => `共 ${total} 个概念`,
              }}
              bordered
              size="small"
            />
          </Card>
        </div>
      )}

      {/* 无结果 */}
      {!loading && searched && !error && concepts.length === 0 && (
        <Card
          style={{
            textAlign: 'center',
            background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
            border: 'none',
          }}
        >
          <Empty
            description="未找到创新高概念"
            style={{ padding: '40px 0' }}
          />
        </Card>
      )}

      {/* 初始状态 */}
      {!searched && (
        <Card
          style={{
            textAlign: 'center',
            background: 'linear-gradient(135deg, #fff9e6 0%, #ffe7ba 100%)',
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

export default NewHighConceptPage;
