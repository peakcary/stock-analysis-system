import React, { useState, useEffect } from 'react';
import { 
  Card, Row, Col, Statistic, Select, DatePicker, Space, Typography, 
  Badge, Tooltip, Button, Drawer, Table, Tag, Segmented, Empty,
  Input, Tabs, Progress, Alert, Spin, List, Avatar, message
} from 'antd';
import { 
  ArrowUpOutlined, ArrowDownOutlined, FireOutlined,
  SearchOutlined, BulbOutlined, DollarOutlined, BarChartOutlined,
  LineChartOutlined, PieChartOutlined, FundOutlined, StockOutlined,
  FilterOutlined, FullscreenOutlined, StarOutlined, EyeOutlined,
  ThunderboltOutlined, CaretUpOutlined, CaretDownOutlined, CrownOutlined,
  ReloadOutlined, SyncOutlined
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import ReactECharts from 'echarts-for-react';
import dayjs from 'dayjs';
import { DailyAnalysisApi, ConceptSummary, ConceptRanking, TopConcept, analysisUtils } from '../services/dailyAnalysisApi';
import ConceptDetailPage from '../components/ConceptDetailPage';
import StockRankingPage from '../components/StockRankingPage';

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
  const [selectedDate, setSelectedDate] = useState<string>(dayjs().format('YYYY-MM-DD'));
  
  // 真实数据状态
  const [conceptSummaries, setConceptSummaries] = useState<ConceptSummary[]>([]);
  const [topConcepts, setTopConcepts] = useState<TopConcept[]>([]);
  const [conceptRankings, setConceptRankings] = useState<ConceptRanking[]>([]);
  const [analysisStatus, setAnalysisStatus] = useState<string>('not_started');
  const [overviewStats, setOverviewStats] = useState({
    totalConcepts: 0,
    totalStocks: 0,
    totalNetInflow: 0,
    topGainer: { name: '', value: '', color: '#10b981' },
    topDecliner: { name: '', value: '', color: '#ef4444' }
  });

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
  
  // 处理概念点击
  const handleConceptClick = (conceptName: string) => {
    if (!isMember) return;
    setSelectedView('concept');
    // 设置选中的概念，用于概念详情页面
    setSelectedConcept(conceptName);
  };
  
  const [selectedConcept, setSelectedConcept] = useState<string>('');

  // 加载数据的函数
  const loadAnalysisData = async (date: string) => {
    setLoading(true);
    try {
      // 检查分析状态
      const statusRes = await DailyAnalysisApi.getAnalysisStatus(date);
      setAnalysisStatus(statusRes.data.overall_status);
      
      if (statusRes.data.overall_status === 'completed') {
        // 并行加载所有数据
        const [summariesRes, topConceptsRes, rankingsRes] = await Promise.all([
          DailyAnalysisApi.getConceptSummaries(date, 50),
          DailyAnalysisApi.getTopConcepts(date, 10),
          DailyAnalysisApi.getConceptRankings(date, undefined, 100)
        ]);
        
        setConceptSummaries(summariesRes.data.summaries);
        setTopConcepts(topConceptsRes.data.top_concepts);
        setConceptRankings(rankingsRes.data.rankings);
        
        // 计算总览统计
        const summaries = summariesRes.data.summaries;
        if (summaries.length > 0) {
          const totalNetInflow = summaries.reduce((sum, s) => sum + s.total_net_inflow, 0);
          const totalStocks = summaries.reduce((sum, s) => sum + s.stock_count, 0);
          const topGainer = summaries[0];
          const topDecliner = summaries[summaries.length - 1];
          
          setOverviewStats({
            totalConcepts: summaries.length,
            totalStocks,
            totalNetInflow: totalNetInflow / 100000000, // 转换为亿
            topGainer: {
              name: topGainer?.concept || '',
              value: analysisUtils.formatNetInflow(topGainer?.total_net_inflow || 0),
              color: '#10b981'
            },
            topDecliner: {
              name: topDecliner?.concept || '',
              value: analysisUtils.formatNetInflow(topDecliner?.total_net_inflow || 0),
              color: '#ef4444'
            }
          });
        }
      }
    } catch (error) {
      message.error('加载分析数据失败');
      console.error('Load analysis data error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // 生成分析报告
  const generateAnalysis = async () => {
    setLoading(true);
    try {
      await DailyAnalysisApi.generateAnalysis(selectedDate);
      message.success('分析报告生成完成');
      await loadAnalysisData(selectedDate);
    } catch (error) {
      message.error('生成分析报告失败');
      console.error('Generate analysis error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // 处理日期变化
  const handleDateChange = (date: any) => {
    if (date) {
      const dateStr = dayjs(date).format('YYYY-MM-DD');
      setSelectedDate(dateStr);
      loadAnalysisData(dateStr);
    }
  };
  
  // 组件挂载时加载数据
  useEffect(() => {
    loadAnalysisData(selectedDate);
  }, []);

  // 总览页面
  const OverviewPage = () => (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* 分析状态提示 */}
      {analysisStatus !== 'completed' && (
        <Alert
          message={
            analysisStatus === 'not_started' ? '今日分析报告尚未生成' :
            analysisStatus === 'processing' ? '正在生成分析报告...' :
            analysisStatus === 'failed' ? '分析报告生成失败' : '未知状态'
          }
          type={analysisStatus === 'failed' ? 'error' : 'info'}
          showIcon
          action={
            analysisStatus === 'not_started' || analysisStatus === 'failed' ? (
              <Button 
                size="small" 
                type="primary" 
                icon={<SyncOutlined />}
                loading={loading}
                onClick={generateAnalysis}
              >
                生成分析报告
              </Button>
            ) : undefined
          }
          style={{ marginBottom: 16 }}
        />
      )}
      
      {/* 核心指标 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
        <Col xs={12} sm={6}>
          <Card style={{ borderRadius: '16px', textAlign: 'center' }}>
            <Statistic
              title="活跃概念"
              value={overviewStats.totalConcepts}
              suffix={`个`}
              prefix={<BulbOutlined style={{ color: '#3b82f6' }} />}
              valueStyle={{ color: '#3b82f6', fontSize: '20px' }}
            />
          </Card>
        </Col>
        
        <Col xs={12} sm={6}>
          <Card style={{ borderRadius: '16px', textAlign: 'center' }}>
            <Statistic
              title="净流入总额"
              value={overviewStats.totalNetInflow.toFixed(2)}
              suffix="亿"
              prefix={<DollarOutlined style={{ color: '#10b981' }} />}
              valueStyle={{ 
                color: overviewStats.totalNetInflow > 0 ? '#10b981' : '#ef4444',
                fontSize: '20px'
              }}
            />
            <Progress 
              percent={Math.min(Math.abs(overviewStats.totalNetInflow) / 200 * 100, 100)}
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
              title="涉及个股"
              value={overviewStats.totalStocks}
              suffix="只"
              prefix={<StockOutlined style={{ color: '#f59e0b' }} />}
              valueStyle={{ color: '#f59e0b', fontSize: '20px' }}
            />
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#6b7280' }}>
              分析日期: {analysisUtils.formatAnalysisDate(selectedDate)}
            </div>
          </Card>
        </Col>
        
        <Col xs={12} sm={6}>
          <Card style={{ borderRadius: '16px', textAlign: 'center' }}>
            <div style={{ marginBottom: '8px' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>净流入最高</Text>
              <div style={{ 
                color: overviewStats.topGainer.color, 
                fontWeight: '600',
                fontSize: '16px'
              }}>
                <CaretUpOutlined /> {overviewStats.topGainer.name || '暂无'}
              </div>
              <Text style={{ color: overviewStats.topGainer.color, fontSize: '14px' }}>
                {overviewStats.topGainer.value || '--'}
              </Text>
            </div>
            <div>
              <Text type="secondary" style={{ fontSize: '12px' }}>净流入最低</Text>
              <div style={{ 
                color: overviewStats.topDecliner.color, 
                fontWeight: '600',
                fontSize: '16px'
              }}>
                <CaretDownOutlined /> {overviewStats.topDecliner.name || '暂无'}
              </div>
              <Text style={{ color: overviewStats.topDecliner.color, fontSize: '14px' }}>
                {overviewStats.topDecliner.value || '--'}
              </Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 热门概念 */}
      <Card 
        title={
          <Space>
            <FireOutlined style={{ color: '#ef4444' }} />
            <span>热门概念</span>
            <Badge count={topConcepts.length} style={{ backgroundColor: '#ef4444' }} />
          </Space>
        }
        extra={
          <Space>
            {isMember && <Button type="link" onClick={() => setSelectedView('concept')}>查看更多</Button>}
            <Button 
              size="small" 
              icon={<ReloadOutlined />} 
              loading={loading}
              onClick={() => loadAnalysisData(selectedDate)}
            >
              刷新
            </Button>
          </Space>
        }
        style={{ borderRadius: '16px', marginBottom: 24 }}
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" tip="加载中..."/>
          </div>
        ) : topConcepts.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            {topConcepts.slice(0, 5).map((concept, index) => (
              <motion.div
                key={concept.concept}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                onClick={() => isMember && handleConceptClick(concept.concept)}
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
                  <Col xs={24} sm={8}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{
                          width: '24px',
                          height: '24px',
                          borderRadius: '50%',
                          background: '#f59e0b',
                          color: 'white',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '12px',
                          fontWeight: '600'
                        }}>
                          {concept.rank}
                        </div>
                        <Text strong style={{ fontSize: '16px' }}>{concept.concept}</Text>
                      </div>
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {concept.stock_count}只股票
                      </Text>
                    </div>
                  </Col>
                  
                  <Col xs={12} sm={6}>
                    <div>
                      <div style={{ fontSize: '18px', fontWeight: '600', color: analysisUtils.getChangeColor(concept.total_net_inflow) }}>
                        {analysisUtils.formatNetInflow(concept.total_net_inflow)}
                      </div>
                      <Text type="secondary" style={{ fontSize: '12px' }}>总净流入</Text>
                    </div>
                  </Col>
                  
                  <Col xs={12} sm={6}>
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: '500', color: analysisUtils.getChangeColor(concept.avg_net_inflow) }}>
                        {analysisUtils.formatNetInflow(concept.avg_net_inflow)}
                      </div>
                      <Text type="secondary" style={{ fontSize: '12px' }}>平均净流入</Text>
                    </div>
                  </Col>
                  
                  <Col xs={24} sm={4}>
                    <div>
                      <Progress
                        percent={Math.min(analysisUtils.calculateHeatScore({ 
                          concept: concept.concept,
                          concept_rank: concept.rank,
                          stock_count: concept.stock_count,
                          total_net_inflow: concept.total_net_inflow,
                          avg_net_inflow: concept.avg_net_inflow,
                          avg_price: 0,
                          avg_turnover_rate: 0,
                          total_reads: 0,
                          total_pages: 0
                        }), 100)}
                        strokeColor="#f59e0b"
                        size="small"
                        showInfo={false}
                      />
                      <Text style={{ fontSize: '10px', color: '#9ca3af' }}>热度评分</Text>
                    </div>
                  </Col>
                </Row>
              </motion.div>
            ))}
          </div>
        ) : (
          <Empty 
            description="暂无概念数据" 
            style={{ padding: '40px' }}
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}

        {!isMember && (
          <Alert
            message="升级会员解锁完整功能"
            description="升级为专业版会员，查看详细的概念分析、个股排名和专业报告"
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
            <ConceptTracking concepts={conceptSummaries.slice(0, 5)} isMember={isMember} />
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
            
            <DatePicker 
              value={dayjs(selectedDate)}
              onChange={handleDateChange}
              size="middle"
              style={{ borderRadius: '8px' }}
              format="YYYY-MM-DD"
              placeholder="选择日期"
              allowClear={false}
            />
            
            {analysisStatus === 'completed' && (
              <Button 
                icon={<ReloadOutlined />}
                loading={loading}
                onClick={() => loadAnalysisData(selectedDate)}
                style={{ borderRadius: '8px' }}
              >
                刷新数据
              </Button>
            )}
            
            {(analysisStatus === 'not_started' || analysisStatus === 'failed') && (
              <Button 
                type="primary"
                icon={<SyncOutlined />}
                loading={loading}
                onClick={generateAnalysis}
                style={{ borderRadius: '8px' }}
              >
                生成分析
              </Button>
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
const ConceptTracking: React.FC<{ concepts: ConceptSummary[], isMember: boolean }> = ({ concepts, isMember }) => {
  return (
    <div>
      {concepts.length > 0 ? concepts.map((concept, index) => (
        <motion.div 
          key={concept.concept}
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
                {concept.concept}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <Progress
                  percent={Math.min(analysisUtils.calculateHeatScore(concept), 100)}
                  size="small"
                  strokeColor="#f59e0b"
                  showInfo={false}
                  style={{ width: '60px' }}
                />
                <Text style={{ fontSize: '10px', color: '#f59e0b', fontWeight: '600' }}>
                  {Math.min(analysisUtils.calculateHeatScore(concept), 100)}
                </Text>
              </div>
              <Text type="secondary" style={{ fontSize: '11px' }}>
                平均价格: {concept.avg_price.toFixed(2)} 元 • 平均换手: {(concept.avg_turnover_rate * 100).toFixed(2)}%
              </Text>
            </div>
            <div style={{ textAlign: 'right', marginLeft: '12px' }}>
              <div style={{
                color: analysisUtils.getChangeColor(concept.total_net_inflow),
                fontWeight: '600',
                fontSize: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '2px'
              }}>
                {concept.total_net_inflow >= 0 ? <CaretUpOutlined /> : <CaretDownOutlined />}
                {analysisUtils.formatNetInflow(concept.total_net_inflow)}
              </div>
              <Text type="secondary" style={{ fontSize: '10px' }}>
                {concept.stock_count}只股票
              </Text>
            </div>
          </div>
        </motion.div>
      )) : (
        <Empty 
          description="暂无概念数据" 
          style={{ padding: '20px' }}
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      )}
      
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
  <StockRankingPage 
    analysisDate={selectedDate}
    user={user}
  />
);

const IndustryPage = () => (
  <Card style={{ textAlign: 'center', padding: '60px', borderRadius: '16px' }}>
    <Title level={3}>🏭 行业分析</Title>
    <Paragraph>全面的行业对比分析，把握行业轮动机会</Paragraph>
    <Alert 
      message="功能开发中" 
      description="行业分析功能正在开发中，敬请期待。" 
      type="info" 
      showIcon 
      style={{ marginTop: '20px' }}
    />
  </Card>
);

const ConceptPage = () => {
  if (selectedConcept) {
    return (
      <ConceptDetailPage 
        conceptName={selectedConcept}
        analysisDate={selectedDate}
        onClose={() => setSelectedConcept('')}
        user={user}
      />
    );
  }
  
  return (
    <Card style={{ textAlign: 'center', padding: '60px', borderRadius: '16px' }}>
      <Title level={3}>💡 概念分析</Title>
      <Paragraph>点击任意概念查看详细分析，或在总览页面点击概念名称。</Paragraph>
      <Alert 
        message="提示" 
        description="请从总览页面点击具体概念查看详情。" 
        type="info" 
        showIcon 
        style={{ marginTop: '20px' }}
      />
    </Card>
  );
};

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