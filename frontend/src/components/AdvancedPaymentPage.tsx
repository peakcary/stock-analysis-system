import React, { useState, useEffect } from 'react';
import {
  Layout, Card, Button, Space, message, Modal, Input, Form, Divider,
  Alert, Typography, Progress, Statistic, Steps, Avatar, Badge, QRCode, Spin
} from 'antd';
import {
  UserOutlined, ShoppingOutlined, CheckCircleOutlined, DollarOutlined,
  LogoutOutlined, CreditCardOutlined, HistoryOutlined, ArrowRightOutlined
} from '@ant-design/icons';
import axios from 'axios';
import dayjs from 'dayjs';
import { getApiUrl } from '../../../shared/api.config';

const { Header, Content, Sider } = Layout;
const { Title, Text, Paragraph } = Typography;

interface PaymentOrder {
  id: number;
  out_trade_no: string;
  amount: string;
  code_url: string;
  expire_time: string;
  status: string;
  created_at: string;
  package_name: string;
}

interface UserInfo {
  id: number;
  username: string;
  email: string;
  membership_type: string;
  queries_remaining: number;
}

const AdvancedPaymentPage: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [username, setUsername] = useState('testuser');
  const [password, setPassword] = useState('testuser');
  const [token, setToken] = useState<string | null>(localStorage.getItem('advanced_payment_token'));
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [paymentOrder, setPaymentOrder] = useState<PaymentOrder | null>(null);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [collapsed, setCollapsed] = useState(false);

  const PAYMENT_AMOUNT = 0.01;
  const ORDER_TIMEOUT = 7200; // 2小时

  // 登录
  const handleLogin = async () => {
    if (!username || !password) {
      message.error('请输入用户名和密码');
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post(getApiUrl('/auth/login'), {
        username,
        password
      });

      const { access_token, user: userData } = response.data;
      setToken(access_token);
      setUserInfo(userData);
      localStorage.setItem('advanced_payment_token', access_token);
      setCurrentStep(1);
      message.success(`欢迎 ${userData.username}！`);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  // 创建支付订单
  const handleCreateOrder = async () => {
    if (!token) {
      message.error('请先登录');
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post(
        getApiUrl('/payment/orders'),
        {
          package_type: 'free_trial',
          payment_method: 'wechat_native'
        },
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      setPaymentOrder(response.data);
      setCurrentStep(2);
      message.success('订单创建成功！');

      // 启动倒计时
      const expireTime = dayjs(response.data.expire_time);
      const timer = setInterval(() => {
        const remaining = Math.max(0, expireTime.diff(dayjs(), 'second'));
        setTimeRemaining(remaining);
        if (remaining === 0) {
          clearInterval(timer);
          message.warning('订单已过期');
        }
      }, 1000);

      return () => clearInterval(timer);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建订单失败');
    } finally {
      setLoading(false);
    }
  };

  // 模拟支付
  const handleSimulatePayment = async () => {
    if (!paymentOrder || !token) {
      message.error('订单信息丢失');
      return;
    }

    Modal.confirm({
      title: '确认支付',
      content: `确定要支付 ¥${PAYMENT_AMOUNT} 吗？`,
      okText: '确定支付',
      cancelText: '取消',
      onOk: async () => {
        try {
          setLoading(true);
          const response = await axios.post(
            getApiUrl(`/payment/mock/complete/${paymentOrder.out_trade_no}`),
            {},
            {
              headers: {
                Authorization: `Bearer ${token}`
              }
            }
          );

          if (response.data.success) {
            setCurrentStep(3);
            message.success('支付成功！');
          } else {
            message.error(response.data.message || '支付失败');
          }
        } catch (error: any) {
          message.error(error.response?.data?.message || '支付失败');
        } finally {
          setLoading(false);
        }
      }
    });
  };

  // 重新开始
  const handleRestart = () => {
    setPaymentOrder(null);
    setTimeRemaining(0);
    setCurrentStep(1);
  };

  // 退出登录
  const handleLogout = () => {
    setToken(null);
    setUserInfo(null);
    setCurrentStep(0);
    setUsername('testuser');
    setPassword('testuser');
    localStorage.removeItem('advanced_payment_token');
    message.success('已退出登录');
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // 渲染左侧用户信息面板
  const renderUserPanel = () => {
    if (!token || !userInfo) {
      return null;
    }

    return (
      <Sider
        theme="light"
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        width={280}
        style={{
          background: 'linear-gradient(180deg, #667eea 0%, #764ba2 100%)',
          color: 'white'
        }}
      >
        <div style={{ padding: '24px', color: 'white' }}>
          {!collapsed && (
            <>
              <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                <Avatar
                  size={80}
                  style={{
                    backgroundColor: '#1890ff',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                  icon={<UserOutlined />}
                />
              </div>

              <Card
                style={{
                  backgroundColor: 'rgba(255,255,255,0.1)',
                  border: 'none',
                  color: 'white'
                }}
              >
                <div style={{ marginBottom: '12px' }}>
                  <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px' }}>用户名</Text>
                  <div style={{ color: 'white', fontWeight: 'bold', marginTop: '4px' }}>
                    {userInfo.username}
                  </div>
                </div>

                <Divider style={{ borderColor: 'rgba(255,255,255,0.2)', margin: '12px 0' }} />

                <div style={{ marginBottom: '12px' }}>
                  <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px' }}>邮箱</Text>
                  <div style={{ color: 'white', marginTop: '4px', fontSize: '12px' }}>
                    {userInfo.email}
                  </div>
                </div>

                <Divider style={{ borderColor: 'rgba(255,255,255,0.2)', margin: '12px 0' }} />

                <div style={{ marginBottom: '12px' }}>
                  <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px' }}>会员等级</Text>
                  <div style={{ color: '#fff', fontWeight: 'bold', marginTop: '4px' }}>
                    <Badge color="#faad14" text={userInfo.membership_type || '免费版'} />
                  </div>
                </div>

                <Divider style={{ borderColor: 'rgba(255,255,255,0.2)', margin: '12px 0' }} />

                <div>
                  <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px' }}>剩余查询次数</Text>
                  <div style={{ color: '#fff', fontWeight: 'bold', marginTop: '4px', fontSize: '18px' }}>
                    {userInfo.queries_remaining}
                  </div>
                </div>
              </Card>

              <Button
                type="primary"
                block
                danger
                icon={<LogoutOutlined />}
                onClick={handleLogout}
                style={{ marginTop: '24px' }}
              >
                退出登录
              </Button>
            </>
          )}
        </div>
      </Sider>
    );
  };

  // 主内容区域
  const renderContent = () => {
    // Step 0: 登录
    if (currentStep === 0) {
      return (
        <div style={{ maxWidth: '500px', margin: '0 auto', paddingTop: '60px' }}>
          <Card
            title={<Title level={3}>🔐 用户登录</Title>}
            style={{ borderRadius: '12px', boxShadow: '0 10px 40px rgba(0,0,0,0.1)' }}
          >
            <Form layout="vertical" onFinish={handleLogin}>
              <Form.Item label="用户名">
                <Input
                  placeholder="输入用户名"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onPressEnter={handleLogin}
                  size="large"
                />
              </Form.Item>

              <Form.Item label="密码">
                <Input.Password
                  placeholder="输入密码"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onPressEnter={handleLogin}
                  size="large"
                />
              </Form.Item>

              <Alert
                message="测试账户"
                description="用户名: testuser | 密码: testuser"
                type="info"
                showIcon
                style={{ marginBottom: '16px' }}
              />

              <Button
                type="primary"
                size="large"
                block
                loading={loading}
                onClick={handleLogin}
              >
                登 录
              </Button>
            </Form>
          </Card>
        </div>
      );
    }

    // Step 1: 选择套餐
    if (currentStep === 1) {
      return (
        <div style={{ maxWidth: '700px', margin: '0 auto' }}>
          <Title level={3}>📦 选择支付套餐</Title>

          <Card
            hoverable
            style={{
              borderRadius: '12px',
              marginBottom: '24px',
              border: '2px solid #1890ff'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <Title level={4} style={{ marginBottom: '8px' }}>免费试用套餐</Title>
                <Text type="secondary">体验完整功能，享受7天有效期</Text>
                <div style={{ marginTop: '12px' }}>
                  <Text>✓ 10次查询机会</Text>
                  <br />
                  <Text>✓ 7天有效期</Text>
                  <br />
                  <Text>✓ 完整功能体验</Text>
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#1890ff', marginBottom: '12px' }}>
                  ¥{PAYMENT_AMOUNT.toFixed(2)}
                </div>
                <Button
                  type="primary"
                  size="large"
                  icon={<CreditCardOutlined />}
                  onClick={handleCreateOrder}
                  loading={loading}
                >
                  选择套餐
                </Button>
              </div>
            </div>
          </Card>

          <Alert
            message="提示"
            description="选择套餐后将生成支付二维码，您可以扫描二维码完成支付"
            type="info"
            showIcon
          />
        </div>
      );
    }

    // Step 2: 支付
    if (currentStep === 2 && paymentOrder) {
      return (
        <div style={{ maxWidth: '700px', margin: '0 auto' }}>
          <Title level={3}>💳 扫码支付</Title>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
            <Card>
              <Statistic
                title="订单号"
                value={paymentOrder.out_trade_no}
                valueStyle={{ fontSize: '14px' }}
                prefix={<HistoryOutlined />}
              />
            </Card>

            <Card>
              <Statistic
                title="支付金额"
                value={`¥${paymentOrder.amount}`}
                valueStyle={{ color: '#ff4d4f', fontSize: '20px' }}
                prefix={<DollarOutlined />}
              />
            </Card>
          </div>

          <Card
            style={{
              textAlign: 'center',
              marginBottom: '24px',
              borderRadius: '12px'
            }}
          >
            <Title level={5} style={{ marginBottom: '16px' }}>二维码已生成，请扫描支付</Title>
            <div style={{
              padding: '32px',
              background: '#f5f5f5',
              borderRadius: '8px',
              display: 'inline-block'
            }}>
              {paymentOrder.code_url ? (
                <QRCode value={paymentOrder.code_url} size={250} />
              ) : (
                <Spin />
              )}
            </div>

            <div style={{ marginTop: '24px' }}>
              <Progress
                type="circle"
                percent={(timeRemaining / ORDER_TIMEOUT) * 100}
                format={() => formatTime(timeRemaining)}
                width={120}
              />
              <Paragraph type="secondary" style={{ marginTop: '12px' }}>
                订单有效期剩余
              </Paragraph>
            </div>
          </Card>

          <Space style={{ width: '100%', justifyContent: 'center' }} size="large">
            <Button
              type="primary"
              size="large"
              icon={<ShoppingOutlined />}
              onClick={handleSimulatePayment}
              loading={loading}
            >
              模拟支付（开发测试）
            </Button>

            <Button size="large" onClick={() => setCurrentStep(1)}>
              返回选择
            </Button>
          </Space>
        </div>
      );
    }

    // Step 3: 成功
    if (currentStep === 3) {
      return (
        <div style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center', paddingTop: '40px' }}>
          <div style={{ fontSize: '80px', marginBottom: '24px' }}>
            ✨
          </div>

          <Title level={2}>支付成功！</Title>

          <Paragraph style={{ fontSize: '16px', color: '#666', marginBottom: '32px' }}>
            您的支付已完成，权限已自动激活
          </Paragraph>

          {paymentOrder && (
            <Card
              style={{
                marginBottom: '24px',
                borderRadius: '12px',
                background: '#fafafa'
              }}
            >
              <Statistic
                title="订单号"
                value={paymentOrder.out_trade_no}
                valueStyle={{ fontSize: '14px' }}
              />
              <Divider />
              <Statistic
                title="支付金额"
                value={`¥${paymentOrder.amount}`}
                valueStyle={{ color: '#52c41a' }}
              />
              <Divider />
              <Statistic
                title="套餐"
                value={paymentOrder.package_name}
                valueStyle={{ fontSize: '14px' }}
              />
            </Card>
          )}

          <Alert
            message="🎉 权限已激活"
            description="您现在可以使用该权限继续进行股票分析查询。"
            type="success"
            showIcon
            style={{ marginBottom: '24px' }}
          />

          <Space direction="vertical" style={{ width: '100%' }}>
            <Button
              type="primary"
              size="large"
              block
              onClick={handleRestart}
            >
              进行新的支付
            </Button>
          </Space>
        </div>
      );
    }
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      {/* 顶部导航 */}
      <Header
        style={{
          background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
        }}
      >
        <Title level={3} style={{ color: 'white', margin: 0 }}>
          💳 高级支付系统
        </Title>
        <Text style={{ color: 'rgba(255,255,255,0.8)' }}>
          完整的支付管理体验
        </Text>
      </Header>

      <Layout>
        {token && userInfo && renderUserPanel()}

        <Content style={{ padding: '24px' }}>
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  );
};

export default AdvancedPaymentPage;
