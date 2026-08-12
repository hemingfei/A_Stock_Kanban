import { useEffect, useRef } from 'react';
import { createChart, IChartApi, ISeriesApi, Time } from 'lightweight-charts';
import type { KLineItem } from '@/types';

interface KLineChartProps {
  data: KLineItem[];
  height?: number;
}

const KLineChart = ({ data, height = 400 }: KLineChartProps) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#333',
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#cccccc',
      },
      timeScale: {
        borderColor: '#cccccc',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    // Create candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#cf1322',
      downColor: '#3f8600',
      borderDownColor: '#3f8600',
      borderUpColor: '#cf1322',
      wickDownColor: '#3f8600',
      wickUpColor: '#cf1322',
    });

    chartRef.current = chart;
    seriesRef.current = candlestickSeries;

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [height]);

  useEffect(() => {
    if (!seriesRef.current || !data.length) return;

    // Format data for lightweight-charts
    const formattedData = data.map((item) => {
      // Parse date - handle both YYYY-MM-DD and YYYY-MM-DD HH:MM formats
      let time: Time;
      if (item.date.includes(' ')) {
        const [datePart] = item.date.split(' ');
        const [year, month, day] = datePart.split('-').map(Number);
        time = year * 10000 + month * 100 + day;
      } else {
        const [year, month, day] = item.date.split('-').map(Number);
        time = year * 10000 + month * 100 + day;
      }

      return {
        time,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
      };
    });

    seriesRef.current.setData(formattedData);

    // Fit content
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  }, [data]);

  return <div ref={chartContainerRef} style={{ width: '100%', height }} />;
};

export default KLineChart;
