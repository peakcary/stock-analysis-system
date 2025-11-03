import React, { useState } from 'react';
import { Card, Form, Input, Button, Row, Col, Avatar, Divider, Space, message, Modal, Spin } from 'antd';
import { UserOutlined, MailOutlined, LockOutlined, LogoutOutlined } from '@ant-design/icons';
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

interface UserCenterPageProps {
  userInfo: UserInfo | null;
  onLogout: () => void;
}

const UserCenterPage: React.FC<UserCenterPageProps> = ({ userInfo, onLogout }) => {
  const [form] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);

  // 会员类型中文
  const getMembershipLabel = (type: string) => {
    switch (type) {
      case 'premium':
        return '高级会员';
      case 'pro':
        return '专业版';
      case 'free_trial':
        return '免费试用';
      default:
        return '免费';
    }
  };

  // 会员类型颜色
  const getMembershipColor = (type: string) => {
    switch (type) {
      case 'premium':
        return '#52c41a';
      case 'pro':
        return '#faad14';
      default:
        return '#d9d9d9';
    }
  };

  // 更新用户信息
  const handleUpdateProfile = async (values: any) => {
    try {
      setLoading(true);
      const response = await api.put(`/auth/users/${userInfo?.id}`, {
        email: values.email,
      });
      message.success('用户信息更新成功');
      // 更新 localStorage
      const updatedUser = { ...userInfo, ...response.data };
      localStorage.setItem('client_system_user', JSON.stringify(updatedUser));
    } catch (error: any) {
      message.error(error.response?.data?.detail || '更新失败');
    } finally {
      setLoading(false);
    }
  };

  // 修改密码
  const handleChangePassword = async (values: any) => {
    if (values.newPassword !== values.confirmPassword) {
      message.error('两次输入的新密码不一致');
      return;
    }

    try {
      setPasswordLoading(true);
      await api.post(`/auth/change-password`, {
        old_password: values.oldPassword,
        new_password: values.newPassword,
      });
      message.success('密码修改成功，请重新登录');
      setTimeout(() => {
        onLogout();
      }, 1000);
      passwordForm.resetFields();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '密码修改失败');
    } finally {
      setPasswordLoading(false);
    }
  };

  // 删除账户
  const handleDeleteAccount = () => {
    Modal.confirm({
      title: '确认删除账户',
      content: '删除账户是不可逆的操作，所有数据将被清空。确认删除吗？',
      okText: '确认删除',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          setLoading(true);
          await api.delete(`/auth/users/${userInfo?.id}`);
          message.success('账户已删除');
          onLogout();
        } catch (error: any) {
          message.error(error.response?.data?.detail || '删除失败');
        } finally {
          setLoading(false);
        }
      },
    });
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
        {/* 用户信息卡片 */}
        <Card
          style={{
            marginBottom: '24px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
          }}
          bodyStyle={{ padding: '32px' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '24px', marginBottom: '32px' }}>
            <Avatar
              size={80}
              icon={<UserOutlined />}
              style={{
                backgroundColor: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              }}
            />
            <div>
              <h2 style={{ margin: '0 0 8px 0', fontSize: '24px', fontWeight: 'bold' }}>
                {userInfo?.username}
              </h2>
              <p style={{ margin: '0 0 8px 0', color: '#999', fontSize: '14px' }}>
                {userInfo?.email}
              </p>
              <div style={{
                display: 'inline-block',
                padding: '4px 12px',
                background: getMembershipColor(userInfo?.membership_type || 'free'),
                color: 'white',
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: 'bold',
              }}>
                {getMembershipLabel(userInfo?.membership_type || 'free')}
              </div>
            </div>
          </div>

          {/* 账户统计 */}
          <Divider />
          <Row gutter={[32, 32]}>
            <Col xs={24} sm={8}>
              <div>
                <div style={{ color: '#999', fontSize: '12px', marginBottom: '8px' }}>
                  账户ID
                </div>
                <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                  #{userInfo?.id}
                </div>
              </div>
            </Col>
            <Col xs={24} sm={8}>
              <div>
                <div style={{ color: '#999', fontSize: '12px', marginBottom: '8px' }}>
                  剩余查询次数
                </div>
                <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#1890ff' }}>
                  {userInfo?.queries_remaining} / {userInfo?.queries_count}
                </div>
              </div>
            </Col>
            <Col xs={24} sm={8}>
              <div>
                <div style={{ color: '#999', fontSize: '12px', marginBottom: '8px' }}>
                  注册时间
                </div>
                <div style={{ fontSize: '14px' }}>
                  {userInfo?.created_at ? new Date(userInfo.created_at).toLocaleDateString('zh-CN') : '-'}
                </div>
              </div>
            </Col>
          </Row>
        </Card>

        {/* 编辑个人信息 */}
        <Card
          title={<span style={{ fontWeight: 'bold', fontSize: '16px' }}>编辑个人信息</span>}
          style={{
            marginBottom: '24px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
          }}
          bodyStyle={{ padding: '24px' }}
        >
          <Spin spinning={loading}>
            <Form
              form={form}
              layout="vertical"
              initialValues={{
                username: userInfo?.username,
                email: userInfo?.email,
              }}
              onFinish={handleUpdateProfile}
            >
              <Row gutter={[24, 24]}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label={<span style={{ fontWeight: '500' }}>用户名</span>}
                    name="username"
                  >
                    <Input
                      prefix={<UserOutlined />}
                      disabled
                      style={{ borderRadius: '6px' }}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label={<span style={{ fontWeight: '500' }}>邮箱</span>}
                    name="email"
                    rules={[
                      { required: true, message: '请输入邮箱地址' },
                      { type: 'email', message: '请输入有效的邮箱地址' },
                    ]}
                  >
                    <Input
                      prefix={<MailOutlined />}
                      placeholder="输入邮箱地址"
                      style={{ borderRadius: '6px' }}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  style={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    border: 'none',
                    borderRadius: '6px',
                  }}
                >
                  保存更改
                </Button>
              </Form.Item>
            </Form>
          </Spin>
        </Card>

        {/* 修改密码 */}
        <Card
          title={<span style={{ fontWeight: 'bold', fontSize: '16px' }}>修改密码</span>}
          style={{
            marginBottom: '24px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
          }}
          bodyStyle={{ padding: '24px' }}
        >
          <Spin spinning={passwordLoading}>
            <Form
              form={passwordForm}
              layout="vertical"
              onFinish={handleChangePassword}
            >
              <Row gutter={[24, 24]}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label={<span style={{ fontWeight: '500' }}>当前密码</span>}
                    name="oldPassword"
                    rules={[{ required: true, message: '请输入当前密码' }]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="输入当前密码"
                      style={{ borderRadius: '6px' }}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={[24, 24]}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label={<span style={{ fontWeight: '500' }}>新密码</span>}
                    name="newPassword"
                    rules={[
                      { required: true, message: '请输入新密码' },
                      { min: 6, message: '新密码至少6位' },
                    ]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="输入新密码（至少6位）"
                      style={{ borderRadius: '6px' }}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label={<span style={{ fontWeight: '500' }}>确认新密码</span>}
                    name="confirmPassword"
                    rules={[{ required: true, message: '请确认新密码' }]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="再次输入新密码"
                      style={{ borderRadius: '6px' }}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={passwordLoading}
                  style={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    border: 'none',
                    borderRadius: '6px',
                  }}
                >
                  修改密码
                </Button>
              </Form.Item>
            </Form>
          </Spin>
        </Card>

        {/* 账户操作 */}
        <Card
          title={<span style={{ fontWeight: 'bold', fontSize: '16px' }}>账户操作</span>}
          style={{
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
          }}
          bodyStyle={{ padding: '24px' }}
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <p style={{ color: '#999', fontSize: '12px', marginBottom: '12px' }}>
                点击下面的按钮退出登录
              </p>
              <Button
                icon={<LogoutOutlined />}
                onClick={onLogout}
                style={{ borderRadius: '6px' }}
              >
                退出登录
              </Button>
            </div>

            <Divider style={{ margin: '16px 0' }} />

            <div>
              <p style={{ color: '#999', fontSize: '12px', marginBottom: '12px' }}>
                删除账户是不可逆的操作，请谨慎操作
              </p>
              <Button
                danger
                onClick={handleDeleteAccount}
                style={{ borderRadius: '6px' }}
              >
                删除账户
              </Button>
            </div>
          </Space>
        </Card>
      </div>
    </div>
  );
};

export default UserCenterPage;
