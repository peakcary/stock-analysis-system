import React, { useState, useEffect } from 'react';
import { 
  Layout, Menu, Button, Input, Card, Table, message, Upload, Space, 
  Divider, Alert, Row, Col, Typography, Steps, Progress, Statistic, 
  Tag, Badge, Tooltip, Spin 
} from 'antd';
import { 
  SearchOutlined, UserOutlined, ApiOutlined, UploadOutlined, 
  CloudUploadOutlined, FileTextOutlined, DatabaseOutlined,
  CheckCircleOutlined, ClockCircleOutlined, GiftOutlined
} from '@ant-design/icons';
import axios from 'axios';
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

  // 组件加载时获取今日导入状态
  useEffect(() => {
    if (activeTab === 'import') {
      getTodayImportStatus();
    }
  }, [activeTab]);

  // 搜索股票
  const searchStocks = async () => {
    if (!searchText.trim()) {
      message.warning('请输入股票代码或名称');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.get(`/api/v1/stocks`, {
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
      const response = await axios.get('/api/v1/stocks');
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
      const response = await axios.get(`/api/v1/data/import-status/${today}`);
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
        
        const baseUrl = 'http://localhost:8000/api/v1/data/import-csv';
        const url = todayImportStatus.csv_imported 
          ? `${baseUrl}?allow_overwrite=true` 
          : baseUrl;
        
        console.log('📡 发送请求到:', url);
        
        const result = await axios.post(url, formData, {
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
        
        const result = await axios.post('/api/v1/simple-import/simple-csv', formData, {
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
        
        const result = await axios.post('/api/v1/simple-import/simple-txt', formData, {
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
        const baseUrl = 'http://localhost:8000/api/v1/data/import-txt';
        const url = todayImportStatus.txt_imported 
          ? `${baseUrl}?allow_overwrite=true` 
          : baseUrl;
        
        console.log('🚀 开始TXT导入:', {
          fileName: selectedFile.name,
          fileSize: selectedFile.size,
          url: url,
          isOverwrite: todayImportStatus.txt_imported
        });
        
        const result = await axios.post(url, formData, {
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
      label: '简化导入',
    },
    {
      key: 'stocks',
      icon: <SearchOutlined />,
      label: '股票查询',
    },
    {
      key: 'import',
      icon: <UploadOutlined />,
      label: '原导入（测试）',
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

        {/* 简化导入页面 */}
            {activeTab === 'simple-import' && (
              <div className="main-content">
                <Card 
                  title="📁 数据文件导入" 
                  style={{ 
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                    marginBottom: 24
                  }}
                >
                  <Row gutter={[24, 24]}>
                    <Col xs={24} md={12}>
                      <Card 
                        style={{ 
                          textAlign: 'center',
                          minHeight: 200,
                          border: '2px dashed #d9d9d9',
                          borderRadius: '8px'
                        }}
                        bodyStyle={{ padding: '40px 20px' }}
                      >
                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
                        <Title level={4}>CSV文件导入</Title>
                        <Text type="secondary">股票概念数据</Text>
                        <br />
                        <Text type="secondary">格式: 股票代码,股票名称,全部页数,热帖首页页阅读总数,价格,行业,概念,换手,净流入</Text>
                        
                        <div style={{ marginTop: '24px' }}>
                          <Button 
                            type="primary"
                            size="large"
                            icon={<UploadOutlined />}
                            loading={csvImportLoading}
                            onClick={handleSimpleCsvImport}
                            style={{ borderRadius: '8px' }}
                          >
                            {csvImportLoading ? '导入中...' : '选择CSV文件'}
                          </Button>
                        </div>
                      </Card>
                    </Col>
                    
                    <Col xs={24} md={12}>
                      <Card 
                        style={{ 
                          textAlign: 'center',
                          minHeight: 200,
                          border: '2px dashed #d9d9d9',
                          borderRadius: '8px'
                        }}
                        bodyStyle={{ padding: '40px 20px' }}
                      >
                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>📈</div>
                        <Title level={4}>TXT文件导入</Title>
                        <Text type="secondary">股票时间序列数据</Text>
                        <br />
                        <Text type="secondary">格式: 股票代码\t日期\t数值 (约280万行数据)</Text>
                        
                        <div style={{ marginTop: '24px' }}>
                          <Button 
                            type="primary"
                            size="large"
                            icon={<UploadOutlined />}
                            loading={txtImportLoading}
                            onClick={handleSimpleTxtImport}
                            style={{ borderRadius: '8px' }}
                          >
                            {txtImportLoading ? '导入中...' : '选择TXT文件'}
                          </Button>
                        </div>
                      </Card>
                    </Col>
                  </Row>
                </Card>

                <Card 
                  title="📋 使用说明" 
                  style={{ 
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
                  }}
                >
                  <Row gutter={[24, 16]}>
                    <Col xs={24} md={12}>
                      <Title level={5}>📊 CSV文件要求</Title>
                      <ul>
                        <li>文件格式：UTF-8编码的CSV文件</li>
                        <li>文件大小：最大50MB</li>
                        <li>数据量：约5.4万行股票概念数据</li>
                        <li>示例路径：<Text code>/Users/cary/Downloads/数据分析/数据文件/2025-08-12-09-38.csv</Text></li>
                      </ul>
                    </Col>
                    <Col xs={24} md={12}>
                      <Title level={5}>📈 TXT文件要求</Title>
                      <ul>
                        <li>文件格式：UTF-8编码的TXT文件</li>
                        <li>文件大小：最大100MB</li>
                        <li>数据量：约280万行时间序列数据</li>
                        <li>示例路径：<Text code>/Users/cary/Downloads/数据分析/数据文件/EEE.txt</Text></li>
                      </ul>
                    </Col>
                  </Row>
                  
                  <Divider />
                  
                  <Title level={5}>⚠️ 注意事项</Title>
                  <ul>
                    <li>大文件导入可能需要几分钟时间，请耐心等待</li>
                    <li>导入过程中请勿关闭浏览器或刷新页面</li>
                    <li>重复导入会覆盖相同股票代码和日期的数据</li>
                    <li>可以在浏览器控制台查看详细的导入日志</li>
                  </ul>
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
                    <Col xs={24} sm={18} md={18} lg={20}>
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
                    <Col xs={24} sm={6} md={6} lg={4}>
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

            {/* 数据导入页面 - 简化重构版本 */}
            {activeTab === 'import' && (
              <div className="main-content">
                {/* 顶部状态卡片 - 响应式网格 */}
                <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                  <Col xs={24} sm={8}>
                    <Card 
                      style={{ 
                        borderRadius: '12px',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        border: 0,
                        color: 'white'
                      }}
                      bodyStyle={{ padding: '20px' }}
                    >
                      <Statistic
                        title={<span style={{color: 'rgba(255,255,255,0.8)'}}>今日进度</span>}
                        value={((importStatus.csv ? 1 : 0) + (importStatus.txt ? 1 : 0)) * 50}
                        suffix="/ 100%"
                        prefix={<DatabaseOutlined />}
                        valueStyle={{ color: 'white' }}
                      />
                      <Progress 
                        percent={((importStatus.csv ? 1 : 0) + (importStatus.txt ? 1 : 0)) * 50}
                        status={importStatus.csv && importStatus.txt ? 'success' : 'normal'}
                        strokeColor="rgba(255,255,255,0.8)"
                        trailColor="rgba(255,255,255,0.2)"
                        style={{ marginTop: 12 }}
                      />
                    </Card>
                  </Col>
                  <Col xs={12} sm={8}>
                    <Card style={{ borderRadius: '12px', textAlign: 'center' }}>
                      <Statistic
                        title="CSV状态"
                        value={importStatus.csv ? "已完成" : "待导入"}
                        prefix={importStatus.csv ? 
                          <CheckCircleOutlined style={{color: '#52c41a', fontSize: '24px'}} /> : 
                          <ClockCircleOutlined style={{color: '#faad14', fontSize: '24px'}} />
                        }
                        valueStyle={{ 
                          color: importStatus.csv ? '#52c41a' : '#faad14',
                          fontSize: '16px' 
                        }}
                      />
                    </Card>
                  </Col>
                  <Col xs={12} sm={8}>
                    <Card style={{ borderRadius: '12px', textAlign: 'center' }}>
                      <Statistic
                        title="TXT状态"
                        value={importStatus.txt ? "已完成" : "待导入"}
                        prefix={importStatus.txt ? 
                          <CheckCircleOutlined style={{color: '#52c41a', fontSize: '24px'}} /> : 
                          <ClockCircleOutlined style={{color: '#faad14', fontSize: '24px'}} />
                        }
                        valueStyle={{ 
                          color: importStatus.txt ? '#52c41a' : '#faad14',
                          fontSize: '16px' 
                        }}
                      />
                    </Card>
                  </Col>
                </Row>

                {/* 简化的导入步骤 */}
                <Card 
                  title="📊 数据导入流程" 
                  style={{ 
                    marginBottom: 24,
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
                  }}
                >
                  <Steps
                    current={importStatus.csv ? (importStatus.txt ? 2 : 1) : 0}
                    responsive={false}
                    size="small"
                    items={[
                      {
                        title: 'CSV数据',
                        icon: <FileTextOutlined />,
                        status: importStatus.csv ? 'finish' : 'wait'
                      },
                      {
                        title: 'TXT数据', 
                        icon: <FileTextOutlined />,
                        status: importStatus.txt ? 'finish' : 'wait'
                      },
                      {
                        title: '完成',
                        icon: <CheckCircleOutlined />,
                        status: (importStatus.csv && importStatus.txt) ? 'finish' : 'wait'
                      }
                    ]}
                  />
                </Card>

                {/* 文件上传区域 - 响应式卡片 */}
                <Row gutter={[16, 16]}>
                  <Col xs={24} md={12}>
                    <Card 
                      style={{ 
                        borderRadius: '12px',
                        minHeight: '240px',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                        border: importStatus.csv ? '2px solid #52c41a' : '1px solid #f0f0f0'
                      }}
                    >
                      <div style={{ textAlign: 'center', padding: '20px 0' }}>
                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>📈</div>
                        <Title level={4}>股票数据</Title>
                        <Text type="secondary">AAA.csv - 基础股票信息</Text>
                        
                        <div style={{ marginTop: '24px' }}>
                          <Button 
                            type="primary"
                            icon={todayImportStatus.csv_imported ? <CheckCircleOutlined /> : <UploadOutlined />}
                            loading={csvImportLoading}
                            size="large"
                            onClick={() => {
                              console.log('🔥 按钮点击事件触发');
                              handleCsvImport();
                            }}
                            style={{ 
                              borderRadius: '8px',
                              backgroundColor: todayImportStatus.csv_imported ? '#52c41a' : undefined,
                              borderColor: todayImportStatus.csv_imported ? '#52c41a' : undefined
                            }}
                          >
                            {todayImportStatus.csv_imported ? 'CSV已导入 - 点击重新导入' : '导入CSV文件'}
                          </Button>
                          
                          {/* 调试按钮 */}
                          <Button 
                            style={{ marginLeft: 8 }}
                            onClick={async () => {
                              console.log('🔍 调试信息:', {
                                csvImportLoading,
                                todayImportStatus,
                                importStatus
                              });
                              
                              // 测试API连通性
                              try {
                                const response = await axios.get('/health');
                                console.log('✅ 后端连接正常:', response.data);
                                message.success('后端连接正常');
                                
                                // 测试获取导入状态
                                await getTodayImportStatus();
                                message.info('已刷新导入状态');
                              } catch (error) {
                                console.error('❌ 后端连接失败:', error);
                                message.error('后端连接失败');
                              }
                            }}
                          >
                            调试
                          </Button>
                          {todayImportStatus.csv_imported && todayImportStatus.csv_record && (
                            <div style={{ marginTop: '12px', textAlign: 'center' }}>
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                已导入 {todayImportStatus.csv_record.imported_records} 条记录
                                {todayImportStatus.csv_record.skipped_records > 0 && 
                                  ` (跳过 ${todayImportStatus.csv_record.skipped_records} 条)`
                                }
                              </Text>
                            </div>
                          )}
                        </div>
                      </div>
                    </Card>
                  </Col>
                  
                  <Col xs={24} md={12}>
                    <Card 
                      style={{ 
                        borderRadius: '12px',
                        minHeight: '240px',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                        border: importStatus.txt ? '2px solid #52c41a' : '1px solid #f0f0f0'
                      }}
                    >
                      <div style={{ textAlign: 'center', padding: '20px 0' }}>
                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔥</div>
                        <Title level={4}>热度数据</Title>
                        <Text type="secondary">EEE.txt - 股票热度指标</Text>
                        
                        <div style={{ marginTop: '24px' }}>
                          <Button 
                            type="primary"
                            icon={todayImportStatus.txt_imported ? <CheckCircleOutlined /> : <UploadOutlined />}
                            loading={txtImportLoading}
                            size="large"
                            onClick={handleTxtImport}
                            style={{ 
                              borderRadius: '8px',
                              backgroundColor: todayImportStatus.txt_imported ? '#52c41a' : undefined,
                              borderColor: todayImportStatus.txt_imported ? '#52c41a' : undefined
                            }}
                          >
                            {todayImportStatus.txt_imported ? 'TXT已导入 - 点击重新导入' : '导入TXT文件'}
                          </Button>
                          {todayImportStatus.txt_imported && todayImportStatus.txt_record && (
                            <div style={{ marginTop: '12px', textAlign: 'center' }}>
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                已导入 {todayImportStatus.txt_record.imported_records} 条记录
                                {todayImportStatus.txt_record.skipped_records > 0 && 
                                  ` (跳过 ${todayImportStatus.txt_record.skipped_records} 条)`
                                }
                              </Text>
                            </div>
                          )}
                        </div>
                      </div>
                    </Card>
                  </Col>
                </Row>

                {/* 今日导入状态 */}
                {(todayImportStatus.csv_imported || todayImportStatus.txt_imported) && (
                  <Card 
                    title="📊 今日导入记录" 
                    style={{ 
                      marginTop: 24,
                      borderRadius: '12px',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
                    }}
                  >
                    <Row gutter={[16, 16]}>
                      {todayImportStatus.csv_record && (
                        <Col xs={24} md={12}>
                          <Card size="small" style={{ background: '#f6ffed', border: '1px solid #b7eb8f' }}>
                            <Space direction="vertical" style={{ width: '100%' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Text strong>📈 CSV数据</Text>
                                <Tag color="green">{todayImportStatus.csv_record.import_status}</Tag>
                              </div>
                              <Text type="secondary">文件: {todayImportStatus.csv_record.file_name}</Text>
                              <div>
                                <Text>导入: {todayImportStatus.csv_record.imported_records}条</Text>
                                {todayImportStatus.csv_record.skipped_records > 0 && (
                                  <Text style={{ marginLeft: 8, color: '#faad14' }}>
                                    跳过: {todayImportStatus.csv_record.skipped_records}条
                                  </Text>
                                )}
                              </div>
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                导入时间: {new Date(todayImportStatus.csv_record.created_at).toLocaleString()}
                              </Text>
                            </Space>
                          </Card>
                        </Col>
                      )}
                      
                      {todayImportStatus.txt_record && (
                        <Col xs={24} md={12}>
                          <Card size="small" style={{ background: '#fff7e6', border: '1px solid #ffd591' }}>
                            <Space direction="vertical" style={{ width: '100%' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Text strong>🔥 TXT数据</Text>
                                <Tag color="orange">{todayImportStatus.txt_record.import_status}</Tag>
                              </div>
                              <Text type="secondary">文件: {todayImportStatus.txt_record.file_name}</Text>
                              <div>
                                <Text>导入: {todayImportStatus.txt_record.imported_records}条</Text>
                                {todayImportStatus.txt_record.skipped_records > 0 && (
                                  <Text style={{ marginLeft: 8, color: '#faad14' }}>
                                    跳过: {todayImportStatus.txt_record.skipped_records}条
                                  </Text>
                                )}
                              </div>
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                导入时间: {new Date(todayImportStatus.txt_record.created_at).toLocaleString()}
                              </Text>
                            </Space>
                          </Card>
                        </Col>
                      )}
                    </Row>
                  </Card>
                )}

                {/* 帮助信息 */}
                <Alert
                  message="💡 使用提示"
                  description={
                    <div>
                      <p>• 文件位置：<Text code>/Users/cary/Desktop/</Text></p>
                      <p>• 快捷键：在 Finder 中按 <Text keyboard>Cmd+Shift+G</Text> 快速定位</p>
                      <p>• 建议每日固定时间导入最新数据</p>
                      <p>• 如果当天已导入，再次导入会询问是否覆盖</p>
                    </div>
                  }
                  type="info"
                  showIcon
                  style={{ 
                    marginTop: 24,
                    borderRadius: '8px'
                  }}
                />
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