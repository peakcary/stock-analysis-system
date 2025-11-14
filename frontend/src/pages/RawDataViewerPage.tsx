import React, { useState, useEffect } from 'react';
import {
  Select,
  Table,
  Spin,
  message,
  Card,
  Row,
  Col,
  Button,
  Space,
  Pagination,
  Tag,
  Statistic,
  Empty,
  Tabs,
  Divider,
  Alert,
  Progress,
  DatePicker,
} from 'antd';
import { DownloadOutlined, ReloadOutlined, DatabaseOutlined, FileOutlined, ClearOutlined } from '@ant-design/icons';
import { adminApiClient } from '../../../shared/admin-auth';
import './RawDataViewerPage.css';
import dayjs from 'dayjs';

interface TableInfo {
  name: string;
  display_name: string;
  record_count: number;
  columns: ColumnInfo[];
}

interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
}

interface RawDataResponse {
  table_name: string;
  total_count: number;
  page: number;
  page_size: number;
  data: Record<string, any>[];
  columns: ColumnInfo[];
}

interface TableStats {
  table_name: string;
  total_count: number;
  first_record_date?: string;
  last_record_date?: string;
  distinct_stocks?: number;
}

interface TabConfig {
  key: string;
  tableName: string;
  displayName: string;
  icon: React.ReactNode;
  color: string;
  description: string;
}

