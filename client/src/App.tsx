import React, { useState, useEffect } from 'react';
import { ConfigProvider, App as AntApp, message } from 'antd';
import { BrowserRouter as Router } from 'react-router-dom';
import { isMobile } from 'react-device-detect';
import zhCN from 'antd/locale/zh_CN';

import AuthPage from './pages/AuthPage';
import MembershipPage from './pages/MembershipPage';
import AnalysisPage from './pages/AnalysisPage';
import MobileLayout from './components/MobileLayout';
import { tokenManager, mockLogin } from './utils/auth';

// 主题配置
const theme = {
  token: {
    colorPrimary: '#667eea',
    colorSuccess: '#10b981',
    colorWarning: '#f59e0b',
    colorError: '#ef4444',
    colorInfo: '#3b82f6',
    borderRadius: 8,
    wireframe: false,
  },
  components: {
    Button: {
      borderRadius: 8,
      controlHeight: 40,
    },
    Card: {
      borderRadius: 12,
    },
    Input: {
      borderRadius: 8,
      controlHeight: 40,
    },
  },
};

interface User {
  id: number;
  name: string;
  email: string;
  memberType: 'free' | 'pro' | 'premium';
  avatar?: string;
}

const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [activeTab, setActiveTab] = useState('home');
  const [loading, setLoading] = useState(true);

  // 初始化应用
  useEffect(() => {
    // 初始化认证和加载用户数据
    const initApp = async () => {
      try {
        // 初始化认证token
        tokenManager.initToken();
        
        // 尝试自动登录用于测试
        if (!tokenManager.getToken()) {
          const loginResult = await mockLogin('admin', 'admin123');
          if (loginResult.success) {
            console.log('自动登录成功:', loginResult.user);
          } else {
            console.log('自动登录失败:', loginResult.error);
          }
        }
        
        // 这里会调用API获取用户信息
        const savedUser = localStorage.getItem('user');
        if (savedUser) {
          setUser(JSON.parse(savedUser));
        }
      } catch (error) {
        console.error('初始化失败:', error);
      } finally {
        // 移除加载动画
        setTimeout(() => {
          const loadingEl = document.querySelector('.loading-container');
          if (loadingEl) {
            loadingEl.remove();
          }
          setLoading(false);
        }, 1000);
      }
    };

    initApp();
  }, []);

  // 处理登录成功
  const handleLoginSuccess = (userData: User) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
    message.success(`欢迎回来，${userData.name}！`);
    setActiveTab('home');
  };

  // 处理会员升级
  const handleMembershipUpgrade = (planId: string) => {
    if (user) {
      const updatedUser = { ...user, memberType: planId as any };
      setUser(updatedUser);
      localStorage.setItem('user', JSON.stringify(updatedUser));
      message.success('会员升级成功！');
      setActiveTab('analysis');
    }
  };

  // 处理菜单点击
  const handleMenuClick = (key: string) => {
    switch (key) {
      case 'login':
        if (!user) {
          setActiveTab('auth');
        }
        break;
      case 'logout':
        setUser(null);
        localStorage.removeItem('user');
        message.success('已退出登录');
        setActiveTab('home');
        break;
      case 'search':
        message.info('搜索功能开发中...');
        break;
      case 'notifications':
        message.info('消息中心开发中...');
        break;
      case 'settings':
        message.info('设置页面开发中...');
        break;
      case 'hotspot':
        message.info('热点追踪功能开发中...');
        break;
      case 'diagnosis':
        if (user?.memberType === 'free') {
          message.warning('请升级会员使用此功能');
          setActiveTab('membership');
        } else {
          message.info('个股诊断功能开发中...');
        }
        break;
      default:
        setActiveTab(key);
    }
  };

  // 渲染当前页面
  const renderCurrentPage = () => {
    if (!user && activeTab !== 'auth' && activeTab !== 'home') {
      return (
        <AuthPage onLoginSuccess={handleLoginSuccess} />
      );
    }

    switch (activeTab) {
      case 'auth':
        return <AuthPage onLoginSuccess={handleLoginSuccess} />;
      
      case 'home':
      case 'analysis':
        return <AnalysisPage user={user} />;
      
      case 'membership':
        return (
          <MembershipPage 
            user={user} 
            onUpgrade={handleMembershipUpgrade} 
          />
        );
      
      case 'profile':
        return <ProfilePage user={user} onLogout={() => handleMenuClick('logout')} />;
      
      default:
        return <AnalysisPage user={user} />;
    }
  };

  if (loading) {
    return null; // 显示初始加载动画
  }

  return (
    <ConfigProvider 
      theme={theme} 
      locale={zhCN}
      button={{ className: 'custom-button' }}
    >
      <AntApp>
        <Router>
          {isMobile ? (
            <MobileLayout 
              user={user}
              activeTab={activeTab}
              onTabChange={setActiveTab}
              onMenuClick={handleMenuClick}
            >
              {renderCurrentPage()}
            </MobileLayout>
          ) : (
            <DesktopLayout 
              user={user}
              activeTab={activeTab}
              onTabChange={setActiveTab}
              onMenuClick={handleMenuClick}
            >
              {renderCurrentPage()}
            </DesktopLayout>
          )}
        </Router>
      </AntApp>
    </ConfigProvider>
  );
};

