import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Grid,
  Typography,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Tabs,
  Tab,
  InputAdornment,
  Slider,
  Switch,
  FormControlLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Chip,
  IconButton,
  Tooltip,
  ButtonGroup,
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import {
  Timeline as TimelineIcon,
  SwapHoriz as SwapIcon,
  KeyboardArrowDown as ArrowDownIcon,
  KeyboardArrowUp as ArrowUpIcon,
  Close as CloseIcon,
  Settings as SettingsIcon,
  Check as CheckIcon,
  Warning as WarningIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
} from '@mui/icons-material';
import TradingViewChart from '../Charts/TradingViewChart';
import OrderBookVisualization from './OrderBookVisualization';
import ExchangeService from '../../services/ExchangeService';
import WebSocketService from '../../services/WebSocketService';
import TradingService from '../../services/TradingService';

// Sparkline mini chart component
const Sparkline = ({ data = [], isPositive = true, width = 60, height = 20 }) => {
  const theme = useTheme();
  
  if (!data || data.length === 0) {
    return <Box sx={{ width, height }}></Box>;
  }
  
  const values = data.map(d => d.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((d.value - min) / range) * height;
    return `${x},${y}`;
  });

  const path = `M${points.join(' L')}`;

  return (
    <svg width={width} height={height}>
      <path
        d={path}
        fill="none"
        stroke={isPositive ? theme.palette.success.main : theme.palette.error.main}
        strokeWidth={1.5}
      />
    </svg>
  );
};