const RawDataViewerPage: React.FC = () => {
  // Tab配置
  const tabConfigs: TabConfig[] = [
    {
      key: 'csv',
      tableName: 'stock_concept_raw_data',
      displayName: 'CSV数据',
      icon: <FileOutlined />,
      color: 'blue',
      description: '来自 CSV 文件的原始概念股数据',
    },
    {
      key: 'ttv',
      tableName: 'ttv_daily_trading',
      displayName: 'TTV数据',
      icon: <DatabaseOutlined />,
      color: 'green',
      description: 'TTV 格式的原始交易数据',
    },
    {
      key: 'eee',
      tableName: 'eee_daily_trading',
      displayName: 'EEE数据',
      icon: <DatabaseOutlined />,
      color: 'orange',
      description: 'EEE 格式的原始交易数据',
    },
  ];

  // 状态管理
  const [activeTab, setActiveTab] = useState<string>('csv');
  const [data, setData] = useState<Record<string, RawDataResponse | null>>({});
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState<Record<string, number>>({});
  const [pageSize, setPageSize] = useState<Record<string, number>>({});
  const [stats, setStats] = useState<Record<string, TableStats | null>>({});
  const [statsLoading, setStatsLoading] = useState(false);
  const [dateRange, setDateRange] = useState<Record<string, [any, any] | null>>({});

  // 初始化分页状态
  useEffect(() => {
    tabConfigs.forEach(config => {
      if (!page[config.key]) setPage(prev => ({ ...prev, [config.key]: 1 }));
      if (!pageSize[config.key]) setPageSize(prev => ({ ...prev, [config.key]: 20 }));
    });
  }, []);

  // 当tab变化时，获取数据
  useEffect(() => {
    const currentConfig = tabConfigs.find(c => c.key === activeTab);
    if (currentConfig) {
      fetchData(currentConfig.tableName, 1);
      fetchStats(currentConfig.tableName);
    }
  }, [activeTab]);

  // 当分页变化时，重新查询
  useEffect(() => {
    const currentConfig = tabConfigs.find(c => c.key === activeTab);
    if (currentConfig && page[activeTab]) {
      fetchData(currentConfig.tableName, page[activeTab]);
    }
  }, [page[activeTab], pageSize[activeTab]]);

  /**
   * 获取数据
   */
  const fetchData = async (tableName: string, pageNum: number) => {
    setLoading(true);
    try {
      const params: any = {
        page: pageNum,
        page_size: pageSize[activeTab] || 20,
        sort_by: null,
        sort_order: 'asc',
      };

      // 添加日期过滤参数（仅对TTV和EEE）
      if ((activeTab === 'ttv' || activeTab === 'eee') && dateRange[activeTab]) {
        const [startDate, endDate] = dateRange[activeTab];
        if (startDate) {
          params.start_date = startDate.format('YYYY-MM-DD');
        }
        if (endDate) {
          params.end_date = endDate.format('YYYY-MM-DD');
        }
      }

      const response = await adminApiClient.post(
        `/raw-data/${tableName}/query`,
        null,
        { params }
      );
      setData(prev => ({ ...prev, [activeTab]: response.data }));
    } catch (error: any) {
      message.error('查询数据失败: ' + (error.response?.data?.detail || error.message));
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 获取统计信息
   */
  const fetchStats = async (tableName: string) => {
    setStatsLoading(true);
    try {
      const response = await adminApiClient.get(`/raw-data/${tableName}/stats`);
      setStats(prev => ({ ...prev, [activeTab]: response.data }));
    } catch (error: any) {
      console.error('Error fetching stats:', error);
    } finally {
      setStatsLoading(false);
    }
  };

  /**
   * 导出为CSV
   */
  const exportToCSV = () => {
    const currentData = data[activeTab];
    if (!currentData || currentData.data.length === 0) {
      message.warning('没有数据可导出');
      return;
    }

    try {
      // 表头
      const headers = currentData.columns.map(col => col.name).join(',');

      // 数据行
      const rows = currentData.data.map(row =>
        currentData.columns
          .map(col => {
            const value = row[col.name];
            if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
              return `"${value.replace(/"/g, '""')}"`;
            }
            return value ?? '';
          })
          .join(',')
      );

      const csv = [headers, ...rows].join('\n');
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);

      link.setAttribute('href', url);
      link.setAttribute('download', `${currentData.table_name}_${new Date().getTime()}.csv`);
      link.style.visibility = 'hidden';

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      message.success('数据已导出');
    } catch (error: any) {
      message.error('导出失败: ' + error.message);
    }
  };

  /**
   * 构建表格列
   */
  const buildColumns = (tableData: RawDataResponse | null) => {
    if (!tableData) return [];
    return tableData.columns.map((col) => ({
      title: col.name,
      dataIndex: col.name,
      key: col.name,
      width: 150,
      render: (value: any) => {
        if (value === null || value === undefined) {
          return <Tag>NULL</Tag>;
        }
        if (typeof value === 'boolean') {
          return <Tag color={value ? 'green' : 'red'}>{value ? 'True' : 'False'}</Tag>;
        }
        if (typeof value === 'number') {
          return <span style={{ color: '#1890ff' }}>{value}</span>;
        }
        return <span title={String(value)}>{String(value).substring(0, 100)}</span>;
      },
    }));
  };

  const currentConfig = tabConfigs.find(c => c.key === activeTab);
  const currentData = data[activeTab];
  const currentStats = stats[activeTab];

  return (
    <div className="raw-data-viewer-page">
      {/* 顶部卡片 */}
      <Card
        style={{ marginBottom: 16 }}
        title={
          <Space>
            <DatabaseOutlined style={{ fontSize: '20px', color: '#1890ff' }} />
            <span>原始数据查看器</span>
          </Space>
        }
        extra={
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                if (currentConfig) {
                  fetchData(currentConfig.tableName, page[activeTab] || 1);
                  fetchStats(currentConfig.tableName);
                }
              }}
              loading={loading || statsLoading}
            >
              刷新
            </Button>
            <Button
              icon={<DownloadOutlined />}
              onClick={exportToCSV}
              disabled={!currentData || currentData.data.length === 0}
              type="primary"
            >
              导出CSV
            </Button>
          </Space>
        }
      >
        <Alert
          message="提示"
          description="选择不同的数据源标签页查看对应的原始数据。可以进行分页查询和数据导出。"
          type="info"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      </Card>

      {/* Tab标签页 */}
      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabConfigs.map(config => ({
            key: config.key,
            label: (
              <Space>
                {config.icon}
                <span>{config.displayName}</span>
                {currentData && currentData.table_name === config.tableName && (
                  <Tag color={config.color}>{currentData.total_count}</Tag>
                )}
              </Space>
            ),
            children: (
              <div style={{ paddingTop: 16 }}>
                {/* 日期过滤（仅TTV和EEE） */}
                {(config.key === 'ttv' || config.key === 'eee') && (
                  <div style={{ marginBottom: 24 }}>
                    <div style={{ marginBottom: 12 }}>
                      <h3 style={{ margin: '0 0 8px 0', color: '#262626', fontSize: '14px' }}>
                        日期过滤
                      </h3>
                    </div>
                    <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
                      <DatePicker.RangePicker
                        value={dateRange[activeTab] || null}
                        onChange={(dates) => {
                          setDateRange(prev => ({ ...prev, [activeTab]: dates }));
                          setPage(prev => ({ ...prev, [activeTab]: 1 }));
                        }}
                        format="YYYY-MM-DD"
                        placeholder={['开始日期', '结束日期']}
                        style={{ flex: 1, minWidth: 300 }}
                      />
                      <Button
                        icon={<ClearOutlined />}
                        onClick={() => {
                          setDateRange(prev => ({ ...prev, [activeTab]: null }));
                          setPage(prev => ({ ...prev, [activeTab]: 1 }));
                        }}
                        disabled={!dateRange[activeTab]}
                      >
                        清除
                      </Button>
                    </div>
                  </div>
                )}

                {/* 统计信息卡片 */}
                {currentStats && (
                  <>
                    <div style={{ marginBottom: 24 }}>
                      <div style={{ marginBottom: 12 }}>
                        <h3 style={{ margin: '0 0 8px 0', color: '#262626', fontSize: '14px' }}>
                          数据统计
                        </h3>
                      </div>
                      <Row gutter={[16, 16]}>
                        <Col xs={24} sm={12} md={6}>
                          <div style={{
                            padding: 16,
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            borderRadius: 8,
                            color: 'white',
                          }}>
                            <div style={{ fontSize: '12px', opacity: 0.8, marginBottom: 4 }}>总记录数</div>
                            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                              {currentStats.total_count?.toLocaleString() || 0}
                            </div>
                          </div>
                        </Col>

                        {currentStats.distinct_stocks && (
                          <Col xs={24} sm={12} md={6}>
                            <div style={{
                              padding: 16,
                              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                              borderRadius: 8,
                              color: 'white',
                            }}>
                              <div style={{ fontSize: '12px', opacity: 0.8, marginBottom: 4 }}>不同股票数</div>
                              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                                {currentStats.distinct_stocks?.toLocaleString() || 0}
                              </div>
                            </div>
                          </Col>
                        )}

                        {currentStats.first_record_date && (
                          <Col xs={24} sm={12} md={6}>
                            <div style={{
                              padding: 16,
                              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                              borderRadius: 8,
                              color: 'white',
                            }}>
                              <div style={{ fontSize: '12px', opacity: 0.8, marginBottom: 4 }}>最早日期</div>
                              <div style={{ fontSize: '14px', fontWeight: 'bold' }}>
                                {currentStats.first_record_date?.substring(0, 10) || '-'}
                              </div>
                            </div>
                          </Col>
                        )}

                        {currentStats.last_record_date && (
                          <Col xs={24} sm={12} md={6}>
                            <div style={{
                              padding: 16,
                              background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
                              borderRadius: 8,
                              color: 'white',
                            }}>
                              <div style={{ fontSize: '12px', opacity: 0.8, marginBottom: 4 }}>最新日期</div>
                              <div style={{ fontSize: '14px', fontWeight: 'bold' }}>
                                {currentStats.last_record_date?.substring(0, 10) || '-'}
                              </div>
                            </div>
                          </Col>
                        )}
                      </Row>
                    </div>

                    <Divider style={{ margin: '16px 0' }} />
                  </>
                )}

                {/* 表描述 */}
                <div style={{
                  padding: 12,
                  backgroundColor: '#fafafa',
                  borderRadius: 4,
                  marginBottom: 16,
                  borderLeft: `4px solid #${config.color}`,
                }}>
                  <p style={{ margin: '0 0 8px 0', fontSize: '12px', color: '#666' }}>
                    <strong>数据源：</strong> {config.description}
                  </p>
                  {currentData && (
                    <>
                      <p style={{ margin: '0 0 8px 0', fontSize: '12px', color: '#666' }}>
                        <strong>总列数：</strong> {currentData.columns.length}
                      </p>
                      <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>
                        <strong>列定义：</strong> {currentData.columns.map(col => `${col.name}(${col.type})`).join(', ')}
                      </p>
                    </>
                  )}
                </div>

                {/* 数据表 */}
                <Spin spinning={loading}>
                  {currentData && currentData.data.length > 0 ? (
                    <>
                      <div style={{ overflowX: 'auto' }}>
                        <Table
                          columns={buildColumns(currentData)}
                          dataSource={currentData.data.map((row, idx) => ({
                            ...row,
                            key: idx,
                          }))}
                          pagination={false}
                          scroll={{ x: 1200 }}
                          size="small"
                        />
                      </div>

                      {/* 分页控件 */}
                      <div style={{
                        marginTop: 24,
                        padding: 16,
                        background: '#fafafa',
                        borderRadius: 4,
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        flexWrap: 'wrap',
                        gap: 16,
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                          <label style={{ fontSize: '14px', margin: 0 }}>每页行数:</label>
                          <Select
                            style={{ width: 100 }}
                            value={pageSize[activeTab] || 20}
                            onChange={(value) => {
                              setPageSize(prev => ({ ...prev, [activeTab]: value }));
                              setPage(prev => ({ ...prev, [activeTab]: 1 }));
                            }}
                            options={[
                              { label: '10', value: 10 },
                              { label: '20', value: 20 },
                              { label: '50', value: 50 },
                              { label: '100', value: 100 },
                            ]}
                          />
                        </div>

                        <Pagination
                          current={page[activeTab] || 1}
                          pageSize={pageSize[activeTab] || 20}
                          total={currentData.total_count}
                          onChange={(newPage) => {
                            setPage(prev => ({ ...prev, [activeTab]: newPage }));
                          }}
                          showSizeChanger={false}
                          showTotal={total => `共 ${total} 条记录`}
                          style={{ margin: 0 }}
                        />
                      </div>
                    </>
                  ) : (
                    <Empty description={loading ? '加载中...' : '暂无数据'} />
                  )}
                </Spin>
              </div>
            ),
          }))}
          tabBarStyle={{
            background: '#fafafa',
            padding: '0 16px',
            margin: '-16px -16px 0 -16px',
            borderBottom: '1px solid #f0f0f0',
          }}
        />
      </Card>
    </div>
  );
};

export default RawDataViewerPage;
