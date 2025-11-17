import React, { useState } from 'react';
import {
  Tabs,
  Card,
  Typography,
  message,
} from 'antd';
import {
  StockOutlined,
  FireOutlined,
  RiseOutlined,
  BankOutlined,
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import StockQueryTab from '../components/concept-analysis/StockQueryTab';
import TopNConceptsTab from '../components/concept-analysis/TopNConceptsTab';
import InnovationConceptsTab from '../components/concept-analysis/InnovationConceptsTab';
import ConvertibleBondsTab from '../components/concept-analysis/ConvertibleBondsTab';

const { Title, Paragraph } = Typography;

interface TabItem {
  key: string;
  label: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

const AdvancedConceptAnalysisPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('stock-query');

  const tabs: TabItem[] = [
    {
      key: 'stock-query',
      label: '股票查询',
      icon: <StockOutlined />,
      children: <StockQueryTab />,
    },
    {
      key: 'top-concepts',
      label: '前N概念股',
      icon: <RiseOutlined />,
      children: <TopNConceptsTab />,
    },
    {
      key: 'innovation-concepts',
      label: '创新高概念',
      icon: <FireOutlined />,
      children: <InnovationConceptsTab />,
    },
    {
      key: 'convertible-bonds',
      label: '可转债分析',
      icon: <BankOutlined />,
      children: <ConvertibleBondsTab />,
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      style={{
        minHeight: '100vh',
        padding: '40px 20px',
        background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
      }}
    >
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {/* 页面标题 */}
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          style={{ textAlign: 'center', marginBottom: '40px', color: 'white' }}
        >
          <Title
            level={1}
            style={{
              fontSize: '48px',
              margin: '0 0 16px 0',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            智能概念分析平台
          </Title>
          <Paragraph
            style={{
              fontSize: '18px',
              color: '#64748b',
              maxWidth: '600px',
              margin: '0 auto',
            }}
          >
            深度分析股票概念，发现投资机会
          </Paragraph>
        </motion.div>

        {/* 主要内容区域 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <Card
            bordered={false}
            style={{
              borderRadius: '16px',
              boxShadow: '0 20px 60px rgba(0,0,0,0.1)',
              overflow: 'hidden',
            }}
          >
            <Tabs
              activeKey={activeTab}
              onChange={setActiveTab}
              items={tabs.map((tab) => ({
                key: tab.key,
                label: (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {tab.icon}
                    {tab.label}
                  </span>
                ),
                children: tab.children,
              }))}
              size="large"
            />
          </Card>
        </motion.div>

        {/* 使用提示 */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          style={{
            marginTop: '40px',
            padding: '20px',
            background: 'white',
            borderRadius: '16px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
          }}
        >
          <Title level={4} style={{ marginBottom: '12px' }}>
            功能说明
          </Title>
          <ul style={{ margin: 0, paddingLeft: '20px', color: '#666' }}>
            <li>
              <strong>股票查询</strong>：输入股票代码查看其所属概念及热度排名
            </li>
            <li>
              <strong>前N概念股</strong>：查询所有概念的前N名股票（去重显示）
            </li>
            <li>
              <strong>创新高概念</strong>：发现概念热度在指定天数内创新高的概念
            </li>
            <li>
              <strong>可转债分析</strong>：独立的转债概念分析（1开头代码）
            </li>
          </ul>
        </motion.div>
      </div>
    </motion.div>
  );
};

export default AdvancedConceptAnalysisPage;
