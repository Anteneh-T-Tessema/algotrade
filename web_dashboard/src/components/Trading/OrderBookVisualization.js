import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, Divider, useTheme } from '@mui/material';
import { scaleLinear } from 'd3-scale';

const OrderBookVisualization = ({ 
  asks = [], 
  bids = [], 
  maxRows = 12,
  baseAsset = "BTC", 
  quoteAsset = "USDT", 
  precision = 2,
  isLoading = false 
}) => {
  const theme = useTheme();
  const [maxTotal, setMaxTotal] = useState(0);
  const [processedAsks, setProcessedAsks] = useState([]);
  const [processedBids, setProcessedBids] = useState([]);

  const formatNumber = (num, digits = precision) => {
    return new Intl.NumberFormat('en-US', { 
      minimumFractionDigits: digits, 
      maximumFractionDigits: digits 
    }).format(num);
  };

  // Process order book data to calculate totals and depths
  useEffect(() => {
    if (!asks.length && !bids.length) return;

    // Take only the specified number of rows
    const limitedAsks = asks.slice(0, maxRows).reverse();
    const limitedBids = bids.slice(0, maxRows);

    // Calculate cumulative totals
    let askCumulative = 0;
    const processedAsksData = limitedAsks.map(([price, amount]) => {
      askCumulative += amount;
      return {
        price: parseFloat(price),
        amount: parseFloat(amount),
        total: askCumulative
      };
    }).reverse();

    let bidCumulative = 0;
    const processedBidsData = limitedBids.map(([price, amount]) => {
      bidCumulative += amount;
      return {
        price: parseFloat(price),
        amount: parseFloat(amount),
        total: bidCumulative
      };
    });

    // Find max total for both asks and bids for scaling
    const maxAskTotal = askCumulative;
    const maxBidTotal = bidCumulative;
    const newMaxTotal = Math.max(maxAskTotal, maxBidTotal);
    
    setMaxTotal(newMaxTotal);
    setProcessedAsks(processedAsksData);
    setProcessedBids(processedBidsData);
  }, [asks, bids, maxRows]);

  // Setup scale for depth visualization
  const depthScale = scaleLinear()
    .domain([0, maxTotal])
    .range([0, 100]);

  // Calculate dynamic spread
  const spread = processedAsks.length && processedBids.length 
    ? processedAsks[processedAsks.length - 1].price - processedBids[0].price 
    : 0;
  
  const spreadPercentage = processedBids.length 
    ? ((spread / processedBids[0].price) * 100).toFixed(2) 
    : "0.00";

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Typography variant="h6" gutterBottom>
        Order Book ({baseAsset}/{quoteAsset})
      </Typography>
      
      <Box sx={{ display: 'flex', mb: 1 }}>
        <Box sx={{ width: '40%' }}>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center' }}>
            Price ({quoteAsset})
          </Typography>
        </Box>
        <Box sx={{ width: '30%' }}>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center' }}>
            Amount ({baseAsset})
          </Typography>
        </Box>
        <Box sx={{ width: '30%' }}>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center' }}>
            Total
          </Typography>
        </Box>
      </Box>

      {/* Asks (Sell Orders) */}
      <Box>
        {processedAsks.map((ask, i) => (
          <Box 
            key={`ask-${i}`} 
            sx={{ 
              display: 'flex', 
              position: 'relative',
              py: 0.5,
              '&:hover': {
                backgroundColor: theme.palette.action.hover
              }
            }}
          >
            <Box 
              sx={{ 
                position: 'absolute', 
                top: 0, 
                right: 0, 
                bottom: 0,
                width: `${depthScale(ask.total)}%`,
                backgroundColor: theme.palette.error.light,
                opacity: 0.2,
                zIndex: 0
              }} 
            />
            <Box sx={{ width: '40%', textAlign: 'center', position: 'relative', zIndex: 1 }}>
              <Typography color="error.main" variant="body2">
                {formatNumber(ask.price)}
              </Typography>
            </Box>
            <Box sx={{ width: '30%', textAlign: 'center', position: 'relative', zIndex: 1 }}>
              <Typography variant="body2">
                {formatNumber(ask.amount)}
              </Typography>
            </Box>
            <Box sx={{ width: '30%', textAlign: 'center', position: 'relative', zIndex: 1 }}>
              <Typography variant="body2" color="text.secondary">
                {formatNumber(ask.total)}
              </Typography>
            </Box>
          </Box>
        ))}
      </Box>

      {/* Spread */}
      <Box 
        sx={{ 
          py: 1,
          my: 1,
          borderTop: `1px dashed ${theme.palette.divider}`,
          borderBottom: `1px dashed ${theme.palette.divider}`,
          display: 'flex',
          justifyContent: 'center'
        }}
      >
        <Typography variant="caption" color="text.secondary">
          Spread: {formatNumber(spread)} ({spreadPercentage}%)
        </Typography>
      </Box>

      {/* Bids (Buy Orders) */}
      <Box>
        {processedBids.map((bid, i) => (
          <Box 
            key={`bid-${i}`} 
            sx={{ 
              display: 'flex', 
              position: 'relative',
              py: 0.5,
              '&:hover': {
                backgroundColor: theme.palette.action.hover
              }
            }}
          >
            <Box 
              sx={{ 
                position: 'absolute', 
                top: 0, 
                left: 0, 
                bottom: 0,
                width: `${depthScale(bid.total)}%`,
                backgroundColor: theme.palette.success.light,
                opacity: 0.2,
                zIndex: 0
              }} 
            />
            <Box sx={{ width: '40%', textAlign: 'center', position: 'relative', zIndex: 1 }}>
              <Typography color="success.main" variant="body2">
                {formatNumber(bid.price)}
              </Typography>
            </Box>
            <Box sx={{ width: '30%', textAlign: 'center', position: 'relative', zIndex: 1 }}>
              <Typography variant="body2">
                {formatNumber(bid.amount)}
              </Typography>
            </Box>
            <Box sx={{ width: '30%', textAlign: 'center', position: 'relative', zIndex: 1 }}>
              <Typography variant="body2" color="text.secondary">
                {formatNumber(bid.total)}
              </Typography>
            </Box>
          </Box>
        ))}
      </Box>
    </Paper>
  );
};

export default OrderBookVisualization;
