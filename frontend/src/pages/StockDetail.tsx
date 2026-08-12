import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Card, Typography, Row, Col, Button, Select, Space, Divider, message, Statistic } from 'antd';
import { ArrowLeftOutlined, StockOutlined } from '@ant-design/icons';
import Layout from '@/components/Layout';
import KLineChart from '@/components/KLineChart';
import { Loading } from '@/components/Loading';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import api from '@/services/api';
import type { Quote, KLineItem } from '@/types';
import { formatPrice, formatChange, formatVolume, formatAmount } from '@/utils/format';

const { Title, Text } = Typography;
const { Option } = Select;

type KLinePeriod = '1d' | '1w' | '1M';

const StockDetail = () => {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const [quote, setQuote] = useState<Quote | null>(null);
  const [klineData, setKlineData] = useState<KLineItem[]>([]);
  const [period, setPeriod] = useState<KLinePeriod>('1d');
  const [loading, setLoading] = useState(true);
  const [klineLoading, setKlineLoading] = useState(false);

  const loadQuote = useCallback(async () => {
    if (!code) return;
    setLoading(true);
    try {
      const response = await api.get(`/api/v1/quotes/${code}`);
      if (response.data.success) {
        setQuote(response.data.data);
      }
    } catch (error) {
      console.error('Failed to load quote:', error);
      message.error('加载行情失败');
    } finally {
      setLoading(false);
    }
  }, [code]);

  const loadKline = useCallback(async () => {
    if (!code) return;
    setKlineLoading(true);
    try {
      const response = await api.get(`/api/v1/quotes/${code}/kline`, {
        params: { period, count: 100 }
      });
      if (response.data.success) {
        setKlineData(response.data.data || []);
      }
    } catch (error) {
      console.error('Failed to load K-line:', error);
      message.error('加载K线失败');
    } finally {
      setKlineLoading(false);
    }
  }, [code, period]);

  useEffect(() => {
    loadQuote();
  }, [loadQuote]);

  useEffect(() => {
    loadKline();
  }, [loadKline]);

  const isUp = quote ? quote.change_percent > 0 : false;
  const isDown = quote ? quote.change_percent < 0 : false;

  if (loading) {
    return (
      <Layout>
        <Loading text="加载中..." fullScreen />
      </Layout>
    );
  }

  if (!quote) {
    return (
      <Layout>
        <div style={{ textAlign: 'center', padding: 64 }}>
          <Title level={4}>未找到股票 {code}</Title>
          <Button type="primary" onClick={() => navigate('/')} style={{ marginTop: 16 }}>
            返回首页
          </Button>
        </div>
      </Layout>
    );
  }

  const infoData = [
    { label: '今开', value: formatPrice(quote.open) },
    { label: '昨收', value: formatPrice(quote.pre_close) },
    { label: '最高', value: formatPrice(quote.high), className: 'stock-up' },
    { label: '最低', value: formatPrice(quote.low), className: 'stock-down' },
    { label: '成交量', value: formatVolume(quote.volume) },
    { label: '成交额', value: formatAmount(quote.amount) },
  ];

  if (quote.bid1 !== undefined) {
    infoData.push({ label: '买一', value: `${formatPrice(quote.bid1)} (${quote.bid1_volume})` });
  }
  if (quote.ask1 !== undefined) {
    infoData.push({ label: '卖一', value: `${formatPrice(quote.ask1)} (${quote.ask1_volume})` });
  }

  return (
    <Layout>
      <ErrorBoundary>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
            <Link to="/">
              <Button type="text" icon={<ArrowLeftOutlined />}>
                返回
              </Button>
            </Link>
            <Title level={3} style={{ margin: '0 16px' }}>
              {quote.name}
              <Text type="secondary" style={{ marginLeft: 8 }}>{quote.code}</Text>
            </Title>
          </div>

          {/* Price Card */}
          <Card>
            <Row gutter={32}>
              <Col>
                <Statistic
                  title="最新价"
                  value={quote.price}
                  precision={2}
                  valueStyle={{ color: isUp ? '#cf1322' : isDown ? '#3f8600' : '#8c8c8c', fontSize: 36 }}
                  formatter={(value) => formatPrice(Number(value))}
                />
              </Col>
              <Col>
                <Statistic
                  title="涨跌额"
                  value={quote.change}
                  precision={2}
                  valueStyle={{ color: isUp ? '#cf1322' : isDown ? '#3f8600' : '#8c8c8c' }}
                  prefix={isUp ? '+' : ''}
                />
              </Col>
              <Col>
                <Statistic
                  title="涨跌幅"
                  value={quote.change_percent}
                  precision={2}
                  valueStyle={{ color: isUp ? '#cf1322' : isDown ? '#3f8600' : '#8c8c8c' }}
                  prefix={isUp ? '+' : ''}
                  suffix="%"
                />
              </Col>
            </Row>

            <Divider />

            <Row gutter={[16, 16]}>
              {infoData.map((item, index) => (
                <Col key={index} xs={12} sm={8} md={6}>
                  <div>
                    <Text type="secondary">{item.label}</Text>
                    <Text strong style={{ marginLeft: 8, display: 'inline-block', minWidth: 80 }}>
                      {item.value}
                    </Text>
                  </div>
                </Col>
              ))}
            </Row>
          </Card>

          {/* K-line Chart */}
          <Card
            title={
              <Space>
                <StockOutlined />
                K线图
              </Space>
            }
            extra={
              <Select
                value={period}
                onChange={setPeriod as (value: string) => void}
                style={{ width: 120 }}
              >
                <Option value="1d">日线</Option>
                <Option value="1w">周线</Option>
                <Option value="1M">月线</Option>
              </Select>
            }
          >
            {klineLoading ? (
              <Loading text="加载中..." />
            ) : (
              <KLineChart data={klineData} />
            )}
          </Card>
        </Space>
      </ErrorBoundary>
    </Layout>
  );
};

export default StockDetail;
