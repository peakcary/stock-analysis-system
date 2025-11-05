import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Tag,
  Space,
  message,
  Modal,
  Descriptions,
  Typography,
  Input,
  Row,
  Col,
  Statistic,
  Alert,
  Tooltip,
  Popconfirm
} from 'antd';
import {
  EyeOutlined,
  RollbackOutlined,
  HistoryOutlined,
  MoneyCollectOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { apiClient } from '../utils/auth';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface PaymentOrder {
  id: number;
  out_trade_no: string;
  package_name: string;
  amount: number;
  status: string;
  payment_method: string;
  created_at: string;
  paid_at?: string;
  expire_time: string;
  transaction_id?: string;
}

interface RefundRecord {
  id: number;
  order_id: number;
  out_refund_no: string;
  refund_id?: string;
  refund_amount: number;
  refund_reason: string;
  refund_status: string;
  refund_channel?: string;
  created_at: string;
  processed_at?: string;
}

interface PaymentStats {
  total_orders: number;
  paid_orders: number;
  total_amount: number;
  membership_type: string;
  queries_remaining: number;
  membership_expires_at?: string;
}

const PaymentHistoryPage: React.FC = () => {
  const [orders, setOrders] = useState<PaymentOrder[]>([]);
  const [refunds, setRefunds] = useState<RefundRecord[]>([]);
  const [stats, setStats] = useState<PaymentStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [orderDetailVisible, setOrderDetailVisible] = useState(false);
  const [refundModalVisible, setRefundModalVisible] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<PaymentOrder | null>(null);
  const [refundReason, setRefundReason] = useState('');
  const [activeTab, setActiveTab] = useState('orders'); // 'orders' | 'refunds'

  // 获取支付统计
  const fetchPaymentStats = async () => {
    try {
      const response = await apiClient.get('/payment/stats');
      setStats(response.data);
    } catch (error) {
      console.error('获取支付统计失败:', error);
      message.error('获取支付统计失败');
    }
  };

  // 获取支付历史
  const fetchPaymentHistory = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/payment/v2/orders/history');

      if (response.data.success) {
        setOrders(response.data.data.orders || []);
      } else {
        message.error(response.data.message || '获取支付历史失败');
      }
    } catch (error) {
      console.error('获取支付历史失败:', error);
      message.error('获取支付历史失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取退款记录
  const fetchRefundHistory = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/payment/refunds');
      setRefunds(response.data.refunds || []);
    } catch (error) {
      console.error('获取退款记录失败:', error);
      message.error('获取退款记录失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPaymentStats();
    fetchPaymentHistory();
    fetchRefundHistory();
  }, []);

  // 获取订单状态标签
  const getOrderStatusTag = (status: string) => {
    const statusMap = {
      pending: { color: 'processing', text: '待支付', icon: <ClockCircleOutlined /> },
      paid: { color: 'success', text: '已支付', icon: <CheckCircleOutlined /> },
      expired: { color: 'default', text: '已过期', icon: <ExclamationCircleOutlined /> },
      cancelled: { color: 'default', text: '已取消', icon: <CloseCircleOutlined /> },
      failed: { color: 'error', text: '支付失败', icon: <CloseCircleOutlined /> },
      refunded: { color: 'warning', text: '已退款', icon: <RollbackOutlined /> }
    };
    const config = statusMap[status as keyof typeof statusMap] || statusMap.pending;
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  // 获取退款状态标签
  const getRefundStatusTag = (status: string) => {
    const statusMap = {
      processing: { color: 'processing', text: '处理中' },
      success: { color: 'success', text: '退款成功' },
      failed: { color: 'error', text: '退款失败' }
    };
    const config = statusMap[status as keyof typeof statusMap] || statusMap.processing;
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 申请退款
  const handleRefund = async () => {
    if (!selectedOrder || !refundReason.trim()) {
      message.error('请填写退款原因');
      return;
    }

    try {
      await apiClient.post(`/api/v1/payment/refund/${selectedOrder.id}`, {
        refund_reason: refundReason
      });

      message.success('退款申请已提交，请等待处理');
      setRefundModalVisible(false);
      setRefundReason('');
      setSelectedOrder(null);

      // 刷新数据
      fetchPaymentHistory();
      fetchRefundHistory();
      fetchPaymentStats();
    } catch (error: any) {
      console.error('申请退款失败:', error);
      const errorMsg = error.response?.data?.detail || '申请退款失败';
      message.error(errorMsg);
    }
  };

  // 查看订单详情
  const viewOrderDetail = (order: PaymentOrder) => {
    setSelectedOrder(order);
    setOrderDetailVisible(true);
  };

  // 申请退款
  const applyRefund = (order: PaymentOrder) => {
    setSelectedOrder(order);
    setRefundModalVisible(true);
  };

  const orderColumns = [
    {
      title: '订单号',
      dataIndex: 'out_trade_no',
      key: 'out_trade_no',
      render: (text: string) => (
        <Text copyable={{ text }} style={{ fontFamily: 'monospace' }}>
          {text.slice(-12)}
        </Text>
      )
    },
    {
      title: '套餐名称',
      dataIndex: 'package_name',
      key: 'package_name'
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => (
        <Text strong style={{ color: '#ff4d4f' }}>¥{amount}</Text>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getOrderStatusTag(status)
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss')
    },
    {
      title: '支付时间',
      dataIndex: 'paid_at',
      key: 'paid_at',
      render: (time?: string) => time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-'
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: PaymentOrder) => (
        <Space>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => viewOrderDetail(record)}
          >
            详情
          </Button>
          {record.status === 'paid' && (
            <Popconfirm
              title="确认申请退款？"
              description="退款申请提交后无法撤回"
              onConfirm={() => applyRefund(record)}
              okText="确认"
              cancelText="取消"
            >
              <Button
                size="small"
                icon={<RollbackOutlined />}
                danger
              >
                退款
              </Button>
            </Popconfirm>
          )}
        </Space>
      )
    }
  ];

  const refundColumns = [
    {
      title: '退款单号',
      dataIndex: 'out_refund_no',
      key: 'out_refund_no',
      render: (text: string) => (
        <Text copyable={{ text }} style={{ fontFamily: 'monospace' }}>
          {text.slice(-12)}
        </Text>
      )
    },
    {
      title: '退款金额',
      dataIndex: 'refund_amount',
      key: 'refund_amount',
      render: (amount: number) => (
        <Text strong style={{ color: '#fa8c16' }}>¥{amount}</Text>
      )
    },
    {
      title: '退款原因',
      dataIndex: 'refund_reason',
      key: 'refund_reason',
      ellipsis: true
    },
    {
      title: '状态',
      dataIndex: 'refund_status',
      key: 'refund_status',
      render: (status: string) => getRefundStatusTag(status)
    },
    {
      title: '申请时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss')
    },
    {
      title: '处理时间',
      dataIndex: 'processed_at',
      key: 'processed_at',
      render: (time?: string) => time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-'
    }
  ];

  return (
    <div style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <Title level={2} style={{ marginBottom: '24px' }}>
          <HistoryOutlined style={{ marginRight: '8px' }} />
          支付管理
        </Title>

        {/* 统计卡片 */}
        {stats && (
          <Row gutter={16} style={{ marginBottom: '24px' }}>
            <Col xs={24} sm={8} md={6}>
              <Card>
                <Statistic
                  title="总订单数"
                  value={stats.total_orders}
                  prefix={<MoneyCollectOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8} md={6}>
              <Card>
                <Statistic
                  title="成功支付"
                  value={stats.paid_orders}
                  prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8} md={6}>
              <Card>
                <Statistic
                  title="消费总额"
                  value={stats.total_amount}
                  precision={2}
                  prefix="¥"
                  valueStyle={{ color: '#cf1322' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8} md={6}>
              <Card>
                <Statistic
                  title="剩余查询"
                  value={stats.queries_remaining}
                  suffix="次"
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
          </Row>
        )}

        {/* 会员状态 */}
        {stats && (
          <Alert
            message={`当前会员等级：${stats.membership_type.toUpperCase()}`}
            description={
              stats.membership_expires_at
                ? `会员有效期至：${dayjs(stats.membership_expires_at).format('YYYY-MM-DD HH:mm:ss')}`
                : '永久有效'
            }
            type="info"
            showIcon
            style={{ marginBottom: '24px' }}
          />
        )}

        {/* 标签页切换 */}
        <Card
          tabList={[
            { key: 'orders', tab: '支付记录' },
            { key: 'refunds', tab: '退款记录' }
          ]}
          activeTabKey={activeTab}
          onTabChange={setActiveTab}
        >
          {activeTab === 'orders' && (
            <Table
              columns={orderColumns}
              dataSource={orders}
              rowKey="id"
              loading={loading}
              pagination={{
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`
              }}
            />
          )}

          {activeTab === 'refunds' && (
            <Table
              columns={refundColumns}
              dataSource={refunds}
              rowKey="id"
              loading={loading}
              pagination={{
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`
              }}
            />
          )}
        </Card>

        {/* 订单详情弹窗 */}
        <Modal
          title="订单详情"
          open={orderDetailVisible}
          onCancel={() => setOrderDetailVisible(false)}
          footer={null}
          width={600}
        >
          {selectedOrder && (
            <Descriptions column={1} bordered>
              <Descriptions.Item label="订单号">
                <Text copyable>{selectedOrder.out_trade_no}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="套餐名称">
                {selectedOrder.package_name}
              </Descriptions.Item>
              <Descriptions.Item label="支付金额">
                <Text strong style={{ color: '#ff4d4f' }}>¥{selectedOrder.amount}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="支付方式">
                {selectedOrder.payment_method === 'wechat_native' ? '微信扫码' : '微信H5'}
              </Descriptions.Item>
              <Descriptions.Item label="订单状态">
                {getOrderStatusTag(selectedOrder.status)}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {dayjs(selectedOrder.created_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="支付时间">
                {selectedOrder.paid_at
                  ? dayjs(selectedOrder.paid_at).format('YYYY-MM-DD HH:mm:ss')
                  : '未支付'}
              </Descriptions.Item>
              <Descriptions.Item label="过期时间">
                {dayjs(selectedOrder.expire_time).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              {selectedOrder.transaction_id && (
                <Descriptions.Item label="交易号">
                  <Text copyable>{selectedOrder.transaction_id}</Text>
                </Descriptions.Item>
              )}
            </Descriptions>
          )}
        </Modal>

        {/* 退款申请弹窗 */}
        <Modal
          title="申请退款"
          open={refundModalVisible}
          onOk={handleRefund}
          onCancel={() => {
            setRefundModalVisible(false);
            setRefundReason('');
            setSelectedOrder(null);
          }}
          okText="提交申请"
          cancelText="取消"
        >
          {selectedOrder && (
            <>
              <Alert
                message="退款说明"
                description="退款申请提交后，我们将在1-3个工作日内处理。退款金额将原路返回到您的支付账户。"
                type="info"
                showIcon
                style={{ marginBottom: '16px' }}
              />

              <Descriptions column={1} size="small" style={{ marginBottom: '16px' }}>
                <Descriptions.Item label="订单号">
                  {selectedOrder.out_trade_no}
                </Descriptions.Item>
                <Descriptions.Item label="套餐名称">
                  {selectedOrder.package_name}
                </Descriptions.Item>
                <Descriptions.Item label="退款金额">
                  <Text strong style={{ color: '#fa8c16' }}>¥{selectedOrder.amount}</Text>
                </Descriptions.Item>
              </Descriptions>

              <div>
                <Text strong>退款原因 *</Text>
                <TextArea
                  value={refundReason}
                  onChange={(e) => setRefundReason(e.target.value)}
                  placeholder="请说明退款原因"
                  maxLength={200}
                  showCount
                  rows={4}
                  style={{ marginTop: '8px' }}
                />
              </div>
            </>
          )}
        </Modal>
      </div>
    </div>
  );
};

export default PaymentHistoryPage;