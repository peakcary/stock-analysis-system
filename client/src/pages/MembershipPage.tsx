import React, { useState, useEffect } from 'react';
import {
  Card, Button, Space, Typography, Row, Col, message
} from 'antd';
import EnhancedPaymentModal from '../components/EnhancedPaymentModal';
import { apiClient } from '../utils/auth';
import {
  StarOutlined, SafetyCertificateOutlined
} from '@ant-design/icons';
import { motion } from 'framer-motion';

const { Title, Text, Paragraph } = Typography;

interface MembershipPageProps {
  user: any;
  onUpgrade: (plan: string) => void;
}

// 移除硬编码的套餐数据，改用API数据

export const MembershipPage: React.FC<MembershipPageProps> = ({ user, onUpgrade }) => {
  const [paymentModalVisible, setPaymentModalVisible] = useState(false);
  const [selectedPackageObj, setSelectedPackageObj] = useState<any>(null);
  const [userStats, setUserStats] = useState<any>(null);
  const [packages, setPackages] = useState<any[]>([]);

  // 客户端不需要支付统计数据，注释掉
  // const fetchUserStats = async () => {
  //   try {
  //     const response = await axios.get('/api/v1/payment/stats');
  //     setUserStats(response.data);
  //   } catch (error) {
  //     console.error('获取用户统计失败:', error);
  //   }
  // };

  // useEffect(() => {
  //   fetchUserStats();
  // }, []);

  // 移除handleSelectPlan，不再需要

  // 支付成功回调
  const handlePaymentSuccess = () => {
    setPaymentModalVisible(false);
    // fetchUserStats(); // 客户端不需要统计数据
    message.success('支付成功，会员权益已生效！');
  };

  // 选择套餐
  const selectPackage = (packageData: any) => {
    console.log('选择套餐:', packageData);
    setSelectedPackageObj(packageData);
    setPaymentModalVisible(true);
  };

  return (
    <div style={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
      padding: '40px 20px'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* 头部标题 */}
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          style={{ textAlign: 'center', marginBottom: '60px' }}
        >
          <Title level={1} style={{ 
            fontSize: '48px',
            margin: '0 0 16px 0',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            选择您的专属方案
          </Title>
          <Paragraph style={{ 
            fontSize: '20px', 
            color: '#64748b',
            maxWidth: '600px',
            margin: '0 auto'
          }}>
            解锁专业投资分析工具，获得更深入的市场洞察，让每一次投资决策都更加精准
          </Paragraph>
          
          {/* 当前会员状态 */}
          {user && (
            <Card style={{
              maxWidth: '400px',
              margin: '30px auto 0',
              borderRadius: '16px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
              color: 'white'
            }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '32px', marginBottom: '8px' }}>
                  <StarOutlined />
                </div>
                <Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: '14px' }}>
                  当前会员等级
                </Text>
                <Title level={3} style={{ color: 'white', margin: '4px 0' }}>
                  {userStats?.membership_type || '免费版'}
                </Title>
                {userStats?.membership_expires_at && (
                  <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px' }}>
                    有效期至：{new Date(userStats.membership_expires_at).toLocaleDateString()}
                  </Text>
                )}
                {userStats && (
                  <div style={{ marginTop: '16px' }}>
                    <Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: '12px' }}>
                      剩余查询次数：{userStats.queries_remaining} 次
                    </Text>
                  </div>
                )}
                <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px' }}>
                  请在下方选择合适的套餐
                </Text>
              </div>
            </Card>
          )}
        </motion.div>

        {/* 套餐展示区域 */}
        <PaymentPackagesInline onSuccess={handlePaymentSuccess} onSelectPackage={selectPackage} packages={packages} setPackages={setPackages} selectedPackageObj={selectedPackageObj} />
        
        {/* 底部保障说明 */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          style={{ 
            textAlign: 'center', 
            marginTop: '80px',
            padding: '40px',
            background: 'white',
            borderRadius: '20px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.08)'
          }}
        >
          <Title level={3} style={{ marginBottom: '24px' }}>
            <SafetyCertificateOutlined style={{ marginRight: '12px', color: '#10b981' }} />
            安全保障承诺
          </Title>
          <Row gutter={[32, 16]} justify="center">
            <Col xs={24} md={6}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '32px', color: '#10b981', marginBottom: '8px' }}>🛡️</div>
                <Text strong>7天无理由退款</Text>
                <br />
                <Text type="secondary" style={{ fontSize: '12px' }}>不满意随时退款</Text>
              </div>
            </Col>
            <Col xs={24} md={6}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '32px', color: '#3b82f6', marginBottom: '8px' }}>🔒</div>
                <Text strong>数据安全加密</Text>
                <br />
                <Text type="secondary" style={{ fontSize: '12px' }}>银行级安全保护</Text>
              </div>
            </Col>
            <Col xs={24} md={6}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '32px', color: '#f59e0b', marginBottom: '8px' }}>⏰</div>
                <Text strong>24小时客户服务</Text>
                <br />
                <Text type="secondary" style={{ fontSize: '12px' }}>专业团队在线支持</Text>
              </div>
            </Col>
            <Col xs={24} md={6}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '32px', color: '#8b5cf6', marginBottom: '8px' }}>📱</div>
                <Text strong>随时取消订阅</Text>
                <br />
                <Text type="secondary" style={{ fontSize: '12px' }}>灵活的订阅管理</Text>
              </div>
            </Col>
          </Row>
        </motion.div>
      </div>

      {/* 支付弹窗 */}
      <EnhancedPaymentModal
        visible={paymentModalVisible}
        onCancel={() => setPaymentModalVisible(false)}
        onSuccess={handlePaymentSuccess}
        selectedPackage={selectedPackageObj}
      />
    </div>
  );
};

