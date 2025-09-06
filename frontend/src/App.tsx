import React, { useState, useEffect } from 'react';
import { 
  Layout, Menu, Button, Input, Card, Table, message, Upload, Space, 
  Divider, Alert, Row, Col, Typography, Steps, Progress, Statistic, 
  Tag, Badge, Tooltip, Spin, Modal 
} from 'antd';
import { 
  SearchOutlined, UserOutlined, ApiOutlined, UploadOutlined, 
  CloudUploadOutlined, FileTextOutlined, DatabaseOutlined,
  CheckCircleOutlined, ClockCircleOutlined, GiftOutlined, DeleteOutlined
} from '@ant-design/icons';
import { apiClient } from '../../shared/auth';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginPage from './components/LoginPage';
import AdminLayout from './components/AdminLayout';
import Dashboard from './components/Dashboard';
import UserManagement from './components/UserManagement';
import PackageManagement from './components/PackageManagement';

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

  // 获取已导入的数据统计
  const getImportedDataStats = async () => {
    setDataLoading(true);
    try {
      // 并行获取统计数据
      const [stocksCountResponse, conceptsCountResponse] = await Promise.all([
        // 获取股票真实总数
        apiClient.get('/api/v1/stocks/count'),
        
        // 获取概念真实总数
        apiClient.get('/api/v1/concepts/count')
      ]);
      
      console.log('获取到的数据:', {
        stocks: stocksCountResponse.data?.total,
        concepts: conceptsCountResponse.data?.total
      });
      
      setImportedData({
        stockCount: stocksCountResponse.data?.total || 0,
        conceptCount: conceptsCountResponse.data?.total || 0
      });
      
    } catch (error) {
      console.error('获取导入数据统计失败:', error);
      // 如果获取失败，设置默认值
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
      
      const response = await apiClient.get(url);
      
      // 股票列表包含部分概念信息
      const stocksData = (response.data || []).map((stock: any) => ({
        ...stock,
        concepts: stock.concepts || [], // 已加载的部分概念
        conceptsLoaded: false, // 标记为可以加载更多概念
        showingPartialConcepts: true // 标记正在显示部分概念
      }));
      
      setStockList(stocksData);
      setPagination(prev => ({ ...prev, total: stocksData.length }));
    } catch (error) {
      console.error('获取股票列表失败:', error);
      setStockList([]);
    } finally {
      setStockLoading(false);
    }
  };

  // 获取单个股票的概念信息
  const getStockConcepts = async (stockCode: string) => {
    try {
      const response = await apiClient.get(`/api/v1/stocks/${stockCode}`);
      return response.data?.concepts || [];
    } catch (error) {
      console.error(`获取股票${stockCode}的概念失败:`, error);
      return [];
    }
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
      await apiClient.delete(`/api/v1/stocks/${deleteStockId}`);
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
      await apiClient.delete('/api/v1/stocks/batch', {
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

  // 搜索股票列表
  const handleStockSearch = async () => {
    await getStockList(stockSearchText);
  };


  // 搜索股票
  const searchStocks = async () => {
    if (!searchText.trim()) {
      message.warning('请输入股票代码或名称');
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.get(`/api/v1/stocks`, {
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
      const response = await apiClient.get('/api/v1/stocks');
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
      const response = await apiClient.get(`/api/v1/data/import-status/${today}`);
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
        
        const result = await apiClient.post(url, formData, {
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
        
        const result = await apiClient.post('/api/v1/simple-import/simple-csv', formData, {
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
        
        const result = await apiClient.post('/api/v1/simple-import/simple-txt', formData, {
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
        
        const response = await apiClient.post('/api/v1/data/import-csv?allow_overwrite=true', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 600000 // 10分钟超时
        });
        
        console.log('✅ CSV导入成功:', response.data);
        hideLoading(); // 隐藏loading提示
        setImportResult(response.data);
        message.success(`CSV导入成功！导入 ${response.data.imported_records} 条记录`);
        
        // 刷新数据统计和股票列表 - 延迟一点确保后端处理完成
        setTimeout(async () => {
          await getImportedDataStats();
          await getStockList(stockSearchText); // 重新加载股票列表
        }, 1000);
        
      } catch (error: any) {
        console.error('❌ CSV导入失败:', error);
        hideLoading(); // 隐藏loading提示
        message.error(`CSV导入失败: ${error.response?.data?.detail || error.message}`);
      } finally {
        setCsvImportLoading(false);
        document.body.removeChild(fileInput);
      }
    };
    
    document.body.appendChild(fileInput);
    fileInput.click();
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
        
        const response = await apiClient.post('/api/v1/data/import-txt?allow_overwrite=true', formData, {
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
        
        const result = await apiClient.post(url, formData, {
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
      key: 'stocks',
      icon: <SearchOutlined />,
      label: '股票查询',
    },
    {
      key: 'concepts',
      icon: <ApiOutlined />,
      label: '概念分析',
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

        {/* 数据导入页面 - 重新设计版本 */}
            {activeTab === 'simple-import' && (
              <div className="main-content">
                <Card 
                  title="📁 数据导入"
                  size="small"
                  style={{ 
                    borderRadius: '8px',
                    marginBottom: 12
                  }}
                  bodyStyle={{ padding: '12px' }}
                >
                  <Row gutter={[12, 12]}>
                    <Col xs={24} md={12}>
                      <div 
                        style={{ 
                          padding: '12px',
                          borderRadius: '6px',
                          background: '#f6ffed',
                          border: '1px solid #d9f7be',
                          textAlign: 'center'
                        }}
                      >
                        <div style={{ marginBottom: '8px' }}>
                          <span style={{ fontSize: '18px', marginRight: '4px' }}>📊</span>
                          <Text strong style={{ color: '#52c41a', fontSize: '14px' }}>
                            CSV基础数据
                          </Text>
                        </div>
                        <Button 
                          size="small"
                          icon={<UploadOutlined />}
                          loading={csvImportLoading}
                          onClick={handleOptimizedCsvImport}
                          type="primary"
                          style={{ background: '#52c41a', borderColor: '#52c41a' }}
                        >
                          {csvImportLoading ? '导入中' : '选择文件'}
                        </Button>
                      </div>
                    </Col>
                    
                    <Col xs={24} md={12}>
                      <div 
                        style={{ 
                          padding: '12px',
                          borderRadius: '6px',
                          background: '#fff7e6',
                          border: '1px solid #ffd591',
                          textAlign: 'center'
                        }}
                      >
                        <div style={{ marginBottom: '8px' }}>
                          <span style={{ fontSize: '18px', marginRight: '4px' }}>📈</span>
                          <Text strong style={{ color: '#fa8c16', fontSize: '14px' }}>
                            TXT热度数据
                          </Text>
                        </div>
                        <Button 
                          size="small"
                          icon={<UploadOutlined />}
                          loading={txtImportLoading}
                          onClick={handleOptimizedTxtImport}
                          type="primary"
                          style={{ background: '#fa8c16', borderColor: '#fa8c16' }}
                        >
                          {txtImportLoading ? '导入中' : '选择文件'}
                        </Button>
                      </div>
                    </Col>
                  </Row>
                </Card>

                {/* 导入结果显示 */}
                {importResult && (
                  <Alert 
                    message={`✅ ${importResult.message || '导入完成'}`}
                    description={
                      <div style={{ marginTop: '8px' }}>
                        <Row gutter={[8, 8]}>
                          <Col xs={12} sm={6}>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              📥 导入: <Text strong>{importResult.imported_records || 0}</Text>
                            </Text>
                          </Col>
                          <Col xs={12} sm={6}>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              ⏭️ 跳过: <Text strong>{importResult.skipped_records || 0}</Text>
                            </Text>
                          </Col>
                          {importResult.errors && importResult.errors.length > 0 && (
                            <Col xs={12} sm={6}>
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                ❌ 错误: <Text strong style={{ color: '#f5222d' }}>{importResult.errors.length}</Text>
                              </Text>
                            </Col>
                          )}
                          <Col xs={12} sm={6}>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              📄 文件: <Text strong>{importResult.filename || '未知'}</Text>
                            </Text>
                          </Col>
                        </Row>
                        {importResult.import_date && (
                          <div style={{ marginTop: '8px', fontSize: '11px' }}>
                            <Text type="secondary">
                              {importResult.import_date} • {importResult.overwrite ? '覆盖模式' : '新增模式'}
                            </Text>
                          </div>
                        )}
                      </div>
                    }
                    type="success"
                    style={{ 
                      marginBottom: 12,
                      borderRadius: '6px'
                    }}
                    showIcon
                  />
                )}


                {/* 股票搜索区域 */}
                <Card 
                  title={
                    <Space>
                      <SearchOutlined />
                      <span>股票列表</span>
                      <Badge count={stockList.length} overflowCount={999999} style={{ backgroundColor: '#52c41a' }} />
                    </Space>
                  }
                  style={{ 
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                    marginBottom: 16
                  }}
                >
                  <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                    <Col xs={24}>
                      <Input.Search
                        placeholder="输入股票代码、名称、行业或概念进行搜索..."
                        value={stockSearchText}
                        onChange={(e) => setStockSearchText(e.target.value)}
                        onSearch={handleStockSearch}
                        loading={stockLoading}
                        enterButton="搜索"
                        size="large"
                      />
                    </Col>
                  </Row>
                  {selectedRowKeys.length > 0 && (
                    <Row style={{ marginBottom: 16 }}>
                      <Col xs={24}>
                        <Alert
                          message={
                            <Space>
                              <span>已选择 {selectedRowKeys.length} 项</span>
                              <Button 
                                size="small" 
                                type="link" 
                                onClick={() => setSelectedRowKeys([])}
                              >
                                取消选择
                              </Button>
                              <Button 
                                size="small" 
                                type="primary" 
                                danger
                                icon={<DeleteOutlined />}
                                loading={deleteLoading}
                                onClick={handleBatchDelete}
                              >
                                批量删除
                              </Button>
                            </Space>
                          }
                          type="info"
                          showIcon
                        />
                      </Col>
                    </Row>
                  )}
                </Card>

                {/* 股票列表表格 */}
                <Card 
                  style={{ 
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
                  }}
                  loading={stockLoading}
                >
                  <Table
                    dataSource={stockList}
                    rowKey="id"
                    pagination={{
                      ...pagination,
                      total: stockList.length,
                      showSizeChanger: true,
                      showQuickJumper: true,
                      pageSizeOptions: ['10', '20', '50', '100', '200'],
                      showTotal: (total, range) => `${range[0]}-${range[1]} 共 ${total} 只股票`,
                      onChange: (page, size) => {
                        setPagination(prev => ({ ...prev, current: page, pageSize: size || prev.pageSize }));
                      },
                      onShowSizeChange: (current, size) => {
                        setPagination(prev => ({ ...prev, current: 1, pageSize: size }));
                      }
                    }}
                    size="middle"
                    scroll={{ x: 'max-content' }}
                    columns={[
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
                                    onClick={async () => {
                                      // 设置加载状态
                                      setStockList(prev => prev.map(stock => 
                                        stock.id === record.id 
                                          ? { ...stock, conceptsLoading: true }
                                          : stock
                                      ));
                                      
                                      try {
                                        const allConcepts = await getStockConcepts(record.stock_code);
                                        setStockList(prev => prev.map(stock => 
                                          stock.id === record.id 
                                            ? { 
                                                ...stock, 
                                                concepts: allConcepts, 
                                                conceptsLoaded: true,
                                                conceptsLoading: false,
                                                showingPartialConcepts: false
                                              }
                                            : stock
                                        ));
                                      } catch (error) {
                                        console.error('获取全部概念失败:', error);
                                        setStockList(prev => prev.map(stock => 
                                          stock.id === record.id 
                                            ? { 
                                                ...stock, 
                                                conceptsLoading: false
                                              }
                                            : stock
                                        ));
                                      }
                                    }}
                                    loading={record.conceptsLoading}
                                    style={{ padding: 0, fontSize: '12px' }}
                                  >
                                    {record.conceptsLoading ? '加载中...' : '查看更多'}
                                  </Button>
                                )}
                                
                                {/* 如果已加载完整概念且数量超过显示的数量 */}
                                {record.conceptsLoaded && record.concepts.length > 3 && (
                                  <Tag color="default" style={{ margin: '2px' }}>
                                    共{record.concepts.length}个概念
                                  </Tag>
                                )}
                              </div>
                            ) : (
                              <Text type="secondary">暂无概念</Text>
                            )}
                          </div>
                        )
                      },
                      {
                        title: '操作',
                        key: 'action',
                        width: 100,
                        fixed: 'right' as const,
                        render: (record: any) => (
                          <Button
                            type="link"
                            danger
                            size="small"
                            icon={<DeleteOutlined />}
                            loading={deleteLoading}
                            onClick={() => {
                              console.log('🖱️ 点击删除按钮, record.id:', record.id);
                              handleDeleteStock(record.id);
                            }}
                            style={{ padding: 0 }}
                          >
                            删除
                          </Button>
                        )
                      }
                    ]}
                    rowSelection={{
                      selectedRowKeys,
                      onChange: (keys) => setSelectedRowKeys(keys),
                      columnWidth: 50,
                    }}
                    locale={{ 
                      emptyText: stockList.length === 0 ? 
                        <div style={{ padding: '40px 0', textAlign: 'center' }}>
                          <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.5 }}>📊</div>
                          <div style={{ color: '#999', fontSize: '14px' }}>暂无股票数据</div>
                          <div style={{ color: '#ccc', fontSize: '12px', marginTop: '8px' }}>
                            请先完成数据导入，或尝试搜索其他关键词
                          </div>
                        </div> : 
                        '暂无数据'
                    }}
                  />
                </Card>
              </div>
            )}

            {/* 股票查询页面 - 响应式设计 */}
            {activeTab === 'stocks' && (
              <div className="main-content">
                {/* 搜索区域 */}
                <Card 
                  style={{ 
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
                  }}
                >
                  <Row gutter={[16, 16]} align="middle">
                    <Col xs={24} sm={16} md={18} lg={20} order={1}>
                      <Input.Search
                        size="large"
                        placeholder="输入股票代码或名称进行搜索..."
                        value={searchText}
                        onChange={(e) => setSearchText(e.target.value)}
                        onSearch={searchStocks}
                        loading={loading}
                        style={{ borderRadius: '8px', width: '100%' }}
                      />
                    </Col>
                    <Col xs={24} sm={8} md={6} lg={4} order={2}>
                      <Button 
                        size="large"
                        block
                        onClick={getAllStocks} 
                        loading={loading}
                        style={{ borderRadius: '8px' }}
                      >
                        获取所有
                      </Button>
                    </Col>
                  </Row>
                </Card>

                {/* 数据表格区域 */}
                <Card 
                  title={
                    <Space>
                      <DatabaseOutlined />
                      <span>股票数据列表</span>
                      <Badge count={stocks.length} style={{ backgroundColor: '#52c41a' }} />
                    </Space>
                  }
                  style={{ 
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
                  }}
                >
                  <Table
                    columns={columns.map(col => ({
                      ...col,
                      responsive: col.key === 'industry' ? ['lg'] : undefined,
                      width: col.key === 'stock_code' ? 120 : 
                             col.key === 'stock_name' ? 200 : 
                             col.key === 'industry' ? 150 : 
                             col.key === 'is_convertible_bond' ? 120 : undefined
                    }))}
                    dataSource={stocks}
                    rowKey="id"
                    loading={loading}
                    pagination={{ 
                      pageSize: 15,
                      showSizeChanger: true,
                      showQuickJumper: true,
                      showTotal: (total, range) => `${range[0]}-${range[1]} 共 ${total} 条`,
                      responsive: true
                    }}
                    scroll={{ x: 'max-content' }}
                    size="middle"
                  />
                </Card>
                
                {/* 添加示例内容来测试滚动 */}
                <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
                  <Col xs={24} sm={12} md={8}>
                    <Card title="📊 数据统计" size="small">
                      <Statistic title="今日查询" value={123} />
                    </Card>
                  </Col>
                  <Col xs={24} sm={12} md={8}>
                    <Card title="🔥 热门股票" size="small">
                      <Statistic title="关注数" value={456} />
                    </Card>
                  </Col>
                  <Col xs={24} sm={12} md={8}>
                    <Card title="💰 市值统计" size="small">
                      <Statistic title="总市值" value={789} suffix="亿" />
                    </Card>
                  </Col>
                </Row>
                
                {/* 更多示例卡片用于测试滚动 */}
                {Array.from({ length: 8 }, (_, i) => (
                  <Card key={i} title={`示例内容 ${i + 1}`} style={{ marginTop: 16 }}>
                    <p>这是用于测试整页滚动效果的示例内容。当内容足够多时，整个页面会出现滚动条，而头部导航会保持固定在顶部。</p>
                    <p>侧边栏会跟随页面一起滚动，这是传统的网页布局方式。</p>
                  </Card>
                ))}
              </div>
            )}


            {/* 其他页面占位 */}
            {activeTab === 'concepts' && (
              <Card title="概念分析" style={{ textAlign: 'center', padding: '60px' }}>
                <h2>🔍 概念分析功能</h2>
                <p>功能开发中...</p>
              </Card>
            )}

            {activeTab === 'user' && (
              <UserManagement />
            )}

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
        onOk={confirmDeleteStock}
        onCancel={cancelDelete}
        okText="确认删除"
        cancelText="取消"
        okType="danger"
        confirmLoading={deleteLoading}
        centered
        maskClosable={false}
      >
        <div style={{ padding: '10px 0' }}>
          <p style={{ margin: 0, fontSize: '14px', color: '#666' }}>
            确定要删除这只股票吗？
          </p>
          <p style={{ margin: '8px 0 0', fontSize: '12px', color: '#999' }}>
            ⚠️ 此操作将永久删除股票数据，无法撤销
          </p>
        </div>
      </Modal>

      {/* 批量删除确认Modal */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', color: '#ff4d4f' }}>
            <DeleteOutlined style={{ marginRight: 8, fontSize: '18px' }} />
            批量删除确认
          </div>
        }
        open={batchDeleteModalVisible}
        onOk={confirmBatchDelete}
        onCancel={cancelBatchDelete}
        okText={`确认删除 ${selectedRowKeys.length} 只股票`}
        cancelText="取消"
        okType="danger"
        confirmLoading={deleteLoading}
        centered
        maskClosable={false}
      >
        <div style={{ padding: '10px 0' }}>
          <p style={{ margin: 0, fontSize: '14px', color: '#666' }}>
            确定要删除选中的 <strong style={{ color: '#ff4d4f' }}>{selectedRowKeys.length}</strong> 只股票吗？
          </p>
          <p style={{ margin: '8px 0 0', fontSize: '12px', color: '#999' }}>
            ⚠️ 此操作将永久删除所有选中的股票数据，无法撤销
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