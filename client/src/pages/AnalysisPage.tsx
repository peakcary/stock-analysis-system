import React, { useState, useEffect } from 'react';
import { 
  Card, Row, Col, Statistic, Select, DatePicker, Space, Typography, 
  Badge, Tooltip, Button, Drawer, Table, Tag, Segmented, Empty,
  Input, Tabs, Progress, Alert, Spin, List, Avatar
} from 'antd';
import { 
  ArrowUpOutlined, ArrowDownOutlined, FireOutlined,
  SearchOutlined, BulbOutlined, DollarOutlined, BarChartOutlined,
  LineChartOutlined, PieChartOutlined, FundOutlined, StockOutlined,
  FilterOutlined, FullscreenOutlined, StarOutlined, EyeOutlined,
  ThunderboltOutlined, CaretUpOutlined, CaretDownOutlined, CrownOutlined
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import ReactECharts from 'echarts-for-react';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;
const { TabPane } = Tabs;

interface AnalysisPageProps {
  user: any;
}

// 模拟数据
const mockData = {
  overview: {
    totalStocks: 4892,
    activeStocks: 3247,
    totalIndustries: 28,
    totalConcepts: 142,
    totalNetInflow: 158.7,
    averageHeat: 67.3,
    topGainer: { name: '人工智能', value: '+15.7%', color: '#10b981' },
    topDecliner: { name: '地产', value: '-8.3%', color: '#ef4444' }
  },
  hotStocks: [
    { code: '002594', name: '比亚迪', price: 245.80, change: 8.5, volume: 1250000, heat: 95, concepts: ['新能源', '汽车'], industry: '汽车制造' },
    { code: '300750', name: '宁德时代', price: 178.90, change: 6.2, volume: 890000, heat: 89, concepts: ['锂电池', '新能源'], industry: '电池制造' },
    { code: '000858', name: '五粮液', price: 156.70, change: -2.1, volume: 650000, heat: 76, concepts: ['白酒', '消费'], industry: '食品饮料' },
    { code: '600036', name: '招商银行', price: 42.80, change: 1.8, volume: 2100000, heat: 72, concepts: ['银行', '金融'], industry: '银行' },
    { code: '000002', name: '万科A', price: 18.45, change: -1.2, volume: 1800000, heat: 68, concepts: ['地产', '城镇化'], industry: '房地产' }
  ],
  industries: [
    { name: '新能源汽车', change: 12.5, stocks: 156, volume: 45.2, heat: 94 },
    { name: '半导体', change: 8.7, stocks: 89, volume: 32.1, heat: 87 },
    { name: '生物医药', change: 6.3, stocks: 134, volume: 28.9, heat: 82 },
    { name: '军工航天', change: 4.8, stocks: 67, volume: 21.5, heat: 78 },
    { name: '银行', change: -2.1, stocks: 34, volume: -15.3, heat: 65 }
  ],
  concepts: [
    { name: '人工智能', heat: 95, change: 28, stocks: 45, reason: 'ChatGPT概念持续发酵' },
    { name: '碳中和', heat: 87, change: 15, stocks: 78, reason: '政策利好频出' },
    { name: '元宇宙', heat: 72, change: -8, stocks: 23, reason: '市场降温调整' },
    { name: '数字货币', heat: 68, change: 12, stocks: 34, reason: '央行数字货币试点' },
    { name: '工业母机', heat: 65, change: 5, stocks: 56, reason: '制造业升级需求' }
  ]
};

export const AnalysisPage: React.FC<AnalysisPageProps> = ({ user }) => {
  const [selectedView, setSelectedView] = useState<'overview' | 'stocks' | 'industry' | 'concept'>('overview');
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedStock, setSelectedStock] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');

  // 根据用户会员等级限制功能
  const isMember = user?.memberType !== 'free';
  const isPremium = user?.memberType === 'premium';

  const handleViewChange = (view: string) => {
    if (!isMember && view !== 'overview') {
      // 非会员只能查看概览
      return;
    }
    setSelectedView(view as any);
  };

  const handleStockClick = (stock: any) => {
    if (!isMember) {
      // 非会员需要升级
      return;
    }
    setSelectedStock(stock);
    setDetailVisible(true);
  };

  // 总览页面
  const OverviewPage = () => (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* 核心指标 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
        <Col xs={12} sm={6}>
          <Card style={{ borderRadius: '16px', textAlign: 'center' }}>
            <Statistic
              title="今日活跃股票"
              value={mockData.overview.activeStocks}
              suffix={`/ ${mockData.overview.totalStocks}`}
              prefix={<StockOutlined style={{ color: '#3b82f6' }} />}
              valueStyle={{ color: '#3b82f6', fontSize: '20px' }}
            />
          </Card>
        </Col>
        
        <Col xs={12} sm={6}>
          <Card style={{ borderRadius: '16px', textAlign: 'center' }}>
            <Statistic
              title="净流入总额"
              value={mockData.overview.totalNetInflow}
              suffix="亿"
              prefix={<DollarOutlined style={{ color: '#10b981' }} />}
              valueStyle={{ 
                color: mockData.overview.totalNetInflow > 0 ? '#10b981' : '#ef4444',
                fontSize: '20px'
              }}
            />
            <Progress 
              percent={Math.min(Math.abs(mockData.overview.totalNetInflow) / 200 * 100, 100)}
              strokeColor="#10b981"
              showInfo={false}
              size="small"
              style={{ marginTop: '8px' }}
            />
          </Card>
        </Col>
        
        <Col xs={12} sm={6}>
          <Card style={{ borderRadius: '16px', textAlign: 'center' }}>
            <Statistic
              title="市场热度"
              value={mockData.overview.averageHeat}
              suffix="分"
              prefix={<FireOutlined style={{ color: '#f59e0b' }} />}
              valueStyle={{ color: '#f59e0b', fontSize: '20px' }}
            />
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#6b7280' }}>
              较昨日 <span style={{ color: '#10b981' }}>+5.2%</span>
            </div>
          </Card>
        </Col>
        
        <Col xs={12} sm={6}>
          <Card style={{ borderRadius: '16px', textAlign: 'center' }}>
            <div style={{ marginBottom: '8px' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>涨幅领先</Text>
              <div style={{ 
                color: mockData.overview.topGainer.color, 
                fontWeight: '600',
                fontSize: '16px'
              }}>
                <CaretUpOutlined /> {mockData.overview.topGainer.name}
              </div>
              <Text style={{ color: mockData.overview.topGainer.color, fontSize: '14px' }}>
                {mockData.overview.topGainer.value}
              </Text>
            </div>
            <div>
              <Text type="secondary" style={{ fontSize: '12px' }}>跌幅领先</Text>
              <div style={{ 
                color: mockData.overview.topDecliner.color, 
                fontWeight: '600',
                fontSize: '16px'
              }}>
                <CaretDownOutlined /> {mockData.overview.topDecliner.name}
              </div>
              <Text style={{ color: mockData.overview.topDecliner.color, fontSize: '14px' }}>
                {mockData.overview.topDecliner.value}
              </Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 热门股票 */}
      <Card 
        title={
          <Space>
            <FireOutlined style={{ color: '#ef4444' }} />
            <span>热门股票</span>
            <Badge count={5} style={{ backgroundColor: '#ef4444' }} />
          </Space>
        }
        extra={isMember && <Button type="link">查看更多</Button>}
        style={{ borderRadius: '16px', marginBottom: 24 }}
      >
        <div style={{ overflowX: 'auto' }}>
          {mockData.hotStocks.map((stock, index) => (
            <motion.div
              key={stock.code}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              onClick={() => handleStockClick(stock)}
              style={{
                padding: '16px',
                borderRadius: '12px',
                marginBottom: '12px',
                background: index % 2 === 0 ? '#fafafa' : 'white',
                border: '1px solid #f0f0f0',
                cursor: isMember ? 'pointer' : 'not-allowed',
                opacity: !isMember ? 0.6 : 1,
                position: 'relative'
              }}
              whileHover={isMember ? { scale: 1.02, backgroundColor: '#f8fafc' } : {}}
            >
              {!isMember && (
                <div style={{
                  position: 'absolute',
                  top: '8px',
                  right: '8px',
                  background: '#f59e0b',
                  color: 'white',
                  padding: '2px 8px',
                  borderRadius: '8px',
                  fontSize: '10px'
                }}>
                  会员专享
                </div>
              )}
              
              <Row align="middle">
                <Col xs={24} sm={6}>
                  <div>
                    <Text strong style={{ fontSize: '16px' }}>{stock.name}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '12px' }}>{stock.code}</Text>
                  </div>
                </Col>
                
                <Col xs={12} sm={4}>
                  <div>
                    <div style={{ fontSize: '18px', fontWeight: '600' }}>
                      ¥{stock.price.toFixed(2)}
                    </div>
                    <div style={{
                      fontSize: '12px',
                      color: stock.change >= 0 ? '#10b981' : '#ef4444',
                      display: 'flex',
                      alignItems: 'center'
                    }}>
                      {stock.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                      <span style={{ marginLeft: '2px' }}>
                        {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)}%
                      </span>
                    </div>
                  </div>
                </Col>
                
                <Col xs={12} sm={4}>
                  <div>
                    <Text type="secondary" style={{ fontSize: '12px' }}>热度</Text>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Progress
                        percent={stock.heat}
                        strokeColor="#f59e0b"
                        size="small"
                        style={{ flex: 1 }}
                        showInfo={false}
                      />
                      <Text style={{ fontSize: '12px', color: '#f59e0b', fontWeight: '600' }}>
                        {stock.heat}
                      </Text>
                    </div>
                  </div>
                </Col>
                
                <Col xs={24} sm={6}>
                  <div>
                    <Text type="secondary" style={{ fontSize: '12px' }}>成交量</Text>
                    <div style={{ fontSize: '14px', fontWeight: '500' }}>
                      {(stock.volume / 10000).toFixed(1)}万手
                    </div>
                  </div>
                </Col>
                
                <Col xs={24} sm={4}>
                  <Space wrap size={[4, 4]}>
                    {stock.concepts.slice(0, 2).map(concept => (
                      <Tag key={concept} style={{ fontSize: '10px' }}>
                        {concept}
                      </Tag>
                    ))}
                  </Space>
                </Col>
              </Row>
            </motion.div>
          ))}
        </div>

        {!isMember && (
          <Alert
            message="升级会员解锁完整功能"
            description="升级为专业版会员，查看详细的股票分析、实时数据和专业报告"
            type="warning"
            action={
              <Button type="primary" size="small">
                立即升级
              </Button>
            }
            style={{ marginTop: '16px' }}
          />
        )}
      </Card>

      {/* 行业和概念表现 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card 
            title="行业表现排行"
            extra={isMember && <Button type="link">查看全部</Button>}
            style={{ borderRadius: '16px' }}
          >
            <IndustryRanking industries={mockData.industries} isMember={isMember} />
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card 
            title="热门概念追踪"
            extra={isMember && <Button type="link">查看全部</Button>}
            style={{ borderRadius: '16px' }}
          >
            <ConceptTracking concepts={mockData.concepts} isMember={isMember} />
          </Card>
        </Col>
      </Row>
    </motion.div>
  );

  return (
    <div style={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
      padding: '20px'
    }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {/* 顶部控制栏 */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '24px',
            flexWrap: 'wrap',
            gap: '16px'
          }}
        >
          <div>
            <Title level={2} style={{ margin: 0, color: '#1f2937' }}>
              智能股票分析
            </Title>
            <Text type="secondary">
              实时数据 • 最后更新: {dayjs().format('HH:mm:ss')}
            </Text>
          </div>
          
          <Space size="middle" wrap>
            <Segmented
              value={selectedView}
              onChange={handleViewChange}
              options={[
                { 
                  label: (
                    <Tooltip title={!isMember ? "会员专享" : ""}>
                      <Space>
                        <BarChartOutlined />
                        <span>总览</span>
                      </Space>
                    </Tooltip>
                  ), 
                  value: 'overview' 
                },
                { 
                  label: (
                    <Tooltip title={!isMember ? "升级会员解锁" : ""}>
                      <Space>
                        <LineChartOutlined />
                        <span>个股</span>
                        {!isMember && <Badge dot />}
                      </Space>
                    </Tooltip>
                  ), 
                  value: 'stocks',
                  disabled: !isMember
                },
                { 
                  label: (
                    <Tooltip title={!isMember ? "升级会员解锁" : ""}>
                      <Space>
                        <PieChartOutlined />
                        <span>行业</span>
                        {!isMember && <Badge dot />}
                      </Space>
                    </Tooltip>
                  ), 
                  value: 'industry',
                  disabled: !isMember
                },
                { 
                  label: (
                    <Tooltip title={!isMember ? "升级会员解锁" : ""}>
                      <Space>
                        <BulbOutlined />
                        <span>概念</span>
                        {!isMember && <Badge dot />}
                      </Space>
                    </Tooltip>
                  ), 
                  value: 'concept',
                  disabled: !isMember
                }
              ]}
            />
            
            {isMember && (
              <>
                <RangePicker 
                  size="middle"
                  style={{ borderRadius: '8px' }}
                  presets={[
                    { label: '今日', value: [dayjs().startOf('day'), dayjs().endOf('day')] },
                    { label: '本周', value: [dayjs().startOf('week'), dayjs().endOf('week')] },
                    { label: '本月', value: [dayjs().startOf('month'), dayjs().endOf('month')] }
                  ]}
                />
                
                <Button 
                  icon={<FilterOutlined />} 
                  style={{ borderRadius: '8px' }}
                >
                  筛选
                </Button>
              </>
            )}
          </Space>
        </motion.div>

        {/* 主内容区域 */}
        <AnimatePresence mode="wait">
          <motion.div
            key={selectedView}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            {selectedView === 'overview' && <OverviewPage />}
            {selectedView === 'stocks' && <StocksPage />}
            {selectedView === 'industry' && <IndustryPage />}
            {selectedView === 'concept' && <ConceptPage />}
          </motion.div>
        </AnimatePresence>

        {/* 股票详情抽屉 */}
        <StockDetailDrawer
          visible={detailVisible}
          onClose={() => setDetailVisible(false)}
          stock={selectedStock}
          isPremium={isPremium}
        />
      </div>
    </div>
  );
};

