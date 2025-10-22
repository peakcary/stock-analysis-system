import React from 'react';
import { Card, Row, Col, Typography, Tabs, Tag, Space, Divider } from 'antd';
import {
  CheckCircleOutlined, LineChartOutlined, DatabaseOutlined,
  ApiOutlined, ZoomInOutlined, BarsOutlined, RiseOutlined
} from '@ant-design/icons';
import { motion } from 'framer-motion';

const { Title, Paragraph, Text } = Typography;

interface ServiceFeaturesProps {
  selectedPackageType?: string;
}

const ServiceFeatures: React.FC<ServiceFeaturesProps> = ({ selectedPackageType }) => {
  // 定义不同套餐包含的功能
  const packageFeatures = {
    'queries_10': {
      name: '轻量包',
      features: [
        { category: '查询权限', items: ['10次API查询', '1个股票代码'] },
        { category: '功能限制', items: ['仅基础查询', '无批量操作'] },
        { category: '有效期', items: ['30天有效期'] }
      ]
    },
    'queries_50': {
      name: '进阶包',
      features: [
        { category: '查询权限', items: ['50次API查询', '5个股票代码', '支持批量查询'] },
        { category: '功能权限', items: ['完整概念分析', '行业对比分析', '基础报表导出'] },
        { category: '有效期', items: ['60天有效期'] }
      ]
    },
    'pro_monthly': {
      name: '专业版',
      features: [
        { category: '查询权限', items: ['无限次查询*', '100+个股票代码', '实时数据更新'] },
        { category: '高级功能', items: ['深度概念分析', '智能研报生成', '自定义指标', '数据导出(Excel/PDF)'] },
        { category: '专属服务', items: ['邮件报告(周/月)', '优先技术支持'] },
        { category: '有效期', items: ['按月订阅，随时取消'] }
      ]
    },
    'premium_monthly': {
      name: '旗舰版',
      features: [
        { category: '查询权限', items: ['无限次查询*', '不限股票代码', '实时+历史数据'] },
        { category: '高级功能', items: ['企业级概念分析', 'AI智能预测', '自定义仪表板', '全格式导出'] },
        { category: '专属服务', items: ['每日交易提醒', '专属顾问支持', '优先API访问', '自定义报告'] },
        { category: '企业功能', items: ['团队协作(2人)', '数据同步功能', 'API集成支持'] },
        { category: '有效期', items: ['按月订阅，随时取消'] }
      ]
    }
  };

  const allFeatures = {
    '查询功能': [
      { name: '股票代码查询', free: true, pro: true, premium: true },
      { name: '概念分析', free: false, pro: true, premium: true },
      { name: '行业对比', free: false, pro: true, premium: true },
      { name: '实时数据', free: false, pro: true, premium: true },
      { name: '历史数据', free: false, pro: true, premium: true },
      { name: '批量查询', free: false, pro: true, premium: true }
    ],
    '数据导出': [
      { name: 'Excel导出', free: false, pro: true, premium: true },
      { name: 'PDF报告', free: false, pro: true, premium: true },
      { name: 'CSV格式', free: false, pro: false, premium: true },
      { name: '自定义导出', free: false, pro: false, premium: true }
    ],
    '高级功能': [
      { name: '智能预测', free: false, pro: false, premium: true },
      { name: '自定义仪表板', free: false, pro: false, premium: true },
      { name: '邮件报告', free: false, pro: true, premium: true },
      { name: '数据同步', free: false, pro: false, premium: true },
      { name: 'API集成', free: false, pro: false, premium: true }
    ]
  };

  const selectedPackage = packageFeatures[selectedPackageType as keyof typeof packageFeatures];

  return (
    <div style={{ marginTop: '40px' }}>
      {/* 选中套餐的功能详情 */}
      {selectedPackage && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          style={{ marginBottom: '40px' }}
        >
          <Card style={{ borderRadius: '16px', boxShadow: '0 8px 24px rgba(0,0,0,0.08)' }}>
            <Title level={3}>
              <LineChartOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
              {selectedPackage.name} - 功能详情
            </Title>
            <Divider />

            <Row gutter={[24, 24]}>
              {selectedPackage.features.map((featureGroup, idx) => (
                <Col xs={24} sm={12} md={8} key={idx}>
                  <Card
                    size="small"
                    style={{
                      background: 'linear-gradient(135deg, #f5f7fa 0%, #e4e9f0 100%)',
                      border: 'none'
                    }}
                  >
                    <Text strong style={{ color: '#1890ff', fontSize: '14px' }}>
                      {featureGroup.category}
                    </Text>
                    <Space direction="vertical" style={{ width: '100%', marginTop: '12px' }} size="small">
                      {featureGroup.items.map((item, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center' }}>
                          <CheckCircleOutlined style={{ color: '#52c41a', marginRight: '8px' }} />
                          <Text style={{ fontSize: '12px' }}>{item}</Text>
                        </div>
                      ))}
                    </Space>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>
        </motion.div>
      )}

      {/* 全套餐对比表 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        <Card style={{ borderRadius: '16px', boxShadow: '0 8px 24px rgba(0,0,0,0.08)' }}>
          <Title level={3}>
            <BarsOutlined style={{ marginRight: '8px', color: '#fa8c16' }} />
            全套餐功能对比
          </Title>
          <Divider />

          <Tabs
            items={Object.entries(allFeatures).map(([category, features]) => ({
              key: category,
              label: category,
              children: (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    fontSize: '14px'
                  }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid #e8e8e8' }}>
                        <th style={{
                          padding: '12px',
                          textAlign: 'left',
                          fontWeight: 'bold',
                          color: '#262626'
                        }}>
                          功能
                        </th>
                        <th style={{
                          padding: '12px',
                          textAlign: 'center',
                          fontWeight: 'bold',
                          color: '#262626'
                        }}>
                          免费版
                        </th>
                        <th style={{
                          padding: '12px',
                          textAlign: 'center',
                          fontWeight: 'bold',
                          color: '#1890ff'
                        }}>
                          专业版
                        </th>
                        <th style={{
                          padding: '12px',
                          textAlign: 'center',
                          fontWeight: 'bold',
                          color: '#fadb14'
                        }}>
                          旗舰版
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {features.map((feature, idx) => (
                        <tr
                          key={idx}
                          style={{
                            borderBottom: '1px solid #f0f0f0',
                            backgroundColor: idx % 2 === 0 ? '#fafafa' : 'white'
                          }}
                        >
                          <td style={{ padding: '12px' }}>{feature.name}</td>
                          <td style={{ padding: '12px', textAlign: 'center' }}>
                            {feature.free ? (
                              <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '16px' }} />
                            ) : (
                              <Text type="secondary">-</Text>
                            )}
                          </td>
                          <td style={{ padding: '12px', textAlign: 'center' }}>
                            {feature.pro ? (
                              <CheckCircleOutlined style={{ color: '#1890ff', fontSize: '16px' }} />
                            ) : (
                              <Text type="secondary">-</Text>
                            )}
                          </td>
                          <td style={{ padding: '12px', textAlign: 'center' }}>
                            {feature.premium ? (
                              <CheckCircleOutlined style={{ color: '#fadb14', fontSize: '16px' }} />
                            ) : (
                              <Text type="secondary">-</Text>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            }))}
          />

          <div style={{ marginTop: '24px', padding: '12px', background: '#f6f8fb', borderRadius: '8px' }}>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              <strong>* 无限次查询：</strong> 在套餐有效期内，可无限制使用API查询功能，不受次数限制
            </Text>
          </div>
        </Card>
      </motion.div>
    </div>
  );
};

export default ServiceFeatures;
