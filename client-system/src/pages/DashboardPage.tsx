import React from 'react';
import { Card, Row, Col, Statistic, Button, Space, Table, Tag } from 'antd';
import {
  UserOutlined, CreditCardOutlined, HistoryOutlined,
  ShoppingOutlined, CheckCircleOutlined
} from '@ant-design/icons';

interface UserInfo {
  id: number;
  username: string;
  email: string;
  membership_type: string;
  queries_remaining: number;
  queries_count: number;
  created_at: string;
}

interface DashboardPageProps {
  userInfo: UserInfo | null;
}

const DashboardPage: React.FC<DashboardPageProps> = ({ userInfo }) => {
  // 会员类型颜色映射
  const getMembershipColor = (type: string) => {
    switch (type) {
      case 'premium':
        return '#52c41a';
      case 'pro':
        return '#faad14';
      default:
        return '#d9d9d9';
    }
  };

  // 会员类型中文
  const getMembershipLabel = (type: string) => {
    switch (type) {
      case 'premium':
        return '高级会员';
      case 'pro':
        return '专业版';
      case 'free_trial':
        return '免费试用';
      default:
        return '免费';
    }
  };

  // 最近订单数据
  const recentOrders = [
    {
      key: '1',
      id: 'ORD202410001',
      package: '免费试用',
      amount: '免费',
      status: 'completed',
      date: '2024-10-20',
    },
    {
      key: '2',
      id: 'ORD202410002',
      package: '专业版月卡',
      amount: '¥99.00',
      status: 'completed',
      date: '2024-10-15',
    },
  ];

  const columns = [
    {
      title: '订单号',
      dataIndex: 'id',
      key: 'id',
      width: 150,
    },
    {
      title: '套餐',
      dataIndex: 'package',
      key: 'package',
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: () => (
        <Tag color="green">
          <CheckCircleOutlined /> 已完成
        </Tag>
      ),
    },
    {
      title: '时间',
      dataIndex: 'date',
      key: 'date',
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 欢迎卡片 */}
      <Card
        style={{
          marginBottom: '24px',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
        }}
        bodyStyle={{ padding: '24px' }}
      >
        <h2 style={{ margin: '0 0 8px 0', fontSize: '28px', fontWeight: 'bold' }}>
          欢迎回来，{userInfo?.username}！
        </h2>
        <p style={{ margin: 0, fontSize: '14px', opacity: 0.9 }}>
          {new Date().toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            weekday: 'long',
          })}
        </p>
      </Card>

      {/* 统计信息 */}
      <Row gutter={[24, 24]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ borderRadius: '8px' }}>
            <Statistic
              title="当前会员级别"
              value={getMembershipLabel(userInfo?.membership_type || 'free')}
              prefix={
                <div
                  style={{
                    width: '12px',
                    height: '12px',
                    borderRadius: '50%',
                    background: getMembershipColor(userInfo?.membership_type || 'free'),
                    display: 'inline-block',
                    marginRight: '8px',
                  }}
                ></div>
              }
              valueStyle={{ fontSize: '16px', fontWeight: '600' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card style={{ borderRadius: '8px' }}>
            <Statistic
              title="剩余查询次数"
              value={userInfo?.queries_remaining || 0}
              suffix={`/ ${userInfo?.queries_count || 0}`}
              prefix={<ShoppingOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ fontSize: '16px', fontWeight: '600', color: '#1890ff' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card style={{ borderRadius: '8px' }}>
            <Statistic
              title="账户创建时间"
              value={new Date(userInfo?.created_at || '').toLocaleDateString('zh-CN')}
              prefix={<HistoryOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ fontSize: '16px', fontWeight: '600', color: '#faad14' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card style={{ borderRadius: '8px' }}>
            <Statistic
              title="账户邮箱"
              value={userInfo?.email?.substring(0, 15) + (userInfo?.email && userInfo.email.length > 15 ? '...' : '')}
              prefix={<UserOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ fontSize: '14px', fontWeight: '600', color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 快速操作 */}
      <Card
        title={<span style={{ fontWeight: 'bold' }}>快速操作</span>}
        style={{ marginBottom: '24px', borderRadius: '8px' }}
        bodyStyle={{ padding: '24px' }}
      >
        <Space wrap>
          <Button
            type="primary"
            size="large"
            icon={<CreditCardOutlined />}
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
              borderRadius: '6px',
            }}
          >
            购买套餐
          </Button>
          <Button
            size="large"
            icon={<HistoryOutlined />}
            style={{ borderRadius: '6px' }}
          >
            查看订单
          </Button>
          <Button
            size="large"
            icon={<UserOutlined />}
            style={{ borderRadius: '6px' }}
          >
            用户中心
          </Button>
        </Space>
      </Card>

      {/* 最近订单 */}
      <Card
        title={<span style={{ fontWeight: 'bold' }}>最近订单</span>}
        style={{ borderRadius: '8px' }}
        bodyStyle={{ padding: '24px' }}
      >
        <Table
          columns={columns}
          dataSource={recentOrders}
          pagination={false}
          size="small"
          style={{ borderRadius: '8px' }}
        />
        <div style={{ marginTop: '16px', textAlign: 'center' }}>
          <Button type="link">查看全部订单</Button>
        </div>
      </Card>
    </div>
  );
};

export default DashboardPage;
