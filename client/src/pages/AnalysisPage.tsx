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
import { ConceptAnalysisApi, ChartDataApi, conceptAnalysisUtils } from '../services/conceptAnalysisApi';
import StockAnalysisPage from '../components/StockAnalysisPage';
import InnovationAnalysisPage from '../components/InnovationAnalysisPage';
import ConvertibleBondPage from '../components/ConvertibleBondPage';
import StockSearchPage from '../components/StockSearchPage';
import './AnalysisPage.css';

const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;
const { TabPane } = Tabs;

interface AnalysisPageProps {
  user: any;
}

// 定义接口类型
export interface ConceptRankingData {
  concept_id: number;
  concept_name: string;
  rank: number;
  total_stocks: number;
  heat_value: number;
}

export interface StockRankingData {
  stock_id: number;
  stock_code: string;
  stock_name: string;
  rank: number;
  heat_value: number;
}

export interface InnovationConceptData {
  concept_id: number;
  concept_name: string;
  total_heat_value: number;
  stock_count: number;
  avg_heat_value: number;
  new_high_days: number;
  top_stocks: Array<{
    stock_code: string;
    stock_name: string;
    heat_value: number;
  }>;
}

export interface ConvertibleBondData {
  stock_id: number;
  stock_code: string;
  stock_name: string;
  heat_value: number;
  concepts: string[];
}

