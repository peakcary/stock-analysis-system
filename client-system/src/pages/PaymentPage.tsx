import React, { useState, useEffect } from 'react';
import { Card, Steps, Button, Form, Select, Table, Spin, message, Tag, Space, QRCode } from 'antd';
import { CheckOutlined, CopyOutlined, ReloadOutlined } from '@ant-design/icons';
import api from '../utils/api';

interface UserInfo {
  id: number;
  username: string;
  email: string;
  membership_type: string;
  queries_remaining: number;
  queries_count: number;
  created_at: string;
}

interface PaymentPageProps {
  userInfo: UserInfo | null;
}

interface Package {
  id: number;
  package_type: string;
  name: string;
  description: string;
  price: number;
  queries: number;
}

interface PaymentOrder {
  id: number;
  order_no: string;
  package_id: number;
  total_price: number;
  status: string;
  qr_code: string;
  payment_url: string;
  transaction_id: string;
  created_at: string;
  paid_at: string;
}

const PaymentPage: React.FC<PaymentPageProps> = () => {
  const [step, setStep] = useState(0);
  const [form] = Form.useForm();
  const [packages, setPackages] = useState<Package[]>([]);
  const [selectedPackage, setSelectedPackage] = useState<Package | null>(null);
  const [paymentOrder, setPaymentOrder] = useState<PaymentOrder | null>(null);
  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false);
  const [countDown, setCountDown] = useState(180);

  // 获取套餐列表
  useEffect(() => {
    const fetchPackages = async () => {
      try {
        setLoading(true);
        const response = await api.get('/payment/packages');
        setPackages(response.data);
      } catch (error) {
        message.error('获取套餐列表失败');
      } finally {
        setLoading(false);
      }
    };
    fetchPackages();
  }, []);

  // 创建支付订单
  const handleCreateOrder = async (values: any) => {
    try {
      setLoading(true);
      const response = await api.post('/payment/orders', {
        package_type: values.package,
        payment_method: 'wechat_native',
      });

      setPaymentOrder(response.data);
      setSelectedPackage(packages.find(p => p.id === values.package) || null);
      setStep(2);
      setPolling(true);
      setCountDown(180);
      message.success('支付订单创建成功，请扫描二维码支付');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建支付订单失败');
    } finally {
      setLoading(false);
    }
  };

  // 轮询检查支付状态
  useEffect(() => {
    if (!polling || !paymentOrder) return;

    const interval = setInterval(async () => {
      try {
        const response = await api.get(`/payment/orders/${paymentOrder.id}`);
        if (response.data.status === 'paid') {
          setPolling(false);
          setStep(3);
          message.success('支付成功！');
        }
      } catch (error) {
        console.error('检查支付状态失败:', error);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [polling, paymentOrder]);

  // 倒计时
  useEffect(() => {
    if (!polling) return;

    const timer = setInterval(() => {
      setCountDown(prev => {
        if (prev <= 1) {
          setPolling(false);
          message.warning('支付超时，请重新创建订单');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [polling]);

  // 模拟支付
  const handleMockPayment = async () => {
    if (!paymentOrder) return;

    try {
      setLoading(true);
      const response = await api.post(`/payment/orders/${paymentOrder.id}/notify`, {
        transaction_id: `MOCK_${paymentOrder.order_no}`,
      });

      if (response.data.notify_processed) {
        setPolling(false);
        setStep(3);
        message.success('模拟支付成功！');
      } else {
        message.warning('支付处理中，请稍候');
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '模拟支付失败');
    } finally {
      setLoading(false);
    }
  };

  // 重新创建订单
  const handleRestart = () => {
    setStep(0);
    setPaymentOrder(null);
    setSelectedPackage(null);
    setPolling(false);
    form.resetFields();
  };

  // 复制订单号
  const handleCopyOrderNo = () => {
    if (paymentOrder?.order_no) {
      navigator.clipboard.writeText(paymentOrder.order_no);
      message.success('订单号已复制');
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card
        style={{
          maxWidth: '800px',
          margin: '0 auto',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        }}
        bodyStyle={{ padding: '32px' }}
      >
        {/* 步骤条 */}
        <Steps
          current={step}
          style={{ marginBottom: '32px' }}
          items={[
            { title: '选择套餐', description: '选择你需要的套餐' },
            { title: '确认信息', description: '确认订单信息' },
            { title: '支付订单', description: '扫码支付' },
            { title: '支付成功', description: '享受服务' },
          ]}
        />

        <Spin spinning={loading}>
          {/* Step 0: 选择套餐 */}
          {step === 0 && (
            <div style={{ padding: '24px 0' }}>
              <h3 style={{ marginBottom: '16px' }}>选择套餐</h3>
              <Form
                form={form}
                layout="vertical"
                onFinish={handleCreateOrder}
              >
                <Form.Item
                  name="package"
                  label="请选择套餐"
                  rules={[{ required: true, message: '请选择套餐' }]}
                >
                  <Select placeholder="选择套餐" style={{ borderRadius: '6px' }}>
                    {packages.map(pkg => (
                      <Select.Option key={pkg.id} value={pkg.id}>
                        {pkg.name} - {pkg.price === 0 ? '免费' : `¥${pkg.price}`} ({pkg.queries}次查询)
                      </Select.Option>
                    ))}
                  </Select>
                </Form.Item>

                <Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    block
                    size="large"
                    style={{
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      border: 'none',
                      borderRadius: '6px',
                    }}
                  >
                    创建支付订单
                  </Button>
                </Form.Item>
              </Form>

              {/* 套餐列表 */}
              <div style={{ marginTop: '32px' }}>
                <h4 style={{ marginBottom: '16px' }}>可用套餐</h4>
                <Table
                  dataSource={packages}
                  pagination={false}
                  size="small"
                  columns={[
                    {
                      title: '套餐名称',
                      dataIndex: 'name',
                      key: 'name',
                    },
                    {
                      title: '价格',
                      dataIndex: 'price',
                      key: 'price',
                      render: (price) => price === 0 ? '免费' : `¥${price}`,
                    },
                    {
                      title: '查询次数',
                      dataIndex: 'queries',
                      key: 'queries',
                    },
                    {
                      title: '描述',
                      dataIndex: 'description',
                      key: 'description',
                    },
                  ]}
                />
              </div>
            </div>
          )}

          {/* Step 2: 支付订单 */}
          {step === 2 && paymentOrder && (
            <div style={{ padding: '24px 0', textAlign: 'center' }}>
              <h3 style={{ marginBottom: '24px' }}>
                请扫描二维码完成支付
              </h3>

              {/* 订单信息 */}
              <Card
                style={{
                  marginBottom: '24px',
                  background: '#fafafa',
                  border: '1px solid #e8e8e8',
                }}
              >
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ color: '#999', fontSize: '12px' }}>订单号</div>
                  <div style={{ fontWeight: 'bold', fontSize: '16px' }}>
                    {paymentOrder.order_no}
                    <Button
                      type="text"
                      size="small"
                      icon={<CopyOutlined />}
                      onClick={handleCopyOrderNo}
                      style={{ marginLeft: '8px' }}
                    />
                  </div>
                </div>

                <div style={{ marginBottom: '16px' }}>
                  <div style={{ color: '#999', fontSize: '12px' }}>套餐</div>
                  <div style={{ fontWeight: 'bold', fontSize: '14px' }}>
                    {selectedPackage?.name}
                  </div>
                </div>

                <div>
                  <div style={{ color: '#999', fontSize: '12px' }}>应付金额</div>
                  <div style={{ fontWeight: 'bold', fontSize: '24px', color: '#ff4d4f' }}>
                    ¥{paymentOrder.total_price}
                  </div>
                </div>
              </Card>

              {/* 二维码 */}
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                marginBottom: '24px',
                padding: '20px',
                background: 'white',
                border: '1px solid #e8e8e8',
                borderRadius: '8px',
              }}>
                <QRCode
                  value={paymentOrder.qr_code || paymentOrder.payment_url || 'mock://payment'}
                  size={256}
                  level="H"
                />
              </div>

              {/* 倒计时 */}
              <div style={{ marginBottom: '24px', fontSize: '14px', color: '#faad14' }}>
                <ReloadOutlined spin /> 支付等待中... {Math.floor(countDown / 60)}:{String(countDown % 60).padStart(2, '0')}
              </div>

              {/* 按钮组 */}
              <Space>
                <Button
                  type="primary"
                  size="large"
                  loading={loading}
                  onClick={handleMockPayment}
                  style={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    border: 'none',
                    borderRadius: '6px',
                  }}
                >
                  模拟支付
                </Button>
                <Button
                  size="large"
                  onClick={handleRestart}
                >
                  返回选择
                </Button>
              </Space>
            </div>
          )}

          {/* Step 3: 支付成功 */}
          {step === 3 && (
            <div style={{ padding: '32px 0', textAlign: 'center' }}>
              <CheckOutlined
                style={{
                  fontSize: '64px',
                  color: '#52c41a',
                  marginBottom: '16px',
                }}
              />
              <h2 style={{ marginBottom: '8px' }}>支付成功！</h2>
              <p style={{ color: '#999', marginBottom: '24px' }}>
                感谢您的购买，祝您使用愉快
              </p>

              {/* 订单详情 */}
              <Card
                style={{
                  marginBottom: '24px',
                  background: '#fafafa',
                  border: '1px solid #e8e8e8',
                }}
              >
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ color: '#999', fontSize: '12px' }}>订单号</div>
                  <div style={{ fontWeight: 'bold' }}>{paymentOrder?.order_no}</div>
                </div>
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ color: '#999', fontSize: '12px' }}>套餐</div>
                  <div style={{ fontWeight: 'bold' }}>{selectedPackage?.name}</div>
                </div>
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ color: '#999', fontSize: '12px' }}>金额</div>
                  <div style={{ fontWeight: 'bold', color: '#ff4d4f' }}>
                    ¥{paymentOrder?.total_price}
                  </div>
                </div>
                <div>
                  <div style={{ color: '#999', fontSize: '12px' }}>状态</div>
                  <Tag color="green">
                    <CheckOutlined /> 已支付
                  </Tag>
                </div>
              </Card>

              <Button
                type="primary"
                size="large"
                onClick={handleRestart}
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none',
                  borderRadius: '6px',
                }}
              >
                继续购买
              </Button>
            </div>
          )}
        </Spin>
      </Card>
    </div>
  );
};

export default PaymentPage;
