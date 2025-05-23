import React, { useEffect, useRef } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';

// Advanced TradingView Chart Component with extended capabilities
const AdvancedTradingViewChart = ({
  symbol = 'BTCUSDT',
  exchange = 'BINANCE',
  interval = '15',
  theme = 'dark',
  height = 500,
  width = '100%',
  estudies = [],
  toolbar = 'full',
  withVolume = true,
  onChartReady = () => {}
}) => {
  const containerRef = useRef(null);
  const tvWidgetRef = useRef(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  useEffect(() => {
    // Clean up any existing widget
    if (tvWidgetRef.current) {
      tvWidgetRef.current.remove();
      tvWidgetRef.current = null;
    }

    // Load TradingView library dynamically
    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = initTradingViewWidget;
    script.onerror = () => setError('Failed to load TradingView widget');
    document.head.appendChild(script);

    // Cleanup function
    return () => {
      if (tvWidgetRef.current) {
        tvWidgetRef.current.remove();
        tvWidgetRef.current = null;
      }
      document.head.removeChild(script);
    };
  }, [symbol, exchange, interval, theme]); // Re-initialize if these props change

  const initTradingViewWidget = () => {
    if (!containerRef.current || !window.TradingView) {
      setError('TradingView not available');
      return;
    }

    setIsLoading(true);
    try {
      // Get custom indicators from user settings or default ones
      const defaultStudies = [
        'MASimple@tv-basicstudies',
        'RSI@tv-basicstudies',
        'MACD@tv-basicstudies',
        'StochasticRSI@tv-basicstudies',
        'VolumeProfle@tv-volumestudies'
      ];

      // Create new widget
      tvWidgetRef.current = new window.TradingView.widget({
        container: containerRef.current,
        symbol: `${exchange}:${symbol}`,
        interval: interval,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        theme: theme,
        style: '1',
        locale: 'en',
        toolbar_bg: theme === 'dark' ? '#151924' : '#f1f3f6',
        enable_publishing: false,
        hide_side_toolbar: false,
        allow_symbol_change: true,
        save_image: true,
        withdateranges: true,
        details: true,
        hotlist: true,
        calendar: true,
        studies_overrides: {
          "volume.volume.color.0": "#eb4d5c",
          "volume.volume.color.1": "#53b987",
        },
        overrides: {
          "paneProperties.background": theme === 'dark' ? "#131722" : "#ffffff",
          "paneProperties.vertGridProperties.color": theme === 'dark' ? "#232323" : "#e6e6e6",
          "paneProperties.horzGridProperties.color": theme === 'dark' ? "#232323" : "#e6e6e6",
          "mainSeriesProperties.candleStyle.upColor": "#53b987",
          "mainSeriesProperties.candleStyle.downColor": "#eb4d5c",
          "mainSeriesProperties.candleStyle.wickUpColor": "#53b987",
          "mainSeriesProperties.candleStyle.wickDownColor": "#eb4d5c",
        },
        loading_screen: { 
          backgroundColor: theme === 'dark' ? "#131722" : "#ffffff",
          foregroundColor: theme === 'dark' ? "#2962ff" : "#2962ff",
        },
        disabled_features: [
          'use_localstorage_for_settings',
        ],
        enabled_features: [
          'study_templates',
          'hide_left_toolbar_by_default',
          'items_favoriting',
          'create_volume_indicator_by_default',
        ],
        charts_storage_url: 'https://saveload.tradingview.com',
        charts_storage_api_version: '1.1',
        client_id: 'crypto_trading_platform',
        user_id: 'public_user',
        fullscreen: false,
        autosize: true,
        studies: withVolume ? [...estudies, ...defaultStudies] : estudies,
        container_id: containerRef.current.id,
      });

      tvWidgetRef.current.onChartReady(() => {
        setIsLoading(false);
        onChartReady(tvWidgetRef.current);
      });
    } catch (err) {
      setError(`Failed to initialize chart: ${err.message}`);
      setIsLoading(false);
    }
  };

  // Methods that can be exposed for parent components to use
  const exportMethods = {
    setSymbol: (newSymbol, newExchange = exchange) => {
      if (tvWidgetRef.current) {
        tvWidgetRef.current.setSymbol(`${newExchange}:${newSymbol}`, interval, () => {
          console.log(`Chart symbol changed to ${newExchange}:${newSymbol}`);
        });
      }
    },
    
    setInterval: (newInterval) => {
      if (tvWidgetRef.current) {
        tvWidgetRef.current.setInterval(newInterval);
      }
    },
    
    addCustomIndicator: (script) => {
      if (tvWidgetRef.current && tvWidgetRef.current.chart) {
        tvWidgetRef.current.chart().createStudy('Custom Script', false, false, [script]);
      }
    },
    
    takeScreenshot: () => {
      if (tvWidgetRef.current) {
        return tvWidgetRef.current.takeScreenshot();
      }
      return null;
    },
    
    saveChart: () => {
      if (tvWidgetRef.current) {
        tvWidgetRef.current.save((chartData) => {
          console.log('Chart saved', chartData);
          // You could store this in user settings or local storage
          localStorage.setItem(`chart_${symbol}_${interval}`, JSON.stringify(chartData));
        });
      }
    },
    
    loadChart: () => {
      if (tvWidgetRef.current) {
        const savedData = localStorage.getItem(`chart_${symbol}_${interval}`);
        if (savedData) {
          tvWidgetRef.current.load(JSON.parse(savedData));
        }
      }
    }
  };

  // Expose methods to parent through ref
  React.useImperativeHandle(
    React.createRef(),
    () => exportMethods,
    [symbol, interval, exchange]
  );

  return (
    <Box sx={{ 
      position: 'relative',
      width, 
      height,
      backgroundColor: theme === 'dark' ? '#131722' : '#ffffff',
      borderRadius: 1,
      overflow: 'hidden'
    }}>
      {isLoading && (
        <Box sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 10,
          backgroundColor: theme === 'dark' ? 'rgba(19, 23, 34, 0.7)' : 'rgba(255, 255, 255, 0.7)'
        }}>
          <CircularProgress />
        </Box>
      )}
      
      {error && (
        <Box sx={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Typography color="error" variant="body1">
            {error}
          </Typography>
        </Box>
      )}
      
      <Box
        ref={containerRef}
        id={`tv-chart-${symbol}-${interval}`}
        sx={{ 
          width: '100%', 
          height: '100%'
        }}
      />
    </Box>
  );
};

export default AdvancedTradingViewChart;
