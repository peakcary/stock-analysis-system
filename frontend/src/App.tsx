import React, { useState, useEffect } from 'react';
import { 
  Layout, Menu, Button, Input, Card, Table, message, Upload, Space, 
  Divider, Alert, Row, Col, Typography, Steps, Progress, Statistic, 
  Tag, Badge, Tooltip, Spin, Modal, Tabs
} from 'antd';
import { 
  SearchOutlined, UserOutlined, ApiOutlined, UploadOutlined, 
  CloudUploadOutlined, FileTextOutlined, DatabaseOutlined,
  CheckCircleOutlined, ClockCircleOutlined, GiftOutlined, DeleteOutlined,
  FireOutlined, ExclamationCircleOutlined
} from '@ant-design/icons';
import { adminApiClient } from '../../shared/admin-auth';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginPage from './components/LoginPage';
import AdminLayout from './components/AdminLayout';
import Dashboard from './components/Dashboard';
import UserManagement from './components/UserManagement';
import AdminManagement from './components/AdminManagement';
import PackageManagement from './components/PackageManagement';
import StockListPage from './components/StockListPage';
import NewStockAnalysisPage from './components/NewStockAnalysisPage';
import InnovationAnalysisPage from './components/InnovationAnalysisPage';
import ConvertibleBondPage from './components/ConvertibleBondPage';
import ConceptAnalysisPage from './components/ConceptAnalysisPage';
import TxtImportRecords from './components/TxtImportRecords';
import DataImportPage from './components/DataImportPage';

const { Header, Content, Sider } = Layout;
const { Title, Text, Paragraph } = Typography;

const AppContent: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh'
      }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return <AdminApp />;
};

