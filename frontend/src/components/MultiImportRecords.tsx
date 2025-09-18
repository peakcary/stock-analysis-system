import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Tag, Typography, message, Modal, Alert, Tooltip,
  Popconfirm, Row, Col
} from 'antd';
import {
  DeleteOutlined, EyeOutlined, FileTextOutlined, CheckCircleOutlined,
  CloseCircleOutlined, ClockCircleOutlined
} from '@ant-design/icons';
import { adminApiClient } from '../../../shared/admin-auth';
import dayjs from 'dayjs';

const { Text } = Typography;

interface MultiImportRecordsProps {
  importType: string;
  typeName: string;
  refreshTrigger?: number;
}

const MultiImportRecords: React.FC<MultiImportRecordsProps> = ({
  importType,
  typeName,
  refreshTrigger = 0
}) => {
  const [records, setRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  });

  // 详情模态框
  const [detailsModal, setDetailsModal] = useState({
    visible: false,
    record: null as any,
    details: null as any
  });

  // 获取导入记录
  const fetchRecords = async (page: number = 1, size: number = 20) => {
    try {
      setLoading(true);
      const params: any = {
        import_type: importType,
        page,
        size
      };

      const response = await adminApiClient.get('/api/v1/typed-import/records', { params });

      if (response.data?.records) {
        setRecords(response.data.records);
        setPagination({
          current: response.data.pagination?.page || page,
          pageSize: response.data.pagination?.size || size,
          total: response.data.pagination?.total || 0
        });
      } else {
        setRecords([]);
        setPagination(prev => ({ ...prev, total: 0 }));
      }
    } catch (error) {
      console.error('获取导入记录失败:', error);
      message.error('获取导入记录失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取处理详情
  const fetchProcessingDetails = async (recordId: number) => {
    try {
      const response = await adminApiClient.get(`/api/v1/typed-import/processing-details/${recordId}`);
      return response.data;
    } catch (error) {
      console.error('获取处理详情失败:', error);
      message.error('获取处理详情失败');
      return null;
    }
  };

  // 删除记录
  const deleteRecord = async (recordId: number) => {
    try {
      await adminApiClient.delete(`/api/v1/typed-import/records/${recordId}`);
      message.success('删除成功');
      fetchRecords(pagination.current, pagination.pageSize);
    } catch (error) {
      console.error('删除记录失败:', error);
      message.error('删除记录失败');
    }
  };


  // 显示详情
  const showDetails = async (record: any) => {
    const details = await fetchProcessingDetails(record.id);
    setDetailsModal({
      visible: true,
      record,
      details
    });
  };

  // 列定义 - 与TxtImportRecords保持一致
  const columns = [
    {
      title: '交易日期',
      dataIndex: 'trading_date',
      key: 'trading_date',
      width: 120,
      render: (date: string) => (
        <Tag color="blue" icon={<FileTextOutlined />}>
          {date}
        </Tag>
      )
    },
    {
      title: '状态',
      dataIndex: 'import_status',
      key: 'import_status',
      width: 100,
      render: (status: string) => {
        const statusMap = {
          success: { color: 'success', icon: <CheckCircleOutlined />, text: '成功' },
          failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
          processing: { color: 'processing', icon: <ClockCircleOutlined />, text: '处理中' }
        };

        const config = statusMap[status as keyof typeof statusMap] || statusMap.processing;

        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        );
      }
    },
    {
      title: '文件大小',
      dataIndex: 'file_size_mb',
      key: 'file_size_mb',
      width: 100,
      render: (sizeMb: number) => `${sizeMb?.toFixed(1) || 0} MB`
    },
    {
      title: '导入记录',
      key: 'records',
      width: 120,
      render: (record: any) => (
        <div>
          <div style={{ fontSize: '12px', color: '#52c41a' }}>
            ✓ 成功: {record.success_records || 0}
          </div>
          {(record.error_records || 0) > 0 && (
            <div style={{ fontSize: '12px', color: '#ff4d4f' }}>
              ✗ 失败: {record.error_records}
            </div>
          )}
          <div style={{ fontSize: '12px', color: '#666' }}>
            总计: {record.total_records || 0}
          </div>
        </div>
      )
    },
    {
      title: '计算汇总结果',
      key: 'calculation',
      width: 150,
      render: (record: any) => (
        <div style={{ fontSize: '12px' }}>
          <div style={{ color: '#722ed1' }}>
            概念汇总: <Text strong>{record.concept_count || 0}</Text>
          </div>
          <div style={{ color: '#fa541c' }}>
            排名记录: <Text strong>{record.ranking_count || 0}</Text>
          </div>
          <div style={{ color: '#52c41a' }}>
            创新高: <Text strong>{record.new_high_count || 0}</Text>
          </div>
        </div>
      )
    },
    {
      title: '导入信息',
      key: 'import_info',
      width: 180,
      render: (record: any) => (
        <div style={{ fontSize: '12px' }}>
          <div>导入人: <Text strong>{record.imported_by}</Text></div>
          <div>开始时间: {record.import_started_at}</div>
          {record.import_completed_at && (
            <div>完成时间: {record.import_completed_at}</div>
          )}
          {record.calculation_time && (
            <div style={{ color: '#1890ff' }}>
              计算用时: <Text strong>{record.calculation_time}s</Text>
            </div>
          )}
        </div>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      fixed: 'right' as const,
      render: (record: any) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => showDetails(record)}
              size="small"
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这条记录吗？"
            onConfirm={() => deleteRecord(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除记录">
              <Button
                type="text"
                icon={<DeleteOutlined />}
                danger
                size="small"
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  // 初始化和刷新
  useEffect(() => {
    fetchRecords();
  }, [importType, refreshTrigger]);


  return (
    <div>
      {/* 数据表格 */}
      <Card title={`${typeName}导入记录`}>
        <Table
          columns={columns}
          dataSource={records}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 条记录`,
            onChange: (page, size) => {
              setPagination({ current: page, pageSize: size || 20, total: pagination.total });
              fetchRecords(page, size || 20);
            }
          }}
          scroll={{ x: 'max-content' }}
          size="middle"
        />
      </Card>

      {/* 详情模态框 */}
      <Modal
        title={`导入详情 - ${detailsModal.record?.filename}`}
        open={detailsModal.visible}
        onCancel={() => setDetailsModal({ visible: false, record: null, details: null })}
        footer={null}
        width={800}
      >
        {detailsModal.details && (
          <div>
            <Alert
              message={`${typeName}导入详情`}
              description={
                <div style={{ marginTop: '12px' }}>
                  <Row gutter={[16, 8]}>
                    <Col span={12}>
                      <Text strong>导入类型:</Text> {detailsModal.details.import_type}
                    </Col>
                    <Col span={12}>
                      <Text strong>文件名:</Text> {detailsModal.details.filename}
                    </Col>
                    <Col span={12}>
                      <Text strong>记录ID:</Text> {detailsModal.details.record_id}
                    </Col>
                  </Row>
                </div>
              }
              type="info"
              style={{ marginBottom: '16px' }}
            />

            {detailsModal.details.metadata && (
              <Card title="元数据信息" size="small" style={{ marginBottom: '16px' }}>
                <pre style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
                  {JSON.stringify(detailsModal.details.metadata, null, 2)}
                </pre>
              </Card>
            )}

            {detailsModal.details.processing_details && (
              <Card title="处理详情" size="small">
                <pre style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
                  {JSON.stringify(detailsModal.details.processing_details, null, 2)}
                </pre>
              </Card>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default MultiImportRecords;