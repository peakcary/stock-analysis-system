import React, { useState } from 'react';
import { Form, Input, Button, Card, message, Spin, Divider } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import api from '../utils/api';
import '../styles/LoginPage.css';

interface LoginPageProps {
  onLogin: (username: string, password: string) => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLogin }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const [registerLoading, setRegisterLoading] = useState(false);

  // 处理登录
  const handleLogin = async (values: any) => {
    try {
      setLoading(true);
      await onLogin(values.username, values.password);
      form.resetFields();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  // 处理注册
  const handleRegister = async (values: any) => {
    if (values.password !== values.confirmPassword) {
      message.error('两次输入的密码不一致');
      return;
    }

    try {
      setRegisterLoading(true);
      await api.post('/auth/register', {
        username: values.username,
        email: values.email,
        password: values.password,
      });

      message.success('注册成功！请用新账号登录');
      setIsRegister(false);
      form.resetFields();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '注册失败，请重试');
    } finally {
      setRegisterLoading(false);
    }
  };

  return (
    <div className="login-page-container">
      <div className="login-background"></div>

      <div className="login-content">
        <Card
          className="login-card"
          style={{
            width: '100%',
            maxWidth: '420px',
            borderRadius: '12px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
          }}
        >
          {/* 标题 */}
          <div style={{ textAlign: 'center', marginBottom: '32px' }}>
            <h1 style={{ fontSize: '24px', fontWeight: 'bold', margin: '0 0 8px 0' }}>
              💳 客户端支付系统
            </h1>
            <p style={{ color: '#999', margin: 0, fontSize: '14px' }}>
              {isRegister ? '创建新账户' : '登录您的账户'}
            </p>
          </div>

          {/* 登录表单 */}
          {!isRegister ? (
            <Spin spinning={loading}>
              <Form
                form={form}
                layout="vertical"
                onFinish={handleLogin}
                autoComplete="off"
              >
                <Form.Item
                  name="username"
                  rules={[{ required: true, message: '请输入用户名' }]}
                  label={<span style={{ fontWeight: '500' }}>用户名</span>}
                >
                  <Input
                    prefix={<UserOutlined style={{ color: '#999' }} />}
                    placeholder="输入用户名"
                    size="large"
                    style={{ borderRadius: '6px' }}
                  />
                </Form.Item>

                <Form.Item
                  name="password"
                  rules={[{ required: true, message: '请输入密码' }]}
                  label={<span style={{ fontWeight: '500' }}>密码</span>}
                >
                  <Input.Password
                    prefix={<LockOutlined style={{ color: '#999' }} />}
                    placeholder="输入密码"
                    size="large"
                    style={{ borderRadius: '6px' }}
                  />
                </Form.Item>

                <Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    block
                    size="large"
                    loading={loading}
                    style={{
                      borderRadius: '6px',
                      fontWeight: '500',
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      border: 'none',
                    }}
                  >
                    登 录
                  </Button>
                </Form.Item>

                <Divider style={{ margin: '16px 0' }}>或</Divider>

                <p style={{ textAlign: 'center', margin: 0 }}>
                  还没有账户？
                  <Button
                    type="link"
                    onClick={() => {
                      setIsRegister(true);
                      form.resetFields();
                    }}
                    style={{ padding: '0 4px' }}
                  >
                    立即注册
                  </Button>
                </p>
              </Form>
            </Spin>
          ) : (
            /* 注册表单 */
            <Spin spinning={registerLoading}>
              <Form
                form={form}
                layout="vertical"
                onFinish={handleRegister}
                autoComplete="off"
              >
                <Form.Item
                  name="username"
                  rules={[{ required: true, message: '请输入用户名' }]}
                  label={<span style={{ fontWeight: '500' }}>用户名</span>}
                >
                  <Input
                    prefix={<UserOutlined style={{ color: '#999' }} />}
                    placeholder="输入用户名（3-20字符）"
                    size="large"
                    style={{ borderRadius: '6px' }}
                  />
                </Form.Item>

                <Form.Item
                  name="email"
                  rules={[
                    { required: true, message: '请输入邮箱地址' },
                    { type: 'email', message: '请输入有效的邮箱地址' },
                  ]}
                  label={<span style={{ fontWeight: '500' }}>邮箱</span>}
                >
                  <Input
                    prefix={<MailOutlined style={{ color: '#999' }} />}
                    placeholder="输入邮箱地址"
                    size="large"
                    type="email"
                    style={{ borderRadius: '6px' }}
                  />
                </Form.Item>

                <Form.Item
                  name="password"
                  rules={[{ required: true, message: '请输入密码' }]}
                  label={<span style={{ fontWeight: '500' }}>密码</span>}
                >
                  <Input.Password
                    prefix={<LockOutlined style={{ color: '#999' }} />}
                    placeholder="输入密码（至少6位）"
                    size="large"
                    style={{ borderRadius: '6px' }}
                  />
                </Form.Item>

                <Form.Item
                  name="confirmPassword"
                  rules={[{ required: true, message: '请确认密码' }]}
                  label={<span style={{ fontWeight: '500' }}>确认密码</span>}
                >
                  <Input.Password
                    prefix={<LockOutlined style={{ color: '#999' }} />}
                    placeholder="再次输入密码"
                    size="large"
                    style={{ borderRadius: '6px' }}
                  />
                </Form.Item>

                <Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    block
                    size="large"
                    loading={registerLoading}
                    style={{
                      borderRadius: '6px',
                      fontWeight: '500',
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      border: 'none',
                    }}
                  >
                    注 册
                  </Button>
                </Form.Item>

                <Divider style={{ margin: '16px 0' }}>或</Divider>

                <p style={{ textAlign: 'center', margin: 0 }}>
                  已有账户？
                  <Button
                    type="link"
                    onClick={() => {
                      setIsRegister(false);
                      form.resetFields();
                    }}
                    style={{ padding: '0 4px' }}
                  >
                    返回登录
                  </Button>
                </p>
              </Form>
            </Spin>
          )}

          {/* 底部提示 */}
          <Divider style={{ margin: '24px 0 16px 0' }} />
          <p style={{ textAlign: 'center', fontSize: '12px', color: '#999', margin: 0 }}>
            测试账号: user1 / 123456
          </p>
        </Card>
      </div>
    </div>
  );
};

export default LoginPage;
