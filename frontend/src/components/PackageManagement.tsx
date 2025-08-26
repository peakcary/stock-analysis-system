import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Input, Space, message, Modal, Form,
  Select, Tag, Statistic, Row, Col, Popconfirm, Badge,
  Typography, Drawer, Descriptions, InputNumber, Switch,
  Alert, Divider
} from 'antd';
import {
  GiftOutlined, SearchOutlined, PlusOutlined, EditOutlined,
  DeleteOutlined, EyeOutlined, SettingOutlined, ReloadOutlined,
  DollarOutlined, CrownOutlined, StarOutlined, ClockCircleOutlined,
  SortAscendingOutlined
} from '@ant-design/icons';
import axios from 'axios';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;
const { TextArea } = Input;

interface PaymentPackage {
  id: number;
  package_type: string;
  name: string;
  price: number;
  queries_count: number;
  validity_days: number;
  membership_type: 'free' | 'pro' | 'premium';
  description?: string;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

interface PackageStats {
  total_packages: number;
  active_packages: number;
  inactive_packages: number;
  membership_distribution: Array<{
    membership_type: string;
    count: number;
  }>;
}

const PackageManagement: React.FC = () => {
  const [packages, setPackages] = useState<PaymentPackage[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [filteredPackages, setFilteredPackages] = useState<PaymentPackage[]>([]);
  const [selectedPackage, setSelectedPackage] = useState<PaymentPackage | null>(null);
  const [showDetail, setShowDetail] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModalVisible, setShowEditModalVisible] = useState(false);
  const [editingPackage, setEditingPackage] = useState<PaymentPackage | null>(null);
  const [stats, setStats] = useState<PackageStats | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loginLoading, setLoginLoading] = useState(false);
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();
  const [loginForm] = Form.useForm();

  // 获取管理员token
  const getAuthToken = () => {
    return localStorage.getItem('token');
  };

  // 检查认证状态
  const checkAuth = () => {
    const token = getAuthToken();
    setIsAuthenticated(!!token);
    return !!token;
  };

