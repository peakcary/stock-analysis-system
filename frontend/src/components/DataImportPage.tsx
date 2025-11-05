import React, { useState, useEffect } from 'react';
import {
  Card, Tabs, Row, Col, Button, message, Upload, Space, Badge,
  Typography, Statistic, Progress, Alert, Table, Input, Tag, Tooltip, Modal
} from 'antd';
import {
  CloudUploadOutlined, UploadOutlined, DatabaseOutlined, SearchOutlined,
  HistoryOutlined, FileTextOutlined, CheckCircleOutlined, DeleteOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { adminApiClient } from '../../../shared/admin-auth';
import TxtImportRecords from './TxtImportRecords';
import TtvImportRecords from './TtvImportRecords';
import EeeImportRecords from './EeeImportRecords';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

interface DataImportPageProps {
  // 从App.tsx传递的原始参数和方法 - 完全保持不变
  stocks: any[];
  loading: boolean;
  csvImportLoading: boolean;
  txtImportLoading: boolean;
  ttvImportLoading?: boolean;
  eeeImportLoading?: boolean;
  importStats: any;
  importResult?: any; // 新增：导入结果信息
  onGetAllStocks: () => void;
  onCsvImport: () => void;
  onTxtImport: () => void;
  onTtvImport?: () => void;
  onEeeImport?: () => void;
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
  ttvImportLoading = false,
  eeeImportLoading = false,
  importStats,
  importResult,
  onGetAllStocks,
  onCsvImport,
  onTxtImport,
  onTtvImport,
  onEeeImport,
  onGetStockList,
  searchText,
  onSearchTextChange,
  onUpdateStock,
  onTxtImportSuccess
}) => {
  const [activeTab, setActiveTab] = useState('stocks');
  const [txtImportRefreshTrigger, setTxtImportRefreshTrigger] = useState(0);
  const [ttvImportRefreshTrigger, setTtvImportRefreshTrigger] = useState(0);
  const [eeeImportRefreshTrigger, setEeeImportRefreshTrigger] = useState(0);
  const [localTtvImportLoading, setLocalTtvImportLoading] = useState(false);
  const [localEeeImportLoading, setLocalEeeImportLoading] = useState(false);

  // 覆盖确认相关状态
  const [overwriteModalVisible, setOverwriteModalVisible] = useState(false);
  const [overwriteData, setOverwriteData] = useState<{
    file: File | null;
    fileType: 'ttv' | 'eee';
    tradingDate: string;
    count: number;
  }>({
    file: null,
    fileType: 'ttv',
    tradingDate: '',
    count: 0
  });
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

  // TTV文件导入处理 - 与TXT导入保持一致
  const handleTtvImport = () => {
    console.log('TTV导入按钮被点击');
    try {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = '.txt,.ttv';
      input.onchange = async (e) => {
        console.log('TTV文件被选择');
        try {
          const file = (e.target as HTMLInputElement).files?.[0];
          if (file) {
            console.log('选择的TTV文件:', file.name);
            await executeFileImport('ttv', file);
          } else {
            console.log('没有选择文件');
          }
        } catch (error) {
          console.error('TTV文件选择处理错误:', error);
        }
      };
      console.log('准备触发文件选择器');
      input.click();
      console.log('文件选择器已触发');
    } catch (error) {
      console.error('TTV导入处理错误:', error);
      message.error('TTV文件选择失败');
    }
  };

  // EEE文件导入处理 - 与TXT导入保持一致
  const handleEeeImport = () => {
    console.log('EEE导入按钮被点击');
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.txt,.eee';
    input.onchange = async (e) => {
      console.log('EEE文件被选择');
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        console.log('选择的EEE文件:', file.name);
        await executeFileImport('eee', file);
      }
    };
    input.click();
  };

  // 解析文件获取交易日期
  const parseFileDate = async (file: File): Promise<string | null> => {
    try {
      const text = await file.text();
      const lines = text.trim().split('\n');

      for (const line of lines) {
        if (!line.trim()) continue;
        const parts = line.split('\t');
        if (parts.length >= 2) {
          const dateStr = parts[1].trim();
          // 验证日期格式 YYYY-MM-DD 或 YYYYMMDD
          const dateRegex1 = /^\d{4}-\d{2}-\d{2}$/;
          const dateRegex2 = /^\d{8}$/;

          if (dateRegex1.test(dateStr)) {
            return dateStr;
          } else if (dateRegex2.test(dateStr)) {
            // 转换 YYYYMMDD 为 YYYY-MM-DD
            return `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`;
          }
        }
      }
      return null;
    } catch (error) {
      console.error('解析文件日期失败:', error);
      return null;
    }
  };

  // 检查日期是否已有导入记录
  const checkDateExists = async (fileType: 'ttv' | 'eee', tradingDate: string) => {
    try {
      const response = await adminApiClient.post(`/api/v1/universal-import/${fileType}/check-date`, {
        trading_date: tradingDate
      });

      return response.data;
    } catch (error) {
      console.error(`检查${fileType.toUpperCase()}日期失败:`, error);
      throw error;
    }
  };

  // 执行文件导入 - 添加日期检查和覆盖确认
  const executeFileImport = async (fileType: 'ttv' | 'eee', file: File, skipCheck: boolean = false, providedDate?: string) => {
    console.log(`开始执行${fileType.toUpperCase()}文件导入:`, file.name);

    let tradingDate = providedDate;

    // 如果没有提供日期，先解析文件获取交易日期
    if (!tradingDate) {
      try {
        tradingDate = await parseFileDate(file);
        if (!tradingDate) {
          message.error(`无法解析${fileType.toUpperCase()}文件中的交易日期，请检查文件格式`);
          return;
        }
      } catch (error) {
        console.error('解析文件日期失败:', error);
        message.error(`解析${fileType.toUpperCase()}文件日期失败，请检查文件格式`);
        return;
      }
    }

    console.log(`解析到交易日期: ${tradingDate}`);

    // 如果不跳过检查，先检查日期是否已有记录
    if (!skipCheck) {
      try {
        const checkResult = await checkDateExists(fileType, tradingDate);

        if (checkResult.exists) {
          // 显示覆盖确认对话框
          setOverwriteData({
            file,
            fileType,
            tradingDate,
            count: checkResult.count
          });
          setOverwriteModalVisible(true);
          return; // 等待用户确认
        }
      } catch (error) {
        // 检查失败时给出提示，但继续导入
        console.warn(`日期检查失败，继续导入:`, error);
        message.warning('无法检查重复数据，将直接导入');
      }
    }

    // 设置loading状态
    if (fileType === 'ttv') {
      setLocalTtvImportLoading(true);
    } else {
      setLocalEeeImportLoading(true);
    }

    let hideLoading: (() => void) | undefined;
    try {
      hideLoading = message.loading(`正在导入${fileType.toUpperCase()}文件...`, 0);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('file_type', fileType);
      formData.append('trading_date', tradingDate);

      const response = await adminApiClient.post('/api/v1/universal-import/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000,
      });

      if (hideLoading) hideLoading();

      if (response.data?.success) {
        const result = response.data;
        message.success(
          `${fileType.toUpperCase()}文件导入成功！导入${result.import_result?.success_records || 0}条记录`,
          5
        );

        // 刷新对应的记录列表
        if (fileType === 'ttv') {
          setTtvImportRefreshTrigger(prev => prev + 1);
        } else {
          setEeeImportRefreshTrigger(prev => prev + 1);
        }

        // 触发全局事件
        window.dispatchEvent(new CustomEvent(`${fileType}ImportSuccess`, {
          detail: result
        }));
      } else {
        message.error(response.data?.message || `${fileType.toUpperCase()}文件导入失败`);
      }
    } catch (error: any) {
      if (hideLoading) hideLoading();
      console.error(`${fileType.toUpperCase()}文件导入失败:`, error);

      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        message.error(`${fileType.toUpperCase()}文件导入超时，请检查文件大小或网络状况`);
      } else if (error.response?.status === 401) {
        message.error('认证失败，请重新登录');
      } else {
        message.error(`${fileType.toUpperCase()}文件导入失败: ${error.response?.data?.detail || error.message}`);
      }
    } finally {
      // 重置loading状态
      if (fileType === 'ttv') {
        setLocalTtvImportLoading(false);
      } else {
        setLocalEeeImportLoading(false);
      }
    }
  };

  // 确认覆盖导入
  const handleOverwriteConfirm = async () => {
    if (!overwriteData.file) return;

    setOverwriteModalVisible(false);

    // 跳过检查直接导入，使用已解析的日期
    await executeFileImport(overwriteData.fileType, overwriteData.file, true, overwriteData.tradingDate);

    // 重置状态
    setOverwriteData({
      file: null,
      fileType: 'ttv',
      tradingDate: '',
      count: 0
    });
  };

  // 取消覆盖导入
  const handleOverwriteCancel = () => {
    setOverwriteModalVisible(false);
    setOverwriteData({
      file: null,
      fileType: 'ttv',
      tradingDate: '',
      count: 0
    });
  };

  // 处理Tab切换，在切换到相应导入记录时刷新数据
  const handleTabChange = (key: string) => {
    setActiveTab(key);
    
    // 根据切换的tab触发相应的刷新
    if (key === 'txt-records') {
      setTxtImportRefreshTrigger(prev => prev + 1);
    } else if (key === 'ttv-records') {
      setTtvImportRefreshTrigger(prev => prev + 1);
    } else if (key === 'eee-records') {
      setEeeImportRefreshTrigger(prev => prev + 1);
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

        {/* 新增TTV和EEE导入区域 */}
        <Row gutter={16} style={{ marginTop: '16px' }}>
          <Col xs={24} md={12}>
            <div 
              style={{ 
                padding: '16px',
                borderRadius: '8px',
                background: '#f6f7ff',
                border: '1px solid #adc6ff',
                textAlign: 'center'
              }}
            >
              <div style={{ marginBottom: '12px' }}>
                <span style={{ fontSize: '20px', marginRight: '8px' }}>📺</span>
                <Text strong style={{ color: '#597ef7', fontSize: '16px' }}>
                  TTV视频数据导入
                </Text>
              </div>
              <Text type="secondary" style={{ display: 'block', marginBottom: '12px' }}>
                股票视频热度相关数据
              </Text>
              <Button 
                icon={<UploadOutlined />}
                loading={localTtvImportLoading}
                onClick={() => {
                  console.log('TTV按钮点击事件触发');
                  handleTtvImport();
                }}
                type="primary"
                size="large"
                style={{ background: '#597ef7', borderColor: '#597ef7' }}
              >
                {ttvImportLoading ? '导入中...' : '选择TTV文件'}
              </Button>
              
              {/* TTV导入结果显示 */}
              {importResult && importResult.filename && importResult.filename.toLowerCase().endsWith('.ttv') && (
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
          
          <Col xs={24} md={12}>
            <div 
              style={{ 
                padding: '16px',
                borderRadius: '8px',
                background: '#fff8e6',
                border: '1px solid #ffe58f',
                textAlign: 'center'
              }}
            >
              <div style={{ marginBottom: '12px' }}>
                <span style={{ fontSize: '20px', marginRight: '8px' }}>⚡</span>
                <Text strong style={{ color: '#faad14', fontSize: '16px' }}>
                  EEE能源数据导入
                </Text>
              </div>
              <Text type="secondary" style={{ display: 'block', marginBottom: '12px' }}>
                股票能源效率相关数据
              </Text>
              <Button 
                icon={<UploadOutlined />}
                loading={localEeeImportLoading}
                onClick={() => {
                  console.log('EEE按钮点击事件触发');
                  handleEeeImport();
                }}
                type="primary"
                size="large"
                style={{ background: '#faad14', borderColor: '#faad14' }}
              >
                {eeeImportLoading ? '导入中...' : '选择EEE文件'}
              </Button>
              
              {/* EEE导入结果显示 */}
              {importResult && importResult.filename && importResult.filename.toLowerCase().endsWith('.eee') && (
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

          {/* TTV导入记录 Tab */}
          <TabPane
            tab={
              <span>
                <HistoryOutlined />
                TTV导入记录
                <Badge count="New" style={{ backgroundColor: '#597ef7', marginLeft: 8, fontSize: '10px' }} />
              </span>
            }
            key="ttv-records"
          >
            <TtvImportRecords refreshTrigger={ttvImportRefreshTrigger} />
          </TabPane>

          {/* EEE导入记录 Tab */}
          <TabPane
            tab={
              <span>
                <HistoryOutlined />
                EEE导入记录
                <Badge count="New" style={{ backgroundColor: '#faad14', marginLeft: 8, fontSize: '10px' }} />
              </span>
            }
            key="eee-records"
          >
            <EeeImportRecords refreshTrigger={eeeImportRefreshTrigger} />
          </TabPane>
        </Tabs>
      </Card>

      {/* TTV/EEE覆盖确认Modal */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', color: '#faad14' }}>
            <ExclamationCircleOutlined style={{ marginRight: 8, fontSize: '18px' }} />
            数据覆盖确认
          </div>
        }
        open={overwriteModalVisible}
        onOk={handleOverwriteConfirm}
        onCancel={handleOverwriteCancel}
        okText="确认覆盖"
        cancelText="取消"
        okType="danger"
        confirmLoading={overwriteData.fileType === 'ttv' ? localTtvImportLoading : localEeeImportLoading}
      >
        <div style={{ padding: '20px 0' }}>
          <p style={{ fontSize: '16px', marginBottom: '16px' }}>
            检测到 <Text strong style={{ color: '#1890ff' }}>{overwriteData.tradingDate}</Text> 日期已有
            <Text strong style={{ color: '#fa541c' }}> {overwriteData.count} 条{overwriteData.fileType.toUpperCase()}导入记录</Text>。
          </p>
          <p style={{ fontSize: '16px', fontWeight: 'bold', color: '#fa541c' }}>
            是否确认覆盖导入？
          </p>
        </div>
      </Modal>

    </div>
  );
};

export default DataImportPage;