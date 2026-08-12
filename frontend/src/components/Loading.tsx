import { Spin } from 'antd';
import React from 'react';

interface LoadingProps {
  size?: 'small' | 'default' | 'large';
  text?: string;
  fullScreen?: boolean;
}

export const Loading = ({ size = 'default', text, fullScreen = false }: LoadingProps) => {
  if (fullScreen) {
    return (
      <div style={{
        position: 'fixed',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        zIndex: 1000
      }}>
        <Spin size={size} />
        {text && <div style={{ marginTop: 16 }}>{text}</div>}
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      padding: 32
    }}>
      <Spin size={size} />
      {text && <div style={{ marginTop: 16 }}>{text}</div>}
    </div>
  );
};

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export const EmptyState = ({
  icon = '📭',
  title,
  description,
  action
}: EmptyStateProps) => (
  <div style={{
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 48,
    textAlign: 'center'
  }}>
    <div style={{ fontSize: 48, marginBottom: 16 }}>{icon}</div>
    <h3 style={{ marginBottom: 8, fontSize: 18 }}>{title}</h3>
    {description && <p style={{ color: '#8c8c8c', marginBottom: 16 }}>{description}</p>}
    {action}
  </div>
);
