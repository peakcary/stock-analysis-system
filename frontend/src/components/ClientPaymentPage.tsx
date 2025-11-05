import React, { useState, useEffect } from 'react';
import {
  Card, Button, Space, message, Modal, Row, Col, Statistic, Steps,
  Empty, Spin, Divider, Alert, Typography, Progress, Badge, QRCode
} from 'antd';
import {
  ShoppingCartOutlined, QrcodeOutlined, CheckCircleOutlined,
  ClockCircleOutlined, CloseCircleOutlined, ReloadOutlined,
  CreditCardOutlined, DollarOutlined
} from '@ant-design/icons';
import { useClientAuth } from '../contexts/ClientAuthContext';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;

// Type definitions
interface PaymentOrder {
  id: number;
  out_trade_no: string;
  amount: number;
  status: string;
  code_url: string;
  expire_time: string;
  created_at: string;
  paid_at?: string;
  transaction_id?: string;
}

interface OrderStatusResponse {
  order_status: {
    out_trade_no: string;
    status: string;
    paid_at?: string;
    transaction_id?: string;
  };
}

const ClientPaymentPage: React.FC = () => {
  const { user, apiClient } = useClientAuth();
  const [loading, setLoading] = useState(false);
  const [paymentOrder, setPaymentOrder] = useState<PaymentOrder | null>(null);
  const [orderStatus, setOrderStatus] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [statusCheckInterval, setStatusCheckInterval] = useState<NodeJS.Timeout | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number>(0);
  const [paidAt, setPaidAt] = useState<string | null>(null);

  // Fixed test amount: 0.01 yuan
  const PAYMENT_AMOUNT = 0.01;

  // Handle timer for order expiration
  useEffect(() => {
    if (paymentOrder && currentStep === 1) {
      const expireTime = dayjs(paymentOrder.expire_time);
      const updateTimer = () => {
        const remaining = expireTime.diff(dayjs(), 'second');
        setTimeRemaining(Math.max(0, remaining));
      };

      updateTimer();
      const timer = setInterval(updateTimer, 1000);

      return () => clearInterval(timer);
    }
  }, [paymentOrder, currentStep]);

  // Check payment status periodically
  useEffect(() => {
    if (!paymentOrder || currentStep !== 1 || !apiClient) {
      return;
    }

    const checkStatus = async () => {
      try {
        const response = await apiClient.get(
          `/api/v1/payment/orders/${paymentOrder.out_trade_no}/status`
        );
        const status = response.data.status;
        setOrderStatus(status);

        if (status === 'paid' || status === 'success') {
          setCurrentStep(2);
          setPaidAt(response.data.paid_at || null);
          message.success('✅ 支付成功！权限已激活');
          if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
            setStatusCheckInterval(null);
          }
        }
      } catch (error) {
        console.error('查询支付状态失败:', error);
      }
    };

    // Check immediately, then every 3 seconds
    checkStatus();
    const interval = setInterval(checkStatus, 3000);
    setStatusCheckInterval(interval);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [paymentOrder, currentStep, apiClient]);

  // Create payment order
  const handleCreateOrder = async () => {
    if (!apiClient) {
      message.error('API客户端未初始化');
      return;
    }

    try {
      setLoading(true);
      setCurrentStep(1);

      const response = await apiClient.post<PaymentOrder>('/payment/orders', {
        package_type: 'free_trial',
        payment_method: 'wechat_native'
      });

      setPaymentOrder(response.data);
      message.info('💳 支付订单已生成，请使用微信扫描二维码');
    } catch (error: any) {
      console.error('创建支付订单失败:', error);
      setCurrentStep(0);
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || '创建支付订单失败';
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // Simulate payment (for testing)
  const handleSimulatePayment = async () => {
    if (!paymentOrder || !apiClient) {
      message.error('订单信息丢失');
      return;
    }

    Modal.confirm({
      title: '模拟支付',
      content: `确定要模拟支付 ¥${PAYMENT_AMOUNT} 吗？（开发测试用）`,
      okText: '确定支付',
      cancelText: '取消',
      onOk: async () => {
        try {
          setLoading(true);
          await apiClient.post(
            `/api/v1/payment/mock/complete/${paymentOrder.out_trade_no}`
          );
          message.success('模拟支付成功');
          // Status check will automatically update via polling
        } catch (error: any) {
          message.error(error.response?.data?.detail || '模拟支付失败');
        } finally {
          setLoading(false);
        }
      }
    });
  };

  // Cancel payment order
  const handleCancelOrder = async () => {
    if (!paymentOrder) return;

    Modal.confirm({
      title: '取消订单',
      content: '确定要取消此支付订单吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          setPaymentOrder(null);
          setOrderStatus(null);
          setCurrentStep(0);
          setPaidAt(null);
          if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
            setStatusCheckInterval(null);
          }
          message.success('订单已取消');
        } catch (error: any) {
          message.error(error.response?.data?.detail || '取消订单失败');
        }
      }
    });
  };

  // Format time remaining
  const formatTimeRemaining = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  // Calculate progress percentage for timer
  const totalTime = 120 * 60; // 2 hours in seconds
  const progressPercent = ((totalTime - timeRemaining) / totalTime) * 100;

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ marginBottom: 32 }}>
        <Title level={2}>
          <CreditCardOutlined /> 支付测试
        </Title>
        <Paragraph type="secondary">
          体验支付功能 - 使用0.01元进行测试支付
        </Paragraph>
      </div>

      {/* Alert for test payment */}
      <Alert
        message="测试支付"
        description="这是一个支付流程测试。测试金额设为¥0.01。您可以使用微信扫描二维码进行支付，或点击下方按钮模拟支付进度。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* User Info */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col xs={24} sm={12}>
            <Statistic
              title="当前用户"
              value={user?.username || '未登录'}
              prefix={<ShoppingCartOutlined />}
            />
          </Col>
          <Col xs={24} sm={12}>
            <Statistic
              title="会员等级"
              value={user?.membership_type || '免费版'}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
        </Row>
      </Card>

      {/* Payment Steps */}
      <Card style={{ marginBottom: 24 }}>
        <Steps
          current={currentStep}
          items={[
            {
              title: '创建订单',
              icon: <ShoppingCartOutlined />,
              description: '生成支付订单'
            },
            {
              title: '扫码支付',
              icon: <QrcodeOutlined />,
              description: '等待支付完成'
            },
            {
              title: '支付成功',
              icon: <CheckCircleOutlined />,
              description: '权限已激活'
            }
          ]}
        />
      </Card>

      {/* Step 0: Order Creation */}
      {currentStep === 0 && (
        <Card style={{ marginBottom: 24 }}>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div>
              <Text strong>支付金额：</Text>
              <Text style={{ fontSize: '24px', color: '#ff4d4f', marginLeft: '8px' }}>
                ¥{PAYMENT_AMOUNT.toFixed(2)}
              </Text>
            </div>

            <div>
              <Text type="secondary">
                点击下方按钮创建支付订单，然后您可以使用微信扫描二维码进行支付。
              </Text>
            </div>

            <Button
              type="primary"
              size="large"
              icon={<ShoppingCartOutlined />}
              onClick={handleCreateOrder}
              loading={loading}
              style={{
                height: '48px',
                fontSize: '16px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                border: 'none'
              }}
            >
              创建支付订单
            </Button>
          </Space>
        </Card>
      )}

      {/* Step 1: QR Code Payment */}
      {currentStep === 1 && paymentOrder && (
        <Card style={{ marginBottom: 24 }}>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            {/* Order Info */}
            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Statistic
                  title="订单号"
                  value={paymentOrder.out_trade_no}
                  valueStyle={{ fontSize: '14px' }}
                />
              </Col>
              <Col xs={24} sm={12}>
                <Statistic
                  title="支付金额"
                  value={`¥${paymentOrder.amount.toFixed(2)}`}
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Col>
            </Row>

            <Divider />

            {/* Time Remaining */}
            <div style={{ textAlign: 'center' }}>
              <Badge
                count={formatTimeRemaining(timeRemaining)}
                style={{
                  backgroundColor: timeRemaining > 300 ? '#52c41a' : '#ff4d4f',
                  padding: '4px 12px',
                  borderRadius: '20px',
                  fontSize: '16px',
                  fontWeight: 'bold'
                }}
              />
              <Paragraph type="secondary" style={{ marginTop: 8 }}>
                订单有效期剩余时间
              </Paragraph>
              <Progress
                percent={progressPercent}
                status={timeRemaining === 0 ? 'exception' : 'active'}
                showInfo={false}
              />
            </div>

            <Divider />

            {/* QR Code */}
            <div style={{ textAlign: 'center' }}>
              {paymentOrder.code_url ? (
                <div style={{
                  padding: '24px',
                  background: '#fafafa',
                  borderRadius: '8px',
                  display: 'inline-block'
                }}>
                  <QRCode value={paymentOrder.code_url} size={250} />
                </div>
              ) : (
                <Empty description="QR Code 生成中..." />
              )}
              <Paragraph type="secondary" style={{ marginTop: 16 }}>
                请使用微信扫描二维码完成支付
              </Paragraph>
            </div>

            <Divider />

            {/* Payment Status */}
            {orderStatus && (
              <Alert
                message="支付状态"
                description={`当前状态: ${orderStatus}`}
                type={orderStatus === 'PENDING' ? 'warning' : 'info'}
                showIcon
              />
            )}

            {/* Test Mode: Simulate Payment Button */}
            <Alert
              message="开发测试模式"
              description="在测试环境中，您可以点击下方按钮模拟支付过程。"
              type="warning"
              showIcon
            />

            {/* Action Buttons */}
            <Space style={{ width: '100%', justifyContent: 'center' }}>
              <Button
                type="primary"
                size="large"
                icon={<DollarOutlined />}
                onClick={handleSimulatePayment}
                loading={loading}
                style={{
                  height: '48px',
                  fontSize: '16px',
                  background: '#52c41a',
                  border: 'none'
                }}
              >
                模拟支付（开发测试）
              </Button>

              <Button
                type="default"
                size="large"
                icon={<CloseCircleOutlined />}
                onClick={handleCancelOrder}
                disabled={loading}
              >
                取消订单
              </Button>
            </Space>
          </Space>
        </Card>
      )}

      {/* Step 2: Payment Success */}
      {currentStep === 2 && paymentOrder && (
        <Card style={{ marginBottom: 24 }}>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div style={{ textAlign: 'center' }}>
              <div style={{
                fontSize: '64px',
                color: '#52c41a',
                marginBottom: '16px'
              }}>
                <CheckCircleOutlined />
              </div>
              <Title level={3}>支付成功！</Title>
              <Paragraph type="success">
                您的支付已完成，权限已自动激活
              </Paragraph>
            </div>

            <Divider />

            {/* Order Summary */}
            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Statistic
                  title="订单号"
                  value={paymentOrder.out_trade_no}
                  valueStyle={{ fontSize: '14px' }}
                />
              </Col>
              <Col xs={24} sm={12}>
                <Statistic
                  title="支付金额"
                  value={`¥${paymentOrder.amount.toFixed(2)}`}
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Col>
            </Row>

            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Statistic
                  title="支付时间"
                  value={paidAt ? dayjs(paidAt).format('YYYY-MM-DD HH:mm:ss') : '即刻'}
                />
              </Col>
              <Col xs={24} sm={12}>
                <Statistic
                  title="支付状态"
                  value="已完成"
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
            </Row>

            <Divider />

            {/* Success Alert */}
            <Alert
              message="权限已激活"
              description="您现在可以使用该权限继续进行股票分析查询。"
              type="success"
              showIcon
            />

            {/* Action Buttons */}
            <Space style={{ width: '100%', justifyContent: 'center' }}>
              <Button
                type="primary"
                size="large"
                onClick={() => {
                  setCurrentStep(0);
                  setPaymentOrder(null);
                  setOrderStatus(null);
                  setPaidAt(null);
                }}
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
                onClick={() => window.history.back()}
              >
                返回上一页
              </Button>
            </Space>
          </Space>
        </Card>
      )}
    </div>
  );
};

export default ClientPaymentPage;