// PaymentPackagesInline 组件 - 直接在页面中显示套餐
interface PaymentPackagesInlineProps {
  onSuccess: () => void;
  onSelectPackage: (packageData: any) => void;
  packages: any[];
  setPackages: (packages: any[]) => void;
  selectedPackageObj?: any;
}

const PaymentPackagesInline: React.FC<PaymentPackagesInlineProps> = ({ onSuccess, onSelectPackage, packages, setPackages, selectedPackageObj }) => {
  const [loading, setLoading] = useState(false);

  // 获取支付套餐列表
  const fetchPackages = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/payment/packages');
      console.log('获取到套餐数据:', response.data);
      setPackages(response.data || []);
    } catch (error) {
      console.error('获取套餐数据失败:', error);
      setPackages([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPackages();
  }, []);

  // 获取套餐图标
  const getPackageIcon = (packageType: string, membershipType: string) => {
    if (packageType.includes('queries_')) {
      return <StarOutlined style={{ fontSize: '32px', color: '#1890ff' }} />;
    }

    switch (membershipType) {
      case 'pro':
        return <SafetyCertificateOutlined style={{ fontSize: '32px', color: '#fa8c16' }} />;
      case 'premium':
        return <StarOutlined style={{ fontSize: '32px', color: '#fadb14' }} />;
      default:
        return <StarOutlined style={{ fontSize: '32px', color: '#52c41a' }} />;
    }
  };

  // 获取套餐颜色
  const getPackageColor = (membershipType: string, isPopular?: boolean) => {
    if (isPopular) return '#fa541c';

    switch (membershipType) {
      case 'pro':
        return '#1890ff';
      case 'premium':
        return '#fadb14';
      default:
        return '#52c41a';
    }
  };

  // 判断是否为热门套餐
  const isPopularPackage = (packageType: string) => {
    return packageType.includes('monthly') || packageType.includes('queries_10');
  };


  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 0' }}>
        <Title level={3}>正在加载套餐信息...</Title>
      </div>
    );
  }

  console.log('当前套餐数据:', packages, '数量:', packages.length);

  return (
    <>
      {/* 套餐选择区域 */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.3 }}
        style={{ marginBottom: '60px' }}
      >
        <Title level={2} style={{ textAlign: 'center', marginBottom: '40px' }}>
          📦 选择适合您的套餐
        </Title>
        <Row gutter={[24, 24]} justify="center">
          {packages.map((pkg, index) => (
            <Col xs={24} sm={12} md={8} lg={6} key={pkg.id}>
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                whileHover={{ scale: 1.02 }}
              >
                <Card
                  hoverable
                  style={{
                    borderRadius: '16px',
                    border: isPopularPackage(pkg.package_type) ? '3px solid #fa541c' : '2px solid #f1f5f9',
                    boxShadow: isPopularPackage(pkg.package_type)
                      ? '0 20px 40px rgba(0,0,0,0.15)'
                      : '0 8px 24px rgba(0,0,0,0.08)',
                    position: 'relative',
                    height: '100%',
                    background: isPopularPackage(pkg.package_type)
                      ? 'linear-gradient(135deg, rgba(245,158,11,0.05) 0%, rgba(251,146,60,0.05) 100%)'
                      : 'white'
                  }}
                  bodyStyle={{ padding: '30px' }}
                >
                  {/* 推荐标签 */}
                  {isPopularPackage(pkg.package_type) && (
                    <div style={{
                      position: 'absolute',
                      top: '-2px',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      background: '#fa541c',
                      color: 'white',
                      padding: '8px 24px',
                      borderRadius: '0 0 16px 16px',
                      fontSize: '14px',
                      fontWeight: '600',
                      zIndex: 1,
                      boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
                    }}>
                      推荐
                    </div>
                  )}

                  <div style={{ textAlign: 'center' }}>
                    <motion.div
                      whileHover={{ scale: 1.1, rotate: 5 }}
                      style={{ marginBottom: '16px' }}
                    >
                      {getPackageIcon(pkg.package_type, pkg.membership_type)}
                    </motion.div>

                    <Title level={4} style={{ marginBottom: '8px' }}>
                      {pkg.name}
                    </Title>

                    <div style={{ margin: '20px 0' }}>
                      <Text
                        style={{
                          fontSize: '36px',
                          fontWeight: '800',
                          color: getPackageColor(pkg.membership_type, isPopularPackage(pkg.package_type)),
                          lineHeight: '1'
                        }}
                      >
                        ¥{pkg.price}
                      </Text>
                    </div>

                    <Space direction="vertical" size="small" style={{ width: '100%', marginBottom: '24px' }}>
                      <Text style={{ color: '#666' }}>
                        📊 {pkg.queries_count}次查询
                      </Text>
                      <Text style={{ color: '#666' }}>
                        ⏰ {pkg.validity_days}天有效期
                      </Text>
                      {pkg.membership_type !== 'free' && (
                        <Text style={{ color: '#666' }}>
                          👑 {pkg.membership_type === 'pro' ? '专业版' : '旗舰版'}权限
                        </Text>
                      )}
                    </Space>

                    <Paragraph style={{
                      color: '#8c8c8c',
                      fontSize: '14px',
                      marginBottom: '24px',
                      minHeight: '40px'
                    }}>
                      {pkg.description}
                    </Paragraph>

                    <Button
                      type="primary"
                      size="large"
                      block
                      onClick={() => onSelectPackage(pkg)}
                      style={{
                        height: '48px',
                        fontSize: '16px',
                        fontWeight: '600',
                        borderRadius: '12px',
                        backgroundColor: getPackageColor(pkg.membership_type, isPopularPackage(pkg.package_type)),
                        borderColor: getPackageColor(pkg.membership_type, isPopularPackage(pkg.package_type)),
                        boxShadow: `0 4px 12px ${getPackageColor(pkg.membership_type, isPopularPackage(pkg.package_type))}40`
                      }}
                    >
                      立即购买
                    </Button>
                  </div>
                </Card>
              </motion.div>
            </Col>
          ))}
        </Row>
      </motion.div>

    </>
  );
};

export default MembershipPage;