// 桌面端布局组件
const DesktopLayout: React.FC<{
  children: React.ReactNode;
  user: User | null;
  activeTab: string;
  onTabChange: (tab: string) => void;
  onMenuClick: (key: string) => void;
}> = ({ children, user, activeTab, onTabChange, onMenuClick }) => {
  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)'
    }}>
      {/* 桌面端顶部导航 */}
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        height: '64px',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', color: 'white' }}>
          <span style={{ fontSize: '24px', marginRight: '12px' }}>📈</span>
          <span style={{ fontSize: '20px', fontWeight: '600' }}>智能股票分析</span>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          {['首页', '分析', '会员', user ? '个人中心' : '登录'].map((item, index) => (
            <button
              key={item}
              onClick={() => {
                const tabMap: Record<string, string> = {
                  '首页': 'home',
                  '分析': 'analysis', 
                  '会员': 'membership',
                  '个人中心': 'profile',
                  '登录': 'auth'
                };
                onTabChange(tabMap[item]);
              }}
              style={{
                background: 'none',
                border: 'none',
                color: 'white',
                fontSize: '16px',
                cursor: 'pointer',
                padding: '8px 16px',
                borderRadius: '8px',
                transition: 'all 0.3s ease',
                opacity: activeTab === (['home', 'analysis', 'membership', user ? 'profile' : 'auth'][index]) ? 1 : 0.8
              }}
            >
              {item}
            </button>
          ))}
        </div>
      </div>
      
      {/* 桌面端内容区域 */}
      <div style={{ paddingTop: '64px', minHeight: '100vh' }}>
        {children}
      </div>
    </div>
  );
};

// 个人中心页面
const ProfilePage: React.FC<{ user: User | null; onLogout: () => void }> = ({ user, onLogout }) => {
  if (!user) return null;

  return (
    <div style={{ padding: '40px 20px', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{
        background: 'white',
        borderRadius: '16px',
        padding: '40px',
        textAlign: 'center',
        boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
      }}>
        <div style={{ fontSize: '64px', marginBottom: '16px' }}>👤</div>
        <h2>{user.name}</h2>
        <p style={{ color: '#666', marginBottom: '24px' }}>{user.email}</p>
        <div style={{
          background: user.memberType === 'free' ? '#f3f4f6' : '#667eea',
          color: user.memberType === 'free' ? '#374151' : 'white',
          padding: '8px 16px',
          borderRadius: '20px',
          display: 'inline-block',
          marginBottom: '32px',
          fontWeight: '600'
        }}>
          {user.memberType === 'free' ? '免费版用户' : 
           user.memberType === 'pro' ? '专业版会员' : '旗舰版会员'}
        </div>
        
        <div style={{ marginTop: '32px' }}>
          <button
            onClick={onLogout}
            style={{
              background: '#ef4444',
              color: 'white',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '8px',
              fontSize: '16px',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            退出登录
          </button>
        </div>
      </div>
    </div>
  );
};

export default App;