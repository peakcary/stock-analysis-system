import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Input, Space, message, Modal, Form,
  Select, Tag, Statistic, Row, Col, Popconfirm, Badge,
  Typography, Drawer, Descriptions, List, Tooltip, DatePicker,
  Switch, Progress, Divider, Alert
} from 'antd';
import {
  UserOutlined, SearchOutlined, PlusOutlined, EditOutlined,
  DeleteOutlined, EyeOutlined, CrownOutlined, HistoryOutlined,
  DollarOutlined, ReloadOutlined, KeyOutlined, LockOutlined,
  UnlockOutlined, SettingOutlined, TrophyOutlined, StarOutlined
} from '@ant-design/icons';
import axios from 'axios';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;

interface User {
  id: number;
  username: string;
  email: string;
  membership_type: 'free' | 'pro' | 'premium';
  queries_remaining: number;
  membership_expires_at?: string;
  created_at: string;
  updated_at: string;
}

interface UserQuery {
  id: number;
  query_type: string;
  query_params: any;
  created_at: string;
}

interface Payment {
  id: number;
  amount: number;
  payment_type: string;
  payment_status: string;
  payment_method: string;
  transaction_id: string;
  created_at: string;
  completed_at?: string;
}

interface UserStats {
  total_users: number;
  free_users: number;
  paid_users: number;
  monthly_users: number;
  yearly_users: number;
  total_queries_today: number;
  total_payments_today: number;
  new_users_today: number;
}

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [selectedMembership, setSelectedMembership] = useState<string>('');
  const [userModalVisible, setUserModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [userDetailVisible, setUserDetailVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [userQueries, setUserQueries] = useState<UserQuery[]>([]);
  const [userPayments, setUserPayments] = useState<Payment[]>([]);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [form] = Form.useForm();
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });

  // 获取用户列表
  const fetchUsers = async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const params: any = {
        skip: (page - 1) * pageSize,
        limit: pageSize
      };
      
      if (searchText) {
        params.search = searchText;
      }
      
      if (selectedMembership) {
        params.membership_type = selectedMembership;
      }

      // 模拟管理员API调用 - 实际使用时需要添加认证
      const response = await axios.get('/api/v1/admin/users', {
        params,
        headers: {
          'Authorization': 'Bearer admin-token' // 实际使用时需要真实token
        }
      });

      setUsers(response.data.users || []);
      setPagination({
        current: page,
        pageSize,
        total: response.data.total
      });
    } catch (error) {
      console.error('获取用户列表失败:', error);
      message.error('获取用户列表失败');
      // 使用模拟数据
      const mockUsers = [
        {
          id: 1,
          username: 'admin',
          email: 'admin@example.com',
          membership_type: 'premium' as const,
          queries_remaining: 999,
          membership_expires_at: '2025-12-31T23:59:59Z',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-08-24T00:00:00Z'
        },
        {
          id: 2,
          username: 'testuser',
          email: 'test@example.com',
          membership_type: 'free' as const,
          queries_remaining: 10,
          created_at: '2024-08-24T10:00:00Z',
          updated_at: '2024-08-24T10:00:00Z'
        }
      ];
      setUsers(mockUsers);
    } finally {
      setLoading(false);
    }
  };

  // 获取用户统计
  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/v1/admin/stats', {
        headers: {
          'Authorization': 'Bearer admin-token'
        }
      });
      setStats(response.data);
    } catch (error) {
      console.error('获取统计数据失败:', error);
      // 使用模拟数据
      setStats({
        total_users: 156,
        free_users: 123,
        paid_users: 33,
        monthly_users: 15,
        yearly_users: 18,
        total_queries_today: 245,
        total_payments_today: 1280.50,
        new_users_today: 8
      });
    }
  };

  // 获取用户详情
  const fetchUserDetail = async (userId: number) => {
    try {
      // 获取用户查询记录
      const queriesResponse = await axios.get(`/api/v1/admin/users/${userId}/queries`, {
        headers: { 'Authorization': 'Bearer admin-token' }
      });
      setUserQueries(queriesResponse.data.queries || []);

      // 获取用户支付记录
      const paymentsResponse = await axios.get(`/api/v1/admin/users/${userId}/payments`, {
        headers: { 'Authorization': 'Bearer admin-token' }
      });
      setUserPayments(paymentsResponse.data.payments || []);
    } catch (error) {
      console.error('获取用户详情失败:', error);
      // 使用模拟数据
      setUserQueries([
        {
          id: 1,
          query_type: 'stock_search',
          query_params: { search: '平安银行' },
          created_at: '2024-08-24T10:30:00Z'
        }
      ]);
      setUserPayments([]);
    }
  };

  // 创建/更新用户
  const handleSaveUser = async (values: any) => {
    try {
      if (editingUser) {
        // 更新用户
        await axios.put(`http://localhost:8000/api/v1/admin/users/${editingUser.id}`, values, {
          headers: { 'Authorization': 'Bearer admin-token' }
        });
        message.success('用户更新成功');
      } else {
        // 创建用户
        await axios.post('/api/v1/admin/users', values, {
          headers: { 'Authorization': 'Bearer admin-token' }
        });
        message.success('用户创建成功');
      }
      setUserModalVisible(false);
      setEditingUser(null);
      form.resetFields();
      fetchUsers();
    } catch (error) {
      console.error('保存用户失败:', error);
      message.error('保存用户失败');
    }
  };

  // 删除用户
  const handleDeleteUser = async (userId: number) => {
    try {
      await axios.delete(`http://localhost:8000/api/v1/admin/users/${userId}`, {
        headers: { 'Authorization': 'Bearer admin-token' }
      });
      message.success('用户删除成功');
      fetchUsers();
    } catch (error) {
      console.error('删除用户失败:', error);
      message.error('删除用户失败');
    }
  };

  // 升级会员
  const handleUpgradeMembership = async (userId: number, membershipType: string) => {
    try {
      await axios.post(`/api/v1/admin/users/${userId}/membership`, {
        membership_type: membershipType,
        queries_to_add: membershipType === 'pro' ? 1000 : membershipType === 'premium' ? 9999 : 0,
        days_to_add: membershipType === 'pro' ? 30 : membershipType === 'premium' ? 365 : 0
      }, {
        headers: { 'Authorization': 'Bearer admin-token' }
      });
      message.success('会员升级成功');
      fetchUsers();
    } catch (error) {
      console.error('会员升级失败:', error);
      message.error('会员升级失败');
    }
  };

  // 重置密码
  const handleResetPassword = async (userId: number) => {
    const newPassword = 'reset123';
    try {
      await axios.post(`/api/v1/admin/users/${userId}/reset-password?new_password=${newPassword}`, {}, {
        headers: { 'Authorization': 'Bearer admin-token' }
      });
      message.success(`密码重置成功，新密码: ${newPassword}`);
    } catch (error) {
      console.error('重置密码失败:', error);
      message.error('重置密码失败');
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchStats();
  }, []);

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      render: (text: string, record: User) => (
        <Space>
          <UserOutlined />
          <Text strong>{text}</Text>
          {record.username === 'admin' && <Tag color="red">管理员</Tag>}
        </Space>
      ),
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '会员类型',
      dataIndex: 'membership_type',
      key: 'membership_type',
      render: (type: string) => {
        const configs = {
          free: { color: 'default', icon: <StarOutlined />, text: '免费版' },
          pro: { color: 'blue', icon: <TrophyOutlined />, text: '专业版' },
          premium: { color: 'gold', icon: <CrownOutlined />, text: '旗舰版' }
        };
        const config = configs[type as keyof typeof configs];
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        );
      },
    },
    {
      title: '剩余查询',
      dataIndex: 'queries_remaining',
      key: 'queries_remaining',
      render: (count: number) => (
        <Badge count={count} showZero color={count > 100 ? '#52c41a' : count > 10 ? '#faad14' : '#ff4d4f'} />
      ),
    },
    {
      title: '会员到期',
      dataIndex: 'membership_expires_at',
      key: 'membership_expires_at',
      render: (date: string) => date ? dayjs(date).format('YYYY-MM-DD') : '-',
    },
    {
      title: '注册时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: User) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => {
                setSelectedUser(record);
                fetchUserDetail(record.id);
                setUserDetailVisible(true);
              }}
            />
          </Tooltip>
          <Tooltip title="编辑用户">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => {
                setEditingUser(record);
                form.setFieldsValue(record);
                setUserModalVisible(true);
              }}
            />
          </Tooltip>
          <Tooltip title="重置密码">
            <Popconfirm
              title="确定要重置此用户的密码吗？"
              onConfirm={() => handleResetPassword(record.id)}
            >
              <Button type="text" icon={<KeyOutlined />} />
            </Popconfirm>
          </Tooltip>
          {record.username !== 'admin' && (
            <Popconfirm
              title="确定要删除此用户吗？"
              onConfirm={() => handleDeleteUser(record.id)}
            >
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 统计卡片 */}
      {stats && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="总用户数"
                value={stats.total_users}
                prefix={<UserOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="付费用户"
                value={stats.paid_users}
                prefix={<CrownOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="今日查询"
                value={stats.total_queries_today}
                prefix={<SearchOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="今日收入"
                value={stats.total_payments_today}
                prefix={<DollarOutlined />}
                precision={2}
                valueStyle={{ color: '#f5222d' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 工具栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Search
              placeholder="搜索用户名或邮箱"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onSearch={() => fetchUsers()}
              allowClear
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="筛选会员类型"
              value={selectedMembership}
              onChange={setSelectedMembership}
              allowClear
              style={{ width: '100%' }}
            >
              <Option value="">全部</Option>
              <Option value="free">免费版</Option>
              <Option value="pro">专业版</Option>
              <Option value="premium">旗舰版</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setEditingUser(null);
                form.resetFields();
                setUserModalVisible(true);
              }}
              block
            >
              新增用户
            </Button>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => fetchUsers()}
              block
            >
              刷新数据
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 用户表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} 共 ${total} 条`,
            onChange: (page, pageSize) => {
              fetchUsers(page, pageSize);
            }
          }}
          scroll={{ x: 'max-content' }}
        />
      </Card>

      {/* 用户编辑弹窗 */}
      <Modal
        title={editingUser ? '编辑用户' : '新增用户'}
        open={userModalVisible}
        onCancel={() => {
          setUserModalVisible(false);
          setEditingUser(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveUser}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="username"
                label="用户名"
                rules={[{ required: true, message: '请输入用户名' }]}
              >
                <Input prefix={<UserOutlined />} placeholder="用户名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="email"
                label="邮箱"
                rules={[
                  { required: true, message: '请输入邮箱' },
                  { type: 'email', message: '请输入有效的邮箱地址' }
                ]}
              >
                <Input placeholder="邮箱地址" />
              </Form.Item>
            </Col>
          </Row>
          
          {!editingUser && (
            <Form.Item
              name="password"
              label="密码"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password placeholder="密码" />
            </Form.Item>
          )}
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="membership_type"
                label="会员类型"
                rules={[{ required: true, message: '请选择会员类型' }]}
              >
                <Select placeholder="选择会员类型">
                  <Option value="free">免费版</Option>
                  <Option value="pro">专业版</Option>
                  <Option value="premium">旗舰版</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="queries_remaining"
                label="剩余查询次数"
                rules={[{ required: true, message: '请输入查询次数' }]}
              >
                <Input type="number" placeholder="查询次数" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* 用户详情抽屉 */}
      <Drawer
        title="用户详情"
        open={userDetailVisible}
        onClose={() => setUserDetailVisible(false)}
        width={720}
      >
        {selectedUser && (
          <div>
            <Descriptions title="基本信息" bordered column={2}>
              <Descriptions.Item label="用户ID">{selectedUser.id}</Descriptions.Item>
              <Descriptions.Item label="用户名">{selectedUser.username}</Descriptions.Item>
              <Descriptions.Item label="邮箱">{selectedUser.email}</Descriptions.Item>
              <Descriptions.Item label="会员类型">
                {selectedUser.membership_type === 'free' ? '免费版' :
                 selectedUser.membership_type === 'pro' ? '专业版' : '旗舰版'}
              </Descriptions.Item>
              <Descriptions.Item label="剩余查询">{selectedUser.queries_remaining}</Descriptions.Item>
              <Descriptions.Item label="会员到期">
                {selectedUser.membership_expires_at ? 
                  dayjs(selectedUser.membership_expires_at).format('YYYY-MM-DD HH:mm') : '无限期'}
              </Descriptions.Item>
              <Descriptions.Item label="注册时间">
                {dayjs(selectedUser.created_at).format('YYYY-MM-DD HH:mm')}
              </Descriptions.Item>
              <Descriptions.Item label="更新时间">
                {dayjs(selectedUser.updated_at).format('YYYY-MM-DD HH:mm')}
              </Descriptions.Item>
            </Descriptions>

            <Divider />
            
            <Space style={{ marginBottom: 16 }}>
              <Button
                type="primary"
                onClick={() => handleUpgradeMembership(selectedUser.id, 'pro')}
              >
                升级为专业版
              </Button>
              <Button
                type="primary"
                onClick={() => handleUpgradeMembership(selectedUser.id, 'premium')}
              >
                升级为旗舰版
              </Button>
              <Button onClick={() => handleResetPassword(selectedUser.id)}>
                重置密码
              </Button>
            </Space>

            <Title level={4}>查询记录</Title>
            <List
              dataSource={userQueries}
              renderItem={(item: UserQuery) => (
                <List.Item>
                  <List.Item.Meta
                    title={`查询类型: ${item.query_type}`}
                    description={`查询时间: ${dayjs(item.created_at).format('YYYY-MM-DD HH:mm:ss')}`}
                  />
                  <div>参数: {JSON.stringify(item.query_params)}</div>
                </List.Item>
              )}
            />

            <Title level={4}>支付记录</Title>
            <List
              dataSource={userPayments}
              renderItem={(item: Payment) => (
                <List.Item>
                  <List.Item.Meta
                    title={`支付金额: ¥${item.amount}`}
                    description={`支付时间: ${dayjs(item.created_at).format('YYYY-MM-DD HH:mm:ss')}`}
                  />
                  <div>
                    <Tag color={item.payment_status === 'completed' ? 'green' : 'orange'}>
                      {item.payment_status}
                    </Tag>
                  </div>
                </List.Item>
              )}
            />
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default UserManagement;