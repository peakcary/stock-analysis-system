import React, { useState, useEffect } from 'react';
import {
  Modal,
  Card,
  Spin,
  Empty,
  message,
  Statistic,
  Row,
  Col,
  Typography,
  Button,
} from 'antd';
import {
  LoadingOutlined,
  FileExcelOutlined,
} from '@ant-design/icons';
import { motion } from 'framer-motion';
import { getStockChartData } from '../../utils/conceptAnalysisApi';
import EChartsReact from 'echarts-for-react';
import * as echarts from 'echarts';

const { Text } = Typography;

interface StockChartModalProps {
  open: boolean;
  onClose: () => void;
  stockCode: string | null;
}

const StockChartModal: React.FC<StockChartModalProps> = ({
  open,
  onClose,
  stockCode,
}) => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open && stockCode) {
      loadChartData();
    }
  }, [open, stockCode]);

  const loadChartData = async () => {
    if (!stockCode) return;

    setLoading(true);
    setError(null);
    setData(null);

    try {
      const response = await getStockChartData(stockCode);
      setData(response);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || '加载失败';
      setError(errorMsg);
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // 构建热度趋势图表选项
  const getChartOption = () => {
    if (!data || !data.dates || data.dates.length === 0) {
      return {};
    }

    return {
      title: {
        text: `${stockCode} 热度走势`,
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(50, 50, 50, 0.8)',
        borderColor: '#666',
        textStyle: { color: '#fff' },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '20%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: data.dates || [],
        boundaryGap: false,
      },
      yAxis: {
        type: 'value',
      },
      series: [
        {
          name: '热度值',
          data: data.heat_values || [],
          type: 'line',
          smooth: true,
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(102, 126, 234, 0.5)' },
              { offset: 1, color: 'rgba(102, 126, 234, 0.1)' },
            ]),
          },
          lineStyle: {
            color: '#667eea',
            width: 3,
          },
          itemStyle: {
            color: '#667eea',
            borderColor: '#fff',
            borderWidth: 2,
          },
          symbolSize: 6,
          emphasis: {
            itemStyle: {
              color: '#764ba2',
              borderColor: '#fff',
              borderWidth: 2,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
              shadowBlur: 10,
            },
          },
        },
      ],
    };
  };

  return (
    <Modal
      title={`${stockCode} - 热度分析图表`}
      open={open}
      onCancel={onClose}
      footer={[
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
      ]}
      width={1000}
      bodyStyle={{ padding: '24px' }}
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 20px' }}>
          <Spin
            indicator={<LoadingOutlined style={{ fontSize: 48, color: '#667eea' }} />}
          />
          <p style={{ marginTop: '16px', color: '#666' }}>正在加载图表数据...</p>
        </div>
      ) : error ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Empty description={error} />
        </div>
      ) : data ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {/* 股票统计信息 */}
          {data.stock_name && (
            <Card
              style={{
                marginBottom: '24px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                borderRadius: '12px',
              }}
            >
              <Row gutter={[24, 24]}>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>股票代码</Text>}
                    value={stockCode}
                    valueStyle={{ color: 'white', fontSize: '20px' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>股票名称</Text>}
                    value={data.stock_name}
                    valueStyle={{ color: 'white', fontSize: '16px' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>最新热度</Text>}
                    value={
                      data.heat_values && data.heat_values.length > 0
                        ? data.heat_values[data.heat_values.length - 1].toFixed(2)
                        : 0
                    }
                    valueStyle={{ color: '#fff23b', fontSize: '20px' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>数据点数</Text>}
                    value={data.dates?.length || 0}
                    suffix="个"
                    valueStyle={{ color: '#52c41a', fontSize: '20px' }}
                  />
                </Col>
              </Row>
            </Card>
          )}

          {/* 热度趋势图表 */}
          <Card
            style={{
              borderRadius: '12px',
              marginBottom: '24px',
            }}
          >
            {data.dates && data.dates.length > 0 ? (
              <EChartsReact
                option={getChartOption()}
                style={{ height: '400px', width: '100%' }}
                notMerge={true}
                lazyUpdate={true}
              />
            ) : (
              <Empty description="暂无图表数据" style={{ padding: '40px' }} />
            )}
          </Card>

          {/* 数据说明 */}
          <Card
            style={{
              background: '#f0f5ff',
              borderRadius: '12px',
              border: 'none',
            }}
          >
            <Row gutter={[24, 12]}>
              <Col span={24}>
                <Text strong style={{ fontSize: '14px' }}>
                  📊 图表说明：
                </Text>
              </Col>
              <Col span={24}>
                <ul style={{ margin: 0, marginLeft: '20px', color: '#666', fontSize: '12px' }}>
                  <li>横轴表示交易日期</li>
                  <li>纵轴表示该股票在所属概念中的热度值</li>
                  <li>热度值越高，表示该股票在市场中的关注度越高</li>
                  <li>鼠标悬停图表可查看具体数据</li>
                </ul>
              </Col>
            </Row>
          </Card>
        </motion.div>
      ) : (
        <Empty description="无数据" />
      )}
    </Modal>
  );
};

export default StockChartModal;
