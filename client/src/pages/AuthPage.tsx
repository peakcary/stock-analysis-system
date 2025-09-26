import React, { useState } from 'react';
import { 
  Card, Form, Input, Button, Tabs, Checkbox, Space, 
  Typography, message
} from 'antd';
import { motion } from 'framer-motion';
import { 
  LockOutlined, UserOutlined, EyeOutlined, EyeInvisibleOutlined,
  SafetyCertificateOutlined
} from '@ant-design/icons';
import { authManager } from '../utils/auth';

const { Title, Text, Link } = Typography;
const { TabPane } = Tabs;

interface AuthPageProps {
  onLoginSuccess: (user: any) => void;
}

export const AuthPage: React.FC<AuthPageProps> = ({ onLoginSuccess }) => {
  const [authType, setAuthType] = useState<'login' | 'register'>('login');
  const [loading, setLoading] = useState(false);

  // 登录处理 - 连接真实API
  const handleLogin = async (values: any) => {
    setLoading(true);
    try {
      const result = await authManager.login(values.username, values.password);
      
      if (result.success && result.user) {
        message.success('登录成功！');
        onLoginSuccess(result.user);
      } else if (result.error) {
        // 使用用户友好的错误信息
        const userFriendlyMessage = authManager.getErrorMessage(result.error);
        message.error(userFriendlyMessage);
      } else {
        message.error('登录失败，请稍后重试');
      }
    } catch (error) {
      console.error('登录异常:', error);
      message.error('登录过程中发生异常，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 注册处理
  const handleRegister = async (values: any) => {
    setLoading(true);
    try {
      const result = await authManager.register(values.username, values.email, values.password);

      if (result.success && result.user) {
        message.success('注册成功！请登录');
        setAuthType('login');
      } else if (result.error) {
        // 使用用户友好的错误信息
        const userFriendlyMessage = authManager.getErrorMessage(result.error);
        message.error(userFriendlyMessage);
      } else {
        message.error('注册失败，请稍后重试');
      }
    } catch (error) {
      console.error('注册异常:', error);
      message.error('注册过程中发生异常，请稍后重试');
    } finally {
      setLoading(false);
    }
  };


  return (
    <div style={{ 
      minHeight: '100vh',
      background: 'var(--primary-gradient)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        style={{ width: '100%', maxWidth: '420px' }}
      >
        <Card 
          style={{ 
            borderRadius: '20px',
            boxShadow: '0 25px 50px rgba(0,0,0,0.15)',
            overflow: 'hidden',
            background: 'rgba(255,255,255,0.95)',
            backdropFilter: 'blur(10px)'
          }}
          bodyStyle={{ padding: 0 }}
        >
          {/* 头部品牌区域 */}
          <div style={{ 
            padding: '40px 40px 30px',
            textAlign: 'center',
            background: 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)'
          }}>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring' }}
              style={{ fontSize: '64px', marginBottom: '16px' }}
            >
              📈
            </motion.div>
            <Title level={2} style={{ 
              margin: 0, 
              color: '#1f2937',
              fontSize: '28px',
              fontWeight: '700'
            }}>
              智能股票分析
            </Title>
            <Text style={{ 
              color: '#6b7280', 
              fontSize: '16px',
              display: 'block',
              marginTop: '8px'
            }}>
              专业的股票投资分析平台
            </Text>
            
          </div>
          
          {/* 登录/注册表单区域 */}
          <div style={{ padding: '20px 40px 40px' }}>
            <Tabs
              activeKey={authType}
              onChange={(key) => setAuthType(key as 'login' | 'register')}
              centered
              size="large"
              style={{ marginBottom: '20px' }}
            >
              <TabPane tab="登录" key="login">
                <LoginForm onLogin={handleLogin} loading={loading} />
              </TabPane>
              <TabPane tab="注册" key="register">
                <RegisterForm 
                  onRegister={handleRegister} 
                  loading={loading}
                />
              </TabPane>
            </Tabs>
          </div>
        </Card>
        
        {/* 底部链接 */}
        <div style={{ 
          textAlign: 'center', 
          marginTop: '30px',
          color: 'rgba(255,255,255,0.8)'
        }}>
          <Space size="large">
            <Link style={{ color: 'rgba(255,255,255,0.9)' }}>用户协议</Link>
            <Link style={{ color: 'rgba(255,255,255,0.9)' }}>隐私政策</Link>
            <Link style={{ color: 'rgba(255,255,255,0.9)' }}>帮助中心</Link>
          </Space>
        </div>
      </motion.div>
    </div>
  );
};

// 登录表单组件
const LoginForm: React.FC<{
  onLogin: (values: any) => void;
  loading: boolean;
}> = ({ onLogin, loading }) => {
  return (
    <Form layout="vertical" size="large" onFinish={onLogin}>
      <Form.Item 
        name="username"
        rules={[{ required: true, message: '请输入用户名' }]}
      >
        <Input 
          prefix={<UserOutlined style={{ color: '#9ca3af' }} />}
          placeholder="用户名"
          style={{ 
            height: '50px',
            fontSize: '16px',
            borderRadius: '12px',
            border: '2px solid #f3f4f6',
            boxShadow: 'none'
          }}
        />
      </Form.Item>
      
      <Form.Item 
        name="password"
        rules={[{ required: true, message: '请输入密码' }]}
      >
        <Input.Password 
          prefix={<LockOutlined style={{ color: '#9ca3af' }} />}
          placeholder="密码"
          iconRender={(visible) => (visible ? <EyeOutlined /> : <EyeInvisibleOutlined />)}
          style={{ 
            height: '50px',
            fontSize: '16px',
            borderRadius: '12px',
            border: '2px solid #f3f4f6'
          }}
        />
      </Form.Item>
      
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '24px'
      }}>
        <Checkbox>记住登录状态</Checkbox>
        <Link style={{ color: 'var(--primary-color)' }}>忘记密码？</Link>
      </div>
      
      <Button 
        type="primary" 
        htmlType="submit"
        loading={loading}
        block 
        className="gradient-button"
        style={{ 
          height: '50px',
          fontSize: '16px',
          fontWeight: '600',
          borderRadius: '12px',
          marginBottom: '20px'
        }}
      >
        立即登录
      </Button>
    </Form>
  );
};

// 注册表单组件
const RegisterForm: React.FC<{
  onRegister: (values: any) => void;
  loading: boolean;
}> = ({ onRegister, loading }) => {
  return (
    <Form layout="vertical" size="large" onFinish={onRegister}>
      <Form.Item
        name="username"
        rules={[
          { required: true, message: '请输入用户名' },
          { min: 3, message: '用户名至少3位' },
          { max: 20, message: '用户名最多20位' }
        ]}
      >
        <Input
          prefix={<UserOutlined style={{ color: '#9ca3af' }} />}
          placeholder="用户名"
          style={{
            height: '50px',
            fontSize: '16px',
            borderRadius: '12px',
            border: '2px solid #f3f4f6',
            boxShadow: 'none'
          }}
        />
      </Form.Item>

      <Form.Item
        name="email"
        rules={[
          { required: true, message: '请输入邮箱地址' },
          { type: 'email', message: '请输入正确的邮箱格式' }
        ]}
      >
        <Input
          prefix={<span style={{ color: '#9ca3af' }}>@</span>}
          placeholder="邮箱地址"
          style={{
            height: '50px',
            fontSize: '16px',
            borderRadius: '12px',
            border: '2px solid #f3f4f6',
            boxShadow: 'none'
          }}
        />
      </Form.Item>
      
      <Form.Item 
        name="password"
        rules={[
          { required: true, message: '请输入密码' },
          { min: 6, message: '密码至少6位' }
        ]}
      >
        <Input.Password 
          prefix={<LockOutlined style={{ color: '#9ca3af' }} />}
          placeholder="密码"
          iconRender={(visible) => (visible ? <EyeOutlined /> : <EyeInvisibleOutlined />)}
          style={{ 
            height: '50px',
            fontSize: '16px',
            borderRadius: '12px',
            border: '2px solid #f3f4f6'
          }}
        />
      </Form.Item>
      
      <Form.Item 
        name="confirmPassword"
        rules={[
          { required: true, message: '请确认密码' },
          ({ getFieldValue }) => ({
            validator(_, value) {
              if (!value || getFieldValue('password') === value) {
                return Promise.resolve();
              }
              return Promise.reject(new Error('两次输入的密码不一致'));
            },
          }),
        ]}
      >
        <Input.Password 
          prefix={<SafetyCertificateOutlined style={{ color: '#9ca3af' }} />}
          placeholder="确认密码"
          iconRender={(visible) => (visible ? <EyeOutlined /> : <EyeInvisibleOutlined />)}
          style={{ 
            height: '50px',
            fontSize: '16px',
            borderRadius: '12px',
            border: '2px solid #f3f4f6'
          }}
        />
      </Form.Item>
      
      <Form.Item 
        name="agreement"
        valuePropName="checked"
        rules={[{ required: true, message: '请同意用户协议' }]}
      >
        <Checkbox>
          我已阅读并同意 
          <Link style={{ marginLeft: '4px' }}>用户服务协议</Link> 和 
          <Link style={{ marginLeft: '4px' }}>隐私政策</Link>
        </Checkbox>
      </Form.Item>
      
      <Button 
        type="primary" 
        htmlType="submit"
        loading={loading}
        block 
        className="gradient-button"
        style={{ 
          height: '50px',
          fontSize: '16px',
          fontWeight: '600',
          borderRadius: '12px',
          marginTop: '12px'
        }}
      >
        立即注册
      </Button>
    </Form>
  );
};

export default AuthPage;