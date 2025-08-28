import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Typography, Space, Tag, Progress, Timeline, Alert } from 'antd';
import {
  UserOutlined, GiftOutlined, DollarOutlined, LineChartOutlined,
  TrophyOutlined, ClockCircleOutlined, CheckCircleOutlined,
  DatabaseOutlined, ApiOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text } = Typography;

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  const systemStats = {
    totalUsers: 1248,
    totalPackages: 4,
    totalRevenue: 12580,
    activeUsers: 342,
    systemUptime: 99.8,
    todayVisits: 156
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>
          📊 管理控制台
        </Title>
        <Text type="secondary">欢迎回来，{user?.username}！</Text>
      </div>

      {/* 系统状态提醒 */}
      <Alert
        message="系统运行正常"
        description="所有服务运行良好，数据库连接正常，API响应时间良好。"
        type="success"
        showIcon
        style={{ marginBottom: 24, borderRadius: '8px' }}
      />

      {/* 核心统计指标 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card style={{ borderRadius: '8px' }}>
            <Statistic
              title="总用户数"
              value={systemStats.totalUsers}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
            <div style={{ marginTop: 8 }}>
              <Tag color="green">+12% 本月</Tag>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <Card style={{ borderRadius: '8px' }}>
            <Statistic
              title="套餐数量"
              value={systemStats.totalPackages}
              prefix={<GiftOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ marginTop: 8 }}>
              <Tag color="blue">全部启用</Tag>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <Card style={{ borderRadius: '8px' }}>
            <Statistic
              title="总收入"
              value={systemStats.totalRevenue}
              prefix={<DollarOutlined />}
              suffix="¥"
              valueStyle={{ color: '#cf1322' }}
            />
            <div style={{ marginTop: 8 }}>
              <Tag color="red">+8% 本月</Tag>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <Card style={{ borderRadius: '8px' }}>
            <Statistic
              title="活跃用户"
              value={systemStats.activeUsers}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
            <div style={{ marginTop: 8 }}>
              <Tag color="orange">24小时内</Tag>
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 系统状态 */}
        <Col xs={24} md={12}>
          <Card title="系统状态" style={{ borderRadius: '8px', height: '300px' }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <Text>系统运行时间</Text>
                  <Text strong>{systemStats.systemUptime}%</Text>
                </div>
                <Progress 
                  percent={systemStats.systemUptime} 
                  status="active"
                  strokeColor="#52c41a"
                />
              </div>
              
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <Text>今日访问量</Text>
                  <Text strong>{systemStats.todayVisits}</Text>
                </div>
                <Progress 
                  percent={78} 
                  strokeColor="#1890ff"
                />
              </div>
              
              <div style={{ marginTop: 16 }}>
                <Space>
                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  <Text>数据库连接正常</Text>
                </Space>
              </div>
              
              <div>
                <Space>
                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  <Text>API服务运行正常</Text>
                </Space>
              </div>
              
              <div>
                <Space>
                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  <Text>支付系统正常</Text>
                </Space>
              </div>
            </Space>
          </Card>
        </Col>

        {/* 最近活动 */}
        <Col xs={24} md={12}>
          <Card title="最近活动" style={{ borderRadius: '8px', height: '300px' }}>
            <Timeline
              items={[
                {
                  dot: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
                  children: (
                    <div>
                      <Text strong>新用户注册</Text>
                      <br />
                      <Text type="secondary">用户 user_1234 完成注册</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: '12px' }}>2分钟前</Text>
                    </div>
                  ),
                },
                {
                  dot: <DollarOutlined style={{ color: '#faad14' }} />,
                  children: (
                    <div>
                      <Text strong>套餐购买</Text>
                      <br />
                      <Text type="secondary">月度会员套餐被购买</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: '12px' }}>15分钟前</Text>
                    </div>
                  ),
                },
                {
                  dot: <DatabaseOutlined style={{ color: '#1890ff' }} />,
                  children: (
                    <div>
                      <Text strong>数据导入</Text>
                      <br />
                      <Text type="secondary">CSV文件导入成功</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: '12px' }}>1小时前</Text>
                    </div>
                  ),
                },
                {
                  dot: <ApiOutlined style={{ color: '#722ed1' }} />,
                  children: (
                    <div>
                      <Text strong>系统更新</Text>
                      <br />
                      <Text type="secondary">套餐管理功能上线</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: '12px' }}>今天</Text>
                    </div>
                  ),
                },
              ]}
            />
          </Card>
        </Col>
      </Row>

      {/* 快捷操作 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="快捷操作" style={{ borderRadius: '8px' }}>
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={8}>
                <Card 
                  hoverable
                  style={{ textAlign: 'center', border: '1px solid #d9d9d9' }}
                  bodyStyle={{ padding: '16px' }}
                >
                  <GiftOutlined style={{ fontSize: '24px', color: '#1890ff', marginBottom: '8px' }} />
                  <div>管理套餐</div>
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card 
                  hoverable
                  style={{ textAlign: 'center', border: '1px solid #d9d9d9' }}
                  bodyStyle={{ padding: '16px' }}
                >
                  <UserOutlined style={{ fontSize: '24px', color: '#52c41a', marginBottom: '8px' }} />
                  <div>用户管理</div>
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card 
                  hoverable
                  style={{ textAlign: 'center', border: '1px solid #d9d9d9' }}
                  bodyStyle={{ padding: '16px' }}
                >
                  <DatabaseOutlined style={{ fontSize: '24px', color: '#faad14', marginBottom: '8px' }} />
                  <div>数据导入</div>
                </Card>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;