  // 管理员登录
  const handleLogin = async (values: { username: string; password: string }) => {
    setLoginLoading(true);
    try {
      const response = await axios.post('http://localhost:3007/api/v1/auth/login', {
        username: values.username,
        password: values.password
      });
      
      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        setIsAuthenticated(true);
        message.success('登录成功');
        loginForm.resetFields();
        // 登录成功后加载数据
        fetchPackages();
        fetchStats();
      }
    } catch (error: any) {
      console.error('登录失败:', error);
      message.error(error.response?.data?.detail || '登录失败');
    } finally {
      setLoginLoading(false);
    }
  };

  // 退出登录
  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    setPackages([]);
    setStats(null);
    message.success('已退出登录');
  };

  // API请求配置
  const getApiConfig = () => {
    const token = getAuthToken();
    return {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    };
  };

  // 获取套餐列表
  const fetchPackages = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:3007/api/v1/admin/packages', getApiConfig());
      setPackages(response.data);
      setFilteredPackages(response.data);
    } catch (error: any) {
      console.error('获取套餐列表失败:', error);
      message.error(error.response?.data?.detail || '获取套餐列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取统计信息
  const fetchStats = async () => {
    try {
      const response = await axios.get('http://localhost:3007/api/v1/admin/packages/stats', getApiConfig());
      setStats(response.data);
    } catch (error: any) {
      console.error('获取统计信息失败:', error);
    }
  };

  // 初始化数据
  useEffect(() => {
    if (checkAuth()) {
      fetchPackages();
      fetchStats();
    }
  }, []);

  // 搜索过滤
  useEffect(() => {
    if (searchText) {
      const filtered = packages.filter(pkg => 
        pkg.name.toLowerCase().includes(searchText.toLowerCase()) ||
        pkg.package_type.toLowerCase().includes(searchText.toLowerCase()) ||
        pkg.description?.toLowerCase().includes(searchText.toLowerCase())
      );
      setFilteredPackages(filtered);
    } else {
      setFilteredPackages(packages);
    }
  }, [searchText, packages]);

  // 创建套餐
  const handleCreate = async (values: any) => {
    try {
      await axios.post('http://localhost:3007/api/v1/admin/packages', values, getApiConfig());
      message.success('套餐创建成功');
      setShowCreateModal(false);
      form.resetFields();
      fetchPackages();
      fetchStats();
    } catch (error: any) {
      console.error('创建套餐失败:', error);
      message.error(error.response?.data?.detail || '创建套餐失败');
    }
  };

  // 更新套餐
  const handleUpdate = async (values: any) => {
    if (!editingPackage) return;
    
    try {
      await axios.put(`http://localhost:3007/api/v1/admin/packages/${editingPackage.id}`, values, getApiConfig());
      message.success('套餐更新成功');
      setShowEditModalVisible(false);
      setEditingPackage(null);
      editForm.resetFields();
      fetchPackages();
      fetchStats();
    } catch (error: any) {
      console.error('更新套餐失败:', error);
      message.error(error.response?.data?.detail || '更新套餐失败');
    }
  };

  // 切换套餐状态
  const handleToggleStatus = async (packageId: number) => {
    try {
      const response = await axios.post(`http://localhost:3007/api/v1/admin/packages/${packageId}/toggle-status`, {}, getApiConfig());
      message.success(response.data.message);
      fetchPackages();
      fetchStats();
    } catch (error: any) {
      console.error('切换套餐状态失败:', error);
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  // 删除套餐
  const handleDelete = async (packageId: number) => {
    try {
      const response = await axios.delete(`http://localhost:3007/api/v1/admin/packages/${packageId}`, getApiConfig());
      message.success(response.data.message);
      fetchPackages();
      fetchStats();
    } catch (error: any) {
      console.error('删除套餐失败:', error);
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  // 显示编辑模态框
  const showEditModal = (pkg: PaymentPackage) => {
    setEditingPackage(pkg);
    editForm.setFieldsValue({
      package_type: pkg.package_type,
      name: pkg.name,
      price: pkg.price,
      queries_count: pkg.queries_count,
      validity_days: pkg.validity_days,
      membership_type: pkg.membership_type,
      description: pkg.description,
      is_active: pkg.is_active,
      sort_order: pkg.sort_order
    });
    setShowEditModalVisible(true);
  };

  // 会员类型映射
  const membershipTypeMap = {
    free: { text: '免费版', color: 'default' },
    pro: { text: '专业版', color: 'blue' },
    premium: { text: '旗舰版', color: 'gold' }
  };

  // 表格列定义
  const columns = [
    {
      title: '排序',
      dataIndex: 'sort_order',
      key: 'sort_order',
      width: 80,
      sorter: (a: PaymentPackage, b: PaymentPackage) => a.sort_order - b.sort_order,
    },
    {
      title: '套餐名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: PaymentPackage) => (
        <Space>
          <GiftOutlined style={{ color: record.is_active ? '#52c41a' : '#d9d9d9' }} />
          <span style={{ fontWeight: 'bold' }}>{text}</span>
          {!record.is_active && <Badge status="default" text="已禁用" />}
        </Space>
      ),
    },
    {
      title: '套餐类型',
      dataIndex: 'package_type',
      key: 'package_type',
      render: (text: string) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => (
        <Text strong style={{ color: '#f50' }}>¥{price}</Text>
      ),
      sorter: (a: PaymentPackage, b: PaymentPackage) => a.price - b.price,
    },
    {
      title: '查询次数',
      dataIndex: 'queries_count',
      key: 'queries_count',
      render: (count: number) => count > 999 ? '无限制' : `${count}次`,
    },
    {
      title: '有效期',
      dataIndex: 'validity_days',
      key: 'validity_days',
      render: (days: number) => (
        days === 0 ? <Tag color="green">永久</Tag> : 
        <Tag color="orange">{days}天</Tag>
      ),
    },
    {
      title: '会员类型',
      dataIndex: 'membership_type',
      key: 'membership_type',
      render: (type: string) => {
        const config = membershipTypeMap[type as keyof typeof membershipTypeMap];
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean, record: PaymentPackage) => (
        <Switch 
          checked={isActive}
          onChange={() => handleToggleStatus(record.id)}
          checkedChildren="启用"
          unCheckedChildren="禁用"
        />
      ),
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
      sorter: (a: PaymentPackage, b: PaymentPackage) => 
        new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime(),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record: PaymentPackage) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedPackage(record);
              setShowDetail(true);
            }}
          >
            详情
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => showEditModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确认删除这个套餐？"
            description="删除后无法恢复，请谨慎操作"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 如果未认证，显示登录界面
  if (!isAuthenticated) {
    return (
      <div style={{ 
        padding: '24px', 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '60vh' 
      }}>
        <Card style={{ width: 400, textAlign: 'center' }}>
          <Title level={2}>
            <GiftOutlined /> 管理员登录
          </Title>
          <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
            请使用管理员账户登录以管理套餐配置
          </Text>
          
          <Form
            form={loginForm}
            layout="vertical"
            onFinish={handleLogin}
          >
            <Form.Item
              label="用户名"
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input placeholder="请输入管理员用户名" />
            </Form.Item>
            
            <Form.Item
              label="密码"
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password placeholder="请输入密码" />
            </Form.Item>
            
            <Form.Item>
              <Button 
                type="primary" 
                htmlType="submit" 
                loading={loginLoading}
                style={{ width: '100%' }}
              >
                登录
              </Button>
            </Form.Item>
          </Form>
          
          <Alert
            message="提示"
            description="请使用 admin 账户登录。如果没有账户，请联系系统管理员。"
            type="info"
            style={{ textAlign: 'left', marginTop: 16 }}
          />
        </Card>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>
          <GiftOutlined /> 套餐配置管理
        </Title>
        <Button 
          onClick={handleLogout}
          style={{ marginLeft: 'auto' }}
        >
          退出登录
        </Button>
      </div>

      {/* 统计卡片 */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总套餐数"
                value={stats.total_packages}
                prefix={<GiftOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="启用套餐"
                value={stats.active_packages}
                prefix={<StarOutlined />}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="禁用套餐"
                value={stats.inactive_packages}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="会员套餐"
                value={stats.membership_distribution.filter(m => m.membership_type !== 'free').reduce((sum, m) => sum + m.count, 0)}
                prefix={<CrownOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 操作栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="搜索套餐名称、类型或描述"
            allowClear
            style={{ width: 300 }}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setShowCreateModal(true)}
          >
            新增套餐
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              fetchPackages();
              fetchStats();
            }}
          >
            刷新
          </Button>
        </Space>
      </Card>

      {/* 套餐列表 */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredPackages}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 创建套餐模态框 */}
      <Modal
        title={<><PlusOutlined /> 新增套餐</>}
        open={showCreateModal}
        onCancel={() => {
          setShowCreateModal(false);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="套餐类型"
                name="package_type"
                rules={[{ required: true, message: '请输入套餐类型' }]}
              >
                <Input placeholder="如: monthly, yearly 等" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="套餐名称"
                name="name"
                rules={[{ required: true, message: '请输入套餐名称' }]}
              >
                <Input placeholder="如: 月度会员" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="价格"
                name="price"
                rules={[{ required: true, message: '请输入价格' }]}
              >
                <InputNumber
                  min={0}
                  max={9999}
                  precision={2}
                  style={{ width: '100%' }}
                  placeholder="0.00"
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="查询次数"
                name="queries_count"
                rules={[{ required: true, message: '请输入查询次数' }]}
              >
                <InputNumber
                  min={0}
                  max={99999}
                  style={{ width: '100%' }}
                  placeholder="999表示无限制"
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="有效天数"
                name="validity_days"
                rules={[{ required: true, message: '请输入有效天数' }]}
              >
                <InputNumber
                  min={0}
                  max={3650}
                  style={{ width: '100%' }}
                  placeholder="0表示永久有效"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="会员类型"
                name="membership_type"
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
                label="排序"
                name="sort_order"
                initialValue={0}
              >
                <InputNumber
                  min={0}
                  max={999}
                  style={{ width: '100%' }}
                  placeholder="数字越小排序越靠前"
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="套餐描述" name="description">
            <TextArea rows={3} placeholder="套餐功能描述" />
          </Form.Item>

          <Form.Item name="is_active" valuePropName="checked" initialValue={true}>
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            <span style={{ marginLeft: 8 }}>套餐状态</span>
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setShowCreateModal(false);
                form.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                创建套餐
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑套餐模态框 */}
      <Modal
        title={<><EditOutlined /> 编辑套餐</>}
        open={showEditModalVisible}
        onCancel={() => {
          setShowEditModalVisible(false);
          setEditingPackage(null);
          editForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleUpdate}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="套餐类型"
                name="package_type"
                rules={[{ required: true, message: '请输入套餐类型' }]}
              >
                <Input placeholder="如: monthly, yearly 等" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="套餐名称"
                name="name"
                rules={[{ required: true, message: '请输入套餐名称' }]}
              >
                <Input placeholder="如: 月度会员" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="价格"
                name="price"
                rules={[{ required: true, message: '请输入价格' }]}
              >
                <InputNumber
                  min={0}
                  max={9999}
                  precision={2}
                  style={{ width: '100%' }}
                  placeholder="0.00"
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="查询次数"
                name="queries_count"
                rules={[{ required: true, message: '请输入查询次数' }]}
              >
                <InputNumber
                  min={0}
                  max={99999}
                  style={{ width: '100%' }}
                  placeholder="999表示无限制"
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="有效天数"
                name="validity_days"
                rules={[{ required: true, message: '请输入有效天数' }]}
              >
                <InputNumber
                  min={0}
                  max={3650}
                  style={{ width: '100%' }}
                  placeholder="0表示永久有效"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="会员类型"
                name="membership_type"
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
                label="排序"
                name="sort_order"
              >
                <InputNumber
                  min={0}
                  max={999}
                  style={{ width: '100%' }}
                  placeholder="数字越小排序越靠前"
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="套餐描述" name="description">
            <TextArea rows={3} placeholder="套餐功能描述" />
          </Form.Item>

          <Form.Item name="is_active" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            <span style={{ marginLeft: 8 }}>套餐状态</span>
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setShowEditModalVisible(false);
                setEditingPackage(null);
                editForm.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                更新套餐
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 套餐详情抽屉 */}
      <Drawer
        title={<><EyeOutlined /> 套餐详情</>}
        placement="right"
        onClose={() => {
          setShowDetail(false);
          setSelectedPackage(null);
        }}
        open={showDetail}
        width={500}
      >
        {selectedPackage && (
          <div>
            <Descriptions column={1} bordered>
              <Descriptions.Item label="套餐ID">{selectedPackage.id}</Descriptions.Item>
              <Descriptions.Item label="套餐类型">{selectedPackage.package_type}</Descriptions.Item>
              <Descriptions.Item label="套餐名称">{selectedPackage.name}</Descriptions.Item>
              <Descriptions.Item label="价格">
                <Text strong style={{ color: '#f50', fontSize: '16px' }}>¥{selectedPackage.price}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="查询次数">
                {selectedPackage.queries_count > 999 ? '无限制' : `${selectedPackage.queries_count}次`}
              </Descriptions.Item>
              <Descriptions.Item label="有效期">
                {selectedPackage.validity_days === 0 ? '永久有效' : `${selectedPackage.validity_days}天`}
              </Descriptions.Item>
              <Descriptions.Item label="会员类型">
                <Tag color={membershipTypeMap[selectedPackage.membership_type].color}>
                  {membershipTypeMap[selectedPackage.membership_type].text}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Badge 
                  status={selectedPackage.is_active ? 'success' : 'default'} 
                  text={selectedPackage.is_active ? '启用' : '禁用'} 
                />
              </Descriptions.Item>
              <Descriptions.Item label="排序">{selectedPackage.sort_order}</Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {dayjs(selectedPackage.created_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="更新时间">
                {dayjs(selectedPackage.updated_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
            </Descriptions>

            {selectedPackage.description && (
              <div style={{ marginTop: 16 }}>
                <Title level={5}>套餐描述</Title>
                <div style={{ 
                  padding: 16, 
                  backgroundColor: '#f5f5f5', 
                  borderRadius: 6,
                  whiteSpace: 'pre-wrap' 
                }}>
                  {selectedPackage.description}
                </div>
              </div>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default PackageManagement;