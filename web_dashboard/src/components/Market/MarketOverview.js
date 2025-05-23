import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  TextField,
  InputAdornment,
  Tabs,
  Tab,
  Chip,
  CircularProgress,
  Button,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Tooltip
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  ArrowUpward as ArrowUpIcon,
  ArrowDownward as ArrowDownIcon,
  Search as SearchIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  ShowChart as ShowChartIcon,
  AccountBalance as AccountBalanceIcon,
  SwapHoriz as SwapIcon,
  MoreVert as MoreVertIcon,
  FilterList as FilterListIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import TradingService from '../../services/TradingService';
import WebSocketService from '../../services/WebSocketService';

// Sparkline mini chart component
const Sparkline = ({ data = [], color = "#000", width = 100, height = 30 }) => {
  const theme = useTheme();
  
  // If no data, return empty space
  if (!data || data.length === 0) {
    return <Box sx={{ width, height }}></Box>;
  }
  
  const values = data.map(d => d.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  // Calculate points for the path
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * width;
    // Inverted Y because SVG coordinates are from top-left
    const y = height - ((d.value - min) / range) * height;
    return `${x},${y}`;
  });

  const path = `M${points.join(' L')}`;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <path
        d={path}
        fill="none"
        stroke={color || theme.palette.primary.main}
        strokeWidth={1.5}
      />
    </svg>
  );
};

