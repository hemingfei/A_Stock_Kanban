import { Card, List, Button, Tooltip, Popconfirm, Space } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, StockOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';
import type { Board, Quote } from '@/types';
import { formatPrice, formatChange } from '@/utils/format';

interface BoardCardProps {
  board: Board;
  quotes?: Map<string, Quote>;
  onAddStock: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onRemoveStock: (stockId: number) => void;
}

const BoardCard = ({ board, quotes, onAddStock, onEdit, onDelete, onRemoveStock }: BoardCardProps) => {
  const getQuoteForStock = (code: string) => quotes?.get(code);

  return (
    <Card
      title={
        <Space>
          <StockOutlined />
          {board.name}
        </Space>
      }
      extra={
        <Space>
          <Tooltip title="编辑板块">
            <Button type="text" icon={<EditOutlined />} onClick={onEdit} />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个板块吗？"
            description="板块内的所有股票也会被移除"
            onConfirm={onDelete}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除板块">
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      }
      size="small"
      className="board-card"
    >
      {board.stocks.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#8c8c8c', padding: 16 }}>
          暂无股票，点击下方按钮添加
        </div>
      ) : (
        <List
          size="small"
          dataSource={board.stocks}
          renderItem={(stock) => {
            const quote = getQuoteForStock(stock.code);
            const isUp = quote ? quote.change_percent > 0 : false;
            const isDown = quote ? quote.change_percent < 0 : false;

            return (
              <List.Item
                actions={[
                  <Popconfirm
                    key="delete"
                    title="确定要移除这只股票吗？"
                    onConfirm={() => onRemoveStock(stock.id)}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button type="text" danger size="small" icon={<DeleteOutlined />} />
                  </Popconfirm>
                ]}
              >
                <List.Item.Meta
                  title={
                    <Link
                      to={`/stock/${stock.code}`}
                      style={{ color: 'inherit', textDecoration: 'none' }}
                    >
                      <Space>
                        <span>{stock.name}</span>
                        <span style={{ fontSize: 12, color: '#8c8c8c' }}>{stock.code}</span>
                      </Space>
                    </Link>
                  }
                  description={
                    quote ? (
                      <Space>
                        <span className={isUp ? 'stock-up' : isDown ? 'stock-down' : 'stock-neutral'}>
                          {formatPrice(quote.price)}
                        </span>
                        <span className={isUp ? 'stock-up' : isDown ? 'stock-down' : 'stock-neutral'}>
                          {formatChange(quote.change_percent)}
                        </span>
                      </Space>
                    ) : (
                      <span style={{ color: '#8c8c8c' }}>--</span>
                    )
                  }
                />
              </List.Item>
            );
          }}
        />
      )}
      <Button type="dashed" block icon={<PlusOutlined />} onClick={onAddStock} style={{ marginTop: 16 }}>
        添加股票
      </Button>
    </Card>
  );
};

export default BoardCard;
