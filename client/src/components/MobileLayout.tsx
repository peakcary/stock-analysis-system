import React, { useState } from 'react';
import { Layout, Button, Badge, Drawer, Avatar, Space, Typography, Divider } from 'antd';
import { 
  MenuOutlined, BellOutlined, UserOutlined, SearchOutlined,
  HomeOutlined, BarChartOutlined, CrownOutlined, SettingOutlined,
  LogoutOutlined, WalletOutlined
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import { isMobile } from 'react-device-detect';

const { Header } = Layout;
const { Text } = Typography;

interface MobileLayoutProps {
  children: React.ReactNode;
  user: any;
  activeTab: string;
  onTabChange: (tab: string) => void;
  onMenuClick: (key: string) => void;
}

export const MobileLayout: React.FC<MobileLayoutProps> = ({ 
  children, 
  user, 
  activeTab, 
  onTabChange,
  onMenuClick
}) => {
  const [drawerVisible, setDrawerVisible] = useState(false);

  // 移动端头部导航
  const MobileHeader = () => (
    <Header style={{
      position: 'fixed',
      top: 0,
      width: '100%',
      zIndex: 1000,
      padding: '0 16px',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      height: '56px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
    }}>
      <Space>
        <Button 
          type="text" 
          icon={<MenuOutlined />}
          onClick={() => setDrawerVisible(true)}
          style={{ color: 'white', padding: '4px 8px' }}
        />
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          style={{ color: 'white', fontSize: '18px', fontWeight: '600' }}
        >
          📈 智能股票分析
        </motion.div>
      </Space>
      
      <Space>
        {user && (
          <Badge count={3} size="small">
            <Button 
              type="text" 
              icon={<BellOutlined />}
              style={{ color: 'white', padding: '4px 8px' }}
              onClick={() => onMenuClick('notifications')}
            />
          </Badge>
        )}
        <Button 
          type="text" 
          icon={user ? <Avatar size="small" src={user.avatar} icon={<UserOutlined />} /> : <UserOutlined />}
          style={{ color: 'white', padding: '4px 8px' }}
          onClick={() => user ? onMenuClick('profile') : onMenuClick('login')}
        />
      </Space>
    </Header>
  );


  // 移动端侧边菜单
  const MobileDrawerMenu = () => (
    <Drawer
      title={null}
      placement="left"
      onClose={() => setDrawerVisible(false)}
      open={drawerVisible}
      width="280px"
      styles={{
        body: { padding: 0 },
        header: { display: 'none' }
      }}
    >
      <div style={{ padding: 0 }}>
        {/* 用户信息区域 */}
        <div style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          padding: '24px 20px',
          color: 'white'
        }}>
          <Space align="start" size={16}>
            <Avatar size={64} src={user?.avatar} icon={<UserOutlined />} />
            <div>
              <div style={{ fontSize: '18px', fontWeight: '600', marginBottom: '4px' }}>
                {user ? user.name : '游客用户'}
              </div>
              <div style={{ fontSize: '12px', opacity: 0.8, marginBottom: '8px' }}>
                {user ? user.email : '点击登录获取更多功能'}
              </div>
              {user && (
                <div style={{
                  background: 'rgba(255,255,255,0.2)',
                  padding: '4px 8px',
                  borderRadius: '12px',
                  fontSize: '10px',
                  fontWeight: '600',
                  display: 'inline-block'
                }}>
                  {user.memberType === 'free' ? '免费版' : 
                   user.memberType === 'pro' ? '专业版' : 
                   (user.memberType === 'premium' && user.queries_remaining >= 999999) ? '超级管理员' : '旗舰版'}
                </div>
              )}
            </div>
          </Space>
        </div>
        
        {/* 菜单项 */}
        <div style={{ padding: '16px 0' }}>
          {[
            {
              icon: '🏠',
              title: '首页',
              desc: '股票分析首页',
              key: 'home',
              color: '#3b82f6'
            },
            {
              icon: '📊',
              title: '数据分析',
              desc: '深度股票分析',
              key: 'analysis',
              color: '#10b981'
            },
            ...(user ? [
              {
                icon: '🔍',
                title: '股票查询',
                desc: '查询股票概念',
                key: 'stock-analysis',
                color: '#667eea'
              },
              {
                icon: '🚀',
                title: '新高概念',
                desc: '达到新高的概念',
                key: 'new-high-concepts',
                color: '#f59e0b'
              },
              {
                icon: '⭐',
                title: '热门股票',
                desc: '概念热门股票',
                key: 'top-concepts',
                color: '#fbbf24'
              },
              {
                icon: '🎁',
                title: '可转债',
                desc: '可转债概念查询',
                key: 'convertible-bonds',
                color: '#f97316'
              }
            ] : []),
            {
              icon: '💎',
              title: '会员中心',
              desc: '升级专业版',
              key: 'membership',
              color: '#f97316'
            },
            ...(user ? [{
              icon: '👤',
              title: '个人中心',
              desc: '账户管理',
              key: 'profile',
              color: '#8b5cf6'
            }] : [])
          ].map((item, index) => (
            <motion.div
              key={item.key}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => {
                onMenuClick(item.key);
                setDrawerVisible(false);
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '16px 20px',
                borderBottom: '1px solid #f5f5f5',
                cursor: 'pointer',
                background: 'white',
                transition: 'background-color 0.3s ease'
              }}
            >
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '12px',
                background: `${item.color}15`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: '16px',
                fontSize: '20px'
              }}>
                {item.icon}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ 
                  fontWeight: '600', 
                  fontSize: '15px',
                  color: '#1f2937',
                  marginBottom: '2px'
                }}>
                  {item.title}
                </div>
                <div style={{ 
                  fontSize: '12px', 
                  color: '#9ca3af' 
                }}>
                  {item.desc}
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* 底部操作 */}
        <div style={{ 
          position: 'absolute',
          bottom: '20px',
          left: '20px',
          right: '20px'
        }}>
          <Divider />
          {user ? (
            <Button 
              type="text" 
              icon={<LogoutOutlined />}
              onClick={() => {
                onMenuClick('logout');
                setDrawerVisible(false);
              }}
              block
              style={{ 
                color: '#ef4444',
                height: '48px',
                borderRadius: '12px',
                border: '1px solid #fecaca',
                background: '#fef2f2'
              }}
            >
              退出登录
            </Button>
          ) : (
            <Button 
              type="primary"
              onClick={() => {
                onMenuClick('login');
                setDrawerVisible(false);
              }}
              block
              style={{ 
                height: '48px',
                borderRadius: '12px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                border: 'none',
                fontWeight: '600'
              }}
            >
              立即登录
            </Button>
          )}
        </div>
      </div>
    </Drawer>
  );

  // 移动端底部导航
  const BottomNavigation = () => {
    const navItems = user ? [
      { icon: '🏠', label: '首页', key: 'home' },
      { icon: '📊', label: '分析', key: 'analysis' },
      { icon: '🔍', label: '查询', key: 'stock-analysis' },
      { icon: '💎', label: '会员', key: 'membership' },
      { icon: '👤', label: '我的', key: 'profile' }
    ] : [
      { icon: '🏠', label: '首页', key: 'home' },
      { icon: '📊', label: '分析', key: 'analysis' },
      { icon: '💎', label: '会员', key: 'membership' },
      { icon: '🔐', label: '登录', key: 'auth' }
    ];

    return (
      <div style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        height: '60px',
        background: 'white',
        borderTop: '1px solid #e5e7eb',
        display: 'flex',
        justifyContent: 'space-around',
        alignItems: 'center',
        zIndex: 999,
        boxShadow: '0 -2px 8px rgba(0,0,0,0.08)'
      }}>
        {navItems.map((item) => (
          <motion.div
            key={item.key}
            whileTap={{ scale: 0.95 }}
            onClick={() => {
              onTabChange(item.key);
            }}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              flex: 1,
              height: '100%',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              opacity: activeTab === item.key ? 1 : 0.6,
            }}
          >
            <div style={{
              fontSize: '20px',
              marginBottom: '2px',
              transition: 'transform 0.2s ease',
              transform: activeTab === item.key ? 'scale(1.1)' : 'scale(1)'
            }}>
              {item.icon}
            </div>
            <div style={{
              fontSize: '10px',
              color: activeTab === item.key ? '#667eea' : '#6b7280',
              fontWeight: activeTab === item.key ? '600' : '400'
            }}>
              {item.label}
            </div>
          </motion.div>
        ))}
      </div>
    );
  };

  if (!isMobile) {
    // 桌面端布局
    return <div style={{ minHeight: '100vh' }}>{children}</div>;
  }

  // 移动端布局
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <MobileHeader />

      <div style={{
        marginTop: '56px',
        marginBottom: '60px',
        minHeight: 'calc(100vh - 116px)',
        background: '#f5f7fa'
      }}>
        {children}
      </div>

      <BottomNavigation />
      <MobileDrawerMenu />
    </Layout>
  );
};

export default MobileLayout;