import React, { useState, useEffect } from 'react';
import {
  Card, Tabs, Row, Col, Button, message, Upload, Space, Badge, 
  Typography, Statistic, Progress, Alert, Table, Input, Tag, Tooltip
} from 'antd';
import {
  CloudUploadOutlined, UploadOutlined, DatabaseOutlined, SearchOutlined,
  HistoryOutlined, FileTextOutlined, CheckCircleOutlined, DeleteOutlined
} from '@ant-design/icons';
import { adminApiClient } from '../../../shared/admin-auth';
import TxtImportRecords from './TxtImportRecords';
import HistoricalDataImport from './HistoricalDataImport';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

interface DataImportPageProps {
  // 从App.tsx传递的原始参数和方法 - 完全保持不变
  stocks: any[];
  loading: boolean;
  csvImportLoading: boolean;
  txtImportLoading: boolean;
  importStats: any;
  importResult?: any; // 新增：导入结果信息
  onGetAllStocks: () => void;
  onCsvImport: () => void;
  onTxtImport: () => void;
  onGetStockList: (searchText?: string) => void;
  searchText: string;
  onSearchTextChange: (value: string) => void;
  onUpdateStock?: (stockCode: string, updatedData: any) => void;
  onTxtImportSuccess?: () => void; // 新增：TXT导入成功回调
}