// 行业排行组件
const IndustryRanking: React.FC<{ industries: any[], isMember: boolean }> = ({ industries, isMember }) => {
  return (
    <div>
      {industries.map((industry, index) => (
        <motion.div 
          key={index}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.1 }}
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '12px 0',
            borderBottom: index < industries.length - 1 ? '1px solid #f0f0f0' : 'none',
            opacity: !isMember && index > 2 ? 0.5 : 1,
            filter: !isMember && index > 2 ? 'blur(2px)' : 'none'
          }}
        >
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                background: industry.change >= 0 ? '#10b981' : '#ef4444',
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '12px',
                fontWeight: '600'
              }}>
                {index + 1}
              </div>
              <div>
                <div style={{ fontWeight: '600', fontSize: '14px' }}>
                  {industry.name}
                </div>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {industry.stocks}只股票 • 成交{Math.abs(industry.volume)}亿
                </Text>
              </div>
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{
              color: industry.change >= 0 ? '#10b981' : '#ef4444',
              fontWeight: '600',
              fontSize: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              {industry.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              {industry.change >= 0 ? '+' : ''}{industry.change.toFixed(1)}%
            </div>
            <div style={{ fontSize: '10px', color: '#9ca3af', marginTop: '2px' }}>
              热度 {industry.heat}
            </div>
          </div>
        </motion.div>
      ))}
      
      {!isMember && (
        <div style={{
          position: 'relative',
          marginTop: '12px',
          padding: '12px',
          background: 'linear-gradient(135deg, #fef3c7 0%, #fbbf24 100%)',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <Text style={{ color: '#92400e', fontSize: '12px', fontWeight: '600' }}>
            🔐 升级会员查看完整排行榜
          </Text>
        </div>
      )}
    </div>
  );
};

