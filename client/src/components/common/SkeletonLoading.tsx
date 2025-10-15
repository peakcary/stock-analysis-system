/**
 * 骨架屏加载组件
 * 提供更好的加载体验，减少感知等待时间
 */

import React from 'react';
import { Card, Skeleton, Row, Col } from 'antd';

/**
 * 概念卡片骨架屏
 */
export const ConceptCardSkeleton: React.FC<{ count?: number }> = ({ count = 1 }) => {
  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <Card
          key={index}
          style={{
            marginBottom: 16,
            borderRadius: 12
          }}
        >
          <Skeleton
            active
            avatar={{ shape: 'circle', size: 48 }}
            paragraph={{ rows: 2 }}
            title={{ width: '60%' }}
          />
        </Card>
      ))}
    </>
  );
};

/**
 * 表格骨架屏
 */
export const TableSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => {
  return (
    <Card style={{ borderRadius: 12 }}>
      <Skeleton
        active
        title={{ width: '40%' }}
        paragraph={{ rows }}
      />
    </Card>
  );
};

/**
 * 统计卡片骨架屏
 */
export const StatCardSkeleton: React.FC<{ count?: number }> = ({ count = 4 }) => {
  return (
    <Row gutter={[16, 16]}>
      {Array.from({ length: count }).map((_, index) => (
        <Col xs={12} sm={6} key={index}>
          <Card
            style={{
              borderRadius: 12,
              textAlign: 'center'
            }}
          >
            <Skeleton
              active
              avatar={false}
              title={{ width: '60%', style: { margin: '0 auto' } }}
              paragraph={{
                rows: 1,
                width: ['80%'],
                style: { textAlign: 'center' }
              }}
            />
          </Card>
        </Col>
      ))}
    </Row>
  );
};

/**
 * 股票列表骨架屏
 */
export const StockListSkeleton: React.FC<{ count?: number }> = ({ count = 3 }) => {
  return (
    <div>
      {Array.from({ length: count }).map((_, index) => (
        <Card
          key={index}
          size="small"
          style={{
            marginBottom: 12,
            borderRadius: 8
          }}
        >
          <Row align="middle" gutter={16}>
            <Col span={4}>
              <Skeleton.Avatar active size={40} shape="circle" />
            </Col>
            <Col span={14}>
              <Skeleton
                active
                title={{ width: '80%' }}
                paragraph={{ rows: 1, width: ['60%'] }}
              />
            </Col>
            <Col span={6}>
              <Skeleton.Input active size="small" style={{ width: '100%' }} />
            </Col>
          </Row>
        </Card>
      ))}
    </div>
  );
};

/**
 * 图表骨架屏
 */
export const ChartSkeleton: React.FC<{ height?: number }> = ({ height = 400 }) => {
  return (
    <Card style={{ borderRadius: 12 }}>
      <Skeleton.Node
        active
        style={{
          width: '100%',
          height: height
        }}
      >
        <div
          style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#f8fafc',
            borderRadius: 8
          }}
        >
          <div style={{ textAlign: 'center', color: '#9ca3af' }}>
            <div style={{ fontSize: 32, marginBottom: 8 }}>📊</div>
            <div style={{ fontSize: 14 }}>加载图表中...</div>
          </div>
        </div>
      </Skeleton.Node>
    </Card>
  );
};

/**
 * 搜索页骨架屏
 */
export const SearchPageSkeleton: React.FC = () => {
  return (
    <div style={{ padding: 24 }}>
      {/* 搜索框骨架 */}
      <Card style={{ marginBottom: 24, borderRadius: 12 }}>
        <Skeleton.Input active size="large" style={{ width: '100%' }} />
      </Card>

      {/* 结果骨架 */}
      <ConceptCardSkeleton count={3} />
    </div>
  );
};

/**
 * 详情页骨架屏
 */
export const DetailPageSkeleton: React.FC = () => {
  return (
    <div style={{ padding: 24 }}>
      {/* 标题骨架 */}
      <Skeleton
        active
        title={{ width: '40%' }}
        paragraph={false}
        style={{ marginBottom: 24 }}
      />

      {/* 统计卡片 */}
      <StatCardSkeleton count={4} />

      {/* 表格 */}
      <div style={{ marginTop: 24 }}>
        <TableSkeleton rows={8} />
      </div>
    </div>
  );
};

/**
 * 分析页骨架屏
 */
export const AnalysisPageSkeleton: React.FC = () => {
  return (
    <div style={{ padding: 24 }}>
      {/* 顶部控制栏 */}
      <Card style={{ marginBottom: 24, borderRadius: 12 }}>
        <Row gutter={16}>
          <Col xs={24} sm={12}>
            <Skeleton.Input active size="large" style={{ width: '100%' }} />
          </Col>
          <Col xs={24} sm={12}>
            <Skeleton.Button active size="large" style={{ width: '100%' }} />
          </Col>
        </Row>
      </Card>

      {/* 统计卡片 */}
      <StatCardSkeleton count={4} />

      {/* 概念列表 */}
      <div style={{ marginTop: 24 }}>
        <ConceptCardSkeleton count={5} />
      </div>
    </div>
  );
};

/**
 * 移动端卡片骨架屏
 */
export const MobileCardSkeleton: React.FC<{ count?: number }> = ({ count = 3 }) => {
  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <Card
          key={index}
          size="small"
          style={{
            marginBottom: 12,
            borderRadius: 8
          }}
        >
          <Skeleton
            active
            avatar={{ size: 32, shape: 'circle' }}
            paragraph={{ rows: 2 }}
            title={{ width: '70%' }}
          />
          <div style={{ marginTop: 12 }}>
            <Skeleton.Button active size="small" block />
          </div>
        </Card>
      ))}
    </>
  );
};

/**
 * 自定义骨架屏
 */
export const CustomSkeleton: React.FC<{
  loading: boolean;
  skeleton?: React.ReactNode;
  children: React.ReactNode;
}> = ({ loading, skeleton, children }) => {
  if (!loading) {
    return <>{children}</>;
  }

  if (skeleton) {
    return <>{skeleton}</>;
  }

  return (
    <Card style={{ borderRadius: 12 }}>
      <Skeleton active paragraph={{ rows: 4 }} />
    </Card>
  );
};

// 导出所有组件
export const SkeletonLoading = {
  ConceptCard: ConceptCardSkeleton,
  Table: TableSkeleton,
  StatCard: StatCardSkeleton,
  StockList: StockListSkeleton,
  Chart: ChartSkeleton,
  SearchPage: SearchPageSkeleton,
  DetailPage: DetailPageSkeleton,
  AnalysisPage: AnalysisPageSkeleton,
  MobileCard: MobileCardSkeleton,
  Custom: CustomSkeleton
};

export default SkeletonLoading;
