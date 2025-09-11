import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Input, Space, message, Modal, Form,
  Select, Tag, Row, Col, Popconfirm, Badge,
  Typography, Descriptions, Tooltip, Switch
} from 'antd';
import {
  UserOutlined, SearchOutlined, PlusOutlined, EditOutlined,
  DeleteOutlined, EyeOutlined, CrownOutlined, KeyOutlined,
  UnlockOutlined, LockOutlined, ReloadOutlined
} from '@ant-design/icons';
import { adminApiClient } from '../../../shared/admin-auth';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;

interface AdminUser {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role: string;
  is_active: boolean;
  is_superuser: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
}

const AdminManagement: React.FC = () => {
  const [admins, setAdmins] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [selectedRole, setSelectedRole] = useState<string>('');
  const [adminModalVisible, setAdminModalVisible] = useState(false);
  const [editingAdmin, setEditingAdmin] = useState<AdminUser | null>(null);
  const [form] = Form.useForm();
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });

  // 获取管理员列表
  const fetchAdmins = async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const params: any = {
        skip: (page - 1) * pageSize,
        limit: pageSize
      };
      
      if (searchText) {
        params.search = searchText;
      }
      
      if (selectedRole) {
        params.role = selectedRole;
      }

      const response = await adminApiClient.get('/api/v1/admin/admins', {
        params
      });

      setAdmins(response.data.admins || []);
      setPagination({
        current: page,
        pageSize,
        total: response.data.total
      });
    } catch (error) {
      console.error('获取管理员列表失败:', error);
      message.error('获取管理员列表失败');
      // 使用模拟数据
      const mockAdmins = [
        {
          id: 1,
          username: 'superadmin',
          email: 'super@example.com',
          full_name: '超级管理员',
          role: 'super_admin',
          is_active: true,
          is_superuser: true,
          last_login: '2024-08-24T10:00:00Z',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-08-24T00:00:00Z'
        },
        {
          id: 2,
          username: 'admin',
          email: 'admin@example.com',
          full_name: '普通管理员',
          role: 'admin',
          is_active: true,
          is_superuser: false,
          last_login: '2024-08-24T09:30:00Z',
          created_at: '2024-02-01T00:00:00Z',
          updated_at: '2024-08-24T09:30:00Z'
        }
      ];
      setAdmins(mockAdmins);
    } finally {
      setLoading(false);
    }
  };

  // 创建/更新管理员
  const handleSaveAdmin = async (values: any) => {
    try {
      if (editingAdmin) {
        // 更新管理员
        await adminApiClient.put(`/api/v1/admin/admins/${editingAdmin.id}`, values);
        message.success('管理员更新成功');
      } else {
        // 创建管理员
        await adminApiClient.post('/api/v1/admin/admins', values);
        message.success('管理员创建成功');
      }
      setAdminModalVisible(false);
      setEditingAdmin(null);
      form.resetFields();
      fetchAdmins();
    } catch (error) {
      console.error('保存管理员失败:', error);
      message.error('保存管理员失败');
    }
  };

  // 删除管理员
  const handleDeleteAdmin = async (adminId: number) => {
    try {
      await adminApiClient.delete(`/api/v1/admin/admins/${adminId}`);
      message.success('管理员删除成功');
      fetchAdmins();
    } catch (error) {
      console.error('删除管理员失败:', error);
      message.error('删除管理员失败');
    }
  };

  // 重置密码
  const handleResetPassword = async (adminId: number) => {
    const newPassword = 'admin123';
    try {
      await adminApiClient.post(`/api/v1/admin/admins/${adminId}/reset-password?new_password=${newPassword}`, {});
      message.success(`密码重置成功，新密码: ${newPassword}`);
    } catch (error) {
      console.error('重置密码失败:', error);
      message.error('重置密码失败');
    }
  };

  // 切换管理员状态
  const handleToggleStatus = async (adminId: number) => {
    try {
      await adminApiClient.post(`/api/v1/admin/admins/${adminId}/toggle-status`, {});
      message.success('管理员状态切换成功');
      fetchAdmins();
    } catch (error) {
      console.error('切换状态失败:', error);
      message.error('切换状态失败');
    }
  };

  useEffect(() => {
    fetchAdmins();
  }, []);

  // 角色标签配置
  const getRoleTag = (role: string) => {
    const configs = {
      super_admin: { color: 'red', text: '超级管理员' },
      admin: { color: 'blue', text: '普通管理员' },
      customer_service: { color: 'green', text: '客服' },
      data_analyst: { color: 'orange', text: '数据分析师' }
    };
    const config = configs[role as keyof typeof configs] || { color: 'default', text: role };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

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
      render: (text: string, record: AdminUser) => (
        <Space>
          <UserOutlined />
          <Text strong>{text}</Text>
          {record.is_superuser && <Tag color="red">超级管理员</Tag>}
        </Space>
      ),
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '姓名',
      dataIndex: 'full_name',
      key: 'full_name',
      render: (text: string) => text || '-',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => getRoleTag(role),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Badge
          status={isActive ? 'success' : 'error'}
          text={isActive ? '正常' : '禁用'}
        />
      ),
    },
    {
      title: '最后登录',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (date: string) => date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '从未登录',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: AdminUser) => (
        <Space>
          <Tooltip title="编辑管理员">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => {
                setEditingAdmin(record);
                form.setFieldsValue(record);
                setAdminModalVisible(true);
              }}
            />
          </Tooltip>
          <Tooltip title="重置密码">
            <Popconfirm
              title="确定要重置此管理员的密码吗？"
              onConfirm={() => handleResetPassword(record.id)}
            >
              <Button type="text" icon={<KeyOutlined />} />
            </Popconfirm>
          </Tooltip>
          <Tooltip title={record.is_active ? '禁用' : '启用'}>
            <Popconfirm
              title={`确定要${record.is_active ? '禁用' : '启用'}此管理员吗？`}
              onConfirm={() => handleToggleStatus(record.id)}
            >
              <Button 
                type="text" 
                icon={record.is_active ? <LockOutlined /> : <UnlockOutlined />}
              />
            </Popconfirm>
          </Tooltip>
          {!record.is_superuser && (
            <Popconfirm
              title="确定要删除此管理员吗？"
              onConfirm={() => handleDeleteAdmin(record.id)}
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
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: '#1f2937' }}>
          管理员账户管理
        </Title>
        <Text type="secondary" style={{ fontSize: '14px' }}>
          管理后台管理员账户，包括权限分配、账户状态和密码管理
        </Text>
      </div>

      {/* 工具栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Search
              placeholder="搜索用户名或邮箱"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onSearch={() => fetchAdmins()}
              allowClear
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="筛选角色"
              value={selectedRole}
              onChange={setSelectedRole}
              allowClear
              style={{ width: '100%' }}
            >
              <Option value="">全部</Option>
              <Option value="super_admin">超级管理员</Option>
              <Option value="admin">普通管理员</Option>
              <Option value="customer_service">客服</Option>
              <Option value="data_analyst">数据分析师</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setEditingAdmin(null);
                form.resetFields();
                setAdminModalVisible(true);
              }}
              block
            >
              新增管理员
            </Button>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => fetchAdmins()}
              block
            >
              刷新数据
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 管理员表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={admins}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} 共 ${total} 条`,
            onChange: (page, pageSize) => {
              fetchAdmins(page, pageSize);
            }
          }}
          scroll={{ x: 'max-content' }}
        />
      </Card>

      {/* 管理员编辑弹窗 */}
      <Modal
        title={editingAdmin ? '编辑管理员' : '新增管理员'}
        open={adminModalVisible}
        onCancel={() => {
          setAdminModalVisible(false);
          setEditingAdmin(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveAdmin}
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
          
          <Form.Item
            name="full_name"
            label="姓名"
          >
            <Input placeholder="真实姓名" />
          </Form.Item>
          
          {!editingAdmin && (
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
                name="role"
                label="角色"
                rules={[{ required: true, message: '请选择角色' }]}
              >
                <Select placeholder="选择角色">
                  <Option value="admin">普通管理员</Option>
                  <Option value="customer_service">客服</Option>
                  <Option value="data_analyst">数据分析师</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="is_active"
                label="账户状态"
                valuePropName="checked"
                initialValue={true}
              >
                <Switch 
                  checkedChildren="启用" 
                  unCheckedChildren="禁用" 
                />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
};

export default AdminManagement;