const TradingInterface = () => {
  const theme = useTheme();
  
  // State for trading interface
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [exchanges, setExchanges] = useState([]);
  const [selectedExchange, setSelectedExchange] = useState('');
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [availableSymbols, setAvailableSymbols] = useState([]);
  const [orderType, setOrderType] = useState('limit');
  const [tradeTab, setTradeTab] = useState('buy');
  const [price, setPrice] = useState('');
  const [amount, setAmount] = useState('');
  const [orderTotal, setOrderTotal] = useState(0);
  const [openOrders, setOpenOrders] = useState([]);
  const [orderHistory, setOrderHistory] = useState([]);
  const [balances, setBalances] = useState({});
  const [orderBook, setOrderBook] = useState({ asks: [], bids: [] });
  const [recentTrades, setRecentTrades] = useState([]);
  const [sliderValue, setSliderValue] = useState(0);
  const [timeframeValue, setTimeframeValue] = useState('15');
  const [advanced, setAdvanced] = useState(false);
  const [stopPrice, setStopPrice] = useState('');
  const [postOnly, setPostOnly] = useState(false);
  const [reduceOnly, setReduceOnly] = useState(false);
  const [wsListeners, setWsListeners] = useState({
    orderbook: null,
    trades: null
  });
  
  // Generate some dummy data for development purposes
  const generateMockData = () => {
    // Mock symbols available
    const symbols = [
      { symbol: 'BTCUSDT', baseAsset: 'BTC', quoteAsset: 'USDT', price: 59842.15 },
      { symbol: 'ETHUSDT', baseAsset: 'ETH', quoteAsset: 'USDT', price: 3521.67 },
      { symbol: 'SOLUSDT', baseAsset: 'SOL', quoteAsset: 'USDT', price: 128.45 },
      { symbol: 'ADAUSDT', baseAsset: 'ADA', quoteAsset: 'USDT', price: 0.45 },
      { symbol: 'BNBUSDT', baseAsset: 'BNB', quoteAsset: 'USDT', price: 615.20 },
    ];
    
    // Mock balances
    const balances = {
      'BTC': 0.12,
      'ETH': 2.5,
      'USDT': 15000,
      'SOL': 25,
      'ADA': 1000,
    };
    
    // Mock order book - generate some realistic order book data
    const generateOrderBook = () => {
      const symbol = symbols.find(s => s.symbol === selectedSymbol);
      if (!symbol) return { asks: [], bids: [] };
      
      const basePrice = symbol.price;
      const asks = [];
      const bids = [];
      
      // Generate some ask orders slightly above current price
      for (let i = 1; i <= 15; i++) {
        const price = basePrice + (basePrice * 0.0001 * i);
        const amount = Math.random() * 2 + 0.1;
        asks.push([price.toFixed(2), amount.toFixed(6)]);
      }
      
      // Generate some bid orders slightly below current price
      for (let i = 1; i <= 15; i++) {
        const price = basePrice - (basePrice * 0.0001 * i);
        const amount = Math.random() * 2 + 0.1;
        bids.push([price.toFixed(2), amount.toFixed(6)]);
      }
      
      return { asks, bids };
    };
    
    // Mock open orders
    const openOrders = [
      { id: 'o123456', symbol: 'BTCUSDT', side: 'buy', type: 'limit', price: 58500, amount: 0.05, filled: 0, status: 'open', timestamp: Date.now() - 3600000 },
      { id: 'o123457', symbol: 'ETHUSDT', side: 'sell', type: 'limit', price: 3600, amount: 1.2, filled: 0, status: 'open', timestamp: Date.now() - 7200000 },
    ];
    
    // Mock order history
    const orderHistory = [
      { id: 'o123450', symbol: 'BTCUSDT', side: 'buy', type: 'market', price: 59120, amount: 0.03, filled: 0.03, status: 'filled', timestamp: Date.now() - 86400000 },
      { id: 'o123451', symbol: 'ETHUSDT', side: 'sell', type: 'limit', price: 3550, amount: 0.5, filled: 0.5, status: 'filled', timestamp: Date.now() - 172800000 },
      { id: 'o123452', symbol: 'BTCUSDT', side: 'buy', type: 'limit', price: 57800, amount: 0.02, filled: 0.02, status: 'filled', timestamp: Date.now() - 259200000 },
    ];
    
    // Mock recent trades
    const generateRecentTrades = () => {
      const symbol = symbols.find(s => s.symbol === selectedSymbol);
      if (!symbol) return [];
      
      const basePrice = symbol.price;
      const trades = [];
      
      for (let i = 0; i < 30; i++) {
        const isBuy = Math.random() > 0.5;
        const price = basePrice + (basePrice * 0.0005 * (Math.random() - 0.5));
        const amount = Math.random() * 0.5 + 0.01;
        
        trades.push({
          id: `t${Date.now() - i}`,
          price: price.toFixed(2),
          amount: amount.toFixed(6),
          side: isBuy ? 'buy' : 'sell',
          timestamp: Date.now() - i * 30000,
        });
      }
      
      return trades;
    };
    
    return { symbols, balances, orderBook: generateOrderBook(), openOrders, orderHistory, recentTrades: generateRecentTrades() };
  };
  
  // Connect to WebSockets for real-time data
  const connectToWebSockets = async (symbol) => {
    try {
      // Connect to orderbook WebSocket
      await WebSocketService.connect('orderbook');
      
      // Listen for orderbook updates
      const orderbookListenerId = WebSocketService.addListener('orderbook', (data) => {
        if (data.symbol === symbol) {
          setOrderBook({
            asks: data.data.asks,
            bids: data.data.bids
          });
        }
      });
      
      // Connect to trades WebSocket
      await WebSocketService.connect('trades');
      
      // Listen for trade updates
      const tradesListenerId = WebSocketService.addListener('trades', (data) => {
        // Prepend new trades to the existing ones and limit to 30
        setRecentTrades(prevTrades => {
          if (Array.isArray(data.data)) {
            return [...data.data, ...prevTrades].slice(0, 30);
          } else if (data.data) {
            return [data.data, ...prevTrades].slice(0, 30);
          }
          return prevTrades;
        });
      });
      
      // Store listener IDs for cleanup
      return { orderbookListenerId, tradesListenerId };
    } catch (error) {
      console.error('Failed to connect to WebSockets:', error);
      setError('Real-time data connection failed. Using fallback data.');
      return null;
    }
  };

  // Fetch data on component mount
  useEffect(() => {
    let websocketListeners = null;
    
    const fetchTradingData = async () => {
      try {
        setIsLoading(true);
        setError('');
        
        // Fetch user exchanges
        const userExchanges = await ExchangeService.getUserExchanges();
        setExchanges(userExchanges || []);
        
        // If we have exchanges, select the first one
        if (userExchanges && userExchanges.length > 0) {
          setSelectedExchange(userExchanges[0].id);
          
          // In a real app, you would fetch these from the exchange API
          // For now, using mock data
          const mockData = generateMockData();
          setAvailableSymbols(mockData.symbols);
          setBalances(mockData.balances);
          setOrderBook(mockData.orderBook);
          setOpenOrders(mockData.openOrders);
          setOrderHistory(mockData.orderHistory);
          setRecentTrades(mockData.recentTrades);
          
          // Set initial price
          const currentSymbol = mockData.symbols.find(s => s.symbol === selectedSymbol);
          if (currentSymbol) {
            setPrice(currentSymbol.price.toString());
          }
          
          // Connect to WebSocket for real-time data
          websocketListeners = await connectToWebSockets(selectedSymbol);
        }
      } catch (err) {
        console.error("Failed to fetch trading data:", err);
        setError(err.message || 'Failed to load trading data');
        
        // For demo purposes, use mock data
        const mockData = generateMockData();
        setAvailableSymbols(mockData.symbols);
        setBalances(mockData.balances);
        setOrderBook(mockData.orderBook);
        setOpenOrders(mockData.openOrders);
        setOrderHistory(mockData.orderHistory);
        setRecentTrades(mockData.recentTrades);
        
        // Even if initial API call fails, try to connect to WebSockets
        websocketListeners = await connectToWebSockets(selectedSymbol);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchTradingData();
    
    // Cleanup function to disconnect WebSockets and remove listeners
    return () => {
      if (websocketListeners) {
        if (websocketListeners.orderbookListenerId) {
          WebSocketService.removeListener('orderbook', websocketListeners.orderbookListenerId);
        }
        if (websocketListeners.tradesListenerId) {
          WebSocketService.removeListener('trades', websocketListeners.tradesListenerId);
        }
      }
      
      WebSocketService.disconnect('orderbook');
      WebSocketService.disconnect('trades');
    };
  }, [selectedSymbol]); // Re-run if selected symbol changes
  
  // Update order total when price or amount changes
  useEffect(() => {
    if (price && amount) {
      setOrderTotal(parseFloat(price) * parseFloat(amount));
    } else {
      setOrderTotal(0);
    }
  }, [price, amount]);
  
  // Update order book when symbol changes
  useEffect(() => {
    if (selectedSymbol) {
      // In a real app, you would fetch the order book from the exchange API
      // For now, using mock data
      const mockData = generateMockData();
      setOrderBook(mockData.orderBook);
      setRecentTrades(mockData.recentTrades);
      
      // Set initial price
      const currentSymbol = mockData.symbols.find(s => s.symbol === selectedSymbol);
      if (currentSymbol) {
        setPrice(currentSymbol.price.toString());
      }
    }
  }, [selectedSymbol]);

  // Handle symbol change
  const handleSymbolChange = (event) => {
    setSelectedSymbol(event.target.value);
  };
  
  // Handle order type change
  const handleOrderTypeChange = (event) => {
    setOrderType(event.target.value);
  };
  
  // Handle trade tab change
  const handleTradeTabChange = (_, newValue) => {
    if (newValue !== null) {
      setTradeTab(newValue);
    }
  };
  
  // Handle timeframe change for chart
  const handleTimeframeChange = (_, newValue) => {
    if (newValue !== null) {
      setTimeframeValue(newValue);
    }
  };
  
  // Handle slider change for order amount
  const handleSliderChange = (_, newValue) => {
    setSliderValue(newValue);
    
    // Calculate amount based on slider percentage
    if (tradeTab === 'buy') {
      const availableUSDT = balances['USDT'] || 0;
      const maxAmount = availableUSDT / parseFloat(price || 1);
      const newAmount = (maxAmount * newValue / 100).toFixed(6);
      setAmount(newAmount);
    } else {
      const symbol = availableSymbols.find(s => s.symbol === selectedSymbol);
      if (symbol) {
        const availableCrypto = balances[symbol.baseAsset] || 0;
        const newAmount = (availableCrypto * newValue / 100).toFixed(6);
        setAmount(newAmount);
      }
    }
  };
  
  // Handle order submission
  const handleSubmitOrder = async () => {
    if (!selectedExchange || !selectedSymbol || !price || !amount) {
      setError('Please fill all required fields');
      return;
    }
    
    try {
      setIsLoading(true);
      
      // In a real app, you would submit the order to the exchange API
      // For now, just simulate a successful order
      const orderData = {
        symbol: selectedSymbol,
        side: tradeTab,
        type: orderType,
        price: orderType === 'market' ? undefined : parseFloat(price),
        amount: parseFloat(amount),
        stopPrice: orderType === 'stop_limit' ? parseFloat(stopPrice) : undefined,
        postOnly,
        reduceOnly,
      };
      
      // In a real app: await ExchangeService.placeOrder(selectedExchange, orderData);
      
      // Simulate success
      alert(`Order placed: ${tradeTab} ${amount} ${selectedSymbol} at ${orderType === 'market' ? 'market price' : price}`);
      
      // Clear the form
      setAmount('');
      setSliderValue(0);
      
      // Refresh open orders (in a real app, you would fetch the updated list)
      const mockOrder = {
        id: `o${Date.now()}`,
        symbol: selectedSymbol,
        side: tradeTab,
        type: orderType,
        price: parseFloat(price),
        amount: parseFloat(amount),
        filled: 0,
        status: 'open',
        timestamp: Date.now(),
      };
      
      setOpenOrders([mockOrder, ...openOrders]);
      
    } catch (err) {
      console.error("Failed to place order:", err);
      setError(err.message || 'Failed to place order');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle order cancellation
  const handleCancelOrder = async (orderId) => {
    try {
      // In a real app, you would cancel the order with the exchange API
      // For now, just simulate a successful cancellation
      
      // Remove the order from the list
      setOpenOrders(openOrders.filter(order => order.id !== orderId));
      
    } catch (err) {
      console.error("Failed to cancel order:", err);
      setError(err.message || 'Failed to cancel order');
    }
  };
  
  // Extract base and quote assets from the selected symbol
  const currentSymbol = availableSymbols.find(s => s.symbol === selectedSymbol);
  const baseAsset = currentSymbol?.baseAsset || 'BTC';
  const quoteAsset = currentSymbol?.quoteAsset || 'USDT';
  
  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
        <Typography variant="h4" component="h1">
          Trading
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: { xs: 2, sm: 0 } }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Exchange</InputLabel>
            <Select
              value={selectedExchange}
              label="Exchange"
              onChange={(e) => setSelectedExchange(e.target.value)}
            >
              {exchanges.map((exchange) => (
                <MenuItem key={exchange.id} value={exchange.id}>
                  {exchange.label || exchange.exchangeName}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Symbol</InputLabel>
            <Select
              value={selectedSymbol}
              label="Symbol"
              onChange={handleSymbolChange}
            >
              {availableSymbols.map((symbol) => (
                <MenuItem key={symbol.symbol} value={symbol.symbol}>
                  {symbol.baseAsset}/{symbol.quoteAsset}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      </Box>
      
      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}
      
      <Grid container spacing={2}>
        <Grid item xs={12} lg={9}>
          <Paper sx={{ p: 2, mb: 2 }}>
            <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6">
                {baseAsset}/{quoteAsset}
              </Typography>
              
              <Box>
                <ToggleButtonGroup
                  value={timeframeValue}
                  exclusive
                  onChange={handleTimeframeChange}
                  size="small"
                >
                  <ToggleButton value="1">1m</ToggleButton>
                  <ToggleButton value="5">5m</ToggleButton>
                  <ToggleButton value="15">15m</ToggleButton>
                  <ToggleButton value="60">1h</ToggleButton>
                  <ToggleButton value="D">1d</ToggleButton>
                </ToggleButtonGroup>
              </Box>
            </Box>
            
            <TradingViewChart 
              symbol={selectedSymbol}
              exchange="BINANCE" // Or dynamically select based on the exchange
              interval={timeframeValue}
              height={500}
            />
          </Paper>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Paper sx={{ p: 2, height: '100%' }}>
                <Typography variant="subtitle1" gutterBottom>
                  Open Orders
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                {openOrders.length === 0 ? (
                  <Box sx={{ textAlign: 'center', py: 3 }}>
                    <Typography variant="body2" color="text.secondary">
                      No open orders
                    </Typography>
                  </Box>
                ) : (
                  <TableContainer sx={{ maxHeight: 200 }}>
                    <Table size="small" stickyHeader>
                      <TableHead>
                        <TableRow>
                          <TableCell>Symbol</TableCell>
                          <TableCell>Type</TableCell>
                          <TableCell align="right">Price</TableCell>
                          <TableCell align="right">Amount</TableCell>
                          <TableCell align="right">Filled</TableCell>
                          <TableCell>Action</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {openOrders.map((order) => (
                          <TableRow key={order.id} hover>
                            <TableCell>
                              <Typography variant="body2">{order.symbol}</Typography>
                              <Typography 
                                variant="caption" 
                                color={order.side === 'buy' ? 'success.main' : 'error.main'}
                              >
                                {order.side.toUpperCase()}
                              </Typography>
                            </TableCell>
                            <TableCell>{order.type.toUpperCase()}</TableCell>
                            <TableCell align="right">
                              {order.price.toLocaleString(undefined, {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2
                              })}
                            </TableCell>
                            <TableCell align="right">
                              {order.amount.toLocaleString(undefined, {
                                minimumFractionDigits: 6,
                                maximumFractionDigits: 6
                              })}
                            </TableCell>
                            <TableCell align="right">
                              {order.filled.toLocaleString(undefined, {
                                minimumFractionDigits: 6,
                                maximumFractionDigits: 6
                              })}
                            </TableCell>
                            <TableCell>
                              <IconButton 
                                size="small" 
                                color="error"
                                onClick={() => handleCancelOrder(order.id)}
                              >
                                <CloseIcon fontSize="small" />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </Paper>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <Paper sx={{ p: 2, height: '100%' }}>
                <Typography variant="subtitle1" gutterBottom>
                  Order History
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                {orderHistory.length === 0 ? (
                  <Box sx={{ textAlign: 'center', py: 3 }}>
                    <Typography variant="body2" color="text.secondary">
                      No order history
                    </Typography>
                  </Box>
                ) : (
                  <TableContainer sx={{ maxHeight: 200 }}>
                    <Table size="small" stickyHeader>
                      <TableHead>
                        <TableRow>
                          <TableCell>Symbol</TableCell>
                          <TableCell>Type</TableCell>
                          <TableCell align="right">Price</TableCell>
                          <TableCell align="right">Amount</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell>Date</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {orderHistory.map((order) => (
                          <TableRow key={order.id} hover>
                            <TableCell>
                              <Typography variant="body2">{order.symbol}</Typography>
                              <Typography 
                                variant="caption" 
                                color={order.side === 'buy' ? 'success.main' : 'error.main'}
                              >
                                {order.side.toUpperCase()}
                              </Typography>
                            </TableCell>
                            <TableCell>{order.type.toUpperCase()}</TableCell>
                            <TableCell align="right">
                              {order.price.toLocaleString(undefined, {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2
                              })}
                            </TableCell>
                            <TableCell align="right">
                              {order.filled.toLocaleString(undefined, {
                                minimumFractionDigits: 6,
                                maximumFractionDigits: 6
                              })}
                            </TableCell>
                            <TableCell>
                              <Chip 
                                label={order.status.toUpperCase()}
                                size="small"
                                color={order.status === 'filled' ? 'success' : 'default'}
                                variant="outlined"
                              />
                            </TableCell>
                            <TableCell>
                              {new Date(order.timestamp).toLocaleDateString()}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </Paper>
            </Grid>
          </Grid>
        </Grid>
        
        <Grid item xs={12} lg={3}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Paper sx={{ p: 2 }}>
                <Box sx={{ mb: 2 }}>
                  <FormControl size="small" fullWidth>
                    <InputLabel>Order Type</InputLabel>
                    <Select
                      value={orderType}
                      label="Order Type"
                      onChange={handleOrderTypeChange}
                    >
                      <MenuItem value="limit">Limit</MenuItem>
                      <MenuItem value="market">Market</MenuItem>
                      <MenuItem value="stop_limit">Stop Limit</MenuItem>
                    </Select>
                  </FormControl>
                </Box>
                
                <ToggleButtonGroup
                  value={tradeTab}
                  exclusive
                  onChange={handleTradeTabChange}
                  fullWidth
                  color={tradeTab === 'buy' ? 'success' : 'error'}
                  sx={{ mb: 2 }}
                >
                  <ToggleButton value="buy" sx={{ py: 1 }}>
                    Buy {baseAsset}
                  </ToggleButton>
                  <ToggleButton value="sell" sx={{ py: 1 }}>
                    Sell {baseAsset}
                  </ToggleButton>
                </ToggleButtonGroup>
                
                {orderType !== 'market' && (
                  <TextField
                    label="Price"
                    type="number"
                    fullWidth
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    variant="outlined"
                    size="small"
                    sx={{ mb: 2 }}
                    InputProps={{
                      endAdornment: <InputAdornment position="end">{quoteAsset}</InputAdornment>,
                    }}
                  />
                )}
                
                {orderType === 'stop_limit' && (
                  <TextField
                    label="Stop Price"
                    type="number"
                    fullWidth
                    value={stopPrice}
                    onChange={(e) => setStopPrice(e.target.value)}
                    variant="outlined"
                    size="small"
                    sx={{ mb: 2 }}
                    InputProps={{
                      endAdornment: <InputAdornment position="end">{quoteAsset}</InputAdornment>,
                    }}
                  />
                )}
                
                <TextField
                  label="Amount"
                  type="number"
                  fullWidth
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  variant="outlined"
                  size="small"
                  sx={{ mb: 2 }}
                  InputProps={{
                    endAdornment: <InputAdornment position="end">{baseAsset}</InputAdornment>,
                  }}
                />
                
                <Box sx={{ px: 1, mb: 2 }}>
                  <Slider
                    value={sliderValue}
                    onChange={handleSliderChange}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(value) => `${value}%`}
                    marks={[
                      { value: 0, label: '0%' },
                      { value: 25, label: '25%' },
                      { value: 50, label: '50%' },
                      { value: 75, label: '75%' },
                      { value: 100, label: '100%' },
                    ]}
                  />
                </Box>
                
                {orderTotal > 0 && (
                  <Typography variant="body2" align="right" sx={{ mb: 2 }}>
                    Total: {orderTotal.toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2
                    })} {quoteAsset}
                  </Typography>
                )}
                
                <Box sx={{ mb: 2 }}>
                  <Button
                    variant="contained"
                    fullWidth
                    size="large"
                    onClick={handleSubmitOrder}
                    disabled={isLoading || !price || !amount}
                    color={tradeTab === 'buy' ? 'success' : 'error'}
                  >
                    {isLoading ? (
                      <CircularProgress size={24} color="inherit" />
                    ) : tradeTab === 'buy' ? (
                      `Buy ${baseAsset}`
                    ) : (
                      `Sell ${baseAsset}`
                    )}
                  </Button>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    Available:
                  </Typography>
                  <Typography variant="body2">
                    {tradeTab === 'buy' 
                      ? `${(balances[quoteAsset] || 0).toLocaleString()} ${quoteAsset}`
                      : `${(balances[baseAsset] || 0).toLocaleString()} ${baseAsset}`
                    }
                  </Typography>
                </Box>
                
                <Divider sx={{ my: 2 }} />
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle2">
                    Advanced
                  </Typography>
                  <Switch
                    size="small"
                    checked={advanced}
                    onChange={(e) => setAdvanced(e.target.checked)}
                  />
                </Box>
                
                {advanced && (
                  <>
                    <FormControlLabel
                      control={
                        <Switch 
                          size="small" 
                          checked={postOnly} 
                          onChange={(e) => setPostOnly(e.target.checked)}
                        />
                      }
                      label={
                        <Typography variant="body2">
                          Post Only
                          <Tooltip title="Order will only be placed if it would be posted to the order book as a maker order">
                            <IconButton size="small">
                              <SettingsIcon fontSize="inherit" />
                            </IconButton>
                          </Tooltip>
                        </Typography>
                      }
                    />
                    
                    <FormControlLabel
                      control={
                        <Switch 
                          size="small" 
                          checked={reduceOnly} 
                          onChange={(e) => setReduceOnly(e.target.checked)}
                        />
                      }
                      label={
                        <Typography variant="body2">
                          Reduce Only
                          <Tooltip title="Order will only reduce your position, not increase it">
                            <IconButton size="small">
                              <SettingsIcon fontSize="inherit" />
                            </IconButton>
                          </Tooltip>
                        </Typography>
                      }
                    />
                  </>
                )}
              </Paper>
            </Grid>
            
            <Grid item xs={12}>
              <OrderBookVisualization 
                asks={orderBook.asks}
                bids={orderBook.bids}
                baseAsset={baseAsset}
                quoteAsset={quoteAsset}
                isLoading={isLoading}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Recent Trades
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                <TableContainer sx={{ maxHeight: 200 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Price</TableCell>
                        <TableCell align="right">Amount</TableCell>
                        <TableCell align="right">Time</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {recentTrades.map((trade) => (
                        <TableRow key={trade.id} hover>
                          <TableCell sx={{ color: trade.side === 'buy' ? 'success.main' : 'error.main' }}>
                            {parseFloat(trade.price).toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2
                            })}
                          </TableCell>
                          <TableCell align="right">
                            {parseFloat(trade.amount).toLocaleString(undefined, {
                              minimumFractionDigits: 6,
                              maximumFractionDigits: 6
                            })}
                          </TableCell>
                          <TableCell align="right">
                            {new Date(trade.timestamp).toLocaleTimeString()}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </Box>
  );
};

export default TradingInterface;
