import React, { useState, useEffect } from 'react';
import {
  Modal, Card, Row, Col, Button, QRCode, message, Spin, Typography,
  Space, Tag, Progress, Divider, Alert, Descriptions
} from 'antd';
import {
  WechatOutlined, ClockCircleOutlined, CheckCircleOutlined,
  CloseCircleOutlined, CopyOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { apiClient } from '../utils/auth';

const { Title, Text } = Typography;

interface PaymentPackage {
  id: number;
  package_type: string;
  name: string;
  price: number;
  queries_count: number;
  validity_days: number;
  membership_type: string;
  description: string;
}

interface PaymentOrder {
  id: number;
  out_trade_no: string;
  package_name: string;
  amount: number;
  status: string;
  payment_method: string;
  code_url?: string;
  h5_url?: string;
  expire_time: string;
  created_at: string;
}

interface PaymentModalProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: () => void;
  packageType: string;
}

const PaymentModal: React.FC<PaymentModalProps> = ({
  visible,
  onCancel,
  onSuccess,
  packageType
}) => {
  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false);
  const [orderData, setOrderData] = useState<PaymentOrder | null>(null);
  const [packageData, setPackageData] = useState<PaymentPackage | null>(null);
  const [countdown, setCountdown] = useState(0);
  const [paymentStatus, setPaymentStatus] = useState<'pending' | 'paid' | 'failed' | 'expired' | 'cancelled'>('pending');

  // 获取套餐信息
  const fetchPackageInfo = async () => {
    try {
      const response = await apiClient.get(`/api/v1/payment/packages/${packageType}`);
      setPackageData(response.data);
    } catch (error) {
      console.error('获取套餐信息失败:', error);
      message.error('获取套餐信息失败');
    }
  };

  // 创建支付订单
  const createPaymentOrder = async () => {
    setLoading(true);
    try {
      const response = await apiClient.post('/api/v1/payment/orders', {
        package_type: packageType,
        payment_method: 'wechat_native',
        client_ip: undefined,
        user_agent: navigator.userAgent
      });

      setOrderData(response.data);
      setPaymentStatus(response.data.status);
      
      // 计算倒计时
      const expireTime = dayjs(response.data.expire_time);
      const now = dayjs();
      setCountdown(expireTime.diff(now, 'second'));

      // 开始轮询支付状态
      startStatusPolling(response.data.out_trade_no);
      
      message.success('支付订单创建成功');
    } catch (error: any) {
      console.error('创建支付订单失败:', error);
      const errorMsg = error.response?.data?.detail || '创建支付订单失败';
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // 轮询支付状态
  const startStatusPolling = (outTradeNo: string) => {
    setPolling(true);
    
    const pollInterval = setInterval(async () => {
      try {
        const response = await apiClient.get(`/api/v1/payment/orders/${outTradeNo}/status`);
        const status = response.data.status;
        
        setPaymentStatus(status);
        
        if (status === 'paid') {
          clearInterval(pollInterval);
          setPolling(false);
          message.success('支付成功！');
          
          // 延迟关闭弹窗，让用户看到成功状态
          setTimeout(() => {
            onSuccess();
            onCancel();
          }, 2000);
        } else if (status === 'failed' || status === 'expired' || status === 'cancelled') {
          clearInterval(pollInterval);
          setPolling(false);
          message.error(getStatusText(status));
        }
      } catch (error) {
        console.error('查询支付状态失败:', error);
      }
    }, 3000);

    // 2分钟后停止轮询
    setTimeout(() => {
      clearInterval(pollInterval);
      setPolling(false);
    }, 120000);
  };

  // 倒计时
  useEffect(() => {
    if (countdown <= 0) return;
    
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          setPaymentStatus('expired');
          setPolling(false);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown]);

  // 获取状态文本
  const getStatusText = (status: string) => {
    const statusMap = {
      pending: '待支付',
      paid: '已支付',
      failed: '支付失败',
      expired: '订单过期',
      cancelled: '已取消'
    };
    return statusMap[status as keyof typeof statusMap] || status;
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    const colorMap = {
      pending: 'processing',
      paid: 'success',
      failed: 'error',
      expired: 'default',
      cancelled: 'default'
    };
    return colorMap[status as keyof typeof colorMap] || 'default';
  };

  // 格式化倒计时
  const formatCountdown = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  // 复制订单号
  const copyOrderNo = () => {
    if (orderData) {
      navigator.clipboard.writeText(orderData.out_trade_no);
      message.success('订单号已复制');
    }
  };

  // 取消订单
  const cancelOrder = async () => {
    if (!orderData) return;
    
    try {
      await apiClient.post(`/api/v1/payment/orders/${orderData.out_trade_no}/cancel`);
      setPaymentStatus('cancelled');
      setPolling(false);
      message.success('订单已取消');
      onCancel();
    } catch (error) {
      message.error('取消订单失败');
    }
  };

  // 模拟支付成功
  const simulatePayment = async () => {
    if (!orderData) return;
    
    try {
      setLoading(true);
      const response = await apiClient.post(`/api/v1/mock/simulate-payment/${orderData.out_trade_no}`);
      
      if (response.data.status === 'success') {
        setPaymentStatus('paid');
        setPolling(false);
        message.success('模拟支付成功！');
        
        // 延迟关闭弹窗
        setTimeout(() => {
          onSuccess();
          onCancel();
        }, 2000);
      }
    } catch (error: any) {
      console.error('模拟支付失败:', error);
      const errorMsg = error.response?.data?.detail || '模拟支付失败';
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // 初始化
  useEffect(() => {
    if (visible && packageType) {
      fetchPackageInfo();
      createPaymentOrder();
    }
  }, [visible, packageType]);

  // 清理
  useEffect(() => {
    if (!visible) {
      setOrderData(null);
      setPackageData(null);
      setPolling(false);
      setCountdown(0);
      setPaymentStatus('pending');
    }
  }, [visible]);

  const getStatusIcon = () => {
    switch (paymentStatus) {
      case 'paid':
        return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '24px' }} />;
      case 'failed':
      case 'expired':
      case 'cancelled':
        return <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: '24px' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#1890ff', fontSize: '24px' }} />;
    }
  };

  return (
    <Modal
      title="微信支付"
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={480}
      maskClosable={false}
    >
      <div style={{ padding: '16px 0' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
            <p style={{ marginTop: 16 }}>正在创建支付订单...</p>
          </div>
        ) : (
          <>
            {/* 套餐信息 */}
            {packageData && (
              <Card size="small" style={{ marginBottom: 16 }}>
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="套餐名称">
                    <Text strong>{packageData.name}</Text>
                  </Descriptions.Item>
                  <Descriptions.Item label="支付金额">
                    <Text type="danger" style={{ fontSize: '18px', fontWeight: 'bold' }}>
                      ¥{packageData.price}
                    </Text>
                  </Descriptions.Item>
                  <Descriptions.Item label="套餐内容">
                    {packageData.queries_count > 0 && (
                      <Tag color="blue">{packageData.queries_count}次查询</Tag>
                    )}
                    {packageData.validity_days > 0 && (
                      <Tag color="green">{packageData.validity_days}天有效期</Tag>
                    )}
                    {packageData.membership_type !== 'free' && (
                      <Tag color="gold">{packageData.membership_type.toUpperCase()}会员</Tag>
                    )}
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            )}

            {/* 支付状态 */}
            <Card size="small" style={{ marginBottom: 16 }}>
              <div style={{ textAlign: 'center' }}>
                <Space direction="vertical" size="small">
                  {getStatusIcon()}
                  <Text strong>{getStatusText(paymentStatus)}</Text>
                  {paymentStatus === 'pending' && countdown > 0 && (
                    <>
                      <Text type="secondary">
                        订单有效期：{formatCountdown(countdown)}
                      </Text>
                      <Progress 
                        percent={((7200 - countdown) / 7200) * 100} 
                        size="small" 
                        status="normal"
                        showInfo={false}
                      />
                    </>
                  )}
                </Space>
              </div>
            </Card>

            {/* 二维码支付 */}
            {orderData && paymentStatus === 'pending' && orderData.code_url && (
              <Card size="small" style={{ marginBottom: 16 }}>
                <div style={{ textAlign: 'center' }}>
                  <QRCode 
                    value={orderData.code_url} 
                    size={200}
                    style={{ marginBottom: 16 }}
                  />
                  <div>
                    <WechatOutlined style={{ color: '#07c160', fontSize: '20px' }} />
                    <Text style={{ marginLeft: 8 }}>请使用微信扫码支付</Text>
                  </div>
                  {polling && (
                    <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                      等待支付中，请勿关闭页面...
                    </Text>
                  )}
                </div>
              </Card>
            )}

            {/* 订单信息 */}
            {orderData && (
              <Card size="small" style={{ marginBottom: 16 }}>
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text type="secondary">订单号</Text>
                    <Space>
                      <Text code style={{ fontSize: '12px' }}>
                        {orderData.out_trade_no}
                      </Text>
                      <Button 
                        type="text" 
                        size="small" 
                        icon={<CopyOutlined />}
                        onClick={copyOrderNo}
                      />
                    </Space>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text type="secondary">创建时间</Text>
                    <Text>{dayjs(orderData.created_at).format('YYYY-MM-DD HH:mm:ss')}</Text>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text type="secondary">过期时间</Text>
                    <Text>{dayjs(orderData.expire_time).format('YYYY-MM-DD HH:mm:ss')}</Text>
                  </div>
                </Space>
              </Card>
            )}

            {/* 支付说明 */}
            <Alert
              message="支付说明"
              description={
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  <li>请在订单有效期内完成支付</li>
                  <li>支付成功后会员权益将立即生效</li>
                  <li>如有问题请联系客服</li>
                </ul>
              }
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            {/* 操作按钮 */}
            <div style={{ textAlign: 'center' }}>
              <Space>
                <Button onClick={onCancel}>关闭</Button>
                {paymentStatus === 'pending' && orderData && (
                  <Button danger onClick={cancelOrder}>
                    取消订单
                  </Button>
                )}
              </Space>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
};

export default PaymentModal;