import React, { useState, useEffect } from 'react';
import {
  Modal,
  Card,
  Button,
  message,
  Spin,
  Typography,
  Space,
  Divider,
  QRCode,
  Alert,
  Tag,
  Row,
  Col,
  Tabs,
  Statistic
} from 'antd';
import {
  WechatOutlined,
  MobileOutlined,
  QrcodeOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

interface PaymentPackage {
  id: number;
  package_type: string;
  name: string;
  price: number;
  queries_count: number;
  validity_days: number;
  description: string;
}

interface PaymentOrder {
  order_id: number;
  out_trade_no: string;
  code_url?: string;
  h5_url?: string;
  expire_time: string;
  amount: number;
  mock_mode?: boolean;
}

interface EnhancedPaymentModalProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: () => void;
  selectedPackage: PaymentPackage | null;
}

const EnhancedPaymentModal: React.FC<EnhancedPaymentModalProps> = ({
  visible,
  onCancel,
  onSuccess,
  selectedPackage,
}) => {
  const [loading, setLoading] = useState(false);
  const [paymentOrder, setPaymentOrder] = useState<PaymentOrder | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<'wechat_native' | 'wechat_h5'>('wechat_native');
  const [orderStatus, setOrderStatus] = useState<'pending' | 'paid' | 'expired' | 'cancelled'>('pending');
  const [pollingInterval, setPollingInterval] = useState<number | null>(null);

  // 清理定时器
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  // 重置状态
  useEffect(() => {
    if (!visible) {
      setPaymentOrder(null);
      setOrderStatus('pending');
      if (pollingInterval) {
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }
    }
  }, [visible, pollingInterval]);

  // 创建支付订单
  const createPaymentOrder = async (method: 'wechat_native' | 'wechat_h5') => {
    if (!selectedPackage) return;

    setLoading(true);
    try {
      const response = await fetch('/api/v1/payment/v2/orders/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          package_type: selectedPackage.package_type,
          payment_method: method,
        }),
      });

      const result = await response.json();

      if (result.success) {
        setPaymentOrder(result.data);
        setPaymentMethod(method);
        startPolling(result.data.out_trade_no);
      } else {
        message.error(result.message || '创建订单失败');
      }
    } catch (error) {
      console.error('创建订单失败:', error);
      message.error('创建订单失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 开始轮询订单状态
  const startPolling = (outTradeNo: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/v1/payment/v2/orders/${outTradeNo}/status`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        });

        const result = await response.json();

        if (result.success) {
          if (result.data.status === 'paid') {
            setOrderStatus('paid');
            clearInterval(interval);
            message.success('支付成功！');
            setTimeout(() => {
              onSuccess();
            }, 2000);
          } else if (result.data.status === 'expired') {
            setOrderStatus('expired');
            clearInterval(interval);
          } else if (result.data.status === 'cancelled') {
            setOrderStatus('cancelled');
            clearInterval(interval);
          }
        }
      } catch (error) {
        console.error('查询订单状态失败:', error);
      }
    }, 3000); // 每3秒查询一次

    setPollingInterval(interval);

    // 15分钟后停止轮询
    setTimeout(() => {
      clearInterval(interval);
      if (orderStatus === 'pending') {
        setOrderStatus('expired');
      }
    }, 15 * 60 * 1000);
  };

  // 取消订单
  const cancelOrder = async () => {
    if (!paymentOrder) return;

    try {
      const response = await fetch(`/api/v1/payment/v2/orders/${paymentOrder.out_trade_no}/cancel`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      const result = await response.json();

      if (result.success) {
        setOrderStatus('cancelled');
        message.info('订单已取消');
        if (pollingInterval) {
          clearInterval(pollingInterval);
        }
      }
    } catch (error) {
      console.error('取消订单失败:', error);
      message.error('取消订单失败');
    }
  };

  // 模拟支付成功 (仅开发模式)
  const simulatePaymentSuccess = async () => {
    if (!paymentOrder || !paymentOrder.mock_mode) return;

    try {
      const response = await fetch(`/api/v1/payment/mock/complete/${paymentOrder.out_trade_no}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      const result = await response.json();

      if (result.success) {
        setOrderStatus('paid');
        message.success('模拟支付成功！');
        setTimeout(() => {
          onSuccess();
        }, 2000);
      }
    } catch (error) {
      console.error('模拟支付失败:', error);
      message.error('模拟支付失败');
    }
  };

  // 获取过期时间倒计时
  const getCountdownDeadline = () => {
    if (!paymentOrder) return Date.now();
    return new Date(paymentOrder.expire_time).getTime();
  };

  // 渲染支付方式选择
  const renderPaymentMethodSelection = () => (
    <Card>
      <Title level={4}>选择支付方式</Title>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card
          hoverable
          onClick={() => createPaymentOrder('wechat_native')}
          style={{
            border: paymentMethod === 'wechat_native' ? '2px solid #1890ff' : '1px solid #d9d9d9'
          }}
        >
          <Row align="middle">
            <Col span={4}>
              <QrcodeOutlined style={{ fontSize: 32, color: '#1890ff' }} />
            </Col>
            <Col span={20}>
              <Title level={5} style={{ margin: 0 }}>微信扫码支付</Title>
              <Text type="secondary">使用微信扫描二维码完成支付</Text>
            </Col>
          </Row>
        </Card>

        <Card
          hoverable
          onClick={() => createPaymentOrder('wechat_h5')}
          style={{
            border: paymentMethod === 'wechat_h5' ? '2px solid #1890ff' : '1px solid #d9d9d9'
          }}
        >
          <Row align="middle">
            <Col span={4}>
              <MobileOutlined style={{ fontSize: 32, color: '#52c41a' }} />
            </Col>
            <Col span={20}>
              <Title level={5} style={{ margin: 0 }}>微信H5支付</Title>
              <Text type="secondary">跳转到微信支付页面完成支付</Text>
            </Col>
          </Row>
        </Card>
      </Space>
    </Card>
  );

  // 渲染二维码支付
  const renderQRCodePayment = () => (
    <Card>
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <div style={{ textAlign: 'center' }}>
            {paymentOrder?.code_url ? (
              <QRCode value={paymentOrder.code_url} size={200} />
            ) : (
              <div style={{
                width: 200,
                height: 200,
                border: '1px dashed #d9d9d9',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto'
              }}>
                <Text type="secondary">生成二维码中...</Text>
              </div>
            )}

            <div style={{ marginTop: 16 }}>
              <Text strong>使用微信扫描二维码支付</Text>
            </div>
          </div>
        </Col>

        <Col span={12}>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <div>
              <Text strong>支付信息</Text>
              <div style={{ marginTop: 8 }}>
                <Text>订单金额：</Text>
                <Text strong style={{ color: '#ff4d4f', fontSize: 18 }}>
                  ¥{paymentOrder?.amount}
                </Text>
              </div>
            </div>

            <div>
              <Text>剩余时间：</Text>
              <Statistic.Countdown
                value={getCountdownDeadline()}
                format="mm:ss"
                onFinish={() => setOrderStatus('expired')}
                prefix={<ClockCircleOutlined />}
              />
            </div>

            <Alert
              message="支付提示"
              description="请在规定时间内完成支付，超时后订单将自动取消"
              type="info"
              showIcon
            />

            {paymentOrder?.mock_mode && (
              <Alert
                message="开发模式"
                description={
                  <Space direction="vertical">
                    <Text>当前为开发模式，可以模拟支付成功</Text>
                    <Button
                      type="primary"
                      size="small"
                      onClick={simulatePaymentSuccess}
                    >
                      模拟支付成功
                    </Button>
                  </Space>
                }
                type="warning"
                showIcon
              />
            )}
          </Space>
        </Col>
      </Row>
    </Card>
  );

  // 渲染H5支付
  const renderH5Payment = () => (
    <Card style={{ textAlign: 'center' }}>
      <WechatOutlined style={{ fontSize: 64, color: '#1890ff', marginBottom: 16 }} />
      <Title level={4}>微信支付</Title>
      <Paragraph>
        点击下方按钮跳转到微信支付页面完成支付
      </Paragraph>

      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Button
          type="primary"
          size="large"
          icon={<WechatOutlined />}
          onClick={() => {
            if (paymentOrder?.h5_url) {
              window.open(paymentOrder.h5_url, '_blank');
            }
          }}
          disabled={!paymentOrder?.h5_url}
        >
          前往微信支付
        </Button>

        <div>
          <Text>支付金额：</Text>
          <Text strong style={{ color: '#ff4d4f', fontSize: 18 }}>
            ¥{paymentOrder?.amount}
          </Text>
        </div>

        <div>
          <Text>剩余时间：</Text>
          <Statistic.Countdown
            value={getCountdownDeadline()}
            format="mm:ss"
            onFinish={() => setOrderStatus('expired')}
            prefix={<ClockCircleOutlined />}
          />
        </div>

        <Alert
          message="支付完成后，页面将自动更新会员状态"
          type="info"
          showIcon
        />
      </Space>
    </Card>
  );

  // 渲染支付状态
  const renderPaymentStatus = () => {
    switch (orderStatus) {
      case 'paid':
        return (
          <Card style={{ textAlign: 'center' }}>
            <CheckCircleOutlined style={{ fontSize: 64, color: '#52c41a', marginBottom: 16 }} />
            <Title level={3} style={{ color: '#52c41a' }}>支付成功！</Title>
            <Paragraph>
              恭喜您成功升级到 <Tag color="blue">{selectedPackage?.name}</Tag>
            </Paragraph>
            <Button type="primary" onClick={onSuccess}>
              确认
            </Button>
          </Card>
        );

      case 'expired':
        return (
          <Card style={{ textAlign: 'center' }}>
            <ClockCircleOutlined style={{ fontSize: 64, color: '#faad14', marginBottom: 16 }} />
            <Title level={3} style={{ color: '#faad14' }}>支付超时</Title>
            <Paragraph>
              订单已过期，请重新发起支付
            </Paragraph>
            <Button type="primary" onClick={() => setPaymentOrder(null)}>
              重新支付
            </Button>
          </Card>
        );

      case 'cancelled':
        return (
          <Card style={{ textAlign: 'center' }}>
            <CloseCircleOutlined style={{ fontSize: 64, color: '#ff4d4f', marginBottom: 16 }} />
            <Title level={3} style={{ color: '#ff4d4f' }}>支付已取消</Title>
            <Paragraph>
              您已取消此次支付
            </Paragraph>
            <Button type="primary" onClick={() => setPaymentOrder(null)}>
              重新支付
            </Button>
          </Card>
        );

      default:
        return null;
    }
  };

  return (
    <Modal
      title="会员升级"
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={800}
      destroyOnClose
    >
      <Spin spinning={loading}>
        {selectedPackage && (
          <Card style={{ marginBottom: 16 }}>
            <Row>
              <Col span={18}>
                <Title level={4} style={{ margin: 0 }}>
                  {selectedPackage.name}
                </Title>
                <Paragraph type="secondary" style={{ margin: '8px 0' }}>
                  {selectedPackage.description}
                </Paragraph>
                <Space>
                  <Tag color="blue">{selectedPackage.queries_count} 次查询</Tag>
                  <Tag color="green">{selectedPackage.validity_days} 天有效期</Tag>
                </Space>
              </Col>
              <Col span={6} style={{ textAlign: 'right' }}>
                <Title level={2} style={{ margin: 0, color: '#ff4d4f' }}>
                  ¥{selectedPackage.price}
                </Title>
              </Col>
            </Row>
          </Card>
        )}

        {orderStatus !== 'pending' ? (
          renderPaymentStatus()
        ) : !paymentOrder ? (
          renderPaymentMethodSelection()
        ) : (
          <div>
            {paymentMethod === 'wechat_native' ? renderQRCodePayment() : renderH5Payment()}

            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <Space>
                <Button onClick={cancelOrder}>取消支付</Button>
                <Button onClick={() => setPaymentOrder(null)}>返回</Button>
              </Space>
            </div>
          </div>
        )}
      </Spin>
    </Modal>
  );
};

export default EnhancedPaymentModal;