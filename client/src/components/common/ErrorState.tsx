/**
 * 错误状态组件
 * 提供上下文相关的错误信息和恢复操作
 */

import React from 'react';
import { Result, Button, Space } from 'antd';
import { ReloadOutlined, HomeOutlined, QuestionCircleOutlined } from '@ant-design/icons';

export type ErrorType = '404' | '500' | 'network' | 'timeout' | 'forbidden' | 'empty' | 'generic';

interface ErrorStateProps {
  type?: ErrorType;
  title?: string;
  description?: string;
  onRetry?: () => void;
  onReset?: () => void;
  onGoHome?: () => void;
  showSupport?: boolean;
}

interface ErrorConfig {
  icon: string;
  status: 'error' | 'warning' | 'info' | '404' | '500' | '403';
  title: string;
  description: string;
  primaryAction?: {
    label: string;
    onClick: () => void;
  };
  secondaryActions?: Array<{
    label: string;
    onClick: () => void;
  }>;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  type = 'generic',
  title,
  description,
  onRetry,
  onReset,
  onGoHome,
  showSupport = false
}) => {
  // 错误类型配置
  const getErrorConfig = (): ErrorConfig => {
    const configs: Record<ErrorType, ErrorConfig> = {
      '404': {
        icon: '🔍',
        status: '404',
        title: title || '未找到数据',
        description: description || '请检查股票代码是否正确，或尝试其他搜索条件',
        primaryAction: onReset ? {
          label: '清空重试',
          onClick: onReset
        } : undefined,
        secondaryActions: [
          ...(onGoHome ? [{
            label: '返回首页',
            onClick: onGoHome
          }] : [])
        ]
      },
      '500': {
        icon: '⚠️',
        status: '500',
        title: title || '服务器错误',
        description: description || '系统暂时无法处理您的请求，请稍后再试',
        primaryAction: onRetry ? {
          label: '重新尝试',
          onClick: onRetry
        } : undefined,
        secondaryActions: [
          ...(showSupport ? [{
            label: '联系支持',
            onClick: () => window.open('mailto:support@example.com')
          }] : [])
        ]
      },
      'network': {
        icon: '📡',
        status: 'error',
        title: title || '网络连接失败',
        description: description || '请检查您的网络连接，然后重试',
        primaryAction: onRetry ? {
          label: '重新连接',
          onClick: onRetry
        } : undefined
      },
      'timeout': {
        icon: '⏱️',
        status: 'warning',
        title: title || '请求超时',
        description: description || '服务器响应时间过长，请稍后重试',
        primaryAction: onRetry ? {
          label: '重新加载',
          onClick: onRetry
        } : undefined
      },
      'forbidden': {
        icon: '🔒',
        status: '403',
        title: title || '访问受限',
        description: description || '您没有权限访问此功能，请升级会员或联系管理员',
        secondaryActions: [
          {
            label: '了解会员',
            onClick: () => {
              // 跳转到会员页面
              window.location.href = '/membership';
            }
          },
          ...(onGoHome ? [{
            label: '返回首页',
            onClick: onGoHome
          }] : [])
        ]
      },
      'empty': {
        icon: '📭',
        status: 'info',
        title: title || '暂无数据',
        description: description || '当前没有符合条件的数据，请尝试调整筛选条件',
        primaryAction: onReset ? {
          label: '重置筛选',
          onClick: onReset
        } : undefined
      },
      'generic': {
        icon: '❌',
        status: 'error',
        title: title || '出错了',
        description: description || '发生了一些问题，请稍后重试',
        primaryAction: onRetry ? {
          label: '重试',
          onClick: onRetry
        } : undefined
      }
    };

    return configs[type];
  };

  const config = getErrorConfig();

  return (
    <Result
      icon={
        <div
          style={{
            fontSize: 64,
            marginBottom: 16
          }}
          role="img"
          aria-label="错误图标"
        >
          {config.icon}
        </div>
      }
      status={config.status}
      title={
        <div style={{ fontSize: 20, fontWeight: 600, color: '#111827' }}>
          {config.title}
        </div>
      }
      subTitle={
        <div style={{ fontSize: 14, color: '#6b7280', maxWidth: 500, margin: '0 auto' }}>
          {config.description}
        </div>
      }
      extra={
        <Space size="middle" wrap>
          {config.primaryAction && (
            <Button
              type="primary"
              size="large"
              icon={<ReloadOutlined />}
              onClick={config.primaryAction.onClick}
              aria-label={config.primaryAction.label}
            >
              {config.primaryAction.label}
            </Button>
          )}
          {config.secondaryActions?.map((action, index) => (
            <Button
              key={index}
              size="large"
              icon={action.label === '返回首页' ? <HomeOutlined /> : <QuestionCircleOutlined />}
              onClick={action.onClick}
              aria-label={action.label}
            >
              {action.label}
            </Button>
          ))}
        </Space>
      }
      style={{
        padding: '48px 24px'
      }}
    />
  );
};

/**
 * 简化的错误状态组件
 */
export const SimpleErrorState: React.FC<{
  message: string;
  onRetry?: () => void;
}> = ({ message, onRetry }) => {
  return (
    <div
      style={{
        textAlign: 'center',
        padding: '48px 24px',
        color: '#6b7280'
      }}
      role="alert"
      aria-live="polite"
    >
      <div style={{ fontSize: 40, marginBottom: 16 }}>⚠️</div>
      <div style={{ fontSize: 16, marginBottom: 16 }}>{message}</div>
      {onRetry && (
        <Button
          type="primary"
          icon={<ReloadOutlined />}
          onClick={onRetry}
        >
          重试
        </Button>
      )}
    </div>
  );
};

export default ErrorState;
