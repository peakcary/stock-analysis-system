import React, { useState } from 'react';
import { Card, Form, Input, Button, Typography, Alert, Space, Tabs, message } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { useClientAuth } from '../contexts/ClientAuthContext';

const { Title, Text } = Typography;

type TabType = 'login' | 'register';

const ClientLoginPage: React.FC = () => {
  const { login, register } = useClientAuth();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('login');
  const [loginForm] = Form.useForm();
  const [registerForm] = Form.useForm();

  const handleLogin = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const success = await login(values.username, values.password);
      if (!success) {
        loginForm.setFields([
          {
            name: 'password',
            errors: ['用户名或密码错误']
          }
        ]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (values: { username: string; email: string; password: string; confirm: string }) => {
    if (values.password !== values.confirm) {
      registerForm.setFields([
        {
          name: 'confirm',
          errors: ['两次输入的密码不一致']
        }
      ]);
      return;
    }

    setLoading(true);
    try {
      const success = await register(values.username, values.email, values.password);
      if (success) {
        message.success('注册成功！正在跳转...');
        // Auto-switch to login tab after successful registration
        setTimeout(() => {
          setActiveTab('login');
          registerForm.resetFields();
        }, 1500);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '20px'
    }}>
      <Card
        style={{
          width: '100%',
          maxWidth: 450,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
          borderRadius: '16px',
          border: 'none'
        }}
        bodyStyle={{ padding: '40px' }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            fontSize: '48px',
            marginBottom: '16px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            💳
          </div>
          <Title level={2} style={{ margin: 0, color: '#333' }}>
            支付系统
          </Title>
          <Text type="secondary" style={{ fontSize: '16px' }}>
            股票分析查询服务
          </Text>
        </div>

        <Tabs
          activeKey={activeTab}
          onChange={(key) => setActiveTab(key as TabType)}
          items={[
            {
              key: 'login',
              label: '登录',
              children: (
                <Form
                  form={loginForm}
                  name="login"
                  onFinish={handleLogin}
                  size="large"
                  layout="vertical"
                >
                  <Form.Item
                    name="username"
                    rules={[{ required: true, message: '请输入用户名' }]}
                  >
                    <Input
                      prefix={<UserOutlined />}
                      placeholder="用户名"
                      style={{ borderRadius: '8px' }}
                    />
                  </Form.Item>

                  <Form.Item
                    name="password"
                    rules={[{ required: true, message: '请输入密码' }]}
                    style={{ marginBottom: 16 }}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="密码"
                      style={{ borderRadius: '8px' }}
                    />
                  </Form.Item>

                  <Form.Item style={{ marginBottom: 16 }}>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading}
                      block
                      style={{
                        height: '48px',
                        borderRadius: '8px',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        border: 'none',
                        fontSize: '16px',
                        fontWeight: 'bold'
                      }}
                    >
                      {loading ? '登录中...' : '登录'}
                    </Button>
                  </Form.Item>
                </Form>
              )
            },
            {
              key: 'register',
              label: '注册',
              children: (
                <Form
                  form={registerForm}
                  name="register"
                  onFinish={handleRegister}
                  size="large"
                  layout="vertical"
                >
                  <Form.Item
                    name="username"
                    rules={[
                      { required: true, message: '请输入用户名' },
                      { min: 3, message: '用户名至少3个字符' }
                    ]}
                  >
                    <Input
                      prefix={<UserOutlined />}
                      placeholder="用户名（至少3个字符）"
                      style={{ borderRadius: '8px' }}
                    />
                  </Form.Item>

                  <Form.Item
                    name="email"
                    rules={[
                      { required: true, message: '请输入邮箱' },
                      { type: 'email', message: '请输入有效的邮箱地址' }
                    ]}
                  >
                    <Input
                      prefix={<MailOutlined />}
                      placeholder="邮箱地址"
                      style={{ borderRadius: '8px' }}
                    />
                  </Form.Item>

                  <Form.Item
                    name="password"
                    rules={[
                      { required: true, message: '请输入密码' },
                      { min: 6, message: '密码至少6个字符' }
                    ]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="密码（至少6个字符）"
                      style={{ borderRadius: '8px' }}
                    />
                  </Form.Item>

                  <Form.Item
                    name="confirm"
                    rules={[{ required: true, message: '请确认密码' }]}
                    style={{ marginBottom: 16 }}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="确认密码"
                      style={{ borderRadius: '8px' }}
                    />
                  </Form.Item>

                  <Form.Item style={{ marginBottom: 0 }}>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading}
                      block
                      style={{
                        height: '48px',
                        borderRadius: '8px',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        border: 'none',
                        fontSize: '16px',
                        fontWeight: 'bold'
                      }}
                    >
                      {loading ? '注册中...' : '注册'}
                    </Button>
                  </Form.Item>
                </Form>
              )
            }
          ]}
        />

        <Alert
          message="提示"
          description="注册后您可以选择升级会员包以获得更多查询次数。初次使用可通过支付0.01元进行体验。"
          type="info"
          showIcon
          style={{
            marginTop: 24,
            borderRadius: '8px',
            background: 'rgba(24, 144, 255, 0.05)',
            border: '1px solid rgba(24, 144, 255, 0.2)'
          }}
        />

        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            © 2025 股票分析系统 v2.0
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default ClientLoginPage;
