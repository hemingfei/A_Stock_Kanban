import { useState, useEffect } from 'react';
import { Modal, Input, List, Button, Space, message } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import api from '@/services/api';

interface StockSearchProps {
  open: boolean;
  onCancel: () => void;
  onSelect: (code: string, name: string) => void;
}

interface SearchResult {
  code: string;
  name: string;
  market?: string;
}

const StockSearch = ({ open, onCancel, onSelect }: StockSearchProps) => {
  const [keyword, setKeyword] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) {
      setKeyword('');
      setResults([]);
    }
  }, [open]);

  useEffect(() => {
    if (!keyword || keyword.length < 1) {
      setResults([]);
      return;
    }

    const search = async () => {
      setLoading(true);
      try {
        const response = await api.get('/api/v1/stocks/search', {
          params: { keyword }
        });
        if (response.data.success) {
          setResults(response.data.data || []);
        } else {
          setResults([]);
          console.error('Search failed:', response.data.error);
        }
      } catch (error) {
        console.error('Search failed:', error);
        setResults([]);
      } finally {
        setLoading(false);
      }
    };

    const timer = setTimeout(search, 300);
    return () => clearTimeout(timer);
  }, [keyword]);

  const handleSelect = (stock: SearchResult) => {
    onSelect(stock.code, stock.name);
    onCancel();
  };

  return (
    <Modal
      title="搜索股票"
      open={open}
      onCancel={onCancel}
      footer={null}
      width={500}
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        <Input
          placeholder="输入股票代码或名称搜索（如：600519、贵州茅台、中际旭创）"
          prefix={<SearchOutlined />}
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          autoFocus
        />
        <List
          loading={loading}
          dataSource={results}
          renderItem={(stock) => (
            <List.Item
              actions={[
                <Button type="primary" size="small" key="add" onClick={() => handleSelect(stock)}>
                  添加
                </Button>
              ]}
              style={{ cursor: 'pointer' }}
            >
              <List.Item.Meta
                title={stock.name}
                description={stock.code}
              />
            </List.Item>
          )}
          locale={{
            emptyText: keyword ? '未找到相关股票，请尝试其他关键词' : '请输入关键词搜索'
          }}
        />
      </Space>
    </Modal>
  );
};

export default StockSearch;
