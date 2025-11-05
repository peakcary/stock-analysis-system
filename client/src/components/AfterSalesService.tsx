import React from 'react';
import { Card, Row, Col, Typography, Collapse, Space, Divider, Timeline, Alert, Tag } from 'antd';
import {
  SafetyOutlined, ThunderboltOutlined, CheckCircleOutlined,
  ClockCircleOutlined, PhoneOutlined, MailOutlined, FileTextOutlined
} from '@ant-design/icons';
import { motion } from 'framer-motion';

const { Title, Paragraph, Text } = Typography;

const AfterSalesService: React.FC = () => {
  const serviceItems = [
    {
      title: '7天无理由退款',
      icon: <ThunderboltOutlined style={{ fontSize: '32px', color: '#52c41a' }} />,
      content: '购买后7天内如对服务不满意，可申请全额退款。无需提供任何理由，退款流程简单快捷。',
      details: [
        '• 支持所有付款方式的退款',
        '• 退款金额原路返回',
        '• 一般3-5个工作日到账',
        '• 无隐藏费用'
      ]
    },
    {
      title: '数据安全保护',
      icon: <SafetyOutlined style={{ fontSize: '32px', color: '#1890ff' }} />,
      content: '采用银行级别的数据加密和安全防护措施，确保您的数据安全。',
      details: [
        '• SSL/TLS 256位加密传输',
        '• 符合国际数据安全标准',
        '• 定期安全审计和漏洞扫描',
        '• 数据备份与恢复机制'
      ]
    },
    {
      title: '持续性升级更新',
      icon: <FileTextOutlined style={{ fontSize: '32px', color: '#fa8c16' }} />,
      content: '我们持续投入研发，定期更新功能和改进服务。',
      details: [
        '• 每月更新新功能',
        '• 性能持续优化',
        '• 用户反馈快速响应',
        '• 免费获享所有升级'
      ]
    }
  ];

  const warrantyTerms = [
    {
      title: '服务可用性保证',
      content: '我们承诺99.5%的服务可用性。如由于我们的原因导致服务中断，将提供相应的服务补偿。'
    },
    {
      title: '数据隐私保护',
      content: '您的交易数据和个人信息受《用户隐私政策》保护，不会被用于其他目的，不会与第三方共享。'
    },
    {
      title: '技术支持保障',
      content: '提供7×24小时的技术支持。一般问题在1小时内响应，紧急问题立即处理。'
    },
    {
      title: '收费透明承诺',
      content: '按套餐标价收费，无隐藏费用。续费前将提前7天通知，用户可自由选择是否续费。'
    }
  ];

  const processSteps = [
    { title: '购买', description: '选择适合的套餐，完成支付' },
    { title: '激活', description: '套餐立即激活，享受所有权益' },
    { title: '使用', description: '在有效期内使用所有功能' },
    { title: '续费', description: '期满前可续费或升级套餐' },
    { title: '退款', description: '7天内可申请退款' }
  ];

  return (
    <div style={{ marginTop: '40px' }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Card style={{ borderRadius: '16px', boxShadow: '0 8px 24px rgba(0,0,0,0.08)' }}>
          <Title level={2} style={{ textAlign: 'center', marginBottom: '40px' }}>
            <SafetyOutlined style={{ marginRight: '12px', color: '#10b981' }} />
            售后服务保障
          </Title>

          {/* 核心服务 */}
          <div style={{ marginBottom: '40px' }}>
            <Title level={3} style={{ marginBottom: '24px' }}>核心服务承诺</Title>
            <Row gutter={[24, 24]}>
              {serviceItems.map((item, idx) => (
                <Col xs={24} sm={12} md={8} key={idx}>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.1 }}
                  >
                    <Card
                      style={{
                        borderRadius: '12px',
                        height: '100%',
                        border: 'none',
                        boxShadow: '0 2px 12px rgba(0,0,0,0.06)'
                      }}
                    >
                      <div style={{ textAlign: 'center', marginBottom: '16px' }}>
                        {item.icon}
                      </div>
                      <Title level={4} style={{ textAlign: 'center', marginBottom: '8px' }}>
                        {item.title}
                      </Title>
                      <Paragraph style={{ textAlign: 'center', fontSize: '12px', marginBottom: '12px' }}>
                        {item.content}
                      </Paragraph>
                      <Divider style={{ margin: '12px 0' }} />
                      <Space direction="vertical" size="small" style={{ width: '100%' }}>
                        {item.details.map((detail, i) => (
                          <Text key={i} style={{ fontSize: '12px', color: '#666' }}>
                            {detail}
                          </Text>
                        ))}
                      </Space>
                    </Card>
                  </motion.div>
                </Col>
              ))}
            </Row>
          </div>

          <Divider />

          {/* 服务流程 */}
          <div style={{ marginBottom: '40px' }}>
            <Title level={3} style={{ marginBottom: '24px' }}>服务流程</Title>
            <Timeline
              items={processSteps.map((step, idx) => ({
                children: (
                  <div>
                    <Title level={5} style={{ margin: 0, marginBottom: '4px' }}>
                      {idx + 1}. {step.title}
                    </Title>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {step.description}
                    </Text>
                  </div>
                ),
                dot: <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '16px' }} />
              }))}
            />
          </div>

          <Divider />

          {/* 服务承诺 */}
          <div style={{ marginBottom: '40px' }}>
            <Title level={3} style={{ marginBottom: '24px' }}>
              <SafetyOutlined style={{ marginRight: '8px' }} />
              完整服务承诺
            </Title>
            <Collapse
              items={warrantyTerms.map((item, idx) => ({
                key: idx,
                label: (
                  <Space>
                    <CheckCircleOutlined style={{ color: '#52c41a' }} />
                    <span>{item.title}</span>
                  </Space>
                ),
                children: <Paragraph>{item.content}</Paragraph>
              }))}
            />
          </div>

          <Divider />

          {/* 重要提示 */}
          <Alert
            message="重要提示"
            description={
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>• 所有承诺基于服务条款，详细条款请查看《完整服务条款》</div>
                <div>• 退款申请需在购买后7天内提出，逾期不再受理</div>
                <div>• 如因用户原因导致数据损失，我们不承担责任</div>
                <div>• 续费前30天，我们将通过邮件提醒用户</div>
              </Space>
            }
            type="info"
            showIcon
            style={{ marginTop: '24px' }}
          />
        </Card>
      </motion.div>

      {/* 联系我们 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        style={{ marginTop: '24px' }}
      >
        <Card style={{ borderRadius: '16px', boxShadow: '0 8px 24px rgba(0,0,0,0.08)' }}>
          <Title level={3} style={{ textAlign: 'center', marginBottom: '24px' }}>
            <PhoneOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
            联系客服
          </Title>

          <Row gutter={[24, 24]}>
            <Col xs={24} sm={12} md={8}>
              <Card size="small" style={{ textAlign: 'center', border: 'none', background: '#f5f7fa' }}>
                <MailOutlined style={{ fontSize: '32px', color: '#1890ff', marginBottom: '12px' }} />
                <div>
                  <Title level={5}>邮件支持</Title>
                  <Text type="secondary">support@qwquant.com</Text>
                </div>
              </Card>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Card size="small" style={{ textAlign: 'center', border: 'none', background: '#f5f7fa' }}>
                <PhoneOutlined style={{ fontSize: '32px', color: '#52c41a', marginBottom: '12px' }} />
                <div>
                  <Title level={5}>在线客服</Title>
                  <Text type="secondary">工作日 9:00-18:00</Text>
                </div>
              </Card>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Card size="small" style={{ textAlign: 'center', border: 'none', background: '#f5f7fa' }}>
                <ClockCircleOutlined style={{ fontSize: '32px', color: '#fa8c16', marginBottom: '12px' }} />
                <div>
                  <Title level={5}>应急支持</Title>
                  <Text type="secondary">7×24小时</Text>
                </div>
              </Card>
            </Col>
          </Row>
        </Card>
      </motion.div>
    </div>
  );
};

export default AfterSalesService;
