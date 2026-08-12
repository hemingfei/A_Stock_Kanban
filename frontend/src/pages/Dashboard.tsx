import { useEffect, useState, useCallback } from 'react';
import { Row, Col, Button, Modal, Form, Input, message, Space, Typography } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import Layout from '@/components/Layout';
import BoardCard from '@/components/BoardCard';
import StockSearch from '@/components/StockSearch';
import { Loading, EmptyState } from '@/components/Loading';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { useBoardStore, useQuoteStore, useAllStockCodes } from '@/store';
import api from '@/services/api';
import ws from '@/services/ws';
import type { Board } from '@/types';

const { Title } = Typography;

const Dashboard = () => {
  const boards = useBoardStore((state) => state.boards);
  const isLoading = useBoardStore((state) => state.isLoading);
  const setBoards = useBoardStore((state) => state.setBoards);
  const addBoard = useBoardStore((state) => state.addBoard);
  const deleteBoard = useBoardStore((state) => state.deleteBoard);
  const updateBoard = useBoardStore((state) => state.updateBoard);
  const addStockToBoard = useBoardStore((state) => state.addStockToBoard);
  const removeStockFromBoard = useBoardStore((state) => state.removeStockFromBoard);
  const setLoading = useBoardStore((state) => state.setLoading);
  const updateQuotes = useQuoteStore((state) => state.updateQuotes);
  const quotes = useQuoteStore((state) => state.quotes);
  const allCodes = useAllStockCodes();

  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [searchModalOpen, setSearchModalOpen] = useState(false);
  const [selectedBoardId, setSelectedBoardId] = useState<number | null>(null);
  const [editingBoard, setEditingBoard] = useState<Board | null>(null);
  const [form] = Form.useForm();

  // Load boards
  const loadBoards = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/v1/boards');
      if (response.data.success) {
        setBoards(response.data.data || []);
      }
    } catch (error) {
      console.error('Failed to load boards:', error);
      message.error('加载板块失败');
    } finally {
      setLoading(false);
    }
  }, [setBoards, setLoading]);

  useEffect(() => {
    loadBoards();
  }, [loadBoards]);

  // WebSocket setup
  useEffect(() => {
    // Connect to WebSocket
    ws.connect();

    // Subscribe to quote updates
    const handleQuotes = (data: any) => {
      if (data.type === 'quotes' && data.data?.quotes) {
        updateQuotes(data.data.quotes);
      }
    };
    ws.onMessage(handleQuotes);

    return () => {
      ws.offMessage(handleQuotes);
      ws.disconnect();
    };
  }, [updateQuotes]);

  // Subscribe to codes when they change
  useEffect(() => {
    if (allCodes.length > 0) {
      ws.subscribe(allCodes);
    }
  }, [allCodes]);

  // Create board
  const handleCreateBoard = async (values: { name: string }) => {
    try {
      const response = await api.post('/api/v1/boards', values);
      if (response.data.success) {
        addBoard(response.data.data);
        setCreateModalOpen(false);
        form.resetFields();
        message.success('板块创建成功');
      }
    } catch (error) {
      console.error('Failed to create board:', error);
      message.error('创建板块失败');
    }
  };

  // Edit board
  const handleEditBoard = async (values: { name: string }) => {
    if (!editingBoard) return;
    try {
      const response = await api.put(`/api/v1/boards/${editingBoard.id}`, values);
      if (response.data.success) {
        updateBoard(editingBoard.id, values);
        setEditModalOpen(false);
        setEditingBoard(null);
        form.resetFields();
        message.success('板块更新成功');
      }
    } catch (error) {
      console.error('Failed to update board:', error);
      message.error('更新板块失败');
    }
  };

  // Delete board
  const handleDeleteBoard = async (boardId: number) => {
    try {
      const response = await api.delete(`/api/v1/boards/${boardId}`);
      if (response.data.success) {
        deleteBoard(boardId);
        message.success('板块删除成功');
      }
    } catch (error) {
      console.error('Failed to delete board:', error);
      message.error('删除板块失败');
    }
  };

  // Add stock to board
  const handleAddStock = async (code: string, name: string) => {
    if (!selectedBoardId) return;
    try {
      const response = await api.post(`/api/v1/boards/${selectedBoardId}/stocks`, { code, name });
      if (response.data.success) {
        addStockToBoard(selectedBoardId, response.data.data);
        message.success('股票添加成功');
      }
    } catch (error) {
      console.error('Failed to add stock:', error);
      message.error('添加股票失败');
    }
  };

  // Remove stock from board
  const handleRemoveStock = async (boardId: number, stockId: number) => {
    try {
      const response = await api.delete(`/api/v1/boards/${boardId}/stocks/${stockId}`);
      if (response.data.success) {
        removeStockFromBoard(boardId, stockId);
        message.success('股票移除成功');
      }
    } catch (error) {
      console.error('Failed to remove stock:', error);
      message.error('移除股票失败');
    }
  };

  const openSearchModal = (boardId: number) => {
    setSelectedBoardId(boardId);
    setSearchModalOpen(true);
  };

  const openEditModal = (board: Board) => {
    setEditingBoard(board);
    form.setFieldsValue({ name: board.name });
    setEditModalOpen(true);
  };

  return (
    <Layout>
      <ErrorBoundary>
        <div>
          <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Title level={3} style={{ margin: 0 }}>我的板块</Title>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
              新建板块
            </Button>
          </div>

          {isLoading ? (
            <Loading text="加载中..." />
          ) : boards.length === 0 ? (
            <EmptyState
              icon="📊"
              title="暂无板块"
              description="点击上方按钮创建您的第一个板块"
              action={
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
                  新建板块
                </Button>
              }
            />
          ) : (
            <Row gutter={[16, 16]}>
              {boards.map((board) => (
                <Col xs={24} sm={12} md={8} lg={8} xl={6} key={board.id}>
                  <BoardCard
                    board={board}
                    quotes={quotes}
                    onAddStock={() => openSearchModal(board.id)}
                    onEdit={() => openEditModal(board)}
                    onDelete={() => handleDeleteBoard(board.id)}
                    onRemoveStock={(stockId) => handleRemoveStock(board.id, stockId)}
                  />
                </Col>
              ))}
            </Row>
          )}
        </div>
      </ErrorBoundary>

      {/* Create Board Modal */}
      <Modal
        title="新建板块"
        open={createModalOpen}
        onCancel={() => {
          setCreateModalOpen(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        okText="创建"
        cancelText="取消"
      >
        <Form form={form} onFinish={handleCreateBoard} layout="vertical">
          <Form.Item
            name="name"
            label="板块名称"
            rules={[{ required: true, message: '请输入板块名称' }]}
          >
            <Input placeholder="例如：白酒、新能源" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit Board Modal */}
      <Modal
        title="编辑板块"
        open={editModalOpen}
        onCancel={() => {
          setEditModalOpen(false);
          setEditingBoard(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} onFinish={handleEditBoard} layout="vertical">
          <Form.Item
            name="name"
            label="板块名称"
            rules={[{ required: true, message: '请输入板块名称' }]}
          >
            <Input placeholder="例如：白酒、新能源" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Stock Search Modal */}
      <StockSearch
        open={searchModalOpen}
        onCancel={() => {
          setSearchModalOpen(false);
          setSelectedBoardId(null);
        }}
        onSelect={handleAddStock}
      />
    </Layout>
  );
};

export default Dashboard;