// 概念追踪组件
const ConceptTracking: React.FC<{ concepts: any[], isMember: boolean }> = ({ concepts, isMember }) => {
  return (
    <div>
      {concepts.map((concept, index) => (
        <motion.div 
          key={index}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: index * 0.1 }}
          style={{
            padding: '12px',
            borderRadius: '8px',
            marginBottom: '8px',
            background: index % 2 === 0 ? '#fafafa' : 'white',
            border: '1px solid #f0f0f0',
            opacity: !isMember && index > 2 ? 0.5 : 1,
            filter: !isMember && index > 2 ? 'blur(1px)' : 'none'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: '600', fontSize: '14px', marginBottom: '4px' }}>
                {concept.name}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <Progress
                  percent={concept.heat}
                  size="small"
                  strokeColor="#f59e0b"
                  showInfo={false}
                  style={{ width: '60px' }}
                />
                <Text style={{ fontSize: '10px', color: '#f59e0b', fontWeight: '600' }}>
                  {concept.heat}
                </Text>
              </div>
              <Text type="secondary" style={{ fontSize: '11px' }}>
                {concept.reason}
              </Text>
            </div>
            <div style={{ textAlign: 'right', marginLeft: '12px' }}>
              <div style={{
                color: concept.change >= 0 ? '#10b981' : '#ef4444',
                fontWeight: '600',
                fontSize: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '2px'
              }}>
                {concept.change >= 0 ? <CaretUpOutlined /> : <CaretDownOutlined />}
                {concept.change >= 0 ? '+' : ''}{concept.change}%
              </div>
              <Text type="secondary" style={{ fontSize: '10px' }}>
                {concept.stocks}只股票
              </Text>
            </div>
          </div>
        </motion.div>
      ))}
      
      {!isMember && (
        <div style={{
          position: 'relative',
          marginTop: '12px',
          padding: '12px',
          background: 'linear-gradient(135deg, #dbeafe 0%, #3b82f6 100%)',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <Text style={{ color: 'white', fontSize: '12px', fontWeight: '600' }}>
            ⭐ 升级解锁概念深度分析
          </Text>
        </div>
      )}
    </div>
  );
};

