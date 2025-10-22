import React, { useState } from 'react';
import { Card, Row, Col, Typography, Collapse, Button, Space, Steps, Divider, Alert, Form, Input, Select, message } from 'antd';
import {
  CustomerServiceOutlined, CheckOutlined, ClockCircleOutlined,
  PhoneOutlined, MessageOutlined, FileTextOutlined, SendOutlined
} from '@ant-design/icons';
import { motion } from 'framer-motion';

const { Title, Paragraph, Text } = Typography;

const SupportAndIssues: React.FC = () => {
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);

  const issueCategories = [
    {
      title: '常见问题',
      icon: '❓',
      items: [
        {
          q: '如何激活购买的套餐？',
          a: '购买完成后，套餐会立即激活。您可以在个人中心查看已激活的套餐和有效期。'
        },
        {
          q: '如何查询剩余查询次数？',
          a: '登录后进入"我的套餐"页面，可以实时查看您的查询次数、有效期和使用情况。'
        },
        {
          q: '套餐过期后会怎样？',
          a: '套餐过期后，您仍可访问历史数据，但无法进行新的查询。可以选择续费或升级套餐。'
        },
        {
          q: '可以中途升级套餐吗？',
          a: '支持。您可以随时升级到更高级的套餐，差价将自动计算并退款或补收。'
        }
      ]
    },
    {
      title: '技术问题',
      icon: '🔧',
      items: [
        {
          q: 'API请求超时怎么办？',
          a: '请检查网络连接。如问题持续存在，请联系技术支持。我们的API响应时间通常在500ms以内。'
        },
        {
          q: '数据导出失败如何处理？',
          a: '确保您有足够的查询次数。如仍无法导出，清除浏览器缓存后重试，或联系我们的技术团队。'
        },
        {
          q: '如何保证导出数据的安全性？',
          a: '导出数据采用加密传输和SSL保护。数据仅保存在您的本地设备，不会被服务器保留。'
        }
      ]
    },
    {
      title: '账户与支付',
      icon: '💳',
      items: [
        {
          q: '支持哪些支付方式？',
          a: '目前支持微信支付、支付宝等主流支付方式。我们也接受企业转账。'
        },
        {
          q: '如何修改支付信息？',
          a: '进入"账户设置 > 支付信息"可修改绑定的支付方式。更换支付方式后，后续购买将使用新方式。'
        },
        {
          q: '发票如何申请？',
          a: '购买后可在"订单管理"申请发票。企业用户可申请增值税发票。通常在5个工作日内完成。'
        }
      ]
    }
  ];

  const complaintProcess = [
    {
      title: '提交投诉',
      description: '通过客服渠道或本表单提交投诉,请详细描述问题'
    },
    {
      title: '确认收据',
      description: '我们会在24小时内确认收到投诉,并分配处理人员'
    },
    {
      title: '初步调查',
      description: '处理人员进行初步调查,通常需要2-3个工作日'
    },
    {
      title: '提出方案',
      description: '提出解决方案,与您协商处理意见'
    },
    {
      title: '解决确认',
      description: '按照协议方案处理,并要求您确认满意'
    }
  ];

  const onSubmit = async (values: any) => {
    setSubmitting(true);
    try {
      // 模拟提交
      await new Promise(resolve => setTimeout(resolve, 2000));
      message.success('感谢您的反馈,我们会尽快处理!');
      form.resetFields();
    } catch (error) {
      message.error('提交失败,请重试');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ marginTop: '40px' }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Card style={{ borderRadius: '16px', boxShadow: '0 8px 24px rgba(0,0,0,0.08)' }}>
          <Title level={2} style={{ textAlign: 'center', marginBottom: '40px' }}>
            <CustomerServiceOutlined style={{ marginRight: '12px', color: '#1890ff' }} />
            技术支持与问题解决
          </Title>

          {/* 常见问题 */}
          <div style={{ marginBottom: '40px' }}>
            <Title level={3} style={{ marginBottom: '24px' }}>常见问题解答</Title>
            <Collapse
              items={issueCategories.map((category) => ({
                key: category.title,
                label: (
                  <Space>
                    <span>{category.icon}</span>
                    <strong>{category.title}</strong>
                  </Space>
                ),
                children: (
                  <div>
                    {category.items.map((item, idx) => (
                      <div key={idx} style={{ marginBottom: '16px' }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          marginBottom: '8px'
                        }}>
                          <span style={{
                            color: '#1890ff',
                            fontWeight: 'bold',
                            marginRight: '8px',
                            minWidth: '20px'
                          }}>Q:</span>
                          <span style={{ fontWeight: '500' }}>{item.q}</span>
                        </div>
                        <div style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          marginLeft: '28px',
                          color: '#666'
                        }}>
                          <span style={{
                            color: '#52c41a',
                            fontWeight: 'bold',
                            marginRight: '8px'
                          }}>A:</span>
                          <span>{item.a}</span>
                        </div>
                        {idx < category.items.length - 1 && <Divider style={{ margin: '12px 0' }} />}
                      </div>
                    ))}
                  </div>
                )
              }))}
            />
          </div>

          <Divider />

          {/* 投诉解决流程 */}
          <div style={{ marginBottom: '40px' }}>
            <Title level={3} style={{ marginBottom: '24px' }}>
              <FileTextOutlined style={{ marginRight: '8px' }} />
              投诉解决流程
            </Title>
            <Steps
              current={-1}
              items={complaintProcess.map((step, idx) => ({
                title: step.title,
                description: step.description,
                icon: idx === 0 ? <MessageOutlined /> :
                      idx === 1 ? <ClockCircleOutlined /> :
                      idx === 2 ? <CustomerServiceOutlined /> :
                      idx === 3 ? <FileTextOutlined /> : <CheckOutlined />,
              }))}
            />
          </div>

          {/* 提交投诉表单 */}
          <div style={{
            padding: '24px',
            background: '#f5f7fa',
            borderRadius: '12px',
            marginBottom: '24px'
          }}>
            <Title level={4}>提交问题或投诉</Title>
            <Form
              form={form}
              layout="vertical"
              onFinish={onSubmit}
            >
              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    name="name"
                    label="您的名字"
                    rules={[{ required: true, message: '请输入名字' }]}
                  >
                    <Input placeholder="请输入您的名字" />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item
                    name="email"
                    label="邮箱地址"
                    rules={[
                      { required: true, message: '请输入邮箱' },
                      { type: 'email', message: '请输入有效邮箱' }
                    ]}
                  >
                    <Input placeholder="请输入邮箱地址" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="category"
                label="问题分类"
                rules={[{ required: true, message: '请选择问题分类' }]}
              >
                <Select placeholder="选择问题分类">
                  <Select.Option value="billing">账户与支付</Select.Option>
                  <Select.Option value="technical">技术问题</Select.Option>
                  <Select.Option value="complaint">投诉</Select.Option>
                  <Select.Option value="suggestion">建议</Select.Option>
                  <Select.Option value="other">其他</Select.Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="title"
                label="问题标题"
                rules={[{ required: true, message: '请输入问题标题' }]}
              >
                <Input placeholder="请简要描述问题标题" />
              </Form.Item>

              <Form.Item
                name="description"
                label="详细描述"
                rules={[{ required: true, message: '请输入详细描述' }]}
              >
                <Input.TextArea
                  rows={5}
                  placeholder="请详细描述您遇到的问题,包括时间、操作步骤等信息"
                />
              </Form.Item>

              <Form.Item
                name="attachment"
                label="附件(可选)"
              >
                <Input placeholder="您可以描述相关截图或附件" />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={submitting}
                  icon={<SendOutlined />}
                  block
                  size="large"
                >
                  提交问题
                </Button>
              </Form.Item>
            </Form>
          </div>

          <Alert
            message="提交后处理"
            description={
              <div>
                <p style={{ margin: '8px 0' }}>
                  • 我们会在24小时内以邮件形式确认收到您的问题
                </p>
                <p style={{ margin: '8px 0' }}>
                  • 根据问题复杂度,通常在3-5个工作日内提供解决方案
                </p>
                <p style={{ margin: '8px 0' }}>
                  • 对于紧急问题,我们会优先处理
                </p>
                <p style={{ margin: '8px 0' }}>
                  • 您可以通过邮件或客服渠道跟进处理进展
                </p>
              </div>
            }
            type="info"
            showIcon
          />
        </Card>
      </motion.div>

      {/* 多渠道支持 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        style={{ marginTop: '24px' }}
      >
        <Card style={{ borderRadius: '16px', boxShadow: '0 8px 24px rgba(0,0,0,0.08)' }}>
          <Title level={3} style={{ textAlign: 'center', marginBottom: '32px' }}>
            <PhoneOutlined style={{ marginRight: '8px', color: '#52c41a' }} />
            多渠道支持
          </Title>

          <Row gutter={[24, 24]}>
            {[
              {
                title: '在线客服',
                icon: '💬',
                time: '工作日 9:00-18:00',
                desc: '实时在线,快速响应您的问题'
              },
              {
                title: '邮件支持',
                icon: '📧',
                time: '全天24小时',
                desc: 'support@qwquant.com'
              },
              {
                title: '电话支持',
                icon: '☎️',
                time: '工作日 9:00-18:00',
                desc: '直接联系技术团队'
              },
              {
                title: '微信反馈',
                icon: '👤',
                time: '全天24小时',
                desc: '关注公众号进行反馈'
              }
            ].map((channel, idx) => (
              <Col xs={24} sm={12} md={6} key={idx}>
                <Card
                  size="small"
                  style={{
                    textAlign: 'center',
                    border: 'none',
                    boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
                    borderRadius: '12px',
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center'
                  }}
                >
                  <div style={{ fontSize: '32px', marginBottom: '12px' }}>
                    {channel.icon}
                  </div>
                  <Title level={5} style={{ margin: 0, marginBottom: '8px' }}>
                    {channel.title}
                  </Title>
                  <Text type="secondary" style={{ fontSize: '12px', marginBottom: '8px' }}>
                    {channel.time}
                  </Text>
                  <Text style={{ fontSize: '12px', color: '#666' }}>
                    {channel.desc}
                  </Text>
                </Card>
              </Col>
            ))}
          </Row>

          <Divider style={{ margin: '32px 0' }} />

          <Alert
            message="服务承诺"
            description={
              <div>
                <p style={{ margin: '8px 0' }}>
                  • <strong>响应时间：</strong> 一般问题在1小时内响应,紧急问题立即处理
                </p>
                <p style={{ margin: '8px 0' }}>
                  • <strong>解决率：</strong> 力争一次性解决90%以上的问题
                </p>
                <p style={{ margin: '8px 0' }}>
                  • <strong>满意度：</strong> 每个问题完成后请您评分,帮助我们不断改进
                </p>
                <p style={{ margin: '8px 0' }}>
                  • <strong>隐私保护：</strong> 您的反馈信息仅用于问题处理,绝不会用于其他目的
                </p>
              </div>
            }
            type="success"
            showIcon
          />
        </Card>
      </motion.div>

      {/* 用户反馈与建议 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        style={{ marginTop: '24px' }}
      >
        <Card style={{ borderRadius: '16px', boxShadow: '0 8px 24px rgba(0,0,0,0.08)' }}>
          <Title level={3} style={{ textAlign: 'center', marginBottom: '24px' }}>
            用户反馈与建议
          </Title>

          <Alert
            message="我们重视您的声音"
            description={
              <div>
                <p>
                  无论您是对我们的服务有意见,还是对新功能有建议,我们都非常欢迎听到您的想法。
                </p>
                <p>
                  您的反馈直接帮助我们改进产品和服务质量。定期优秀建议的用户,我们会提供服务折扣作为感谢。
                </p>
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: '16px' }}
          />

          <Space style={{ width: '100%', marginTop: '16px' }} direction="vertical">
            <Button type="primary" size="large" block>
              提交建议
            </Button>
            <Button size="large" block>
              查看改进历史
            </Button>
          </Space>
        </Card>
      </motion.div>
    </div>
  );
};

export default SupportAndIssues;