const DataImportPage: React.FC<DataImportPageProps> = ({
  stocks,
  loading,
  csvImportLoading,
  txtImportLoading,
  importStats,
  importResult,
  onGetAllStocks,
  onCsvImport,
  onTxtImport,
  onGetStockList,
  searchText,
  onSearchTextChange,
  onUpdateStock,
  onTxtImportSuccess
}) => {
  const [activeTab, setActiveTab] = useState('stocks');
  const [txtImportRefreshTrigger, setTxtImportRefreshTrigger] = useState(0);
  const [searchFilters, setSearchFilters] = useState({
    code: '',
    name: '',
    industry: '',
    concept: ''
  });
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });

  // 获取单个股票的概念信息
  const getStockConcepts = async (stockCode: string) => {
    try {
      const response = await adminApiClient.get(`/api/v1/stocks/${stockCode}`);
      return response.data?.concepts || [];
    } catch (error) {
      console.error(`获取股票${stockCode}的概念失败:`, error);
      return [];
    }
  };

  // 完整的股票表格列定义 - 恢复原有的完整功能包括概念列
  const stockColumns = [
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 120,
      fixed: 'left' as const,
      render: (code: string) => (
        <Text strong style={{ color: '#1890ff' }}>{code}</Text>
      )
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      width: 150,
      fixed: 'left' as const,
      ellipsis: true,
      render: (name: string) => (
        <Text strong>{name}</Text>
      )
    },
    {
      title: '行业',
      dataIndex: 'industry',
      key: 'industry',
      width: 120,
      ellipsis: true,
      render: (industry: string) => (
        <Tag color="blue">{industry || '未知'}</Tag>
      )
    },
    {
      title: '所属概念',
      key: 'concepts',
      width: 300,
      render: (record: any) => (
        <div>
          {record.concepts && record.concepts.length > 0 ? (
            <div style={{ maxHeight: 80, overflowY: 'auto' }}>
              {/* 显示已加载的概念 */}
              {record.concepts.map((concept: any) => (
                <Tag key={concept.id} color="purple" style={{ margin: '2px' }}>
                  {concept.concept_name}
                </Tag>
              ))}
              
              {/* 如果是部分概念，显示查看更多按钮 */}
              {record.showingPartialConcepts && !record.conceptsLoaded && (
                <Button 
                  type="link" 
                  size="small"
                  style={{ padding: 0, height: 'auto' }}
                  onClick={async () => {
                    try {
                      // 加载完整概念信息
                      const allConcepts = await getStockConcepts(record.stock_code);
                      
                      // 通过回调更新父组件中的股票数据
                      if (onUpdateStock) {
                        onUpdateStock(record.stock_code, {
                          ...record,
                          concepts: allConcepts,
                          conceptsLoaded: true,
                          showingPartialConcepts: false
                        });
                      }
                    } catch (error) {
                      message.error('加载概念信息失败');
                      console.error('加载概念失败:', error);
                    }
                  }}
                >
                  查看更多...
                </Button>
              )}
            </div>
          ) : (
            <Tag color="default">暂无概念</Tag>
          )}
        </div>
      )
    },
    {
      title: '是否可转债',
      dataIndex: 'is_convertible_bond',
      key: 'is_convertible_bond',
      width: 120,
      render: (value: boolean) => (
        <Tag color={value ? 'orange' : 'green'}>
          {value ? '可转债' : '股票'}
        </Tag>
      )
    }
  ];

  // 多条件过滤股票数据
  const filteredStocks = stocks.filter(stock => {
    // 分离的搜索条件过滤
    const matchesCode = !searchFilters.code.trim() || 
      stock.stock_code?.toLowerCase().includes(searchFilters.code.toLowerCase());
      
    const matchesName = !searchFilters.name.trim() || 
      stock.stock_name?.toLowerCase().includes(searchFilters.name.toLowerCase());
      
    const matchesIndustry = !searchFilters.industry.trim() || 
      stock.industry?.toLowerCase().includes(searchFilters.industry.toLowerCase());
      
    const matchesConcept = !searchFilters.concept.trim() || 
      (stock.concepts && stock.concepts.some((concept: any) => 
        concept.concept_name?.toLowerCase().includes(searchFilters.concept.toLowerCase())
      ));
    
    return matchesCode && matchesName && matchesIndustry && matchesConcept;
  });

  // 分页后的股票数据
  const paginatedStocks = filteredStocks.slice(
    (pagination.current - 1) * pagination.pageSize,
    pagination.current * pagination.pageSize
  );

  // 分离搜索函数
  const handleSeparateSearch = () => {
    const { code, name, industry, concept } = searchFilters;
    const searchTerms = [];
    
    if (code.trim()) searchTerms.push(code.trim());
    if (name.trim()) searchTerms.push(name.trim());
    if (industry.trim()) searchTerms.push(industry.trim());
    if (concept.trim()) searchTerms.push(concept.trim());
    
    const combinedSearch = searchTerms.join(' ');
    onGetStockList(combinedSearch);
    // 重置分页到第一页
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  // 清除搜索条件
  const clearSearchFilters = () => {
    setSearchFilters({
      code: '',
      name: '',
      industry: '',
      concept: ''
    });
    onGetStockList(''); // 重新加载全部数据
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  // 当过滤结果变化时更新分页总数
  useEffect(() => {
    setPagination(prev => ({
      ...prev,
      total: filteredStocks.length,
      current: prev.current > Math.ceil(filteredStocks.length / prev.pageSize) ? 1 : prev.current
    }));
  }, [filteredStocks.length]);

  // 处理Tab切换，在切换到TXT导入记录时刷新数据
  const handleTabChange = (key: string) => {
    setActiveTab(key);
    
    // 如果切换到TXT导入记录tab，触发刷新
    if (key === 'txt-records') {
      setTxtImportRefreshTrigger(prev => prev + 1);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题和导入操作 */}
      <Card 
        title={
          <Space>
            <CloudUploadOutlined style={{ color: '#1890ff' }} />
            <span style={{ fontSize: '18px' }}>数据导入中心</span>
          </Space>
        }
        style={{ marginBottom: '24px', borderRadius: '12px' }}
      >
        <Row gutter={16}>
          <Col xs={24} md={12}>
            <div 
              style={{ 
                padding: '16px',
                borderRadius: '8px',
                background: '#f6ffed',
                border: '1px solid #b7eb8f',
                textAlign: 'center'
              }}
            >
              <div style={{ marginBottom: '12px' }}>
                <span style={{ fontSize: '20px', marginRight: '8px' }}>📊</span>
                <Text strong style={{ color: '#52c41a', fontSize: '16px' }}>
                  CSV基础数据导入
                </Text>
              </div>
              <Text type="secondary" style={{ display: 'block', marginBottom: '12px' }}>
                股票基本信息、概念关系数据
              </Text>
              <Button 
                icon={<UploadOutlined />}
                loading={csvImportLoading}
                onClick={onCsvImport}
                type="primary"
                size="large"
                style={{ background: '#52c41a', borderColor: '#52c41a' }}
              >
                {csvImportLoading ? '导入中...' : '选择CSV文件'}
              </Button>
              
              {/* CSV导入结果显示 */}
              {importResult && importResult.filename && importResult.filename.toLowerCase().endsWith('.csv') && (
                <div style={{ marginTop: '16px' }}>
                  <Alert
                    message={importResult.error ? "导入失败" : "导入成功"}
                    description={
                      <div>
                        <p><strong>文件:</strong> {importResult.filename}</p>
                        <p><strong>结果:</strong> {importResult.message}</p>
                        {!importResult.error && (
                          <div style={{ marginTop: '8px' }}>
                            <p><strong>导入记录:</strong> {importResult.imported_records}条</p>
                            {importResult.concept_summaries > 0 && (
                              <p><strong>概念数量:</strong> {importResult.concept_summaries}个</p>
                            )}
                          </div>
                        )}
                      </div>
                    }
                    type={importResult.error ? "error" : "success"}
                    showIcon
                    style={{ textAlign: 'left' }}
                  />
                </div>
              )}
            </div>
          </Col>
          
          <Col xs={24} md={12}>
            <div 
              style={{ 
                padding: '16px',
                borderRadius: '8px',
                background: '#fff7e6',
                border: '1px solid #ffd591',
                textAlign: 'center'
              }}
            >
              <div style={{ marginBottom: '12px' }}>
                <span style={{ fontSize: '20px', marginRight: '8px' }}>📈</span>
                <Text strong style={{ color: '#fa8c16', fontSize: '16px' }}>
                  TXT热度数据导入
                </Text>
              </div>
              <Text type="secondary" style={{ display: 'block', marginBottom: '12px' }}>
                股票每日交易量热度数据
              </Text>
              <Button 
                icon={<UploadOutlined />}
                loading={txtImportLoading}
                onClick={onTxtImport}
                type="primary"
                size="large"
                style={{ background: '#fa8c16', borderColor: '#fa8c16' }}
              >
                {txtImportLoading ? '导入中...' : '选择TXT文件'}
              </Button>
              
              {/* TXT导入结果显示 */}
              {importResult && importResult.filename && importResult.filename.toLowerCase().endsWith('.txt') && (
                <div style={{ marginTop: '16px' }}>
                  <Alert
                    message={importResult.error ? "导入失败" : "导入成功"}
                    description={
                      <div>
                        <p><strong>文件:</strong> {importResult.filename}</p>
                        <p><strong>结果:</strong> {importResult.message}</p>
                        {!importResult.error && importResult.trading_date && (
                          <div style={{ marginTop: '8px' }}>
                            <p><strong>交易日期:</strong> {importResult.trading_date}</p>
                            <p><strong>导入记录:</strong> {importResult.imported_records}条</p>
                            <p><strong>概念汇总:</strong> {importResult.concept_summaries}个</p>
                            <p><strong>排名记录:</strong> {importResult.ranking_records}条</p>
                            <p><strong>创新高:</strong> {importResult.new_high_records}条</p>
                          </div>
                        )}
                      </div>
                    }
                    type={importResult.error ? "error" : "success"}
                    showIcon
                    style={{ textAlign: 'left' }}
                  />
                </div>
              )}
            </div>
          </Col>
        </Row>

      </Card>

      {/* Tabs 区域 */}
      <Card style={{ borderRadius: '12px' }}>
        <Tabs
          activeKey={activeTab}
          onChange={handleTabChange}
          size="large"
          tabBarStyle={{ marginBottom: '24px' }}
        >
          {/* 股票列表 Tab */}
          <TabPane
            tab={
              <span>
                <DatabaseOutlined />
                股票数据列表
                <Badge count={stocks.length} overflowCount={999999} style={{ marginLeft: 8 }} />
              </span>
            }
            key="stocks"
          >
            {/* 股票搜索和操作区域 */}
            <Card 
              style={{ marginBottom: '16px', borderRadius: '8px' }}
              bodyStyle={{ padding: '16px' }}
            >
              <Row gutter={[8, 8]} align="middle">
                {/* 标题 */}
                <Col flex="auto" style={{ minWidth: '60px' }}>
                  <Space>
                    <SearchOutlined />
                    <Text strong>筛选:</Text>
                  </Space>
                </Col>
                
                {/* 搜索条件输入框 - 紧凑布局 */}
                <Col flex="140px">
                  <Input
                    placeholder="股票代码"
                    value={searchFilters.code}
                    onChange={(e) => setSearchFilters(prev => ({ ...prev, code: e.target.value }))}
                    allowClear
                    onPressEnter={handleSeparateSearch}
                    size="small"
                  />
                </Col>
                
                <Col flex="140px">
                  <Input
                    placeholder="股票名称"
                    value={searchFilters.name}
                    onChange={(e) => setSearchFilters(prev => ({ ...prev, name: e.target.value }))}
                    allowClear
                    onPressEnter={handleSeparateSearch}
                    size="small"
                  />
                </Col>
                
                <Col flex="120px">
                  <Input
                    placeholder="行业"
                    value={searchFilters.industry}
                    onChange={(e) => setSearchFilters(prev => ({ ...prev, industry: e.target.value }))}
                    allowClear
                    onPressEnter={handleSeparateSearch}
                    size="small"
                  />
                </Col>
                
                <Col flex="140px">
                  <Input
                    placeholder="概念"
                    value={searchFilters.concept}
                    onChange={(e) => setSearchFilters(prev => ({ ...prev, concept: e.target.value }))}
                    allowClear
                    onPressEnter={handleSeparateSearch}
                    size="small"
                  />
                </Col>
                
                {/* 操作按钮 - 小尺寸 */}
                <Col flex="60px">
                  <Button 
                    type="primary"
                    icon={<SearchOutlined />}
                    onClick={handleSeparateSearch}
                    loading={loading}
                    size="small"
                    block
                  >
                    搜索
                  </Button>
                </Col>
                
                <Col flex="50px">
                  <Button 
                    onClick={clearSearchFilters}
                    loading={loading}
                    size="small"
                    block
                  >
                    清空
                  </Button>
                </Col>
                
                <Col flex="50px">
                  <Button 
                    onClick={() => {
                      onGetStockList('');
                      setPagination(prev => ({ ...prev, current: 1 }));
                    }}
                    loading={loading}
                    size="small"
                    block
                  >
                    刷新
                  </Button>
                </Col>
              </Row>
            </Card>

            {/* 搜索结果提示 */}
            {(searchFilters.code.trim() || searchFilters.name.trim() || 
              searchFilters.industry.trim() || searchFilters.concept.trim()) && (
              <Row style={{ marginBottom: '16px' }}>
                <Col xs={24}>
                  <Alert
                    message={
                      <Space>
                        <span>搜索结果：共找到 <Text strong style={{ color: '#1890ff' }}>{filteredStocks.length}</Text> 条记录</span>
                        {stocks.length > 0 && (
                          <Text type="secondary">（总共 {stocks.length} 条）</Text>
                        )}
                      </Space>
                    }
                    type="info"
                    showIcon
                    style={{ borderRadius: '6px' }}
                  />
                </Col>
              </Row>
            )}

            {/* 股票数据表格 */}
            <Table
              columns={stockColumns}
              dataSource={paginatedStocks}
              rowKey="id"
              loading={loading}
              pagination={{
                current: pagination.current,
                pageSize: pagination.pageSize,
                total: filteredStocks.length,
                showSizeChanger: true,
                showQuickJumper: true,
                pageSizeOptions: ['10', '20', '50', '100', '200'],
                showTotal: (total, range) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 条记录`,
                onChange: (page, size) => {
                  setPagination({ 
                    current: page, 
                    pageSize: size || pagination.pageSize,
                    total: filteredStocks.length 
                  });
                },
                onShowSizeChange: (current, size) => {
                  setPagination({ 
                    current: 1, 
                    pageSize: size,
                    total: filteredStocks.length 
                  });
                },
                responsive: true
              }}
              scroll={{ x: 'max-content' }}
              size="middle"
            />
          </TabPane>

          {/* TXT导入记录 Tab */}
          <TabPane
            tab={
              <span>
                <HistoryOutlined />
                TXT导入记录
              </span>
            }
            key="txt-records"
          >
            <TxtImportRecords refreshTrigger={txtImportRefreshTrigger} />
          </TabPane>

          {/* 历史数据导入 Tab */}
          <TabPane
            tab={
              <span>
                <CloudUploadOutlined />
                历史数据导入
              </span>
            }
            key="historical-import"
          >
            <HistoricalDataImport />
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default DataImportPage;