import React, { useState, useEffect, useRef } from 'react';
import {
  Card, Upload, Button, Progress, Alert, Steps, Modal, Descriptions,
  Typography, Space, Tag, message, Divider, Table, Collapse, Statistic
} from 'antd';
import {
  CloudUploadOutlined, EyeOutlined, PlayCircleOutlined,
  CheckCircleOutlined, ExclamationCircleOutlined, InfoCircleOutlined,
  HistoryOutlined, FileTextOutlined, ClockCircleOutlined
} from '@ant-design/icons';
import { adminApiClient } from '../../../shared/admin-auth';

const { Title, Text, Paragraph } = Typography;
const { Step } = Steps;
const { Panel } = Collapse;

interface PreviewData {
  total_lines: number;
  preview_lines: number;
  estimated_dates: number;
  estimated_total_dates?: number;
  date_preview: Record<string, {
    count: number;
    sample_lines: string[];
  }>;
}

interface ImportProgress {
  status: string;
  current: number;
  total: number;
  current_date: string;
  completed_dates: string[];
  failed_dates: string[];
  start_time: string;
  end_time?: string;
  filename: string;
  result?: any;
  error?: string;
}

const HistoricalDataImport: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [importProgress, setImportProgress] = useState<ImportProgress | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isLargeFile, setIsLargeFile] = useState(false);
  const [chunkUploadId, setChunkUploadId] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const progressInterval = useRef<NodeJS.Timeout | null>(null);

  // 清理定时器
  useEffect(() => {
    return () => {
      if (progressInterval.current) {
        clearInterval(progressInterval.current);
      }
    };
  }, []);

  // 文件选择处理
  const handleFileSelect = (info: any) => {
    console.log('文件选择事件:', info);
    const { file, fileList } = info;

    // 由于设置了 beforeUpload={() => false}，文件不会上传，直接处理
    if (file) {
      const actualFile = file.originFileObj || file;
      console.log('实际文件对象:', actualFile);

      // 验证文件类型
      if (!actualFile.name.endsWith('.txt')) {
        message.error('请选择TXT格式的文件');
        return;
      }

      // 验证文件大小并判断处理策略
      const fileSizeMB = actualFile.size / 1024 / 1024;

      if (fileSizeMB > 500) {
        message.error(`文件过大 (${fileSizeMB.toFixed(2)} MB)，超过最大限制 500MB`);
        return;
      }

      const isLarge = fileSizeMB > 50;
      setIsLargeFile(isLarge);

      if (fileSizeMB > 100) {
        message.warning(`超大文件 (${fileSizeMB.toFixed(2)} MB)，将使用分块上传和流式处理，预计处理时间较长`);
      } else if (isLarge) {
        message.info(`大文件 (${fileSizeMB.toFixed(2)} MB)，将使用优化的直接上传模式`);
      } else if (fileSizeMB > 10) {
        message.info(`中型文件 (${fileSizeMB.toFixed(2)} MB)，将使用流式处理模式`);
      } else {
        message.success(`小文件 (${fileSizeMB.toFixed(2)} MB)，将使用标准处理模式`);
      }

      setSelectedFile(actualFile);
      setPreviewData(null);
      setImportProgress(null);
      setTaskId(null);
      setImporting(false);
      setCurrentStep(1);

      message.success(`已选择文件: ${actualFile.name} (${fileSizeMB.toFixed(2)} MB)`);
    }
  };

  // 预览文件
  const handlePreview = async () => {
    if (!selectedFile) {
      message.error('请先选择文件');
      return;
    }

    setPreviewing(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('preview_lines', '2000');

    try {
      // 模拟上传进度
      const progressTimer = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressTimer);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const response = await adminApiClient.post('/api/v1/historical-txt-import/preview', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      clearInterval(progressTimer);
      setUploadProgress(100);

      setTimeout(() => {
        setPreviewData(response.data.preview);
        setCurrentStep(2);
        setPreviewing(false);
        setUploadProgress(0);
        message.success('文件预览完成');
      }, 500);

    } catch (error: any) {
      setPreviewing(false);
      setUploadProgress(0);
      message.error(error.response?.data?.detail || '预览失败');
    }
  };

  // 大文件直接上传处理
  const handleLargeFileUpload = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      setImporting(true);
      setCurrentStep(3);
      setUploadProgress(0);

      message.info('开始上传大文件，请耐心等待...');

      const response = await adminApiClient.post('/api/v1/large-file-upload/direct-large-upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(percent);
          }
        }
      });

      if (response.data.success) {
        setTaskId(response.data.upload_id);
        message.success('大文件上传完成，开始后台处理...');
        startProgressMonitoring(response.data.upload_id, '/api/v1/large-file-upload/progress/');
      }
    } catch (error: any) {
      setImporting(false);
      setUploadProgress(0);
      message.error(error.response?.data?.detail || '大文件上传失败');
    }
  };

  // 开始导入
  const handleStartImport = async () => {
    if (!selectedFile) {
      message.error('请先选择文件');
      return;
    }

    // 大文件使用专门的上传方式
    if (isLargeFile) {
      return handleLargeFileUpload();
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      setImporting(true);
      setCurrentStep(3);
      setUploadProgress(0);

      // 判断文件大小，选择同步或异步导入
      const fileSizeMB = selectedFile.size / 1024 / 1024;
      const isAsyncFile = fileSizeMB > 10; // 大于10MB使用异步导入

      let response;
      if (isAsyncFile) {
        // 异步导入 - 显示上传进度
        message.info('大文件检测，启动异步处理模式...');

        // 模拟上传进度
        const uploadTimer = setInterval(() => {
          setUploadProgress(prev => {
            if (prev >= 90) {
              clearInterval(uploadTimer);
              return 90;
            }
            return prev + 5;
          });
        }, 300);

        response = await adminApiClient.post('/api/v1/historical-txt-import/import-async', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        clearInterval(uploadTimer);
        setUploadProgress(100);

        if (response.data.success) {
          setTaskId(response.data.task_id);
          setTimeout(() => {
            setUploadProgress(0);
            message.success('文件上传完成，开始后台处理...');
            startProgressMonitoring(response.data.task_id);
          }, 500);
        }
      } else {
        // 同步导入 - 显示处理进度
        message.info('开始处理数据，请稍候...');

        // 模拟处理进度
        const processTimer = setInterval(() => {
          setUploadProgress(prev => {
            if (prev >= 80) {
              return prev;
            }
            return prev + 10;
          });
        }, 500);

        response = await adminApiClient.post('/api/v1/historical-txt-import/import-sync', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        clearInterval(processTimer);
        setUploadProgress(100);

        if (response.data.success) {
          setTimeout(() => {
            setImportProgress({
              status: 'completed',
              current: response.data.success_dates || 0,
              total: response.data.total_dates || 0,
              current_date: '',
              completed_dates: Object.keys(response.data.date_results || {}),
              failed_dates: response.data.failed_dates_detail?.map((f: any) => f.date) || [],
              start_time: new Date().toISOString(),
              filename: selectedFile.name,
              result: response.data
            });
            setCurrentStep(4);
            setImporting(false);
            setUploadProgress(0);
            message.success('数据导入完成！');
          }, 1000);
        }
      }
    } catch (error: any) {
      setImporting(false);
      setUploadProgress(0);
      message.error(error.response?.data?.detail || '导入失败');
    }
  };

  // 开始进度监控
  const startProgressMonitoring = (taskId: string, progressUrl?: string) => {
    const url = progressUrl ? `${progressUrl}${taskId}` : `/api/v1/historical-txt-import/progress/${taskId}`;

    progressInterval.current = setInterval(async () => {
      try {
        const response = await adminApiClient.get(url);
        const progress = response.data.progress;

        // 转换大文件上传的进度格式到统一格式
        if (progress.import_stage) {
          const normalizedProgress = {
            status: progress.status,
            current: progress.import_progress || 0,
            total: 100,
            current_date: progress.import_message || '',
            completed_dates: [],
            failed_dates: [],
            start_time: progress.start_time,
            end_time: progress.end_time,
            filename: progress.filename,
            result: progress.import_result,
            error: progress.error
          };
          setImportProgress(normalizedProgress);
        } else {
          setImportProgress(progress);
        }

        if (progress.status === 'completed' || progress.status === 'failed') {
          if (progressInterval.current) {
            clearInterval(progressInterval.current);
          }
          setImporting(false);
          setCurrentStep(4);

          if (progress.status === 'completed') {
            message.success('历史数据导入完成！');
          } else {
            message.error('导入过程中发生错误');
          }
        }
      } catch (error) {
        console.error('获取进度失败:', error);
      }
    }, 2000); // 每2秒检查一次
  };

  // 重置状态
  const handleReset = () => {
    setCurrentStep(0);
    setSelectedFile(null);
    setPreviewData(null);
    setImportProgress(null);
    setTaskId(null);
    setImporting(false);
    setPreviewing(false);
    setUploadProgress(0);
    if (progressInterval.current) {
      clearInterval(progressInterval.current);
    }
  };

  // 预览数据表格列
  const previewColumns = [
    {
      title: '交易日期',
      dataIndex: 'date',
      key: 'date',
      render: (date: string) => <Text strong>{date}</Text>
    },
    {
      title: '记录数量',
      dataIndex: 'count',
      key: 'count',
      render: (count: number) => <Tag color="blue">{count.toLocaleString()}</Tag>
    },
    {
      title: '示例数据',
      dataIndex: 'sample_lines',
      key: 'sample_lines',
      render: (lines: string[]) => (
        <div>
          {lines.slice(0, 2).map((line, idx) => (
            <div key={idx} style={{ fontSize: '12px', color: '#666' }}>
              {line.substring(0, 50)}...
            </div>
          ))}
        </div>
      )
    }
  ];

  // 预览数据源
  const previewDataSource = previewData ? Object.entries(previewData.date_preview)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, data]) => ({
      key: date,
      date,
      count: data.count,
      sample_lines: data.sample_lines
    })) : [];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: '24px' }}>
          <Title level={3}>
            <HistoryOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
            历史数据批量导入
          </Title>
          <Paragraph type="secondary">
            支持导入包含多个交易日期的大型TXT文件，系统将自动按日期分割并逐日导入数据。
          </Paragraph>
        </div>

        {/* 步骤指示器 */}
        <Steps current={currentStep} style={{ marginBottom: '32px' }}>
          <Step title="选择文件" icon={<FileTextOutlined />} />
          <Step title="预览数据" icon={<EyeOutlined />} />
          <Step title="确认导入" icon={<PlayCircleOutlined />} />
          <Step title="导入进度" icon={<ClockCircleOutlined />} />
          <Step title="完成" icon={<CheckCircleOutlined />} />
        </Steps>

        {/* 第一步：文件选择 */}
        {currentStep === 0 && (
          <Card>
            <div style={{ textAlign: 'center', padding: '48px 24px' }}>
              <Upload.Dragger
                accept=".txt"
                multiple={false}
                beforeUpload={() => false}
                onChange={handleFileSelect}
                showUploadList={false}
                style={{ marginBottom: '24px' }}
                maxCount={1}
              >
                <p className="ant-upload-drag-icon">
                  <CloudUploadOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
                </p>
                <p className="ant-upload-text" style={{ fontSize: '18px' }}>
                  点击或拖拽文件到此区域上传
                </p>
                <p className="ant-upload-hint" style={{ fontSize: '14px' }}>
                  支持包含多个交易日期的大型TXT文件<br />
                  格式：股票代码 ⇥ 日期 ⇥ 交易量
                </p>
              </Upload.Dragger>

              {selectedFile && (
                <div>
                  <Alert
                    message="文件选择成功"
                    description={
                      <div>
                        <p><strong>文件名:</strong> {selectedFile.name}</p>
                        <p><strong>文件大小:</strong> {(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                    }
                    type="success"
                    showIcon
                    style={{ marginBottom: '16px', textAlign: 'left' }}
                  />
                  <div>
                    <Button
                      type="primary"
                      size="large"
                      onClick={handlePreview}
                      loading={previewing}
                      disabled={previewing}
                    >
                      {previewing ? '正在预览...' : '预览文件内容'}
                    </Button>

                    {previewing && (
                      <div style={{ marginTop: '16px' }}>
                        <Text type="secondary">正在上传和解析文件...</Text>
                        <Progress
                          percent={uploadProgress}
                          status="active"
                          style={{ marginTop: '8px' }}
                          strokeColor={{
                            '0%': '#108ee9',
                            '100%': '#87d068',
                          }}
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </Card>
        )}

        {/* 第二步：数据预览 */}
        {currentStep >= 1 && previewData && (
          <Card title="数据预览" style={{ marginBottom: '16px' }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {/* 文件概览 */}
              <Card size="small" title="文件概览">
                <Descriptions column={4} size="small">
                  <Descriptions.Item label="总行数">
                    <Statistic value={previewData.total_lines} />
                  </Descriptions.Item>
                  <Descriptions.Item label="预览行数">
                    <Statistic value={previewData.preview_lines} />
                  </Descriptions.Item>
                  <Descriptions.Item label="发现日期数">
                    <Statistic value={previewData.estimated_dates} />
                  </Descriptions.Item>
                  <Descriptions.Item label="预估总日期数">
                    <Statistic value={previewData.estimated_total_dates || previewData.estimated_dates} />
                  </Descriptions.Item>
                </Descriptions>
              </Card>

              {/* 日期分布 */}
              <Card size="small" title="日期分布预览">
                <Table
                  columns={previewColumns}
                  dataSource={previewDataSource}
                  size="small"
                  pagination={{ pageSize: 10 }}
                  scroll={{ y: 300 }}
                />
              </Card>

              {currentStep === 2 && (
                <div style={{ textAlign: 'center', marginTop: '16px' }}>
                  <Space>
                    <Button onClick={handleReset} disabled={importing}>重新选择</Button>
                    <Button
                      type="primary"
                      onClick={handleStartImport}
                      loading={importing}
                      disabled={importing}
                      icon={<PlayCircleOutlined />}
                    >
                      {importing ? '正在导入...' : '开始导入'}
                    </Button>
                  </Space>

                  {importing && (
                    <div style={{ marginTop: '16px' }}>
                      <Text type="secondary">
                        {uploadProgress < 100 ? '正在上传文件...' : '正在处理数据...'}
                      </Text>
                      <Progress
                        percent={uploadProgress}
                        status="active"
                        style={{ marginTop: '8px' }}
                        strokeColor={{
                          '0%': '#fa8c16',
                          '100%': '#52c41a',
                        }}
                      />
                    </div>
                  )}
                </div>
              )}
            </Space>
          </Card>
        )}

        {/* 第三步：上传进度或导入进度 */}
        {currentStep >= 3 && (importing || importProgress) && (
          <Card title="导入进度">
            <Space direction="vertical" style={{ width: '100%' }}>
              {/* 上传/处理进度 */}
              {importing && !importProgress && (
                <div>
                  <div style={{ marginBottom: '8px' }}>
                    <Text strong>
                      {uploadProgress < 100 ? '上传进度' : '处理进度'}
                    </Text>
                    <Text type="secondary" style={{ marginLeft: '16px' }}>
                      {uploadProgress < 100 ? '正在上传文件到服务器...' : '服务器正在解析文件...'}
                    </Text>
                  </div>
                  <Progress
                    percent={uploadProgress}
                    status="active"
                    strokeColor={{
                      '0%': '#fa8c16',
                      '100%': '#52c41a',
                    }}
                  />
                </div>
              )}

              {/* 整体进度 */}
              {importProgress && (
                <div>
                  <div style={{ marginBottom: '8px' }}>
                    <Text strong>整体进度: </Text>
                    <Text>{importProgress.current} / {importProgress.total}</Text>
                    {importProgress.current_date && (
                      <Text type="secondary" style={{ marginLeft: '16px' }}>
                        当前处理: {importProgress.current_date}
                      </Text>
                    )}
                  </div>
                  <Progress
                    percent={importProgress.total > 0 ? Math.round((importProgress.current / importProgress.total) * 100) : 0}
                    status={importProgress.status === 'failed' ? 'exception' :
                            importProgress.status === 'completed' ? 'success' : 'active'}
                  />
                </div>
              )}

              {/* 状态信息 */}
              <Descriptions column={3} size="small">
                <Descriptions.Item label="状态">
                  <Tag color={
                    importProgress.status === 'completed' ? 'green' :
                    importProgress.status === 'failed' ? 'red' : 'blue'
                  }>
                    {importProgress.status === 'completed' ? '已完成' :
                     importProgress.status === 'failed' ? '失败' : '进行中'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="开始时间">
                  {new Date(importProgress.start_time).toLocaleString()}
                </Descriptions.Item>
                <Descriptions.Item label="文件名">
                  {importProgress.filename}
                </Descriptions.Item>
              </Descriptions>

              {/* 详细进度 */}
              <Collapse>
                <Panel header="详细进度信息" key="details">
                  <Descriptions column={2} size="small">
                    <Descriptions.Item label="成功日期">
                      <Tag color="green">{importProgress.completed_dates.length}</Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="失败日期">
                      <Tag color="red">{importProgress.failed_dates.length}</Tag>
                    </Descriptions.Item>
                  </Descriptions>

                  {importProgress.completed_dates.length > 0 && (
                    <div style={{ marginTop: '16px' }}>
                      <Text strong>成功导入的日期:</Text>
                      <div style={{ marginTop: '8px' }}>
                        {importProgress.completed_dates.map(date => (
                          <Tag key={date} color="green" style={{ margin: '2px' }}>
                            {date}
                          </Tag>
                        ))}
                      </div>
                    </div>
                  )}

                  {importProgress.failed_dates.length > 0 && (
                    <div style={{ marginTop: '16px' }}>
                      <Text strong>失败的日期:</Text>
                      <div style={{ marginTop: '8px' }}>
                        {importProgress.failed_dates.map(date => (
                          <Tag key={date} color="red" style={{ margin: '2px' }}>
                            {date}
                          </Tag>
                        ))}
                      </div>
                    </div>
                  )}
                </Panel>
              </Collapse>

              {/* 最终结果 */}
              {importProgress.status === 'completed' && importProgress.result && (
                <Alert
                  message="导入完成"
                  description={
                    <div>
                      <p>总日期数: {importProgress.result.total_dates}</p>
                      <p>成功: {importProgress.result.success_dates} 失败: {importProgress.result.failed_dates}</p>
                      <p>总记录数: {importProgress.result.total_records}</p>
                      <p>耗时: {importProgress.result.total_time} 秒</p>
                    </div>
                  }
                  type="success"
                  showIcon
                />
              )}

              {importProgress.status === 'failed' && (
                <Alert
                  message="导入失败"
                  description={importProgress.error}
                  type="error"
                  showIcon
                />
              )}

              {/* 操作按钮 */}
              {(importProgress.status === 'completed' || importProgress.status === 'failed') && (
                <div style={{ textAlign: 'center', marginTop: '16px' }}>
                  <Button type="primary" onClick={handleReset}>
                    导入新文件
                  </Button>
                </div>
              )}
            </Space>
          </Card>
        )}

        {/* 使用说明 */}
        <Card title="使用说明" style={{ marginTop: '24px' }}>
          <Collapse>
            <Panel header="文件格式要求" key="format">
              <div>
                <p><strong>文件格式:</strong> TXT文本文件，使用TAB制表符分隔</p>
                <p><strong>列格式:</strong> 股票代码 ⇥ 交易日期 ⇥ 交易量</p>
                <p><strong>示例:</strong></p>
                <pre style={{ background: '#f5f5f5', padding: '8px', fontSize: '12px' }}>
{`SH600000	2024-01-15	1000000
SZ000001	2024-01-15	2000000
SH600036	2024-01-16	1500000`}
                </pre>
              </div>
            </Panel>
            <Panel header="支持的股票代码格式" key="codes">
              <ul>
                <li>SH前缀: SH600000 (上海A股)</li>
                <li>SZ前缀: SZ000001 (深圳A股)</li>
                <li>BJ前缀: BJ001001 (北京A股)</li>
                <li>纯数字: 600000 (自动判断市场)</li>
              </ul>
            </Panel>
            <Panel header="处理策略" key="strategy">
              <ul>
                <li><strong>数据分组:</strong> 系统将自动按交易日期分组数据</li>
                <li><strong>顺序导入:</strong> 按时间顺序逐日导入，确保数据一致性</li>
                <li><strong>概念计算:</strong> 每个日期的数据导入完成后立即进行概念计算</li>
                <li><strong>容错处理:</strong> 如果某个日期导入失败，不影响其他日期的处理</li>
                <li><strong>小文件(&lt;10MB):</strong> 使用标准同步处理，快速完成</li>
                <li><strong>中型文件(10-50MB):</strong> 使用异步处理，实时显示进度</li>
                <li><strong>大文件(50-100MB):</strong> 使用直接上传+流式处理，内存优化</li>
                <li><strong>超大文件(&gt;100MB):</strong> 使用分块上传+流式处理，确保稳定性</li>
              </ul>
            </Panel>
          </Collapse>
        </Card>
      </Card>
    </div>
  );
};

export default HistoricalDataImport;