// 其他页面组件（占位符）
const StocksPage = () => (
  <Card style={{ textAlign: 'center', padding: '60px', borderRadius: '16px' }}>
    <Title level={3}>🔍 个股分析</Title>
    <Paragraph>专业的个股分析工具，提供详细的技术分析和基本面分析</Paragraph>
  </Card>
);

const IndustryPage = () => (
  <Card style={{ textAlign: 'center', padding: '60px', borderRadius: '16px' }}>
    <Title level={3}>🏭 行业分析</Title>
    <Paragraph>全面的行业对比分析，把握行业轮动机会</Paragraph>
  </Card>
);

const ConceptPage = () => (
  <Card style={{ textAlign: 'center', padding: '60px', borderRadius: '16px' }}>
    <Title level={3}>💡 概念追踪</Title>
    <Paragraph>智能概念热点追踪，捕捉市场热点变化</Paragraph>
  </Card>
);

// 股票详情抽屉
const StockDetailDrawer: React.FC<{
  visible: boolean;
  onClose: () => void;
  stock: any;
  isPremium: boolean;
}> = ({ visible, onClose, stock, isPremium }) => {
  if (!stock) return null;

  return (
    <Drawer
      title={`${stock.name} (${stock.code})`}
      open={visible}
      onClose={onClose}
      width={600}
      style={{ borderRadius: '16px 0 0 16px' }}
    >
      <div>
        <Card style={{ marginBottom: '16px', borderRadius: '12px' }}>
          <Row gutter={16}>
            <Col span={12}>
              <Statistic
                title="当前价格"
                value={stock.price}
                prefix="¥"
                precision={2}
                valueStyle={{ fontSize: '24px' }}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="涨跌幅"
                value={stock.change}
                suffix="%"
                precision={2}
                valueStyle={{ 
                  color: stock.change >= 0 ? '#10b981' : '#ef4444',
                  fontSize: '24px'
                }}
                prefix={stock.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              />
            </Col>
          </Row>
        </Card>

        {isPremium ? (
          <div>
            <Title level={4}>技术分析</Title>
            <div style={{ 
              height: '300px', 
              background: '#f8fafc', 
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Text type="secondary">专业K线图表区域</Text>
            </div>
          </div>
        ) : (
          <Card style={{ textAlign: 'center', borderRadius: '12px' }}>
            <Title level={4} style={{ color: '#f59e0b' }}>
              <CrownOutlined /> 旗舰版专享
            </Title>
            <Paragraph type="secondary">
              升级旗舰版解锁完整的技术分析功能
            </Paragraph>
            <Button type="primary">立即升级</Button>
          </Card>
        )}
      </div>
    </Drawer>
  );
};

export default AnalysisPage;