const MarketOverview = () => {
  const theme = useTheme();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [marketData, setMarketData] = useState([]);
  const [activeTab, setActiveTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: 'marketCap', direction: 'desc' });
  const [favorites, setFavorites] = useState([]);
  const [anchorEl, setAnchorEl] = useState(null);
  const [filterMenuAnchor, setFilterMenuAnchor] = useState(null);
  const [activeFilters, setActiveFilters] = useState({
    trending: false,
    gainers: false,
    losers: false
  });
  const [wsConnected, setWsConnected] = useState(false);
  const [wsListenerId, setWsListenerId] = useState(null);
  
  // Transform WebSocket market data to component format
  const transformWebSocketData = (wsData) => {
    return Object.entries(wsData).map(([symbol, details]) => {
      const existingCoin = marketData.find(coin => 
        coin.symbol === symbol || coin.symbol === symbol.toLowerCase() || coin.symbol === symbol.toUpperCase()
      );
      
      // Generate random historical data for sparkline if it doesn't exist
      let sparklineData = existingCoin?.sparkline || existingCoin?.sparklineData;
      
      if (!sparklineData || sparklineData.length === 0) {
        sparklineData = Array(24).fill(0).map((_, i) => ({
          time: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
          value: details.price * (1 + (Math.random() * 0.1 - 0.05))
        }));
      } else if (Array.isArray(sparklineData) && sparklineData.length > 0) {
        // Make sure the sparkline data has the correct format
        if (!sparklineData[0].time) {
          sparklineData = sparklineData.map((value, i) => ({
            time: new Date(Date.now() - (sparklineData.length - i) * 3600000).toISOString(),
            value: typeof value === 'number' ? value : value.value || details.price
          }));
        }

        // Add the latest price point to sparkline
        if (sparklineData.length > 23) {
          sparklineData.shift();
        }
        sparklineData.push({
          time: new Date().toISOString(),
          value: details.price
        });
      }
      
      return {
        id: symbol.toLowerCase(),
        name: details.name || symbol,
        symbol: symbol,
        price: details.price,
        currentPrice: details.price,
        change24h: details.change24h,
        priceChange24h: details.change24h,
        marketCap: details.marketCap || existingCoin?.marketCap || Math.random() * 1000000000,
        volume24h: details.volume24h || 0,
        totalVolume: details.volume24h || existingCoin?.totalVolume || Math.random() * 100000000,
        sparkline: sparklineData,
        sparklineData: sparklineData
      };
    });
  };
  
  // Fetch market data and set up WebSocket connection
  useEffect(() => {
    let marketListenerId = null;
    
    const fetchMarketData = async () => {
      try {
        setIsLoading(true);
        setError('');
        
        // First try to get initial market data from the API
        try {
          const data = await TradingService.getMarketData(100, sortConfig.key, sortConfig.direction);
          
          if (data && data.length > 0) {
            console.log("Received API market data:", data.length, "items");
            setMarketData(data);
          }
        } catch (apiErr) {
          console.error("Error fetching initial market data from API:", apiErr);
          // Don't set error yet as we'll try WebSocket next
        }
        
        // Initialize real-time market data connection
        try {
          await WebSocketService.connect('market');
          setWsConnected(true);
          console.log("Connected to market WebSocket");
          
          // Add listener for market updates
          marketListenerId = WebSocketService.addListener('market', (data) => {
            console.log("Received WebSocket market data:", data);
            
            if (data.type === 'market_update' && data.data) {
              // Transform WebSocket data format to our component's format
              const updatedMarketData = transformWebSocketData(data.data);
              
              // Merge with existing data - replace existing coins and keep others
              if (updatedMarketData.length > 0) {
                setMarketData(prevData => {
                  const updatedSymbols = updatedMarketData.map(coin => coin.symbol);
                  const filteredPrevData = prevData.filter(coin => !updatedSymbols.includes(coin.symbol));
                  return [...updatedMarketData, ...filteredPrevData];
                });
              }
              setWsListenerId(marketListenerId);
            } else if (data.type === 'heartbeat') {
              console.log("Received heartbeat from server at", new Date().toLocaleTimeString());
            } else if (data.type === 'connection_error') {
              setError(data.error || "WebSocket connection error");
              console.error('WebSocket error:', data.error);
              setWsConnected(false);
            }
          });
        } catch (wsErr) {
          console.error("Error connecting to market WebSocket:", wsErr);
          setError("Real-time market updates unavailable. Using static data.");
          setWsConnected(false);
          
          // If WebSocket fails and we don't have API data yet, try API again as fallback
          if (marketData.length === 0) {
            try {
              const data = await TradingService.getMarketData(100, sortConfig.key, sortConfig.direction);
              if (data && data.length > 0) {
                setMarketData(data);
              }
            } catch (fallbackErr) {
              console.error("API fallback also failed:", fallbackErr);
              setError("Failed to load market data. Please try again later.");
            }
          }
        }
        
        // Load saved favorites from localStorage
        const savedFavorites = localStorage.getItem('marketFavorites');
        if (savedFavorites) {
          try {
            setFavorites(JSON.parse(savedFavorites));
          } catch (e) {
            console.error('Failed to parse saved favorites:', e);
          }
        }
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchMarketData();
    
    // Cleanup function
    return () => {
      if (marketListenerId) {
        WebSocketService.removeListener('market', marketListenerId);
      }
      WebSocketService.disconnect('market');
      setWsConnected(false);
    };
  }, []);

  // Handle sorting
  const requestSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  // Toggle favorite status
  const toggleFavorite = (cryptoId) => {
    const newFavorites = favorites.includes(cryptoId)
      ? favorites.filter(id => id !== cryptoId)
      : [...favorites, cryptoId];
    
    setFavorites(newFavorites);
    localStorage.setItem('marketFavorites', JSON.stringify(newFavorites));
  };

  // Handle action menu
  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  // Handle filter menu
  const handleFilterMenuOpen = (event) => {
    setFilterMenuAnchor(event.currentTarget);
  };

  const handleFilterMenuClose = () => {
    setFilterMenuAnchor(null);
  };

  const toggleFilter = (filter) => {
    setActiveFilters({
      ...activeFilters,
      [filter]: !activeFilters[filter]
    });
  };

  // Filter market data based on search, tab, and active filters
  const filteredMarketData = marketData.filter(crypto => {
    // Handle search
    const matchesSearch = crypto.name?.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          crypto.symbol?.toLowerCase().includes(searchQuery.toLowerCase());
    if (!matchesSearch) return false;
    
    // Handle tabs
    if (activeTab === 1 && !favorites.includes(crypto.id)) return false;
    
    // Handle active filters
    if (activeFilters.trending && crypto.marketCapRank > 20) return false;
    if (activeFilters.gainers && crypto.change24h <= 0) return false;
    if (activeFilters.losers && crypto.change24h >= 0) return false;
    
    return true;
  });

  // Sort filtered data
  const sortedMarketData = [...filteredMarketData].sort((a, b) => {
    if (a[sortConfig.key] < b[sortConfig.key]) {
      return sortConfig.direction === 'asc' ? -1 : 1;
    }
    if (a[sortConfig.key] > b[sortConfig.key]) {
      return sortConfig.direction === 'asc' ? 1 : -1;
    }
    return 0;
  });

  // Format large numbers
  const formatNumber = (num, maximumFractionDigits = 2) => {
    if (!num) return '$0';
    if (num >= 1e9) {
      return `$${(num / 1e9).toLocaleString(undefined, { maximumFractionDigits })}B`;
    }
    if (num >= 1e6) {
      return `$${(num / 1e6).toLocaleString(undefined, { maximumFractionDigits })}M`;
    }
    if (num >= 1e3) {
      return `$${(num / 1e3).toLocaleString(undefined, { maximumFractionDigits })}K`;
    }
    return `$${num.toLocaleString(undefined, { maximumFractionDigits })}`;
  };

  // Format price values according to their magnitude
  const formatPrice = (price) => {
    if (price === undefined || price === null) return '$0.00';
    
    if (price >= 1000) {
      return `$${price.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
    } else if (price >= 1) {
      return `$${price.toLocaleString(undefined, { maximumFractionDigits: 4 })}`;
    } else if (price >= 0.01) {
      return `$${price.toLocaleString(undefined, { maximumFractionDigits: 6 })}`;
    } else {
      return `$${price.toLocaleString(undefined, { maximumFractionDigits: 8 })}`;
    }
  };
  
  // Format percentage values
  const formatPercent = (value) => {
    if (value === undefined || value === null) return '0.00%';
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <Paper sx={{ p: { xs: 1, sm: 3 }, height: '100%' }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
        <Typography variant="h6" component="h2" sx={{ display: 'flex', alignItems: 'center' }}>
          Market Overview
          {wsConnected && (
            <Chip 
              label="Live" 
              color="success" 
              size="small" 
              sx={{ ml: 1, height: 20, fontSize: '0.7rem' }}
              icon={<span className="blink-dot" style={{
                display: 'inline-block',
                width: '8px',
                height: '8px',
                backgroundColor: 'currentColor',
                borderRadius: '50%',
                animation: 'blink 1s infinite',
                marginRight: '-4px'
              }} />}
            />
          )}
          <style>
            {`
              @keyframes blink {
                0% { opacity: 0; }
                50% { opacity: 1; }
                100% { opacity: 0; }
              }
            `}
          </style>
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: { xs: 2, sm: 0 } }}>
          {activeFilters.trending && (
            <Chip 
              label="Trending" 
              color="primary" 
              size="small"
              onDelete={() => toggleFilter('trending')}
            />
          )}
          {activeFilters.gainers && (
            <Chip 
              label="Gainers" 
              color="success" 
              size="small"
              onDelete={() => toggleFilter('gainers')}
            />
          )}
          {activeFilters.losers && (
            <Chip 
              label="Losers" 
              color="error" 
              size="small"
              onDelete={() => toggleFilter('losers')}
            />
          )}
          
          <Tooltip title="Filter">
            <IconButton onClick={handleFilterMenuOpen}>
              <FilterListIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Menu
        anchorEl={filterMenuAnchor}
        open={Boolean(filterMenuAnchor)}
        onClose={handleFilterMenuClose}
      >
        <MenuItem onClick={() => { toggleFilter('trending'); handleFilterMenuClose(); }}>
          <ListItemIcon>
            <TrendingUpIcon color={activeFilters.trending ? 'primary' : 'inherit'} />
          </ListItemIcon>
          <ListItemText>Trending</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => { toggleFilter('gainers'); handleFilterMenuClose(); }}>
          <ListItemIcon>
            <ArrowUpIcon color={activeFilters.gainers ? 'success' : 'inherit'} />
          </ListItemIcon>
          <ListItemText>Top Gainers</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => { toggleFilter('losers'); handleFilterMenuClose(); }}>
          <ListItemIcon>
            <ArrowDownIcon color={activeFilters.losers ? 'error' : 'inherit'} />
          </ListItemIcon>
          <ListItemText>Top Losers</ListItemText>
        </MenuItem>
      </Menu>

      {error && (
        <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography color="error">
            {error}
          </Typography>
          {!wsConnected && (
            <Button 
              variant="outlined" 
              color="primary" 
              size="small"
              onClick={() => {
                setError('');
                WebSocketService.connect('market')
                  .then(() => {
                    setWsConnected(true);
                    console.log('Reconnected to market WebSocket');
                  })
                  .catch(err => {
                    setError("Failed to reconnect. Please try again later.");
                    console.error('Failed to reconnect:', err);
                  });
              }}
            >
              Reconnect
            </Button>
          )}
        </Box>
      )}

      <Box sx={{ my: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Tabs
            value={activeTab}
            onChange={(e, newValue) => setActiveTab(newValue)}
            sx={{ mb: 2 }}
          >
            <Tab label="All Cryptocurrencies" />
            <Tab label="Favorites" />
          </Tabs>
        </Box>
        
        <Box display="flex" gap={1}>
          {!wsConnected && (
            <Button
              variant="outlined"
              color="primary"
              size="small"
              onClick={() => {
                setError('');
                WebSocketService.connect('market')
                  .then(() => {
                    setWsConnected(true);
                    console.log('Reconnected to market WebSocket');
                  })
                  .catch(err => {
                    setError("Failed to reconnect to WebSocket. Please try again later.");
                    console.error('Failed to reconnect:', err);
                  });
              }}
            >
              Connect to WebSocket
            </Button>
          )}
          
          <Button
            variant="outlined"
            color="info"
            size="small"
            onClick={() => {
              // Send a ping to test the connection
              if (WebSocketService.isConnected('market')) {
                try {
                  const ws = WebSocketService.getConnection('market');
                  if (ws) {
                    ws.send(JSON.stringify({
                      action: "ping",
                      timestamp: new Date().toISOString()
                    }));
                    console.log("Ping sent to server");
                  } else {
                    console.error("WebSocket reference not available");
                  }
                } catch (err) {
                  console.error("Error sending ping:", err);
                }
              } else {
                console.log("WebSocket not connected");
                setError("WebSocket not connected. Please connect first.");
              }
            }}
            disabled={!wsConnected}
          >
            Test Connection
          </Button>
        </Box>
      </Box>

      <Box sx={{ mb: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={(_, newValue) => setActiveTab(newValue)}
          variant="fullWidth"
        >
          <Tab label="All Cryptocurrencies" />
          <Tab label="Favorites" />
        </Tabs>
      </Box>

      <Box sx={{ mb: 2 }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Search cryptocurrencies..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          }}
        />
      </Box>

      <TableContainer sx={{ maxHeight: 'calc(100vh - 320px)' }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ width: 50 }}>#</TableCell>
              <TableCell>
                <Typography 
                  variant="subtitle2"
                  sx={{ cursor: 'pointer' }}
                  onClick={() => requestSort('name')}
                >
                  Name
                  {sortConfig.key === 'name' && (
                    sortConfig.direction === 'asc' ? ' ↑' : ' ↓'
                  )}
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography 
                  variant="subtitle2"
                  sx={{ cursor: 'pointer' }}
                  onClick={() => requestSort('currentPrice')}
                >
                  Price
                  {sortConfig.key === 'currentPrice' && (
                    sortConfig.direction === 'asc' ? ' ↑' : ' ↓'
                  )}
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography 
                  variant="subtitle2"
                  sx={{ cursor: 'pointer' }}
                  onClick={() => requestSort('priceChange24h')}
                >
                  24h %
                  {sortConfig.key === 'priceChange24h' && (
                    sortConfig.direction === 'asc' ? ' ↑' : ' ↓'
                  )}
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography 
                  variant="subtitle2"
                  sx={{ cursor: 'pointer' }}
                  onClick={() => requestSort('marketCap')}
                >
                  Market Cap
                  {sortConfig.key === 'marketCap' && (
                    sortConfig.direction === 'asc' ? ' ↑' : ' ↓'
                  )}
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography 
                  variant="subtitle2"
                  sx={{ cursor: 'pointer' }}
                  onClick={() => requestSort('totalVolume')}
                >
                  Volume (24h)
                  {sortConfig.key === 'totalVolume' && (
                    sortConfig.direction === 'asc' ? ' ↑' : ' ↓'
                  )}
                </Typography>
              </TableCell>
              <TableCell align="center">Last 7 Days</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <CircularProgress size={32} sx={{ my: 3 }} />
                </TableCell>
              </TableRow>
            ) : sortedMarketData.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography variant="body2" sx={{ py: 3 }}>
                    {searchQuery ? 'No cryptocurrencies found matching your search' : 'No cryptocurrencies found'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              sortedMarketData.map((crypto) => (
                <TableRow key={crypto.id || crypto.symbol} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <IconButton
                        size="small"
                        onClick={() => toggleFavorite(crypto.id || crypto.symbol.toLowerCase())}
                        sx={{ mr: 1 }}
                      >
                        {favorites.includes(crypto.id || crypto.symbol.toLowerCase()) ? (
                          <StarIcon fontSize="small" color="warning" />
                        ) : (
                          <StarBorderIcon fontSize="small" />
                        )}
                      </IconButton>
                      <Typography variant="body2">{crypto.marketCapRank || '-'}</Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {crypto.image && (
                        <Box 
                          component="img" 
                          src={crypto.image} 
                          alt={crypto.name} 
                          sx={{ width: 24, height: 24, mr: 1 }}
                        />
                      )}
                      <Box>
                        <Typography variant="body2">{crypto.name}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {crypto.symbol.toUpperCase()}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2">
                      {formatPrice(crypto.price || crypto.currentPrice)}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Box display="flex" alignItems="center" justifyContent="flex-end">
                      {(crypto.change24h || crypto.priceChange24h) > 0 ? (
                        <ArrowUpIcon color="success" fontSize="small" />
                      ) : (
                        <ArrowDownIcon color="error" fontSize="small" />
                      )}
                      <Typography 
                        variant="body2" 
                        color={(crypto.change24h || crypto.priceChange24h) >= 0 ? "success.main" : "error.main"}
                      >
                        {formatPercent(Math.abs(crypto.change24h || crypto.priceChange24h))}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2">
                      {formatNumber(crypto.marketCap)}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2">
                      {formatNumber(crypto.volume24h || crypto.totalVolume)}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Box display="flex" justifyContent="center">
                      <Sparkline 
                        data={crypto.sparkline || crypto.sparklineData || []} 
                        color={(crypto.change24h || crypto.priceChange24h) >= 0 
                          ? theme.palette.success.main 
                          : theme.palette.error.main}
                      />
                    </Box>
                  </TableCell>
                  <TableCell align="center">
                    <IconButton size="small" onClick={handleMenuOpen}>
                      <MoreVertIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleMenuClose}>
          <ListItemIcon>
            <ShowChartIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Chart</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <ListItemIcon>
            <SwapIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Trade</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <ListItemIcon>
            <AccountBalanceIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Create Strategy</ListItemText>
        </MenuItem>
      </Menu>
    </Paper>
  );
};

export default MarketOverview;
