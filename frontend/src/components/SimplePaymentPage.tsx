import React, { useState } from 'react';
import {
  Card, Button, Space, message, Modal, Input, Row, Col, Statistic,
  Steps, Empty, Spin, Divider, Alert, Typography, Progress, Badge, QRCode
} from 'antd';
import {
  ShoppingCartOutlined, QrcodeOutlined, CheckCircleOutlined,
  DollarOutlined, LogoutOutlined
} from '@ant-design/icons';
import axios from 'axios';
import dayjs from 'dayjs';
import { getApiUrl } from '../../../shared/api.config';

const { Title, Text, Paragraph } = Typography;

interface PaymentOrder {
  out_trade_no: string;
  amount: number;
  code_url: string;
  expire_time: string;
}

const SimplePaymentPage: React.FC = () => {
  const [step, setStep] = useState(0); // 0: login, 1: create order, 2: qr code, 3: success
  const [username, setUsername] = useState('testuser');
  const [password, setPassword] = useState('testuser');
  const [token, setToken] = useState<string | null>(localStorage.getItem('simple_payment_token'));
  const [user, setUser] = useState<any>(localStorage.getItem('simple_payment_user') ? JSON.parse(localStorage.getItem('simple_payment_user')!) : null);
  const [loading, setLoading] = useState(false);
  const [paymentOrder, setPaymentOrder] = useState<PaymentOrder | null>(null);
  const [timeRemaining, setTimeRemaining] = useState(0);

  const PAYMENT_AMOUNT = 0.01;

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
      setUser(userData);
      localStorage.setItem('simple_payment_token', access_token);
      localStorage.setItem('simple_payment_user', JSON.stringify(userData));
      setStep(1);
      message.success(`欢迎 ${userData.username}！`);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  // 创建订单
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
      setStep(2);
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
      console.error('Create order error:', error);
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
      title: '模拟支付',
      content: `确定要模拟支付 ¥${PAYMENT_AMOUNT} 吗？（开发测试用）`,
      okText: '确定',
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
            setStep(3);
            message.success('✅ 支付成功！');
          } else {
            message.error(response.data.message || '支付失败');
          }
        } catch (error: any) {
          message.error(error.response?.data?.message || '支付失败');
          console.error('Payment error:', error);
        } finally {
          setLoading(false);
        }
      }
    });
  };

  // 取消订单
  const handleCancelOrder = () => {
    setPaymentOrder(null);
    setTimeRemaining(0);
    setStep(1);
    message.info('订单已取消');
  };

  // 退出登录
  const handleLogout = () => {
    setToken(null);
    setUser(null);
    setStep(0);
    setUsername('testuser');
    setPassword('testuser');
    localStorage.removeItem('simple_payment_token');
    localStorage.removeItem('simple_payment_user');
    message.success('已退出登录');
  };

  // 重新开始
  const handleRestart = () => {
    setPaymentOrder(null);
    setTimeRemaining(0);
    setStep(1);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', padding: '40px 20px' }}>
      <div style={{ maxWidth: '600px', margin: '0 auto' }}>
        {/* 顶部标题 */}
        <div style={{ textAlign: 'center', marginBottom: '40px', color: 'white' }}>
          <Title level={2} style={{ color: 'white', marginBottom: '8px' }}>
            💳 支付系统
          </Title>
          <Text style={{ color: 'rgba(255,255,255,0.8)' }}>
            完整的支付流程演示
          </Text>
        </div>

        {/* Step 0: 登录 */}
        {step === 0 && (
          <Card style={{ borderRadius: '12px', boxShadow: '0 10px 40px rgba(0,0,0,0.2)' }}>
            <div style={{ padding: '20px' }}>
              <Title level={3} style={{ textAlign: 'center', marginBottom: '30px' }}>
                用户登录
              </Title>

              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <div>
                  <Text strong>用户名：</Text>
                  <Input
                    placeholder="输入用户名"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    style={{ marginTop: '8px' }}
                    onPressEnter={handleLogin}
                  />
                </div>

                <div>
                  <Text strong>密码：</Text>
                  <Input.Password
                    placeholder="输入密码"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    style={{ marginTop: '8px' }}
                    onPressEnter={handleLogin}
                  />
                </div>

                <Alert
                  message="测试账户信息"
                  description="用户名: testuser | 密码: testuser"
                  type="info"
                  showIcon
                />

                <Button
                  type="primary"
                  size="large"
                  block
                  loading={loading}
                  onClick={handleLogin}
                  style={{
                    height: '48px',
                    fontSize: '16px',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    border: 'none'
                  }}
                >
                  登 录
                </Button>
              </Space>
            </div>
          </Card>
        )}

        {/* Step 1: 创建订单 */}
        {step === 1 && token && (
          <Card style={{ borderRadius: '12px', boxShadow: '0 10px 40px rgba(0,0,0,0.2)' }}>
            <div style={{ padding: '20px' }}>
              {/* 用户信息 */}
              <div style={{ marginBottom: '30px', padding: '16px', background: '#f5f5f5', borderRadius: '8px' }}>
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="当前用户"
                      value={user?.username}
                      valueStyle={{ fontSize: '18px' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="会员等级"
                      value={user?.membership_type || '免费版'}
                      valueStyle={{ fontSize: '18px', color: '#1890ff' }}
                    />
                  </Col>
                </Row>
              </div>

              <Divider />

              {/* 支付金额 */}
              <div style={{ textAlign: 'center', marginBottom: '30px' }}>
                <Text style={{ fontSize: '14px', color: '#666' }}>支付金额</Text>
                <div style={{ fontSize: '48px', color: '#ff4d4f', fontWeight: 'bold', margin: '10px 0' }}>
                  ¥{PAYMENT_AMOUNT.toFixed(2)}
                </div>
                <Text type="secondary">这是测试金额</Text>
              </div>

              <Divider />

              {/* 按钮 */}
              <Space direction="vertical" style={{ width: '100%' }}>
                <Button
                  type="primary"
                  size="large"
                  block
                  icon={<ShoppingCartOutlined />}
                  loading={loading}
                  onClick={handleCreateOrder}
                  style={{
                    height: '50px',
                    fontSize: '16px',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    border: 'none'
                  }}
                >
                  创建支付订单
                </Button>

                <Button
                  type="default"
                  size="large"
                  block
                  icon={<LogoutOutlined />}
                  onClick={handleLogout}
                >
                  退出登录
                </Button>
              </Space>
            </div>
          </Card>
        )}

        {/* Step 2: QR 码 */}
        {step === 2 && paymentOrder && (
          <Card style={{ borderRadius: '12px', boxShadow: '0 10px 40px rgba(0,0,0,0.2)' }}>
            <div style={{ padding: '20px' }}>
              <Title level={3} style={{ textAlign: 'center', marginBottom: '24px' }}>
                扫码支付
              </Title>

              {/* 订单信息 */}
              <Row gutter={16} style={{ marginBottom: '20px' }}>
                <Col span={12}>
                  <Statistic
                    title="订单号"
                    value={paymentOrder.out_trade_no}
                    valueStyle={{ fontSize: '14px' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="支付金额"
                    value={`¥${paymentOrder.amount.toFixed(2)}`}
                    valueStyle={{ color: '#ff4d4f' }}
                  />
                </Col>
              </Row>

              <Divider />

              {/* 倒计时 */}
              <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                <Badge
                  count={formatTime(timeRemaining)}
                  style={{
                    backgroundColor: timeRemaining > 300 ? '#52c41a' : '#ff4d4f',
                    padding: '4px 12px',
                    borderRadius: '20px',
                    fontSize: '18px',
                    fontWeight: 'bold'
                  }}
                />
                <Paragraph type="secondary" style={{ marginTop: 12 }}>
                  订单有效期剩余时间
                </Paragraph>
                <Progress
                  percent={(timeRemaining / 7200) * 100}
                  status={timeRemaining === 0 ? 'exception' : 'active'}
                  showInfo={false}
                />
              </div>

              <Divider />

              {/* QR 码 */}
              <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                <div style={{
                  padding: '24px',
                  background: '#fafafa',
                  borderRadius: '8px',
                  display: 'inline-block'
                }}>
                  {paymentOrder.code_url ? (
                    <QRCode value={paymentOrder.code_url} size={250} />
                  ) : (
                    <Empty description="QR 码生成中..." />
                  )}
                </div>
                <Paragraph type="secondary" style={{ marginTop: 16 }}>
                  请使用微信扫描二维码完成支付
                </Paragraph>
              </div>

              <Divider />

              {/* 按钮 */}
              <Space style={{ width: '100%', justifyContent: 'center' }} size="large">
                <Button
                  type="primary"
                  size="large"
                  icon={<DollarOutlined />}
                  loading={loading}
                  onClick={handleSimulatePayment}
                  style={{
                    height: '48px',
                    paddingLeft: '24px',
                    paddingRight: '24px',
                    background: '#52c41a',
                    border: 'none'
                  }}
                >
                  模拟支付（开发测试）
                </Button>

                <Button
                  type="default"
                  size="large"
                  onClick={handleCancelOrder}
                  disabled={loading}
                >
                  取消订单
                </Button>
              </Space>
            </div>
          </Card>
        )}

        {/* Step 3: 成功 */}
        {step === 3 && (
          <Card style={{ borderRadius: '12px', boxShadow: '0 10px 40px rgba(0,0,0,0.2)' }}>
            <div style={{ padding: '40px 20px', textAlign: 'center' }}>
              <div style={{ fontSize: '80px', color: '#52c41a', marginBottom: '20px' }}>
                ✅
              </div>

              <Title level={2} style={{ marginBottom: '10px' }}>
                支付成功！
              </Title>

              <Paragraph type="success" style={{ fontSize: '16px', marginBottom: '30px' }}>
                您的支付已完成，权限已自动激活
              </Paragraph>

              <Divider />

              {/* 订单详情 */}
              {paymentOrder && (
                <Row gutter={16} style={{ marginBottom: '30px' }}>
                  <Col span={12}>
                    <Statistic
                      title="订单号"
                      value={paymentOrder.out_trade_no}
                      valueStyle={{ fontSize: '14px' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="支付金额"
                      value={`¥${paymentOrder.amount.toFixed(2)}`}
                      valueStyle={{ color: '#ff4d4f' }}
                    />
                  </Col>
                </Row>
              )}

              <Alert
                message="权限已激活"
                description="您现在可以使用该权限继续进行股票分析查询。"
                type="success"
                showIcon
                style={{ marginBottom: '30px' }}
              />

              {/* 按钮 */}
              <Space direction="vertical" style={{ width: '100%' }}>
                <Button
                  type="primary"
                  size="large"
                  block
                  onClick={handleRestart}
                  style={{
                    height: '48px',
                    fontSize: '16px',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    border: 'none'
                  }}
                >
                  进行新的支付
                </Button>

                <Button
                  type="default"
                  size="large"
                  block
                  onClick={handleLogout}
                >
                  退出登录
                </Button>
              </Space>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};

export default SimplePaymentPage;
