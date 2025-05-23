import React, { useEffect, useRef } from 'react';
import { Box, Paper, Typography, CircularProgress } from '@mui/material';

// This component integrates with TradingView's advanced charting library
// It provides professional-grade charts with technical indicators

const TradingViewChart = ({ 
  symbol = 'BTCUSDT',
  exchange = 'BINANCE',
  interval = '15', // Timeframe: 1, 5, 15, 30, 60, 240, D, W, M
  theme = 'light',
  withdateranges = true,
  backgroundColor = 'white',
  height = 500,
  allowFullscreen = true,
  showPublishMessage = false
}) => {
  const container = useRef(null);
  const scriptLoaded = useRef(false);
  const widgetLoaded = useRef(false);

  useEffect(() => {
    // Only create widget once container is ready and script is loaded
    if (container.current && scriptLoaded.current && !widgetLoaded.current) {
      widgetLoaded.current = true;

      // Create TradingView widget
      new window.TradingView.widget({
        container_id: container.current.id,
        autosize: true,
        symbol: `${exchange}:${symbol}`,
        interval,
        timezone: "Etc/UTC",
        theme: theme === 'dark' ? 'dark' : 'light',
        style: "1",
        locale: "en",
        toolbar_bg: backgroundColor,
        enable_publishing: showPublishMessage,
        withdateranges,
        allow_symbol_change: true,
        hide_top_toolbar: false,
        hide_side_toolbar: false,
        details: true,
        hotlist: true,
        calendar: true,
        studies: [
          "RSI@tv-basicstudies",
          "MASimple@tv-basicstudies",
          "MACD@tv-basicstudies"
        ],
        show_popup_button: true,
        popup_width: "1000",
        popup_height: "650",
        enable_screener: true,
      });
    }
  }, [container, exchange, symbol, interval, theme, withdateranges, backgroundColor, showPublishMessage]);

  // Load TradingView script if not already loaded
  useEffect(() => {
    if (!document.getElementById('tradingview-widget-script') && !scriptLoaded.current) {
      const script = document.createElement('script');
      script.id = 'tradingview-widget-script';
      script.src = 'https://s3.tradingview.com/tv.js';
      script.async = true;
      script.onload = () => {
        scriptLoaded.current = true;
        
        // If container is already rendered, create widget
        if (container.current && !widgetLoaded.current) {
          widgetLoaded.current = true;
          
          new window.TradingView.widget({
            container_id: container.current.id,
            autosize: true,
            symbol: `${exchange}:${symbol}`,
            interval,
            timezone: "Etc/UTC",
            theme: theme === 'dark' ? 'dark' : 'light',
            style: "1",
            locale: "en",
            toolbar_bg: backgroundColor,
            enable_publishing: showPublishMessage,
            withdateranges,
            allow_symbol_change: true,
            hide_top_toolbar: false,
            hide_side_toolbar: false,
            details: true,
            hotlist: true,
            calendar: true,
            studies: [
              "RSI@tv-basicstudies",
              "MASimple@tv-basicstudies",
              "MACD@tv-basicstudies"
            ],
            show_popup_button: true,
            popup_width: "1000",
            popup_height: "650",
            enable_screener: true,
          });
        }
      };
      
      document.head.appendChild(script);
    }
  }, [exchange, symbol, interval, theme, withdateranges, backgroundColor, showPublishMessage]);

  return (
    <Paper 
      sx={{ 
        position: 'relative', 
        width: '100%', 
        height: height, 
        overflow: 'hidden',
        mb: 3
      }}
      elevation={2}
    >
      {(!scriptLoaded.current || !widgetLoaded.current) && (
        <Box 
          sx={{ 
            position: 'absolute', 
            top: 0, 
            left: 0, 
            right: 0, 
            bottom: 0, 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            backgroundColor: 'rgba(255, 255, 255, 0.7)',
            zIndex: 10
          }}
        >
          <CircularProgress />
        </Box>
      )}
      <Box 
        id="tradingview-widget-container" 
        ref={container} 
        sx={{ 
          height: '100%', 
          width: '100%'
        }}
      />
    </Paper>
  );
};

export default TradingViewChart;
