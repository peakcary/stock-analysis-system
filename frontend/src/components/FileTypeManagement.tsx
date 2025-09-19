import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Table,
  Tag,
  Modal,
  Form,
  Input,
  Switch,
  Space,
  Typography,
  Alert,
  Spin,
  Tabs,
  Badge,
  Statistic,
  Tooltip,
  message,
  Popconfirm,
  Divider
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  ReloadOutlined,
  HeartOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SettingOutlined
} from '@ant-design/icons';
import { adminApiClient } from '../../../shared/admin-auth';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { TextArea } = Input;

interface FileTypeConfig {
  file_type: string;
  display_name: string;
  description: string;
  enabled: boolean;
  file_extensions: string[];
  max_file_size: number;
  created_at?: string;
  updated_at?: string;
}

interface SystemSummary {
  total_registered_types: number;
  enabled_types: number;
  disabled_types: number;
  total_tables: number;
  total_models: number;
  health_issues: number;
}

interface HealthStatus {
  file_type: string;
  config_valid: boolean;
  tables_exist: boolean;
  models_generated: boolean;
  service_healthy: boolean;
  issues: string[];
}

const FileTypeManagement: React.FC = () => {
  const [fileTypes, setFileTypes] = useState<FileTypeConfig[]>([]);
  const [systemSummary, setSystemSummary] = useState<SystemSummary | null>(null);
  const [healthStatuses, setHealthStatuses] = useState<Record<string, HealthStatus>>({});
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingType, setEditingType] = useState<FileTypeConfig | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [form] = Form.useForm();

  // 获取系统概览
  const fetchSystemSummary = async () => {
    try {
      const response = await adminApiClient.get('/api/v1/file-types/system/summary');
      if (response.data.success) {
        setSystemSummary(response.data.summary);
      }
    } catch (error) {
      console.error('获取系统概览失败:', error);
      message.error('获取系统概览失败');
    }
  };

  // 获取文件类型列表
  const fetchFileTypes = async () => {
    setLoading(true);
    try {
      const response = await adminApiClient.get('/api/v1/file-types');
      if (response.data.success) {
        setFileTypes(response.data.file_types);
      }
    } catch (error) {
      console.error('获取文件类型列表失败:', error);
      message.error('获取文件类型列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取健康状态
  const fetchHealthStatuses = async () => {
    try {
      const response = await adminApiClient.get('/api/v1/file-types/health/all');
      if (response.data.success) {
        const healthMap: Record<string, HealthStatus> = {};
        response.data.health_statuses.forEach((status: HealthStatus) => {
          healthMap[status.file_type] = status;
        });
        setHealthStatuses(healthMap);
      }
    } catch (error) {
      console.error('获取健康状态失败:', error);
    }
  };

  useEffect(() => {
    fetchSystemSummary();
    fetchFileTypes();
    fetchHealthStatuses();
  }, []);

  // 打开新增/编辑对话框
  const openModal = (fileType?: FileTypeConfig) => {
    setEditingType(fileType || null);
    if (fileType) {
      form.setFieldsValue({
        ...fileType,
        file_extensions: fileType.file_extensions.join(', ')
      });
    } else {
      form.resetFields();
    }
    setModalVisible(true);
  };

  // 保存文件类型
  const saveFileType = async (values: any) => {
    try {
      const payload = {
        ...values,
        file_extensions: values.file_extensions.split(',').map((ext: string) => ext.trim()),
        max_file_size: parseInt(values.max_file_size)
      };

      if (editingType) {
        // 更新
        await adminApiClient.put(`/api/v1/file-types/${editingType.file_type}`, payload);
        message.success('文件类型更新成功');
      } else {
        // 新增
        await adminApiClient.post('/api/v1/file-types', payload);
        message.success('文件类型创建成功');
      }

      setModalVisible(false);
      fetchFileTypes();
      fetchSystemSummary();
      fetchHealthStatuses();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  // 删除文件类型
  const deleteFileType = async (fileType: string) => {
    try {
      await adminApiClient.delete(`/api/v1/file-types/${fileType}`);
      message.success('文件类型删除成功');
      fetchFileTypes();
      fetchSystemSummary();
      fetchHealthStatuses();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  // 切换启用状态
  const toggleEnabled = async (fileType: string, enabled: boolean) => {
    try {
      await adminApiClient.patch(`/api/v1/file-types/${fileType}/toggle`, { enabled });
      message.success(`文件类型已${enabled ? '启用' : '禁用'}`);
      fetchFileTypes();
      fetchSystemSummary();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  // 修复文件类型
  const repairFileType = async (fileType: string) => {
    try {
      await adminApiClient.post(`/api/v1/file-types/${fileType}/repair`);
      message.success('文件类型修复成功');
      fetchHealthStatuses();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '修复失败');
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '文件类型',
      dataIndex: 'file_type',
      key: 'file_type',
      width: 120,
      render: (type: string) => <Text code>{type}</Text>
    },
    {
      title: '显示名称',
      dataIndex: 'display_name',
      key: 'display_name',
      width: 150
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 80,
      render: (enabled: boolean) => (
        <Tag color={enabled ? 'green' : 'red'}>
          {enabled ? '启用' : '禁用'}
        </Tag>
      )
    },
    {
      title: '支持扩展名',
      dataIndex: 'file_extensions',
      key: 'file_extensions',
      width: 150,
      render: (extensions: string[]) => (
        <Space wrap>
          {extensions.map(ext => (
            <Tag key={ext} size="small">{ext}</Tag>
          ))}
        </Space>
      )
    },
    {
      title: '健康状态',
      key: 'health',
      width: 100,
      render: (_: any, record: FileTypeConfig) => {
        const health = healthStatuses[record.file_type];
        if (!health) return <Spin size="small" />;

        const isHealthy = health.config_valid && health.tables_exist &&
                         health.models_generated && health.service_healthy;

        return (
          <Tooltip title={isHealthy ? '健康' : `问题: ${health.issues.join(', ')}`}>
            {isHealthy ?
              <CheckCircleOutlined style={{ color: 'green' }} /> :
              <ExclamationCircleOutlined style={{ color: 'red' }} />
            }
          </Tooltip>
        );
      }
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_: any, record: FileTypeConfig) => (
        <Space>
          <Tooltip title="编辑">
            <Button
              icon={<EditOutlined />}
              size="small"
              onClick={() => openModal(record)}
            />
          </Tooltip>
          <Tooltip title={record.enabled ? '禁用' : '启用'}>
            <Button
              icon={record.enabled ? <CloseCircleOutlined /> : <CheckCircleOutlined />}
              size="small"
              onClick={() => toggleEnabled(record.file_type, !record.enabled)}
            />
          </Tooltip>
          {healthStatuses[record.file_type] && !healthStatuses[record.file_type].service_healthy && (
            <Tooltip title="修复">
              <Button
                icon={<SettingOutlined />}
                size="small"
                type="primary"
                onClick={() => repairFileType(record.file_type)}
              />
            </Tooltip>
          )}
          <Popconfirm
            title="确定要删除这个文件类型吗？"
            onConfirm={() => deleteFileType(record.file_type)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                icon={<DeleteOutlined />}
                size="small"
                danger
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '20px' }}>
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane
            tab={
              <span>
                <EyeOutlined />
                系统概览
              </span>
            }
            key="overview"
          >
            {systemSummary && (
              <Row gutter={[16, 16]}>
                <Col span={6}>
                  <Card size="small">
                    <Statistic title="已注册类型" value={systemSummary.total_registered_types} />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card size="small">
                    <Statistic
                      title="启用的类型"
                      value={systemSummary.enabled_types}
                      valueStyle={{ color: '#3f8600' }}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card size="small">
                    <Statistic title="数据表总数" value={systemSummary.total_tables} />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card size="small">
                    <Statistic
                      title="健康问题"
                      value={systemSummary.health_issues}
                      valueStyle={{ color: systemSummary.health_issues > 0 ? '#cf1322' : '#3f8600' }}
                    />
                  </Card>
                </Col>

                {systemSummary.health_issues > 0 && (
                  <Col span={24}>
                    <Alert
                      message="系统健康提醒"
                      description="检测到一些文件类型存在健康问题，请在文件类型管理中进行修复"
                      type="warning"
                      showIcon
                    />
                  </Col>
                )}
              </Row>
            )}
          </TabPane>

          <TabPane
            tab={
              <span>
                <SettingOutlined />
                文件类型管理
                {fileTypes.length > 0 && (
                  <Badge count={fileTypes.length} style={{ marginLeft: 8 }} />
                )}
              </span>
            }
            key="management"
          >
            <Card
              size="small"
              title="文件类型管理"
              extra={
                <Space>
                  <Button
                    icon={<ReloadOutlined />}
                    onClick={() => {
                      fetchFileTypes();
                      fetchHealthStatuses();
                      fetchSystemSummary();
                    }}
                    size="small"
                  >
                    刷新
                  </Button>
                  <Button
                    icon={<PlusOutlined />}
                    type="primary"
                    onClick={() => openModal()}
                    size="small"
                  >
                    新增文件类型
                  </Button>
                </Space>
              }
            >
              <Table
                dataSource={fileTypes}
                columns={columns}
                rowKey="file_type"
                loading={loading}
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

      {/* 新增/编辑对话框 */}
      <Modal
        title={editingType ? '编辑文件类型' : '新增文件类型'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={saveFileType}
        >
          <Form.Item
            name="file_type"
            label="文件类型标识"
            rules={[
              { required: true, message: '请输入文件类型标识' },
              { pattern: /^[a-zA-Z0-9_-]+$/, message: '只能包含字母、数字、下划线和横线' }
            ]}
          >
            <Input placeholder="例如: ttv, eee, aaa" disabled={!!editingType} />
          </Form.Item>

          <Form.Item
            name="display_name"
            label="显示名称"
            rules={[{ required: true, message: '请输入显示名称' }]}
          >
            <Input placeholder="例如: TTV文件导入" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea placeholder="文件类型的详细描述" rows={3} />
          </Form.Item>

          <Form.Item
            name="file_extensions"
            label="支持的文件扩展名"
            rules={[{ required: true, message: '请输入支持的文件扩展名' }]}
          >
            <Input placeholder="例如: .ttv, .txt (用逗号分隔)" />
          </Form.Item>

          <Form.Item
            name="max_file_size"
            label="最大文件大小(字节)"
            rules={[{ required: true, message: '请输入最大文件大小' }]}
          >
            <Input placeholder="例如: 104857600 (100MB)" type="number" />
          </Form.Item>

          <Form.Item
            name="enabled"
            label="启用状态"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default FileTypeManagement;