import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, Space, Modal, Spin, message, Empty, Pagination } from 'antd';
import { EyeOutlined, ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
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

interface Order {
  id: number;
  order_no: string;
  package_id: number;
  package_name: string;
  total_price: number;
  status: string;
  transaction_id: string;
  created_at: string;
  paid_at: string;
}

interface OrderHistoryPageProps {
  userInfo: UserInfo | null;
}

const OrderHistoryPage: React.FC<OrderHistoryPageProps> = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });

  // 获取订单列表
  const fetchOrders = async (page = 1, pageSize = 10) => {
    try {
      setLoading(true);
      const response = await api.get('/payment/orders', {
        params: {
          skip: (page - 1) * pageSize,
          limit: pageSize,
        },
      });

      // 处理响应格式
      const data = Array.isArray(response.data) ? response.data : response.data.items || [];
      const total = response.data.total || data.length;

      setOrders(data);
      setPagination({ ...pagination, current: page, total });
    } catch (error) {
      message.error('获取订单列表失败');
      setOrders([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders(1, pagination.pageSize);
  }, []);

  // 显示订单详情
  const handleShowDetail = (order: Order) => {
    setSelectedOrder(order);
    setDetailModalVisible(true);
  };

  // 关闭详情弹窗
  const handleCloseDetail = () => {
    setDetailModalVisible(false);
    setSelectedOrder(null);
  };

  // 重新加载
  const handleRefresh = () => {
    fetchOrders(pagination.current, pagination.pageSize);
  };

  // 导出订单
  const handleExport = () => {
    message.info('订单导出功能开发中...');
  };

  // 状态颜色映射
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid':
      case 'completed':
        return 'green';
      case 'pending':
        return 'orange';
      case 'cancelled':
        return 'red';
      default:
        return 'default';
    }
  };

  // 状态中文
  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'paid':
        return '已支付';
      case 'completed':
        return '已完成';
      case 'pending':
        return '待支付';
      case 'cancelled':
        return '已取消';
      default:
        return status;
    }
  };

  const columns = [
    {
      title: '订单号',
      dataIndex: 'order_no',
      key: 'order_no',
      width: 180,
      render: (text: string) => (
        <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>{text}</span>
      ),
    },
    {
      title: '套餐',
      dataIndex: 'package_name',
      key: 'package_name',
      width: 150,
    },
    {
      title: '金额',
      dataIndex: 'total_price',
      key: 'total_price',
      width: 100,
      render: (price: number) => (
        <span style={{ fontWeight: 'bold', color: '#ff4d4f' }}>
          ¥{price.toFixed(2)}
        </span>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {getStatusLabel(status)}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '支付时间',
      dataIndex: 'paid_at',
      key: 'paid_at',
      width: 180,
      render: (date: string) => date ? new Date(date).toLocaleString('zh-CN') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: Order) => (
        <Button
          type="link"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => handleShowDetail(record)}
        >
          详情
        </Button>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题和操作栏 */}
      <Card
        style={{
          marginBottom: '24px',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
        }}
        bodyStyle={{ padding: '20px' }}
      >
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}>
          <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 'bold' }}>
            订单历史
          </h2>
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              loading={loading}
            >
              刷新
            </Button>
            <Button
              icon={<DownloadOutlined />}
              onClick={handleExport}
            >
              导出
            </Button>
          </Space>
        </div>

        {/* 统计信息 */}
        <div style={{
          marginTop: '16px',
          display: 'flex',
          gap: '32px',
          flexWrap: 'wrap',
          fontSize: '14px',
        }}>
          <div>
            <span style={{ color: '#999' }}>总订单数:</span>
            <span style={{ fontWeight: 'bold', marginLeft: '8px' }}>{pagination.total}</span>
          </div>
          <div>
            <span style={{ color: '#999' }}>已支付订单:</span>
            <span style={{ fontWeight: 'bold', marginLeft: '8px', color: '#52c41a' }}>
              {orders.filter(o => o.status === 'paid' || o.status === 'completed').length}
            </span>
          </div>
          <div>
            <span style={{ color: '#999' }}>待支付订单:</span>
            <span style={{ fontWeight: 'bold', marginLeft: '8px', color: '#faad14' }}>
              {orders.filter(o => o.status === 'pending').length}
            </span>
          </div>
        </div>
      </Card>

      {/* 订单表格 */}
      <Card
        style={{
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
        }}
        bodyStyle={{ padding: '0' }}
      >
        <Spin spinning={loading}>
          {orders.length > 0 ? (
            <>
              <Table
                columns={columns}
                dataSource={orders}
                pagination={false}
                size="middle"
                scroll={{ x: 1200 }}
                style={{ borderRadius: '8px' }}
              />
              <div style={{
                padding: '16px 24px',
                display: 'flex',
                justifyContent: 'flex-end',
                borderTop: '1px solid #f0f0f0',
              }}>
                <Pagination
                  current={pagination.current}
                  pageSize={pagination.pageSize}
                  total={pagination.total}
                  onChange={(page) => fetchOrders(page, pagination.pageSize)}
                  showSizeChanger
                  onShowSizeChange={(_, pageSize) => fetchOrders(1, pageSize)}
                  showTotal={(total) => `共 ${total} 条订单`}
                />
              </div>
            </>
          ) : (
            <Empty
              description="暂无订单"
              style={{ padding: '48px 0' }}
            />
          )}
        </Spin>
      </Card>

      {/* 订单详情弹窗 */}
      <Modal
        title="订单详情"
        open={detailModalVisible}
        onCancel={handleCloseDetail}
        footer={[
          <Button key="close" type="primary" onClick={handleCloseDetail}>
            关闭
          </Button>,
        ]}
        width={600}
      >
        {selectedOrder && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ color: '#999', fontSize: '12px' }}>订单号</label>
                <div style={{ fontSize: '14px', fontWeight: 'bold', marginTop: '4px' }}>
                  {selectedOrder.order_no}
                </div>
              </div>
              <div>
                <label style={{ color: '#999', fontSize: '12px' }}>订单状态</label>
                <div style={{ marginTop: '4px' }}>
                  <Tag color={getStatusColor(selectedOrder.status)}>
                    {getStatusLabel(selectedOrder.status)}
                  </Tag>
                </div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ color: '#999', fontSize: '12px' }}>套餐</label>
                <div style={{ fontSize: '14px', fontWeight: 'bold', marginTop: '4px' }}>
                  {selectedOrder.package_name}
                </div>
              </div>
              <div>
                <label style={{ color: '#999', fontSize: '12px' }}>金额</label>
                <div style={{ fontSize: '14px', fontWeight: 'bold', marginTop: '4px', color: '#ff4d4f' }}>
                  ¥{selectedOrder.total_price.toFixed(2)}
                </div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ color: '#999', fontSize: '12px' }}>创建时间</label>
                <div style={{ fontSize: '14px', marginTop: '4px' }}>
                  {new Date(selectedOrder.created_at).toLocaleString('zh-CN')}
                </div>
              </div>
              <div>
                <label style={{ color: '#999', fontSize: '12px' }}>支付时间</label>
                <div style={{ fontSize: '14px', marginTop: '4px' }}>
                  {selectedOrder.paid_at ? new Date(selectedOrder.paid_at).toLocaleString('zh-CN') : '-'}
                </div>
              </div>
            </div>

            {selectedOrder.transaction_id && (
              <div>
                <label style={{ color: '#999', fontSize: '12px' }}>交易号</label>
                <div style={{
                  fontSize: '12px',
                  marginTop: '4px',
                  fontFamily: 'monospace',
                  padding: '8px 12px',
                  background: '#f5f5f5',
                  borderRadius: '4px',
                  wordBreak: 'break-all',
                }}>
                  {selectedOrder.transaction_id}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default OrderHistoryPage;
