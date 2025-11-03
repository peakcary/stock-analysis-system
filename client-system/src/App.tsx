import React, { useState, useEffect } from 'react';
import { Layout, Menu, Modal, message, Spin, Badge, Avatar, Dropdown } from 'antd';
import {
  UserOutlined, LogoutOutlined, HistoryOutlined,
  CreditCardOutlined, DashboardOutlined
} from '@ant-design/icons';
import api from './utils/api';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import PaymentPage from './pages/PaymentPage';
import OrderHistoryPage from './pages/OrderHistoryPage';
import UserCenterPage from './pages/UserCenterPage';
import './App.css';

const { Header, Sider, Content } = Layout;

interface UserInfo {
  id: number;
  username: string;
  email: string;
  membership_type: string;
  queries_remaining: number;
  queries_count: number;
  created_at: string;
}

const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'payment' | 'orders' | 'center'>('dashboard');
  const [collapsed, setCollapsed] = useState(false);

  // 初始化 - 检查已登录状态
  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = localStorage.getItem('client_system_token');
        const userStr = localStorage.getItem('client_system_user');

        if (token && userStr) {
          const userData = JSON.parse(userStr) as UserInfo;
          setUserInfo(userData);
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error('Init auth error:', error);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  // 处理登录
  const handleLogin = async (username: string, password: string) => {
    try {
      setLoading(true);
      const response = await api.post('/auth/login', { username, password });

      const { access_token, user } = response.data;
      localStorage.setItem('client_system_token', access_token);
      localStorage.setItem('client_system_user', JSON.stringify(user));

      setUserInfo(user);
      setIsAuthenticated(true);
      message.success(`欢迎 ${user.username}！`);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理退出登录
  const handleLogout = () => {
    Modal.confirm({
      title: '确认退出',
      content: '确定要退出登录吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: () => {
        localStorage.removeItem('client_system_token');
        localStorage.removeItem('client_system_user');
        setUserInfo(null);
        setIsAuthenticated(false);
        setCurrentPage('dashboard');
        message.success('已退出登录');
      }
    });
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <Spin size="large" style={{ color: 'white' }} />
      </div>
    );
  }

  // 未登录 - 显示登录页面
  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} />;
  }

  // 已登录 - 显示主界面
  const userMenu: any[] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '用户中心',
      onClick: () => setCurrentPage('center')
    },
    {
      type: 'divider'
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
      onClick: handleLogout
    }
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 侧边栏 */}
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        style={{
          background: 'linear-gradient(180deg, #667eea 0%, #764ba2 100%)',
          boxShadow: '2px 0 8px rgba(0,0,0,0.1)'
        }}
        theme="dark"
      >
        <div style={{ padding: '16px', textAlign: 'center' }}>
          <h2 style={{ color: 'white', margin: 0, fontSize: '18px' }}>
            {!collapsed && '客户端系统'}
          </h2>
        </div>

        <Menu
          theme="dark"
          mode="inline"
          defaultSelectedKeys={['dashboard']}
          selectedKeys={[currentPage]}
          onClick={(e) => setCurrentPage(e.key as any)}
          style={{
            background: 'transparent',
            borderRight: 'none'
          }}
          items={[
            {
              key: 'dashboard',
              icon: <DashboardOutlined />,
              label: '仪表板'
            },
            {
              key: 'payment',
              icon: <CreditCardOutlined />,
              label: '支付订单'
            },
            {
              key: 'orders',
              icon: <HistoryOutlined />,
              label: '订单历史'
            }
          ]}
        />
      </Sider>

      <Layout>
        {/* 顶部导航 */}
        <Header
          style={{
            background: 'white',
            padding: '0 24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
            💳 客户端支付系统
          </div>

          <Dropdown menu={{ items: userMenu }} placement="bottomRight">
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                cursor: 'pointer',
                padding: '8px 12px',
                borderRadius: '4px',
                transition: 'background 0.3s'
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = '#f0f0f0')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
            >
              <Avatar size={32} icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '14px', fontWeight: '500' }}>{userInfo?.username}</span>
                <span style={{ fontSize: '12px', color: '#999' }}>
                  <Badge
                    color={userInfo?.membership_type === 'pro' ? '#faad14' : userInfo?.membership_type === 'premium' ? '#52c41a' : '#d9d9d9'}
                    text={userInfo?.membership_type || '免费'}
                  />
                </span>
              </div>
            </div>
          </Dropdown>
        </Header>

        {/* 内容区域 */}
        <Content style={{ padding: '24px', background: '#f5f5f5' }}>
          {currentPage === 'dashboard' && <DashboardPage userInfo={userInfo} />}
          {currentPage === 'payment' && <PaymentPage userInfo={userInfo} />}
          {currentPage === 'orders' && <OrderHistoryPage userInfo={userInfo} />}
          {currentPage === 'center' && <UserCenterPage userInfo={userInfo} onLogout={handleLogout} />}
        </Content>
      </Layout>
    </Layout>
  );
};

export default App;
