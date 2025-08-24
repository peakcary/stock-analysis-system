import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Button, Typography, Tag, Space, message, Spin,
  Descriptions, Modal, Alert
} from 'antd';
import {
  CrownOutlined, StarOutlined, FireOutlined, ThunderboltOutlined,
  CheckOutlined, WechatOutlined
} from '@ant-design/icons';
import axios from 'axios';
import PaymentModal from './PaymentModal';

const { Title, Text } = Typography;

interface PaymentPackage {
  id: number;
  package_type: string;
  name: string;
  price: number;
  queries_count: number;
  validity_days: number;
  membership_type: string;
  description: string;
  is_active: boolean;
  sort_order: number;
}

interface PaymentPackagesProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: () => void;
}

const PaymentPackages: React.FC<PaymentPackagesProps> = ({
  visible,
  onCancel,
  onSuccess
}) => {
  const [packages, setPackages] = useState<PaymentPackage[]>([]);
  const [loading, setLoading] = useState(false);
  const [paymentModalVisible, setPaymentModalVisible] = useState(false);
  const [selectedPackage, setSelectedPackage] = useState<string>('');

  // 获取支付套餐列表
  const fetchPackages = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/v1/payment/packages');
      setPackages(response.data);
    } catch (error) {
      console.error('获取套餐列表失败:', error);
      message.error('获取套餐列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (visible) {
      fetchPackages();
    }
  }, [visible]);

  // 获取套餐图标
  const getPackageIcon = (packageType: string, membershipType: string) => {
    if (packageType.includes('queries_')) {
      return <ThunderboltOutlined style={{ fontSize: '32px', color: '#1890ff' }} />;
    }
    
    switch (membershipType) {
      case 'pro':
        return <FireOutlined style={{ fontSize: '32px', color: '#fa8c16' }} />;
      case 'premium':
        return <CrownOutlined style={{ fontSize: '32px', color: '#fadb14' }} />;
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

  // 获取会员类型标签
  const getMembershipTag = (membershipType: string) => {
    const configs = {
      free: { color: 'default', text: '查询包' },
      pro: { color: 'processing', text: '专业版' },
      premium: { color: 'warning', text: '旗舰版' }
    };
    const config = configs[membershipType as keyof typeof configs] || configs.free;
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 判断是否为热门套餐
  const isPopularPackage = (packageType: string) => {
    return packageType.includes('monthly') || packageType === 'queries_50';
  };

  // 选择套餐
  const selectPackage = (packageType: string) => {
    setSelectedPackage(packageType);
    setPaymentModalVisible(true);
  };

  // 支付成功回调
  const handlePaymentSuccess = () => {
    setPaymentModalVisible(false);
    onSuccess();
    message.success('支付成功，会员权益已生效！');
  };

  // 按类型分组套餐
  const groupedPackages = {
    queries: packages.filter(pkg => pkg.package_type.startsWith('queries_')),
    pro: packages.filter(pkg => pkg.membership_type === 'pro'),
    premium: packages.filter(pkg => pkg.membership_type === 'premium')
  };

  return (
    <>
      <Modal
        title="选择支付套餐"
        open={visible}
        onCancel={onCancel}
        footer={null}
        width={1000}
        style={{ top: 20 }}
      >
        <div style={{ padding: '16px 0' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <Spin size="large" />
              <p style={{ marginTop: 16 }}>正在加载套餐信息...</p>
            </div>
          ) : (
            <div>
              {/* 套餐介绍 */}
              <Alert
                message="套餐说明"
                description={
                  <div>
                    <p>• <strong>查询包</strong>：适合偶尔使用，购买固定次数查询</p>
                    <p>• <strong>专业版</strong>：月度订阅，包含大量查询次数和专业功能</p>
                    <p>• <strong>旗舰版</strong>：全功能版本，享受最优质的服务体验</p>
                  </div>
                }
                type="info"
                showIcon
                style={{ marginBottom: 24 }}
              />

              {/* 查询包套餐 */}
              {groupedPackages.queries.length > 0 && (
                <div style={{ marginBottom: 32 }}>
                  <Title level={4}>
                    <ThunderboltOutlined /> 查询包套餐
                  </Title>
                  <Row gutter={[16, 16]}>
                    {groupedPackages.queries.map(pkg => (
                      <Col xs={24} sm={12} md={8} lg={6} key={pkg.id}>
                        <Card
                          hoverable
                          style={{
                            border: isPopularPackage(pkg.package_type) ? '2px solid #fa541c' : '1px solid #d9d9d9',
                            position: 'relative'
                          }}
                        >
                          {isPopularPackage(pkg.package_type) && (
                            <div
                              style={{
                                position: 'absolute',
                                top: '-1px',
                                right: '16px',
                                background: '#fa541c',
                                color: 'white',
                                padding: '4px 12px',
                                fontSize: '12px',
                                borderRadius: '0 0 8px 8px',
                                fontWeight: 'bold'
                              }}
                            >
                              推荐
                            </div>
                          )}
                          
                          <div style={{ textAlign: 'center' }}>
                            {getPackageIcon(pkg.package_type, pkg.membership_type)}
                            <Title level={5} style={{ marginTop: 8, marginBottom: 4 }}>
                              {pkg.name}
                            </Title>
                            {getMembershipTag(pkg.membership_type)}
                            
                            <div style={{ margin: '16px 0' }}>
                              <Text
                                style={{
                                  fontSize: '24px',
                                  fontWeight: 'bold',
                                  color: getPackageColor(pkg.membership_type, isPopularPackage(pkg.package_type))
                                }}
                              >
                                ¥{pkg.price}
                              </Text>
                            </div>

                            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                              <div>
                                <CheckOutlined style={{ color: '#52c41a' }} />
                                <Text style={{ marginLeft: 4 }}>{pkg.queries_count}次查询</Text>
                              </div>
                              <div>
                                <CheckOutlined style={{ color: '#52c41a' }} />
                                <Text style={{ marginLeft: 4 }}>{pkg.validity_days}天有效期</Text>
                              </div>
                            </Space>

                            <Button
                              type="primary"
                              icon={<WechatOutlined />}
                              onClick={() => selectPackage(pkg.package_type)}
                              style={{
                                marginTop: 16,
                                backgroundColor: getPackageColor(pkg.membership_type, isPopularPackage(pkg.package_type)),
                                borderColor: getPackageColor(pkg.membership_type, isPopularPackage(pkg.package_type)),
                                width: '100%'
                              }}
                            >
                              立即购买
                            </Button>
                          </div>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </div>
              )}

              {/* 专业版套餐 */}
              {groupedPackages.pro.length > 0 && (
                <div style={{ marginBottom: 32 }}>
                  <Title level={4}>
                    <FireOutlined /> 专业版套餐
                  </Title>
                  <Row gutter={[16, 16]}>
                    {groupedPackages.pro.map(pkg => (
                      <Col xs={24} sm={12} md={8} lg={6} key={pkg.id}>
                        <Card
                          hoverable
                          style={{
                            border: isPopularPackage(pkg.package_type) ? '2px solid #fa541c' : '1px solid #d9d9d9',
                            position: 'relative'
                          }}
                        >
                          {isPopularPackage(pkg.package_type) && (
                            <div
                              style={{
                                position: 'absolute',
                                top: '-1px',
                                right: '16px',
                                background: '#fa541c',
                                color: 'white',
                                padding: '4px 12px',
                                fontSize: '12px',
                                borderRadius: '0 0 8px 8px',
                                fontWeight: 'bold'
                              }}
                            >
                              热门
                            </div>
                          )}
                          
                          <div style={{ textAlign: 'center' }}>
                            {getPackageIcon(pkg.package_type, pkg.membership_type)}
                            <Title level={5} style={{ marginTop: 8, marginBottom: 4 }}>
                              {pkg.name}
                            </Title>
                            {getMembershipTag(pkg.membership_type)}
                            
                            <div style={{ margin: '16px 0' }}>
                              <Text
                                style={{
                                  fontSize: '24px',
                                  fontWeight: 'bold',
                                  color: getPackageColor(pkg.membership_type, isPopularPackage(pkg.package_type))
                                }}
                              >
                                ¥{pkg.price}
                              </Text>
                              {pkg.package_type.includes('monthly') && (
                                <Text type="secondary" style={{ display: 'block', fontSize: '12px' }}>
                                  约 ¥{(pkg.price / (pkg.validity_days / 30)).toFixed(2)}/月
                                </Text>
                              )}
                            </div>

                            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                              <div>
                                <CheckOutlined style={{ color: '#52c41a' }} />
                                <Text style={{ marginLeft: 4 }}>{pkg.queries_count}次查询</Text>
                              </div>
                              <div>
                                <CheckOutlined style={{ color: '#52c41a' }} />
                                <Text style={{ marginLeft: 4 }}>{pkg.validity_days}天有效期</Text>
                              </div>
                              <div>
                                <CheckOutlined style={{ color: '#52c41a' }} />
                                <Text style={{ marginLeft: 4 }}>专业功能权限</Text>
                              </div>
                            </Space>

                            <Button
                              type="primary"
                              icon={<WechatOutlined />}
                              onClick={() => selectPackage(pkg.package_type)}
                              style={{
                                marginTop: 16,
                                backgroundColor: getPackageColor(pkg.membership_type, isPopularPackage(pkg.package_type)),
                                borderColor: getPackageColor(pkg.membership_type, isPopularPackage(pkg.package_type)),
                                width: '100%'
                              }}
                            >
                              立即购买
                            </Button>
                          </div>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </div>
              )}

              {/* 旗舰版套餐 */}
              {groupedPackages.premium.length > 0 && (
                <div>
                  <Title level={4}>
                    <CrownOutlined /> 旗舰版套餐
                  </Title>
                  <Row gutter={[16, 16]}>
                    {groupedPackages.premium.map(pkg => (
                      <Col xs={24} sm={12} md={8} lg={6} key={pkg.id}>
                        <Card
                          hoverable
                          style={{
                            border: '2px solid #fadb14',
                            background: 'linear-gradient(145deg, #fff7e6 0%, #fff2d3 100%)',
                            position: 'relative'
                          }}
                        >
                          <div
                            style={{
                              position: 'absolute',
                              top: '-1px',
                              right: '16px',
                              background: 'linear-gradient(45deg, #fadb14, #fa8c16)',
                              color: 'white',
                              padding: '4px 12px',
                              fontSize: '12px',
                              borderRadius: '0 0 8px 8px',
                              fontWeight: 'bold'
                            }}
                          >
                            至尊
                          </div>
                          
                          <div style={{ textAlign: 'center' }}>
                            {getPackageIcon(pkg.package_type, pkg.membership_type)}
                            <Title level={5} style={{ marginTop: 8, marginBottom: 4 }}>
                              {pkg.name}
                            </Title>
                            {getMembershipTag(pkg.membership_type)}
                            
                            <div style={{ margin: '16px 0' }}>
                              <Text
                                style={{
                                  fontSize: '24px',
                                  fontWeight: 'bold',
                                  color: '#fa8c16'
                                }}
                              >
                                ¥{pkg.price}
                              </Text>
                              {pkg.package_type.includes('monthly') && (
                                <Text type="secondary" style={{ display: 'block', fontSize: '12px' }}>
                                  约 ¥{(pkg.price / (pkg.validity_days / 30)).toFixed(2)}/月
                                </Text>
                              )}
                            </div>

                            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                              <div>
                                <CheckOutlined style={{ color: '#52c41a' }} />
                                <Text style={{ marginLeft: 4 }}>{pkg.queries_count}次查询</Text>
                              </div>
                              <div>
                                <CheckOutlined style={{ color: '#52c41a' }} />
                                <Text style={{ marginLeft: 4 }}>{pkg.validity_days}天有效期</Text>
                              </div>
                              <div>
                                <CheckOutlined style={{ color: '#52c41a' }} />
                                <Text style={{ marginLeft: 4 }}>全功能权限</Text>
                              </div>
                              <div>
                                <CheckOutlined style={{ color: '#52c41a' }} />
                                <Text style={{ marginLeft: 4 }}>优先技术支持</Text>
                              </div>
                            </Space>

                            <Button
                              type="primary"
                              icon={<WechatOutlined />}
                              onClick={() => selectPackage(pkg.package_type)}
                              style={{
                                marginTop: 16,
                                background: 'linear-gradient(45deg, #fadb14, #fa8c16)',
                                borderColor: '#fa8c16',
                                width: '100%'
                              }}
                            >
                              立即购买
                            </Button>
                          </div>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </div>
              )}
            </div>
          )}
        </div>
      </Modal>

      {/* 支付弹窗 */}
      <PaymentModal
        visible={paymentModalVisible}
        onCancel={() => setPaymentModalVisible(false)}
        onSuccess={handlePaymentSuccess}
        packageType={selectedPackage}
      />
    </>
  );
};

export default PaymentPackages;