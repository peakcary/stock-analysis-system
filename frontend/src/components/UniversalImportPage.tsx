import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Upload,
  Select,
  DatePicker,
  Form,
  Table,
  Tag,
  Progress,
  Alert,
  Modal,
  Tabs,
  Statistic,
  Space,
  Typography,
  Tooltip,
  message,
  Badge,
  Divider
} from 'antd';
import {
  CloudUploadOutlined,
  ReloadOutlined,
  BarChartOutlined,
  HistoryOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import dayjs from 'dayjs';
import axios from 'axios';
import { adminApiClient } from '../../../shared/admin-auth';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;

interface SupportedFileType {
  display_name: string;
  description: string;
  file_extensions: string[];
  max_file_size: number;
}

interface ImportRecord {
  id: number;
  filename: string;
  file_type: string;
  trading_date: string;
  import_status: 'success' | 'failed' | 'processing';
  success_records: number;
  failed_records: number;
  file_size: number;
  calculation_time?: number;
  imported_by: string;
  imported_at: string;
  error_message?: string;
}

interface FileTypeStatistics {
  total_imports: number;
  successful_imports: number;
  failed_imports: number;
  success_rate: number;
  total_records_imported: number;
  total_file_size_mb: number;
  avg_calculation_time: number;
}

const UniversalImportPage: React.FC = () => {
  const [supportedTypes, setSupportedTypes] = useState<Record<string, SupportedFileType>>({});
  const [selectedFileType, setSelectedFileType] = useState<string>('');
  const [selectedDate, setSelectedDate] = useState<dayjs.Dayjs>(dayjs());
  const [importMode, setImportMode] = useState<'overwrite' | 'append'>('overwrite');
  const [uploading, setUploading] = useState(false);
  const [importRecords, setImportRecords] = useState<ImportRecord[]>([]);
  const [recordsLoading, setRecordsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('import');
  const [statistics, setStatistics] = useState<Record<string, FileTypeStatistics>>({});
  const [statisticsLoading, setStatisticsLoading] = useState(false);

  // 获取支持的文件类型
  const fetchSupportedTypes = async () => {
    try {
      const response = await adminApiClient.get('/api/v1/universal-import/supported-types');
      if (response.data.success) {
        setSupportedTypes(response.data.type_configs);
        // 自动选择第一个支持的文件类型
        const types = Object.keys(response.data.type_configs);
        if (types.length > 0 && !selectedFileType) {
          setSelectedFileType(types[0]);
        }
      }
    } catch (error) {
      console.error('获取支持的文件类型失败:', error);
      message.error('获取支持的文件类型失败');
    }
  };

  // 获取导入记录
  const fetchImportRecords = async (fileType: string) => {
    if (!fileType) return;

    setRecordsLoading(true);
    try {
      const response = await adminApiClient.get(`/api/v1/universal-import/${fileType}/records?limit=50`);
      if (response.data.success) {
        setImportRecords(response.data.records);
      }
    } catch (error) {
      console.error('获取导入记录失败:', error);
      message.error('获取导入记录失败');
    } finally {
      setRecordsLoading(false);
    }
  };

  // 获取统计信息
  const fetchStatistics = async (fileType: string) => {
    if (!fileType) return;

    setStatisticsLoading(true);
    try {
      const response = await adminApiClient.get(`/api/v1/universal-import/${fileType}/statistics?days=30`);
      if (response.data.success) {
        setStatistics(prev => ({
          ...prev,
          [fileType]: response.data.statistics
        }));
      }
    } catch (error) {
      console.error('获取统计信息失败:', error);
    } finally {
      setStatisticsLoading(false);
    }
  };

  useEffect(() => {
    fetchSupportedTypes();
  }, []);

  useEffect(() => {
    if (selectedFileType) {
      fetchImportRecords(selectedFileType);
      fetchStatistics(selectedFileType);
    }
  }, [selectedFileType]);

  // 文件上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    action: `/api/v1/universal-import/import`,
    data: {
      file_type: selectedFileType,
      trading_date: selectedDate.format('YYYY-MM-DD'),
      mode: importMode
    },
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
    },
    beforeUpload: (file) => {
      if (!selectedFileType) {
        message.error('请先选择文件类型');
        return false;
      }

      const config = supportedTypes[selectedFileType];
      if (config) {
        const fileExtension = `.${file.name.split('.').pop()?.toLowerCase()}`;
        if (!config.file_extensions.includes(fileExtension)) {
          message.error(`不支持的文件类型，支持的扩展名: ${config.file_extensions.join(', ')}`);
          return false;
        }

        if (file.size > config.max_file_size) {
          message.error(`文件大小超过限制: ${(config.max_file_size / 1024 / 1024).toFixed(1)}MB`);
          return false;
        }
      }

      setUploading(true);
      return true;
    },
    onChange: (info) => {
      if (info.file.status === 'done') {
        setUploading(false);
        if (info.file.response?.success) {
          message.success('文件导入成功');
          fetchImportRecords(selectedFileType);
          fetchStatistics(selectedFileType);
        } else {
          message.error(info.file.response?.error || '文件导入失败');
        }
      } else if (info.file.status === 'error') {
        setUploading(false);
        message.error('文件上传失败');
      }
    },
    showUploadList: false
  };

  // 表格列定义
  const columns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      width: 200,
      ellipsis: true
    },
    {
      title: '交易日期',
      dataIndex: 'trading_date',
      key: 'trading_date',
      width: 120
    },
    {
      title: '状态',
      dataIndex: 'import_status',
      key: 'import_status',
      width: 100,
      render: (status: string) => {
        const colorMap = {
          success: 'green',
          failed: 'red',
          processing: 'blue'
        };
        const textMap = {
          success: '成功',
          failed: '失败',
          processing: '处理中'
        };
        return <Tag color={colorMap[status as keyof typeof colorMap]}>{textMap[status as keyof typeof textMap]}</Tag>;
      }
    },
    {
      title: '成功记录数',
      dataIndex: 'success_records',
      key: 'success_records',
      width: 100
    },
    {
      title: '失败记录数',
      dataIndex: 'failed_records',
      key: 'failed_records',
      width: 100
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size: number) => `${(size / 1024).toFixed(1)}KB`
    },
    {
      title: '计算时间',
      dataIndex: 'calculation_time',
      key: 'calculation_time',
      width: 100,
      render: (time: number) => time ? `${time.toFixed(2)}s` : '-'
    },
    {
      title: '导入时间',
      dataIndex: 'imported_at',
      key: 'imported_at',
      width: 160,
      render: (time: string) => dayjs(time).format('MM-DD HH:mm:ss')
    }
  ];

  const currentStats = selectedFileType ? statistics[selectedFileType] : null;

  return (
    <div style={{ padding: '20px' }}>
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane
            tab={
              <span>
                <CloudUploadOutlined />
                文件导入
              </span>
            }
            key="import"
          >
            <Row gutter={[16, 16]}>
              {/* 导入配置 */}
              <Col span={24}>
                <Card size="small" title="导入配置">
                  <Form layout="inline">
                    <Form.Item label="文件类型">
                      <Select
                        style={{ width: 160 }}
                        value={selectedFileType}
                        onChange={setSelectedFileType}
                        placeholder="选择文件类型"
                      >
                        {Object.entries(supportedTypes).map(([type, config]) => (
                          <Option key={type} value={type}>
                            {config.display_name}
                          </Option>
                        ))}
                      </Select>
                    </Form.Item>

                    <Form.Item label="交易日期">
                      <DatePicker
                        value={selectedDate}
                        onChange={(date) => date && setSelectedDate(date)}
                        format="YYYY-MM-DD"
                      />
                    </Form.Item>

                    <Form.Item label="导入模式">
                      <Select
                        style={{ width: 120 }}
                        value={importMode}
                        onChange={setImportMode}
                      >
                        <Option value="overwrite">覆盖</Option>
                        <Option value="append">追加</Option>
                      </Select>
                    </Form.Item>
                  </Form>
                </Card>
              </Col>

              {/* 文件上传 */}
              <Col span={24}>
                <Card size="small" title="文件上传">
                  <Upload.Dragger {...uploadProps} disabled={!selectedFileType || uploading}>
                    <p className="ant-upload-drag-icon">
                      <CloudUploadOutlined style={{ fontSize: 48, color: uploading ? '#ccc' : '#1890ff' }} />
                    </p>
                    <p className="ant-upload-text">
                      {uploading ? '正在上传...' : '点击或拖拽文件到此区域上传'}
                    </p>
                    {selectedFileType && supportedTypes[selectedFileType] && (
                      <p className="ant-upload-hint">
                        支持扩展名: {supportedTypes[selectedFileType].file_extensions.join(', ')} |
                        最大文件大小: {(supportedTypes[selectedFileType].max_file_size / 1024 / 1024).toFixed(1)}MB
                      </p>
                    )}
                  </Upload.Dragger>
                </Card>
              </Col>

              {/* 统计信息 */}
              {currentStats && (
                <Col span={24}>
                  <Card size="small" title="统计信息 (最近30天)" loading={statisticsLoading}>
                    <Row gutter={16}>
                      <Col span={6}>
                        <Statistic title="总导入次数" value={currentStats.total_imports} />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="成功率"
                          value={currentStats.success_rate}
                          suffix="%"
                          precision={1}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic title="总记录数" value={currentStats.total_records_imported} />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="平均处理时间"
                          value={currentStats.avg_calculation_time}
                          suffix="s"
                          precision={2}
                        />
                      </Col>
                    </Row>
                  </Card>
                </Col>
              )}
            </Row>
          </TabPane>

          <TabPane
            tab={
              <span>
                <HistoryOutlined />
                导入记录
                {importRecords.length > 0 && (
                  <Badge count={importRecords.length} style={{ marginLeft: 8 }} />
                )}
              </span>
            }
            key="records"
          >
            <Card
              size="small"
              title={`${selectedFileType ? supportedTypes[selectedFileType]?.display_name : ''} 导入记录`}
              extra={
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => fetchImportRecords(selectedFileType)}
                  size="small"
                >
                  刷新
                </Button>
              }
            >
              <Table
                dataSource={importRecords}
                columns={columns}
                rowKey="id"
                loading={recordsLoading}
                size="small"
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `共 ${total} 条记录`
                }}
              />
            </Card>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default UniversalImportPage;