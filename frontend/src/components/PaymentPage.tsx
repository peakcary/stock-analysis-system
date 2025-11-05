import React, { useState, useEffect, useRef } from 'react';
import {
  Card, Button, Space, message, Modal, Row, Col, Statistic, Steps,
  Select, Empty, Spin, Divider, Tag, Alert, Typography, Progress,
  QRCode as AntQRCode
} from 'antd';
import {
  ShoppingCartOutlined, QrcodeOutlined, CheckCircleOutlined,
  ClockCircleOutlined, CloseCircleOutlined, ReloadOutlined,
  CreditCardOutlined, DollarOutlined, GiftOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { adminApiClient } from '../../../shared/admin-auth';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

// Type definitions
interface PaymentPackage {
  id: number;
  package_type: string;
  name: string;
  price: number;
  queries_count: number;
  validity_days: number;
  membership_type: string;
  description?: string;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

interface PaymentOrder {
  id: number;
  out_trade_no: string;
  package_type: string;
  package_name: string;
  amount: number;
  status: string;
  code_url: string;
  h5_url?: string;
  expire_time: string;
  created_at: string;
  paid_at?: string;
  transaction_id?: string;
}

interface OrderStatus {
  out_trade_no: string;
  status: string;
  paid_at?: string;
  transaction_id?: string;
}

const PaymentPage: React.FC = () => {
  const { user } = useAuth();
  const [packages, setPackages] = useState<PaymentPackage[]>([]);
  const [selectedPackageType, setSelectedPackageType] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [packagesLoading, setPackagesLoading] = useState(true);
  const [paymentOrder, setPaymentOrder] = useState<PaymentOrder | null>(null);
  const [orderStatus, setOrderStatus] = useState<OrderStatus | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [statusCheckInterval, setStatusCheckInterval] = useState<NodeJS.Timeout | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number>(0);
  const qrCodeRef = useRef<HTMLDivElement>(null);

  // Fetch available payment packages
  const fetchPackages = async () => {
    try {
      setPackagesLoading(true);
      const response = await adminApiClient.get('/api/v1/payment/packages');
      setPackages(response.data);
      if (response.data.length > 0) {
        setSelectedPackageType(response.data[0].package_type);
      }
    } catch (error: any) {
      console.error('获取支付套餐失败:', error);
      message.error(error.response?.data?.detail || '获取支付套餐失败');
    } finally {
      setPackagesLoading(false);
    }
  };

  useEffect(() => {
    fetchPackages();
  }, []);

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
    if (!paymentOrder || currentStep !== 1) {
      return;
    }

    const checkStatus = async () => {
      try {
        const response = await adminApiClient.get(
          `/api/v1/payment/orders/${paymentOrder.out_trade_no}/status`
        );
        setOrderStatus(response.data);

        if (response.data.status === 'PAID' || response.data.status === 'SUCCESS') {
          setCurrentStep(2);
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
  }, [paymentOrder, currentStep]);

  // Create payment order
  const handleCreateOrder = async () => {
    if (!selectedPackageType) {
      message.warning('请先选择支付套餐');
      return;
    }

    try {
      setLoading(true);
      setCurrentStep(1);

      const response = await adminApiClient.post('/api/v1/payment/orders', {
        package_type: selectedPackageType,
        payment_method: 'wechat_native'
      });

      setPaymentOrder(response.data);
      message.info('💳 支付订单已生成，请使用微信扫描二维码');
    } catch (error: any) {
      console.error('创建支付订单失败:', error);
      setCurrentStep(0);
      message.error(error.response?.data?.detail || '创建支付订单失败');
    } finally {
      setLoading(false);
    }
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
          await adminApiClient.post(
            `/api/v1/payment/orders/${paymentOrder.out_trade_no}/cancel`
          );
          message.success('订单已取消');
          setPaymentOrder(null);
          setOrderStatus(null);
          setCurrentStep(0);
          if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
            setStatusCheckInterval(null);
          }
        } catch (error: any) {
          message.error(error.response?.data?.detail || '取消订单失败');
        }
      }
    });
  };

  // Get selected package details
  const selectedPackage = packages.find(p => p.package_type === selectedPackageType);

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
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 32 }}>
        <Title level={2}>
          <CreditCardOutlined /> 支付套餐购买
        </Title>
        <Paragraph type="secondary">
          升级您的会员等级，解锁更多分析功能
        </Paragraph>
      </div>

      {/* User Info */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col span={12}>
            <Statistic
              title="当前用户"
              value={user?.username || '未登录'}
              prefix={<ShoppingCartOutlined />}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="当前会员等级"
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
              title: '选择套餐',
              description: '选择适合您的支付套餐'
            },
            {
              title: '扫码支付',
              description: '使用微信扫描二维码完成支付'
            },
            {
              title: '支付成功',
              description: '订单已完成，权限已激活'
            }
          ]}
        />
      </Card>

      {/* Step 1: Package Selection */}
      {currentStep === 0 && (
        <Card style={{ marginBottom: 24 }}>
          <Title level={4}>第1步：选择支付套餐</Title>
          <Divider />

          {packagesLoading ? (
            <Spin size="large" />
          ) : packages.length === 0 ? (
            <Empty description="暂无可用套餐" />
          ) : (
            <div>
              <Row gutter={16} style={{ marginBottom: 24 }}>
                {packages.map((pkg) => (
                  <Col key={pkg.id} span={24} sm={12} lg={6}>
                    <Card
                      hoverable
                      onClick={() => setSelectedPackageType(pkg.package_type)}
                      style={{
                        cursor: 'pointer',
                        border: selectedPackageType === pkg.package_type ? '2px solid #1890ff' : '1px solid #d9d9d9',
                        background: selectedPackageType === pkg.package_type ? '#f0f5ff' : 'white'
                      }}
                    >
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Title level={5}>{pkg.name}</Title>

                        <div>
                          <Text strong style={{ fontSize: '20px', color: '#ff4d4f' }}>
                            ¥{pkg.price}
                          </Text>
                        </div>

                        <Space wrap>
                          <Tag color="blue">{pkg.membership_type}</Tag>
                          {pkg.validity_days === 0 ? (
                            <Tag color="green">永久有效</Tag>
                          ) : (
                            <Tag color="orange">{pkg.validity_days}天有效期</Tag>
                          )}
                        </Space>

                        {pkg.queries_count > 999 ? (
                          <Text type="success">无限查询</Text>
                        ) : (
                          <Text>{pkg.queries_count} 次查询</Text>
                        )}

                        {pkg.description && (
                          <Paragraph ellipsis={{ rows: 2 }} style={{ fontSize: '12px', marginBottom: 0 }}>
                            {pkg.description}
                          </Paragraph>
                        )}

                        {selectedPackageType === pkg.package_type && (
                          <Text type="success">
                            <CheckCircleOutlined /> 已选择
                          </Text>
                        )}
                      </Space>
                    </Card>
                  </Col>
                ))}
              </Row>

              {selectedPackage && (
                <Alert
                  message="确认支付信息"
                  description={`您即将购买【${selectedPackage.name}】，金额为 ¥${selectedPackage.price}`}
                  type="info"
                  showIcon
                  style={{ marginBottom: 24 }}
                />
              )}

              <Space>
                <Button
                  type="primary"
                  size="large"
                  icon={<QrcodeOutlined />}
                  loading={loading}
                  onClick={handleCreateOrder}
                  disabled={!selectedPackageType}
                >
                  下一步：生成支付二维码
                </Button>
                <Button size="large" onClick={fetchPackages}>
                  <ReloadOutlined /> 刷新套餐列表
                </Button>
              </Space>
            </div>
          )}
        </Card>
      )}

      {/* Step 2: Payment QR Code */}
      {currentStep === 1 && paymentOrder && (
        <Card style={{ marginBottom: 24 }}>
          <Title level={4}>第2步：使用微信扫码支付</Title>
          <Divider />

          <Alert
            message={timeRemaining > 60 ? '⏳ 订单已生成' : '⚠️ 订单即将过期'}
            description={
              <>
                <div>订单号: {paymentOrder.out_trade_no}</div>
                <div>支付金额: <Text strong style={{ color: '#ff4d4f' }}>¥{paymentOrder.amount}</Text></div>
                <div>
                  有效期剩余: <Text strong>{formatTimeRemaining(timeRemaining)}</Text>
                </div>
              </>
            }
            type={timeRemaining > 300 ? 'success' : timeRemaining > 0 ? 'warning' : 'error'}
            showIcon
            style={{ marginBottom: 24 }}
          />

          <Progress
            percent={progressPercent}
            status={timeRemaining > 60 ? 'active' : 'exception'}
            style={{ marginBottom: 24 }}
          />

          {/* QR Code Display */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              marginBottom: 32,
              padding: '20px',
              background: '#fafafa',
              borderRadius: '8px'
            }}
          >
            {paymentOrder.code_url ? (
              <div ref={qrCodeRef} style={{ padding: '20px', background: 'white', borderRadius: '8px' }}>
                <AntQRCode
                  value={paymentOrder.code_url}
                  size={256}
                  level="H"
                  includeMargin={true}
                  errorLevel="H"
                />
                <div style={{ textAlign: 'center', marginTop: 16 }}>
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    使用微信扫描上方二维码
                  </Text>
                </div>
              </div>
            ) : (
              <Empty description="二维码生成中..." />
            )}
          </div>

          {/* Payment Instructions */}
          <Card type="inner" style={{ marginBottom: 24, background: '#f6ffed', borderColor: '#b7eb8f' }}>
            <Title level={5}>📋 支付步骤</Title>
            <ol style={{ marginBottom: 0 }}>
              <li>打开微信应用</li>
              <li>点击"扫一扫"</li>
              <li>扫描上方二维码</li>
              <li>确认金额并输入支付密码</li>
              <li>支付完成后，系统将自动更新状态</li>
            </ol>
          </Card>

          {/* Payment Status Check */}
          <Row gutter={16}>
            <Col span={24}>
              <Spin spinning={false}>
                <Card type="inner">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text>✅ 系统正在监听支付状态，完成支付后将自动更新</Text>
                    {orderStatus?.status && (
                      <div>
                        <Text strong>当前状态：</Text>
                        {orderStatus.status === 'PENDING' ? (
                          <Tag color="processing">等待支付中</Tag>
                        ) : (
                          <Tag color="success">支付成功</Tag>
                        )}
                      </div>
                    )}
                  </Space>
                </Card>
              </Spin>
            </Col>
          </Row>

          {/* Action Buttons */}
          <Divider />
          <Space>
            <Button
              type="primary"
              size="large"
              icon={<ReloadOutlined />}
              onClick={async () => {
                try {
                  const response = await adminApiClient.get(
                    `/api/v1/payment/orders/${paymentOrder.out_trade_no}/status`
                  );
                  setOrderStatus(response.data);
                  if (response.data.status === 'PAID' || response.data.status === 'SUCCESS') {
                    setCurrentStep(2);
                    message.success('✅ 支付成功！权限已激活');
                  } else {
                    message.info('支付状态已更新');
                  }
                } catch (error) {
                  message.error('查询支付状态失败');
                }
              }}
            >
              手动检查支付状态
            </Button>
            <Button danger onClick={handleCancelOrder}>
              取消订单
            </Button>
          </Space>
        </Card>
      )}

      {/* Step 3: Payment Success */}
      {currentStep === 2 && paymentOrder && (
        <Card style={{ marginBottom: 24 }}>
          <div style={{ textAlign: 'center', padding: '40px 20px' }}>
            <CheckCircleOutlined
              style={{
                fontSize: '64px',
                color: '#52c41a',
                marginBottom: '24px'
              }}
            />

            <Title level={2}>支付成功！</Title>

            <Card type="inner" style={{ marginBottom: 24, marginTop: 24, textAlign: 'left' }}>
              <Row gutter={16} style={{ marginBottom: 16 }}>
                <Col span={12}>
                  <Statistic
                    title="订单号"
                    value={paymentOrder.out_trade_no}
                    valueStyle={{ fontSize: '14px', wordBreak: 'break-all' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="支付金额"
                    value={`¥${paymentOrder.amount}`}
                    valueStyle={{ color: '#ff4d4f' }}
                  />
                </Col>
              </Row>
              <Row gutter={16} style={{ marginBottom: 16 }}>
                <Col span={12}>
                  <Statistic
                    title="支付套餐"
                    value={paymentOrder.package_name}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="支付时间"
                    value={paymentOrder.paid_at ? dayjs(paymentOrder.paid_at).format('YYYY-MM-DD HH:mm:ss') : '处理中'}
                  />
                </Col>
              </Row>
            </Card>

            <Alert
              message="权限已激活"
              description="您的会员权限已激活，可以继续使用系统的各项功能"
              type="success"
              showIcon
              style={{ marginBottom: 24 }}
            />

            <Space>
              <Button
                type="primary"
                size="large"
                onClick={() => {
                  setCurrentStep(0);
                  setPaymentOrder(null);
                  setOrderStatus(null);
                  setSelectedPackageType('');
                  window.location.href = '/';
                }}
              >
                返回首页
              </Button>
              <Button
                size="large"
                onClick={() => {
                  setCurrentStep(0);
                  setPaymentOrder(null);
                  setOrderStatus(null);
                }}
              >
                继续购买其他套餐
              </Button>
            </Space>
          </div>
        </Card>
      )}
    </div>
  );
};

export default PaymentPage;