export const AnalysisPage: React.FC<AnalysisPageProps> = ({ user }) => {
  const [selectedView, setSelectedView] = useState<'overview' | 'stock-analysis' | 'innovation' | 'convertible-bond' | 'stock-search'>('overview');
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedStock, setSelectedStock] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  // 使用当前日期作为默认值
  const [selectedDate, setSelectedDate] = useState<string>(dayjs().format('YYYY-MM-DD'));
  
  // 概念分析数据状态
  const [innovationConcepts, setInnovationConcepts] = useState<InnovationConceptData[]>([]);
  const [analysisStatus, setAnalysisStatus] = useState<string>('not_started');
  const [overviewStats, setOverviewStats] = useState({
    totalConcepts: 0,
    totalStocks: 0,
    innovationCount: 0,
    convertibleBondCount: 0
  });

  // 根据用户会员等级限制功能
  const isSuperAdmin = user?.memberType === 'premium' && user?.queries_remaining >= 999999;
  const isMember = user?.memberType !== 'free' || isSuperAdmin;
  const isPremium = user?.memberType === 'premium' || isSuperAdmin;

  const handleViewChange = (view: string) => {
    if (!isMember && view !== 'overview') {
      // 非会员只能查看概览
      message.warning('请升级会员以使用此功能');
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
    // 暂时不处理概念点击，因为没有单独的概念详情页面
    console.log('Concept clicked:', conceptName);
  };
  
  const [selectedConcept, setSelectedConcept] = useState<string>('');

  // 加载概念分析数据
  const loadAnalysisData = async (date: string) => {
    setLoading(true);
    try {
      // 并行加载概念分析数据
      const [innovationRes, marketRes] = await Promise.all([
        ConceptAnalysisApi.getInnovationConcepts(date, 10, 1, 20).catch(() => ({ innovation_concepts: [] })),
        ChartDataApi.getMarketOverview(date).catch(() => ({ market_stats: {} }))
      ]);
      
      setInnovationConcepts(innovationRes.innovation_concepts || []);
      
      // 更新概览统计
      const marketStats = marketRes.market_stats || {};
      setOverviewStats({
        totalConcepts: marketStats.total_concepts ?? 0,
        totalStocks: marketStats.total_stocks ?? 0,
        innovationCount: innovationRes.innovation_concepts?.length || 0,
        convertibleBondCount: 0 // 将在可转债页面加载时更新
      });
      
      setAnalysisStatus('completed');
    } catch (error) {
      console.error('Load analysis data error:', error);
      setAnalysisStatus('failed');
      // 重置统计数据
      setOverviewStats({
        totalConcepts: 0,
        totalStocks: 0,
        innovationCount: 0,
        convertibleBondCount: 0
      });
    } finally {
      setLoading(false);
    }
  };
  
  // 触发分析计算
  const triggerAnalysis = async () => {
    setLoading(true);
    try {
      await ConceptAnalysisApi.triggerAnalysis(selectedDate);
      message.success('分析计算已触发，请稍后查看结果');
      setTimeout(() => {
        loadAnalysisData(selectedDate);
      }, 2000); // 延迟2秒重新加载数据
    } catch (error) {
      message.error('触发分析失败，请稍后重试');
      console.error('Trigger analysis error:', error);
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
      {analysisStatus === 'failed' && (
        <Alert
          message="数据加载失败"
          description="部分功能可能无法正常使用，点击重新加载或触发分析计算"
          type="warning"
          showIcon
          action={
            <Space>
              <Button 
                size="small" 
                icon={<ReloadOutlined />}
                loading={loading}
                onClick={() => loadAnalysisData(selectedDate)}
              >
                重新加载
              </Button>
              <Button 
                size="small" 
                type="primary"
                icon={<SyncOutlined />}
                loading={loading}
                onClick={triggerAnalysis}
              >
                触发分析
              </Button>
            </Space>
          }
          style={{ marginBottom: 16 }}
        />
      )}
      
      {/* 核心指标 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
        <Col xs={12} sm={6}>
          <Card style={{ borderRadius: '16px', textAlign: 'center' }}>
            <Statistic
              title="总概念数"
              value={overviewStats.totalConcepts}
              suffix="个"
              prefix={<BulbOutlined style={{ color: '#3b82f6' }} />}
              valueStyle={{ color: '#3b82f6', fontSize: '20px' }}
            />
          </Card>
        </Col>
        
        <Col xs={12} sm={6}>
          <Card style={{ borderRadius: '16px', textAlign: 'center' }}>
            <Statistic
              title="总股票数"
              value={overviewStats.totalStocks}
              suffix="只"
              prefix={<StockOutlined style={{ color: '#10b981' }} />}
              valueStyle={{ color: '#10b981', fontSize: '20px' }}
            />
          </Card>
        </Col>
        
        <Col xs={12} sm={6}>
          <Card style={{ borderRadius: '16px', textAlign: 'center' }}>
            <Statistic
              title="创新概念数"
              value={overviewStats.innovationCount}
              suffix="个"
              prefix={<ThunderboltOutlined style={{ color: '#f59e0b' }} />}
              valueStyle={{ color: '#f59e0b', fontSize: '20px' }}
            />
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#6b7280' }}>
              分析日期: {conceptAnalysisUtils.formatDate(selectedDate)}
            </div>
          </Card>
        </Col>
        
        <Col xs={12} sm={6}>
          <Card style={{ borderRadius: '16px', textAlign: 'center' }}>
            <Statistic
              title="可转债数量"
              value={overviewStats.convertibleBondCount}
              suffix="只"
              prefix={<CrownOutlined style={{ color: '#6366f1' }} />}
              valueStyle={{ color: '#6366f1', fontSize: '20px' }}
            />
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#6b7280' }}>
              1字头转债
            </div>
          </Card>
        </Col>
      </Row>

      {/* 热门概念 */}
      <Card 
        title={
          <Space>
            <FireOutlined style={{ color: '#ef4444' }} />
            <span>创新高概念</span>
            <Badge count={innovationConcepts.length} style={{ backgroundColor: '#ef4444' }} />
          </Space>
        }
        extra={
          <Space>
            {isMember && <Button type="link" onClick={() => setSelectedView('innovation')}>查看更多</Button>}
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
        ) : innovationConcepts.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            {innovationConcepts.slice(0, 5).map((concept, index) => (
              <motion.div
                key={concept.concept_name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                onClick={() => isMember && handleConceptClick(concept.concept_name)}
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
                          {index + 1}
                        </div>
                        <Text strong style={{ fontSize: '16px' }}>{concept.concept_name}</Text>
                      </div>
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {concept.stock_count}只股票 • {concept.new_high_days}天新高
                      </Text>
                    </div>
                  </Col>
                  
                  <Col xs={12} sm={6}>
                    <div>
                      <div style={{ fontSize: '18px', fontWeight: '600', color: conceptAnalysisUtils.getHeatColor(concept.total_heat_value / 10000) }}>
                        {conceptAnalysisUtils.formatHeatValue(concept.total_heat_value)}
                      </div>
                      <Text type="secondary" style={{ fontSize: '12px' }}>总热度值</Text>
                    </div>
                  </Col>
                  
                  <Col xs={12} sm={6}>
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: '500', color: conceptAnalysisUtils.getHeatColor(concept.avg_heat_value) }}>
                        {conceptAnalysisUtils.formatHeatValue(concept.avg_heat_value)}
                      </div>
                      <Text type="secondary" style={{ fontSize: '12px' }}>平均热度</Text>
                    </div>
                  </Col>
                  
                  <Col xs={24} sm={4}>
                    <div>
                      <Progress
                        percent={Math.min((concept.total_heat_value / 100000) * 100, 100)}
                        strokeColor="#ef4444"
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

      {/* 功能快捷入口 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <Card 
            title="个股概念分析"
            style={{ borderRadius: '16px', textAlign: 'center' }}
            hoverable
            onClick={() => isMember && setSelectedView('stock-analysis')}
          >
            <div style={{ padding: '20px' }}>
              <StockOutlined style={{ fontSize: '32px', color: '#3b82f6', marginBottom: '12px' }} />
              <div style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>个股分析</div>
              <Text type="secondary">查询个股在各概念中的排名表现</Text>
              {!isMember && (
                <div style={{ marginTop: '8px' }}>
                  <Tag color="orange">会员专享</Tag>
                </div>
              )}
            </div>
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <Card 
            title="创新高概念"
            style={{ borderRadius: '16px', textAlign: 'center' }}
            hoverable
            onClick={() => isMember && setSelectedView('innovation')}
          >
            <div style={{ padding: '20px' }}>
              <ThunderboltOutlined style={{ fontSize: '32px', color: '#ef4444', marginBottom: '12px' }} />
              <div style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>创新分析</div>
              <Text type="secondary">发现市场热点，捕捉创新高投资机会</Text>
              {!isMember && (
                <div style={{ marginTop: '8px' }}>
                  <Tag color="orange">会员专享</Tag>
                </div>
              )}
            </div>
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <Card 
            title="可转债分析"
            style={{ borderRadius: '16px', textAlign: 'center' }}
            hoverable
            onClick={() => isMember && setSelectedView('convertible-bond')}
          >
            <div style={{ padding: '20px' }}>
              <CrownOutlined style={{ fontSize: '32px', color: '#6366f1', marginBottom: '12px' }} />
              <div style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>可转债</div>
              <Text type="secondary">分析可转债市场表现和投资价值</Text>
              {!isMember && (
                <div style={{ marginTop: '8px' }}>
                  <Tag color="orange">会员专享</Tag>
                </div>
              )}
            </div>
          </Card>
        </Col>
      </Row>
    </motion.div>
  );

  return (
    <div className="analysis-page-container" style={{
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
                    <Tooltip title="概念分析总览">
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
                    <Tooltip title={!isMember ? "升级会员解锁" : "个股概念分析"}>
                      <Space>
                        <StockOutlined />
                        <span>个股分析</span>
                        {!isMember && <Badge dot />}
                      </Space>
                    </Tooltip>
                  ), 
                  value: 'stock-analysis',
                  disabled: !isMember
                },
                { 
                  label: (
                    <Tooltip title={!isMember ? "升级会员解锁" : "创新高概念分析"}>
                      <Space>
                        <ThunderboltOutlined />
                        <span>创新分析</span>
                        {!isMember && <Badge dot />}
                      </Space>
                    </Tooltip>
                  ), 
                  value: 'innovation',
                  disabled: !isMember
                },
                {
                  label: (
                    <Tooltip title={!isMember ? "升级会员解锁" : "可转债分析"}>
                      <Space>
                        <CrownOutlined />
                        <span>可转债</span>
                        {!isMember && <Badge dot />}
                      </Space>
                    </Tooltip>
                  ),
                  value: 'convertible-bond',
                  disabled: !isMember
                },
                {
                  label: (
                    <Tooltip title="个股查询">
                      <Space>
                        <SearchOutlined />
                        <span>个股查询</span>
                      </Space>
                    </Tooltip>
                  ),
                  value: 'stock-search'
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
              disabledDate={(current) => {
                // 禁用未来日期
                const isFuture = current && current.isAfter(dayjs().endOf('day'));
                return !!isFuture;
              }}
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
                onClick={triggerAnalysis}
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
            {selectedView === 'stock-analysis' && <StockAnalysisPage user={user} tradeDate={selectedDate} />}
            {selectedView === 'innovation' && <InnovationAnalysisPage user={user} tradeDate={selectedDate} />}
            {selectedView === 'convertible-bond' && <ConvertibleBondPage user={user} tradeDate={selectedDate} />}
            {selectedView === 'stock-search' && <StockSearchPage />}
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