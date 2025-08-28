import React, { type ReactNode } from 'react';
import { Layout, Menu, Button, Avatar, Dropdown, Space, Typography, Tag } from 'antd';
import {
  SearchOutlined, UserOutlined, ApiOutlined, UploadOutlined,
  CloudUploadOutlined, GiftOutlined, SettingOutlined, LogoutOutlined,
  DashboardOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const { Header, Content, Sider } = Layout;
const { Text } = Typography;

interface AdminLayoutProps {
  children: ReactNode;
  activeTab: string;
  onTabChange: (key: string) => void;
}

const AdminLayout: React.FC<AdminLayoutProps> = ({ children, activeTab, onTabChange }) => {
  const { user, logout } = useAuth();

  const menuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: '控制台',
    },
    {
      key: 'simple-import',
      icon: <CloudUploadOutlined />,
      label: '简化导入',
    },
    {
      key: 'stocks',
      icon: <SearchOutlined />,
      label: '股票查询',
    },
    {
      key: 'import',
      icon: <UploadOutlined />,
      label: '原导入（测试）',
    },
    {
      key: 'concepts',
      icon: <ApiOutlined />,
      label: '概念分析',
    },
    {
      key: 'user',
      icon: <UserOutlined />,
      label: '用户管理',
    },
    {
      key: 'packages',
      icon: <GiftOutlined />,
      label: '套餐管理',
    },
  ];

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: logout,
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '0 24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <div style={{
          color: 'white',
          fontSize: '20px',
          fontWeight: 'bold',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <SettingOutlined />
          股票分析系统 - 管理后台
          <Tag color="blue" style={{ marginLeft: 8 }}>v2.0</Tag>
        </div>

        <Space>
          <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px' }}>
            {new Date().toLocaleDateString('zh-CN')}
          </div>
          
          <Dropdown
            menu={{
              items: userMenuItems
            }}
            placement="bottomRight"
            arrow
          >
            <Button
              type="text"
              style={{
                color: 'white',
                border: '1px solid rgba(255,255,255,0.3)',
                background: 'rgba(255,255,255,0.1)',
                borderRadius: '8px'
              }}
            >
              <Space>
                <Avatar size="small" icon={<UserOutlined />} />
                <span>{user?.username || '管理员'}</span>
              </Space>
            </Button>
          </Dropdown>
        </Space>
      </Header>

      <Layout>
        <Sider
          width={220}
          theme="light"
          style={{
            background: '#fafafa',
            boxShadow: '2px 0 8px rgba(0,0,0,0.06)'
          }}
        >
          <div style={{ padding: '16px 16px 8px', borderBottom: '1px solid #f0f0f0' }}>
            <Text type="secondary" style={{ fontSize: '12px', fontWeight: 500 }}>
              功能导航
            </Text>
          </div>
          
          <Menu
            mode="inline"
            selectedKeys={[activeTab]}
            style={{
              height: 'calc(100vh - 120px)',
              borderRight: 0,
              background: 'transparent'
            }}
            items={menuItems.map(item => ({
              ...item,
              style: {
                margin: '4px 8px',
                borderRadius: '8px',
                height: '44px',
                lineHeight: '44px'
              }
            }))}
            onClick={({ key }) => onTabChange(key)}
          />
        </Sider>

        <Layout style={{ background: '#f5f5f5' }}>
          <Content style={{ 
            margin: '24px',
            minHeight: 'calc(100vh - 112px)',
            overflow: 'auto'
          }}>
            {children}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default AdminLayout;