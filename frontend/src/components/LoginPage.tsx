import React, { useState } from 'react';
import { Card, Form, Input, Button, Typography, Alert, Space } from 'antd';
import { UserOutlined, LockOutlined, SettingOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text } = Typography;

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const handleLogin = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const success = await login(values.username, values.password);
      if (!success) {
        form.setFields([
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
          maxWidth: 400,
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
            <SettingOutlined />
          </div>
          <Title level={2} style={{ margin: 0, color: '#333' }}>
            后台管理系统
          </Title>
          <Text type="secondary" style={{ fontSize: '16px' }}>
            股票分析系统管理平台
          </Text>
        </div>

        <Form
          form={form}
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
              placeholder="管理员用户名"
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
              placeholder="管理员密码"
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

        <Alert
          message="管理员账户信息"
          description={
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <div>
                <Text strong>用户名：</Text>
                <Text code>admin</Text>
              </div>
              <div>
                <Text strong>密码：</Text>
                <Text code>admin123</Text>
              </div>
            </Space>
          }
          type="info"
          showIcon
          style={{
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

export default LoginPage;