const AdminApp: React.FC = () => {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [csvImportLoading, setCsvImportLoading] = useState(false);
  const [txtImportLoading, setTxtImportLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [importActiveTab, setImportActiveTab] = useState('stocks');
  const [importStatus, setImportStatus] = useState({
    csv: false,
    txt: false
  });
  const [importHistory, setImportHistory] = useState([]);
  const [todayImportStatus, setTodayImportStatus] = useState({
    csv_imported: false,
    txt_imported: false,
    csv_record: null,
    txt_record: null
  });
  const [importResult, setImportResult] = useState(null);
  const [importedData, setImportedData] = useState({
    stockCount: 0,
    conceptCount: 0
  });
  const [dataLoading, setDataLoading] = useState(false);
  const [stockList, setStockList] = useState([]);
  const [stockLoading, setStockLoading] = useState(false);
  const [stockSearchText, setStockSearchText] = useState('');
  const [searchFilters, setSearchFilters] = useState({
    code: '',
    name: '', 
    industry: '',
    concept: ''
  });
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteModalVisible, setDeleteModalVisible] = useState(false);
  const [deleteStockId, setDeleteStockId] = useState<number | null>(null);
  const [batchDeleteModalVisible, setBatchDeleteModalVisible] = useState(false);
  const [txtOverwriteModalVisible, setTxtOverwriteModalVisible] = useState(false);
  const [txtOverwriteFile, setTxtOverwriteFile] = useState<File | null>(null);
  const [txtOverwriteDate, setTxtOverwriteDate] = useState<string>('');
  const [txtOverwriteCount, setTxtOverwriteCount] = useState<number>(0);

  // 获取已导入的数据统计
  const getImportedDataStats = async () => {
    setDataLoading(true);
    try {
      // 并行获取统计数据
      const [stocksCountResponse, conceptsCountResponse] = await Promise.all([
        // 获取股票真实总数
        adminApiClient.get('/api/v1/stocks/count'),
        
        // 获取概念真实总数
        adminApiClient.get('/api/v1/concepts/count')
      ]);
      
      console.log('获取到的数据:', {
        stocks: stocksCountResponse.data?.total,
        concepts: conceptsCountResponse.data?.total
      });
      
      setImportedData({
        stockCount: stocksCountResponse.data?.total || 0,
        conceptCount: conceptsCountResponse.data?.total || 0
      });
      
    } catch (error: any) {
      console.error('获取导入数据统计失败:', error);
      
      // 如果是401错误，说明认证失效，不需要额外处理（拦截器会处理）
      if (error.response?.status === 401) {
        console.log('认证失效，等待自动跳转...');
        return;
      }
      
      // 其他错误，设置默认值
      setImportedData({
        stockCount: 0,
        conceptCount: 0
      });
    } finally {
      setDataLoading(false);
    }
  };

  // 获取股票列表（支持搜索）
  const getStockList = async (searchText: string = '') => {
    setStockLoading(true);
    try {
      let url = '/api/v1/stocks/simple?limit=10000&include_concepts=true'; // 包含概念信息
      if (searchText.trim()) {
        url += `&search=${encodeURIComponent(searchText.trim())}`;
      }
      
      const response = await adminApiClient.get(url);
      
      // 股票列表包含部分概念信息
      const stocksData = (response.data || []).map((stock: any) => ({
        ...stock,
        concepts: stock.concepts || [], // 已加载的部分概念
        conceptsLoaded: false, // 标记为可以加载更多概念
        showingPartialConcepts: (stock.concepts || []).length > 0 // 只有当已有概念时才可能有更多概念
      }));
      
      setStockList(stocksData);
      setPagination(prev => ({ ...prev, total: stocksData.length }));
    } catch (error: any) {
      console.error('获取股票列表失败:', error);
      
      // 如果是401错误，说明认证失效，不需要额外处理（拦截器会处理）
      if (error.response?.status === 401) {
        console.log('认证失效，等待自动跳转...');
        return;
      }
      
      // 其他错误，清空列表
      setStockList([]);
    } finally {
      setStockLoading(false);
    }
  };

  // 获取单个股票的概念信息
  const getStockConcepts = async (stockCode: string) => {
    try {
      const response = await adminApiClient.get(`/api/v1/stocks/${stockCode}`);
      // 后端返回的数据结构是 {stock: ..., concepts: [...]}
      const concepts = response.data?.concepts || [];
      return concepts;
    } catch (error) {
      console.error(`获取股票${stockCode}的概念失败:`, error);
      return [];
    }
  };

  // 更新单个股票数据
  const updateStockInList = (stockCode: string, updatedData: any) => {
    setStockList(prevList => 
      prevList.map(stock => 
        stock.stock_code === stockCode 
          ? { ...stock, ...updatedData }
          : stock
      )
    );
  };

  // 组件加载时获取数据
  useEffect(() => {
    if (activeTab === 'simple-import') {
      getImportedDataStats();
      getStockList(); // 初始加载股票列表
    }
  }, [activeTab]);

  // 删除单个股票
  const handleDeleteStock = async (stockId: number) => {
    console.log('🗑️ handleDeleteStock 被调用，股票ID:', stockId);
    setDeleteStockId(stockId);
    setDeleteModalVisible(true);
  };

  // 确认删除股票
  const confirmDeleteStock = async () => {
    if (!deleteStockId) return;
    
    try {
      console.log('🚀 开始删除股票，ID:', deleteStockId);
      setDeleteLoading(true);
      await adminApiClient.delete(`/api/v1/stocks/${deleteStockId}`);
      console.log('✅ 删除成功，ID:', deleteStockId);
      message.success('删除成功');
      // 刷新列表
      await getStockList(stockSearchText);
      console.log('🔄 列表已刷新');
      // 关闭Modal
      setDeleteModalVisible(false);
      setDeleteStockId(null);
    } catch (error) {
      console.error('❌ 删除股票失败:', error);
      message.error('删除失败，请重试');
    } finally {
      setDeleteLoading(false);
    }
  };

  // 取消删除
  const cancelDelete = () => {
    setDeleteModalVisible(false);
    setDeleteStockId(null);
  };

  // 批量删除股票
  const handleBatchDelete = async () => {
    console.log('🗑️ handleBatchDelete 被调用，选中数量:', selectedRowKeys.length);
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要删除的股票');
      return;
    }
    setBatchDeleteModalVisible(true);
  };

  // 确认批量删除
  const confirmBatchDelete = async () => {
    try {
      console.log('🚀 开始批量删除，IDs:', selectedRowKeys);
      setDeleteLoading(true);
      // 批量删除API调用
      await adminApiClient.delete('/api/v1/stocks/batch', {
        data: { stock_ids: selectedRowKeys }
      });
      console.log('✅ 批量删除成功');
      message.success(`成功删除 ${selectedRowKeys.length} 只股票`);
      // 清空选择
      setSelectedRowKeys([]);
      // 刷新列表
      await getStockList(stockSearchText);
      console.log('🔄 列表已刷新');
      // 关闭Modal
      setBatchDeleteModalVisible(false);
    } catch (error) {
      console.error('❌ 批量删除失败:', error);
      message.error('批量删除失败，请重试');
    } finally {
      setDeleteLoading(false);
    }
  };

  // 取消批量删除
  const cancelBatchDelete = () => {
    setBatchDeleteModalVisible(false);
  };

  // 确认覆盖导入
  const handleTxtOverwriteConfirm = async () => {
    if (!txtOverwriteFile) return;
    
    setTxtOverwriteModalVisible(false);
    setTxtImportLoading(true);
    
    try {
      await performTxtImport(txtOverwriteFile);
    } finally {
      setTxtOverwriteFile(null);
      setTxtOverwriteDate('');
      setTxtOverwriteCount(0);
    }
  };

  // 取消覆盖导入
  const handleTxtOverwriteCancel = () => {
    setTxtOverwriteModalVisible(false);
    setTxtOverwriteFile(null);
    setTxtOverwriteDate('');
    setTxtOverwriteCount(0);
    setTxtImportLoading(false);
  };

  // 搜索股票列表
  const handleStockSearch = async () => {
    await getStockList(stockSearchText);
  };

  // 分离搜索函数
  const handleSeparateSearch = async () => {
    const { code, name, industry, concept } = searchFilters;
    const searchTerms = [];
    
    if (code.trim()) searchTerms.push(code.trim());
    if (name.trim()) searchTerms.push(name.trim());
    if (industry.trim()) searchTerms.push(industry.trim());
    if (concept.trim()) searchTerms.push(concept.trim());
    
    const combinedSearch = searchTerms.join(' ');
    await getStockList(combinedSearch);
  };

  // 清除搜索条件
  const clearSearchFilters = () => {
    setSearchFilters({
      code: '',
      name: '', 
      industry: '',
      concept: ''
    });
    getStockList(''); // 重新加载全部数据
  };


  // 搜索股票
  const searchStocks = async () => {
    if (!searchText.trim()) {
      message.warning('请输入股票代码或名称');
      return;
    }

    setLoading(true);
    try {
      const response = await adminApiClient.get(`/api/v1/stocks`, {
        params: { search: searchText }
      });
      setStocks(response.data || []);
      message.success(`找到 ${response.data?.length || 0} 只股票`);
    } catch (error) {
      console.error('搜索失败:', error);
      message.error('搜索失败，请检查网络连接');
      setStocks([]);
    } finally {
      setLoading(false);
    }
  };

  // 获取所有股票
  const getAllStocks = async () => {
    setLoading(true);
    try {
      const response = await adminApiClient.get('/api/v1/stocks');
      setStocks(response.data || []);
      message.success(`获取到 ${response.data?.length || 0} 只股票`);
    } catch (error) {
      console.error('获取失败:', error);
      message.error('获取失败，请检查网络连接');
      setStocks([]);
    } finally {
      setLoading(false);
    }
  };

  // 获取今日导入状态
  const getTodayImportStatus = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      console.log('获取导入状态，日期:', today);
      const response = await adminApiClient.get(`/api/v1/data/import-status/${today}`);
      console.log('导入状态响应:', response.data);
      setTodayImportStatus(response.data);
      
      // 更新本地状态
      setImportStatus({
        csv: response.data.csv_imported,
        txt: response.data.txt_imported
      });
    } catch (error) {
      console.error('获取导入状态失败:', error);
      console.error('错误详情:', error.response?.data);
      // 在获取失败时设置默认状态，避免阻塞后续操作
      setTodayImportStatus({
        csv_imported: false,
        txt_imported: false,
        csv_record: null,
        txt_record: null
      });
    }
  };

  // 处理CSV文件导入（简化版本用于调试）
  const handleCsvImport = async () => {
    console.log('🔥 CSV导入函数开始执行!', { csvImportLoading, todayImportStatus });
    
    // 防止重复点击
    if (csvImportLoading) {
      console.log('⚠️ 正在导入中，忽略重复点击');
      message.warning('正在导入中，请稍候...');
      return;
    }

    // 创建文件输入元素
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.csv';
    fileInput.style.display = 'none';
    
    fileInput.onchange = async (e: any) => {
      const file = e.target.files?.[0];
      console.log('📁 用户选择的文件:', file);
      
      if (!file) {
        console.log('❌ 没有选择文件');
        return;
      }

      // 验证文件名
      if (file.name !== 'AAA.csv') {
        message.error('请选择名为 AAA.csv 的文件');
        return;
      }

      // 验证文件大小
      if (file.size > 100 * 1024 * 1024) {
        message.error('文件大小不能超过100MB');
        return;
      }

      setCsvImportLoading(true);
      
      try {
        console.log('🚀 开始上传文件...');
        const formData = new FormData();
        formData.append('file', file);
        
        const url = todayImportStatus.csv_imported 
          ? '/api/v1/data/import-csv?allow_overwrite=true' 
          : '/api/v1/data/import-csv';
        
        console.log('📡 发送请求到:', url);
        
        const result = await adminApiClient.post(url, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 300000
        });
        
        console.log('✅ 导入成功:', result.data);
        
        setImportStatus(prev => ({ ...prev, csv: true }));
        
        const statusText = todayImportStatus.csv_imported ? '（覆盖导入）' : '（首次导入）';
        message.success(`CSV导入成功！导入${result.data.imported_records}条记录${statusText}`);
        
        // 刷新状态
        await getTodayImportStatus();
        
      } catch (error: any) {
        console.error('❌ 导入失败:', error);
        message.error(`导入失败: ${error.response?.data?.detail || error.message}`);
      } finally {
        setCsvImportLoading(false);
        document.body.removeChild(fileInput);
      }
    };
    
    // 用户取消选择
    fileInput.oncancel = () => {
      console.log('❌ 用户取消选择文件');
      document.body.removeChild(fileInput);
    };
    
    // 添加到DOM并点击
    document.body.appendChild(fileInput);
    console.log('📂 触发文件选择对话框');
    fileInput.click();
  };

  // 处理TXT文件导入（重构版本 - 更加可靠）
  // 简化CSV导入
  const handleSimpleCsvImport = async () => {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.csv';
    fileInput.style.display = 'none';
    
    fileInput.onchange = async (e: any) => {
      const file = e.target.files?.[0];
      console.log('📁 选择CSV文件:', file?.name);
      
      if (!file) return;
      
      setCsvImportLoading(true);
      
      try {
        console.log('🚀 开始上传CSV文件...');
        const formData = new FormData();
        formData.append('file', file);
        
        const result = await adminApiClient.post('/api/v1/simple-import/simple-csv', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 600000 // 10分钟超时
        });
        
        console.log('✅ CSV导入成功:', result.data);
        message.success(`CSV导入成功！成功${result.data.data.success_rows}条，失败${result.data.data.error_rows}条`);
        
      } catch (error: any) {
        console.error('❌ CSV导入失败:', error);
        message.error(`CSV导入失败: ${error.response?.data?.detail || error.message}`);
      } finally {
        setCsvImportLoading(false);
        document.body.removeChild(fileInput);
      }
    };
    
    document.body.appendChild(fileInput);
    fileInput.click();
  };

  // 简化TXT导入  
  const handleSimpleTxtImport = async () => {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.txt';
    fileInput.style.display = 'none';
    
    fileInput.onchange = async (e: any) => {
      const file = e.target.files?.[0];
      console.log('📁 选择TXT文件:', file?.name);
      
      if (!file) return;
      
      setTxtImportLoading(true);
      
      try {
        console.log('🚀 开始上传TXT文件...');
        const formData = new FormData();
        formData.append('file', file);
        
        const result = await adminApiClient.post('/api/v1/simple-import/simple-txt', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 1800000 // 30分钟超时，TXT文件很大
        });
        
        console.log('✅ TXT导入成功:', result.data);
        message.success(`TXT导入成功！成功${result.data.data.success_rows}条，失败${result.data.data.error_rows}条`);
        
      } catch (error: any) {
        console.error('❌ TXT导入失败:', error);
        message.error(`TXT导入失败: ${error.response?.data?.detail || error.message}`);
      } finally {
        setTxtImportLoading(false);
        document.body.removeChild(fileInput);
      }
    };
    
    document.body.appendChild(fileInput);
    fileInput.click();
  };

  // 优化后的CSV导入（使用详细统计API）
  const handleOptimizedCsvImport = async () => {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.csv';
    fileInput.style.display = 'none';
    
    fileInput.onchange = async (e: any) => {
      const file = e.target.files?.[0];
      if (!file) return;
      
      setCsvImportLoading(true);
      setImportResult(null); // 清空之前的结果
      
      // 显示导入开始提示
      const hideLoading = message.loading('CSV文件导入中，请稍候...', 0);
      
      try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await adminApiClient.post('/api/v1/data/import-csv?allow_overwrite=true', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 600000 // 10分钟超时
        });
        
        console.log('✅ CSV导入成功:', response.data);
        hideLoading(); // 隐藏loading提示
        
        if (response.data.success !== false) {
          // 成功导入
          setImportResult({
            success: true,
            error: false,
            message: `CSV导入成功！导入 ${response.data.imported_records} 条记录`,
            filename: file.name,
            imported_records: response.data.imported_records,
            concept_summaries: response.data.concept_count || 0,
            ranking_records: 0,
            new_high_records: 0
          });
          
          message.success(`CSV导入成功！导入 ${response.data.imported_records} 条记录`);
          
          // 刷新数据统计和股票列表 - 延迟一点确保后端处理完成
          setTimeout(async () => {
            await getImportedDataStats();
            await getStockList(stockSearchText); // 重新加载股票列表
          }, 1000);
        } else {
          // 业务逻辑失败
          const errorMsg = response.data.message || 'CSV导入失败';
          setImportResult({
            success: false,
            error: true,
            message: errorMsg,
            filename: file.name,
            imported_records: 0,
            concept_summaries: 0,
            ranking_records: 0,
            new_high_records: 0
          });
          
          message.error(errorMsg);
        }
        
      } catch (error: any) {
        console.error('❌ CSV导入异常:', error);
        hideLoading(); // 隐藏loading提示
        
        let errorMessage = 'CSV导入失败';
        if (error.response?.data?.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response?.data?.message) {
          errorMessage = error.response.data.message;
        } else if (error.message) {
          errorMessage = error.message;
        }
        
        // 如果是网络超时错误
        if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
          errorMessage = 'CSV导入超时，文件可能过大或服务器处理时间过长';
        }
        
        // 显示错误结果信息
        setImportResult({
          success: false,
          error: true,
          message: errorMessage,
          filename: file.name,
          imported_records: 0,
          concept_summaries: 0,
          ranking_records: 0,
          new_high_records: 0
        });
        
        message.error(`CSV导入失败: ${errorMessage}`);
      } finally {
        setCsvImportLoading(false);
        document.body.removeChild(fileInput);
      }
    };
    
    document.body.appendChild(fileInput);
    fileInput.click();
  };

  // 解析TXT文件获取交易日期
  const parseTxtFileDate = async (file: File): Promise<string | null> => {
    try {
      const text = await file.text();
      const lines = text.trim().split('\n');
      
      for (const line of lines) {
        if (!line.trim()) continue;
        const parts = line.split('\t');
        if (parts.length >= 2) {
          const dateStr = parts[1].trim();
          // 验证日期格式
          const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
          if (dateRegex.test(dateStr)) {
            return dateStr;
          }
        }
      }
      return null;
    } catch (error) {
      console.error('解析TXT文件日期失败:', error);
      return null;
    }
  };

  // 新的TXT导入功能（使用新API）
  const handleNewTxtImport = async () => {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.txt';
    fileInput.style.display = 'none';
    
    fileInput.onchange = async (e: any) => {
      const file = e.target.files?.[0];
      if (!file) return;
      
      setTxtImportLoading(true);
      setImportResult(null);
      
      try {
        // 先解析文件获取交易日期
        const tradingDate = await parseTxtFileDate(file);
        if (!tradingDate) {
          message.error('无法解析文件中的交易日期，请检查文件格式');
          setTxtImportLoading(false);
          document.body.removeChild(fileInput);
          return;
        }

        // 检查该日期是否已有导入记录
        const checkResponse = await adminApiClient.post('/api/v1/txt-import/check-date', {
          trading_date: tradingDate
        });

        console.log('检查日期响应:', checkResponse.data);

        if (checkResponse.data.exists) {
          console.log('检测到已有记录，准备弹出确认对话框');
          
          // 先清理文件输入元素，避免异步问题  
          setTxtImportLoading(false);
          document.body.removeChild(fileInput);
          
          // 设置覆盖确认Modal的数据
          setTxtOverwriteFile(file);
          setTxtOverwriteDate(tradingDate);
          setTxtOverwriteCount(checkResponse.data.count);
          setTxtOverwriteModalVisible(true);
        } else {
          console.log('直接导入，无需覆盖');
          // 直接导入
          await performTxtImport(file);
          document.body.removeChild(fileInput);
        }
        
      } catch (error: any) {
        console.error('❌ 检查TXT导入日期失败:', error);
        message.error(`检查失败: ${error.response?.data?.detail || error.message}`);
        setTxtImportLoading(false);
        document.body.removeChild(fileInput);
      }
    };
    
    document.body.appendChild(fileInput);
    fileInput.click();
  };

  // 执行实际的导入操作
  const performTxtImport = async (file: File) => {
    const hideLoading = message.loading('TXT文件导入中，正在计算汇总数据...', 0);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await adminApiClient.post('/api/v1/txt-import/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 1800000 // 30分钟超时
      });
      
      console.log('✅ 新TXT导入成功:', response.data);
      hideLoading();
      
        if (response.data.success) {
        const stats = response.data.stats;
        setImportResult({
          message: response.data.message,
          imported_records: stats?.trading_data_count || 0,
          concept_summaries: stats?.concept_summary_count || 0,
          ranking_records: stats?.ranking_count || 0,
          new_high_records: stats?.new_high_count || 0,
          trading_date: stats?.trading_date,
          filename: file.name
        });
        
        const parseFail = stats?.parse_error_count || 0;
        const extra = parseFail > 0 ? `，解析失败${parseFail}条` : '';
        message.success(`TXT导入成功！交易数据${stats?.trading_data_count || 0}条，概念汇总${stats?.concept_summary_count || 0}个${extra}`);
        // 若存在解析失败，弹出预览详情
        if ((stats?.parse_error_count || 0) > 0 && stats?.parse_errors_preview?.length) {
          Modal.info({
            title: `解析失败 ${stats.parse_error_count} 条（仅显示前${stats.parse_errors_preview.length}条）`,
            width: 720,
            content: (
              <div style={{ maxHeight: 360, overflowY: 'auto' }}>
                {stats.parse_errors_preview.map((e: any, idx: number) => (
                  <div key={idx} style={{ padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                    <div style={{ color: '#fa541c' }}>第 {e.line_number} 行：{e.reason}</div>
                    <div style={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', color: '#555' }}>{e.content}</div>
                  </div>
                ))}
                {stats.parse_errors_truncated && (
                  <div style={{ marginTop: 8 }}>
                    <Tag color="warning">仅显示前{stats.parse_errors_preview.length}条</Tag>
                  </div>
                )}
              </div>
            )
          });
        }
        
        // 发送全局事件通知TXT导入记录组件刷新
        window.dispatchEvent(new CustomEvent('txtImportSuccess', {
          detail: { stats, tradingDate: stats?.trading_date }
        }));
      } else {
        const errorMsg = response.data.message || 'TXT导入失败';
        console.error('❌ TXT导入失败:', response.data);
        hideLoading(); // 确保隐藏loading
        
        // 显示错误结果信息
        setImportResult({
          success: false,
          error: true,
          message: errorMsg,
          filename: file.name,
          imported_records: 0,
          concept_summaries: 0,
          ranking_records: 0,
          new_high_records: 0
        });
        
        // 同时显示toast
        message.error({
          content: errorMsg,
          duration: 6,
          key: 'txt-import-error'
        });
      }
      
    } catch (error: any) {
      console.error('❌ 新TXT导入异常:', error);
      hideLoading();
      
      let errorMessage = 'TXT导入失败';
      
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      // 如果是网络超时错误
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        errorMessage = '导入超时，文件可能过大或服务器处理时间过长';
      }
      
      // 显示错误结果信息
      setImportResult({
        success: false,
        error: true,
        message: errorMessage,
        filename: file.name,
        imported_records: 0,
        concept_summaries: 0,
        ranking_records: 0,
        new_high_records: 0
      });
      
      // 同时显示toast
      message.error({
        content: `导入失败: ${errorMessage}`,
        duration: 6,
        key: 'txt-import-error'
      });
    } finally {
      setTxtImportLoading(false);
    }
  };

  // 优化后的TXT导入（使用详细统计API）
  const handleOptimizedTxtImport = async () => {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.txt';
    fileInput.style.display = 'none';
    
    fileInput.onchange = async (e: any) => {
      const file = e.target.files?.[0];
      if (!file) return;
      
      setTxtImportLoading(true);
      setImportResult(null); // 清空之前的结果
      
      // 显示导入开始提示
      const hideLoading = message.loading('TXT文件导入中，请稍候...', 0);
      
      try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await adminApiClient.post('/api/v1/data/import-txt?allow_overwrite=true', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 1800000 // 30分钟超时
        });
        
        console.log('✅ TXT导入成功:', response.data);
        hideLoading(); // 隐藏loading提示
        setImportResult(response.data);
        message.success(`TXT导入成功！导入 ${response.data.imported_records} 条记录`);
        
        // 刷新数据统计和股票列表 - 延迟一点确保后端处理完成
        setTimeout(async () => {
          await getImportedDataStats();
          await getStockList(stockSearchText); // 重新加载股票列表
        }, 1000);
        
      } catch (error: any) {
        console.error('❌ TXT导入失败:', error);
        hideLoading(); // 隐藏loading提示
        message.error(`TXT导入失败: ${error.response?.data?.detail || error.message}`);
      } finally {
        setTxtImportLoading(false);
        document.body.removeChild(fileInput);
      }
    };
    
    document.body.appendChild(fileInput);
    fileInput.click();
  };

  const handleTxtImport = async () => {
    // 防止重复点击
    if (txtImportLoading) {
      return;
    }

    try {
      const fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.accept = '.txt';
      fileInput.style.display = 'none';
      
      // 使用Promise包装文件选择
      const selectedFile = await new Promise<File | null>((resolve) => {
        fileInput.onchange = (e: any) => {
          const file = e.target.files?.[0] || null;
          resolve(file);
          document.body.removeChild(fileInput);
        };
        
        fileInput.oncancel = () => {
          resolve(null);
          document.body.removeChild(fileInput);
        };
        
        // 添加到DOM以确保事件正常触发
        document.body.appendChild(fileInput);
        fileInput.click();
      });

      // 用户取消选择
      if (!selectedFile) {
        return;
      }

      // 验证文件名
      if (selectedFile.name !== 'EEE.txt') {
        message.error('请选择名为 EEE.txt 的文件');
        return;
      }

      // 验证文件大小 (限制50MB)
      if (selectedFile.size > 50 * 1024 * 1024) {
        message.error('文件大小不能超过50MB');
        return;
      }

      setTxtImportLoading(true);
      
      try {
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        // 构建请求URL
        const url = todayImportStatus.txt_imported 
          ? '/api/v1/data/import-txt?allow_overwrite=true' 
          : '/api/v1/data/import-txt';
        
        console.log('🚀 开始TXT导入:', {
          fileName: selectedFile.name,
          fileSize: selectedFile.size,
          url: url,
          isOverwrite: todayImportStatus.txt_imported
        });
        
        const result = await adminApiClient.post(url, formData, {
          headers: { 
            'Content-Type': 'multipart/form-data'
          },
          timeout: 300000, // 5分钟超时
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / (progressEvent.total || 1)
            );
            console.log('上传进度:', percentCompleted + '%');
          }
        });
        
        console.log('✅ TXT导入成功:', result.data);
        
        // 更新状态
        setImportStatus(prev => ({ ...prev, txt: true }));
        
        const statusText = todayImportStatus.txt_imported ? '（覆盖导入）' : '（首次导入）';
        const successMsg = `TXT导入成功！导入${result.data.imported_records}条记录${statusText}`;
        
        if (result.data.skipped_records > 0) {
          message.warning(`${successMsg}，跳过${result.data.skipped_records}条记录`);
        } else {
          message.success(successMsg);
        }
        
        // 刷新导入状态
        await getTodayImportStatus();
        
      } catch (error: any) {
        console.error('❌ TXT导入失败:', error);
        
        let errorMsg = 'TXT导入失败';
        if (error.response?.data?.detail) {
          errorMsg = `TXT导入失败: ${error.response.data.detail}`;
        } else if (error.code === 'ECONNABORTED') {
          errorMsg = 'TXT导入超时，请检查文件大小或网络连接';
        } else if (error.message) {
          errorMsg = `TXT导入失败: ${error.message}`;
        }
        
        message.error(errorMsg);
      }
    } catch (error) {
      console.error('❌ 文件选择过程出错:', error);
      message.error('文件选择过程出错');
    } finally {
      setTxtImportLoading(false);
    }
  };

  const columns = [
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
    },
    {
      title: '股票名称', 
      dataIndex: 'stock_name',
      key: 'stock_name',
    },
    {
      title: '行业',
      dataIndex: 'industry',
      key: 'industry',
    },
    {
      title: '是否可转债',
      dataIndex: 'is_convertible_bond',
      key: 'is_convertible_bond',
      render: (value: boolean) => value ? '是' : '否',
    },
  ];

  const menuItems = [
    {
      key: 'simple-import',
      icon: <CloudUploadOutlined />,
      label: '数据导入',
    },
    {
      key: 'concepts',
      icon: <ApiOutlined />,
      label: '概念分析',
    },
    {
      key: 'stock-analysis',
      icon: <SearchOutlined />,
      label: '个股分析',
    },
    {
      key: 'innovation-analysis',
      icon: <FireOutlined />,
      label: '创新高分析',
    },
    {
      key: 'convertible-bonds',
      icon: <DatabaseOutlined />,
      label: '转债分析',
    },
    {
      key: 'user',
      icon: <UserOutlined />,
      label: '用户管理',
    },
    {
      key: 'packages',
      icon: <GiftOutlined />,
      label: '套餐管理',
    },
  ];

  return (
    <AdminLayout activeTab={activeTab} onTabChange={setActiveTab}>
      <div>
        {/* 控制台页面 */}
        {activeTab === 'dashboard' && <Dashboard />}

        {/* 数据导入页面 - 使用Tab分离股票列表和导入记录 */}
            {activeTab === 'simple-import' && (
              <DataImportPage 
                stocks={stockList}
                loading={stockLoading}
                csvImportLoading={csvImportLoading}
                txtImportLoading={txtImportLoading}
                importStats={importedData}
                importResult={importResult}
                onGetAllStocks={getAllStocks}
                onCsvImport={handleOptimizedCsvImport}
                onTxtImport={handleNewTxtImport}
                onGetStockList={getStockList}
                searchText={stockSearchText}
                onSearchTextChange={setStockSearchText}
                onUpdateStock={updateStockInList}
              />
            )}


            {/* 概念分析页面 */}
            {activeTab === 'concepts' && <ConceptAnalysisPage />}


            {/* 新的业务分析页面 */}
            {activeTab === 'stock-analysis' && <NewStockAnalysisPage />}

            {activeTab === 'innovation-analysis' && (
              <InnovationAnalysisPage />
            )}

            {activeTab === 'convertible-bonds' && (
              <ConvertibleBondPage />
            )}

        {activeTab === 'client-users' && <UserManagement />}
        {activeTab === 'admin-users' && <AdminManagement />}
        {activeTab === 'packages' && <PackageManagement />}
      </div>

      {/* 删除确认Modal */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', color: '#ff4d4f' }}>
            <DeleteOutlined style={{ marginRight: 8, fontSize: '18px' }} />
            确认删除
          </div>
        }
        open={deleteModalVisible}
        onOk={handleBatchDelete}
        onCancel={() => setDeleteModalVisible(false)}
        okText="删除"
        cancelText="取消"
        okType="danger"
        confirmLoading={deleteLoading}
      >
        <div style={{ padding: '20px 0' }}>
          <p style={{ marginBottom: 16, fontSize: '16px' }}>
            你确定要删除这些股票数据吗？此操作将不可恢复。
          </p>
          <Alert
            message={`将删除 ${selectedRowKeys.length} 条股票记录`}
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
        </div>
      </Modal>

      {/* TXT覆盖确认Modal */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', color: '#faad14' }}>
            <ExclamationCircleOutlined style={{ marginRight: 8, fontSize: '18px' }} />
            数据覆盖确认
          </div>
        }
        open={txtOverwriteModalVisible}
        onOk={handleTxtOverwriteConfirm}
        onCancel={handleTxtOverwriteCancel}
        okText="确认覆盖"
        cancelText="取消"
        okType="danger"
        confirmLoading={txtImportLoading}
      >
        <div style={{ padding: '20px 0' }}>
          <p style={{ marginBottom: 16, fontSize: '16px' }}>
            检测到 <strong style={{ color: '#1890ff' }}>{txtOverwriteDate}</strong> 已有导入记录 (共<strong>{txtOverwriteCount}</strong>条)。
          </p>
          <p style={{ marginBottom: 16 }}>
            继续导入将<span style={{ color: '#ff4d4f', fontWeight: 'bold' }}>删除原有数据</span>并重新导入，此操作不可撤销。
          </p>
          <p style={{ fontSize: '16px', fontWeight: 'bold', color: '#fa541c' }}>
            是否确认覆盖导入？
          </p>
        </div>
      </Modal>
    </AdminLayout>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
