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
  Chip,
  IconButton,
  CircularProgress,
  Tooltip,
  TextField,
  InputAdornment,
  Tabs,
  Tab,
  Button,
  Divider
} from '@mui/material';
import {
  ArrowUpward as ArrowUpIcon,
  ArrowDownward as ArrowDownIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  ShowChart as ShowChartIcon,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, Sector } from 'recharts';
import ExchangeService from '../../services/ExchangeService';

// Define colors for the pie chart
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#A442F1', '#42F1F1', '#F142D4'];

// Component for rendering the active pie sector
const renderActiveShape = (props) => {
  const {
    cx,
    cy, 
    midAngle, 
    innerRadius,
    outerRadius,
    startAngle,
    endAngle,
    fill,
    payload,
    percent,
    value
  } = props;

  return (
    <g>
      <text x={cx} y={cy} dy={-20} textAnchor="middle" fill="#333">
        {payload.asset}
      </text>
      <text x={cx} y={cy} textAnchor="middle" fill="#999">
        {`$${payload.usdValue.toFixed(2)}`}
      </text>
      <text x={cx} y={cy} dy={20} textAnchor="middle" fill="#999">
        {`${(percent * 100).toFixed(2)}%`}
      </text>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius + 10}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
      />
      <Sector
        cx={cx}
        cy={cy}
        startAngle={startAngle}
        endAngle={endAngle}
        innerRadius={innerRadius - 5}
        outerRadius={innerRadius - 2}
        fill={fill}
      />
    </g>
  );
};

const PortfolioOverview = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [exchanges, setExchanges] = useState([]);
  const [assets, setAssets] = useState([]);
  const [totalPortfolioValue, setTotalPortfolioValue] = useState(0);
  const [activeTab, setActiveTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: 'usdValue', direction: 'desc' });
  const [activePieIndex, setActivePieIndex] = useState(0);

  // Fetch portfolio data from all connected exchanges
  useEffect(() => {
    const fetchPortfolioData = async () => {
      try {
        setIsLoading(true);
        setError('');

        // Get all user exchanges
        const userExchanges = await ExchangeService.getUserExchanges();
        setExchanges(userExchanges || []);

        // Fetch balances for each exchange
        const balancesPromises = userExchanges.map(exchange => 
          ExchangeService.getBalances(exchange.id)
        );

        const allBalancesResults = await Promise.all(balancesPromises);

        // Combine all balances and convert to a format for displaying
        const assetsMap = new Map();
        let portfolioTotal = 0;

        allBalancesResults.forEach((result, index) => {
          const exchange = userExchanges[index];
          
          if (result.balances) {
            Object.entries(result.balances).forEach(([asset, balance]) => {
              // Skip small balances (dust)
              const numBalance = parseFloat(balance);
              if (numBalance <= 0.000001) return;

              // Get price in USD (this would come from your API)
              const price = result.prices ? result.prices[asset] : 0;
              const usdValue = numBalance * price;
              
              // Add to portfolio total
              portfolioTotal += usdValue;

              // Update or create asset in map
              if (assetsMap.has(asset)) {
                const existingAsset = assetsMap.get(asset);
                assetsMap.set(asset, {
                  ...existingAsset,
                  balance: existingAsset.balance + numBalance,
                  usdValue: existingAsset.usdValue + usdValue,
                  exchanges: [...existingAsset.exchanges, {
                    name: exchange.exchangeName,
                    label: exchange.label,
                    balance: numBalance
                  }]
                });
              } else {
                assetsMap.set(asset, {
                  asset,
                  balance: numBalance,
                  price,
                  usdValue,
                  change24h: result.changes ? (result.changes[asset] || 0) : 0,
                  exchanges: [{
                    name: exchange.exchangeName,
                    label: exchange.label,
                    balance: numBalance
                  }]
                });
              }
            });
          }
        });

        // Convert map to array and sort
        const assetsArray = Array.from(assetsMap.values());
        setAssets(assetsArray);
        setTotalPortfolioValue(portfolioTotal);

      } catch (err) {
        console.error("Failed to fetch portfolio data:", err);
        setError(err.message || 'Failed to load portfolio data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchPortfolioData();
  }, []);

  // Handle manual refresh
  const handleRefresh = async () => {
    // Re-fetch all data
    setIsLoading(true);
    try {
      const userExchanges = await ExchangeService.getUserExchanges();
      setExchanges(userExchanges || []);

      // Now refresh balances for each exchange
      const refreshPromises = userExchanges.map(exchange => 
        ExchangeService.getBalances(exchange.id)
      );

      await Promise.all(refreshPromises);
      
      // Re-fetch portfolio data
      // This is a simplified approach - in a real app, you might want to update the state directly
      // with the new data instead of making an additional fetch
      const balancesPromises = userExchanges.map(exchange => 
        ExchangeService.getBalances(exchange.id)
      );

      const allBalancesResults = await Promise.all(balancesPromises);

      // Process data as in useEffect
      const assetsMap = new Map();
      let portfolioTotal = 0;

      allBalancesResults.forEach((result, index) => {
        const exchange = userExchanges[index];
        
        if (result.balances) {
          Object.entries(result.balances).forEach(([asset, balance]) => {
            const numBalance = parseFloat(balance);
            if (numBalance <= 0.000001) return;

            const price = result.prices ? result.prices[asset] : 0;
            const usdValue = numBalance * price;
            portfolioTotal += usdValue;

            if (assetsMap.has(asset)) {
              const existingAsset = assetsMap.get(asset);
              assetsMap.set(asset, {
                ...existingAsset,
                balance: existingAsset.balance + numBalance,
                usdValue: existingAsset.usdValue + usdValue,
                exchanges: [...existingAsset.exchanges, {
                  name: exchange.exchangeName,
                  label: exchange.label,
                  balance: numBalance
                }]
              });
            } else {
              assetsMap.set(asset, {
                asset,
                balance: numBalance,
                price,
                usdValue,
                change24h: result.changes ? (result.changes[asset] || 0) : 0,
                exchanges: [{
                  name: exchange.exchangeName,
                  label: exchange.label,
                  balance: numBalance
                }]
              });
            }
          });
        }
      });

      const assetsArray = Array.from(assetsMap.values());
      setAssets(assetsArray);
      setTotalPortfolioValue(portfolioTotal);
      
    } catch (err) {
      setError(err.message || 'Failed to refresh portfolio data');
    } finally {
      setIsLoading(false);
    }
  };

  // Filter assets based on search
  const filteredAssets = assets.filter(asset => 
    asset.asset.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Sort assets based on current sort config
  const sortedAssets = [...filteredAssets].sort((a, b) => {
    if (a[sortConfig.key] < b[sortConfig.key]) {
      return sortConfig.direction === 'asc' ? -1 : 1;
    }
    if (a[sortConfig.key] > b[sortConfig.key]) {
      return sortConfig.direction === 'asc' ? 1 : -1;
    }
    return 0;
  });

  // Handle sorting
  const requestSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  // Get pie chart data
  const pieChartData = sortedAssets
    .filter(asset => asset.usdValue > 0)
    .sort((a, b) => b.usdValue - a.usdValue)
    .slice(0, 7);

  return (
    <Paper sx={{ p: 3, height: '100%' }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" component="h2">
          Portfolio Overview
        </Typography>
        
        <Box>
          <IconButton onClick={handleRefresh} disabled={isLoading}>
            {isLoading ? <CircularProgress size={24} /> : <RefreshIcon />}
          </IconButton>
        </Box>
      </Box>

      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="div" gutterBottom>
          ${totalPortfolioValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </Typography>
        
        <Typography variant="body2" color="text.secondary">
          Assets across {exchanges.length} exchanges
        </Typography>
      </Box>

      <Box sx={{ mb: 3, display: 'flex', flexDirection: { xs: 'column', md: 'row' } }}>
        {/* Pie Chart */}
        <Box sx={{ height: 300, width: { xs: '100%', md: '50%' }, mb: { xs: 3, md: 0 } }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                activeIndex={activePieIndex}
                activeShape={renderActiveShape}
                data={pieChartData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                fill="#8884d8"
                dataKey="usdValue"
                onMouseEnter={(_, index) => setActivePieIndex(index)}
              >
                {pieChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </Box>

        {/* Asset Highlights */}
        <Box sx={{ width: { xs: '100%', md: '50%' }, pl: { md: 3 } }}>
          <Typography variant="subtitle2" gutterBottom>
            Top Assets
          </Typography>
          <Divider sx={{ mb: 2 }} />
          {pieChartData.slice(0, 5).map((asset) => (
            <Box 
              key={asset.asset} 
              sx={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                mb: 1.5,
                pb: 1,
                borderBottom: '1px solid rgba(0, 0, 0, 0.05)'
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Box sx={{ mr: 1.5 }}>
                  <Typography variant="body1">
                    {asset.asset}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    ${asset.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}
                  </Typography>
                </Box>
              </Box>
              <Box sx={{ textAlign: 'right' }}>
                <Typography variant="body2">
                  ${asset.usdValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                  {asset.change24h > 0 ? (
                    <ArrowUpIcon color="success" fontSize="small" />
                  ) : (
                    <ArrowDownIcon color="error" fontSize="small" />
                  )}
                  <Typography 
                    variant="caption" 
                    color={asset.change24h >= 0 ? "success.main" : "error.main"}
                  >
                    {Math.abs(asset.change24h).toFixed(2)}%
                  </Typography>
                </Box>
              </Box>
            </Box>
          ))}
        </Box>
      </Box>

      <Box sx={{ mb: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={(_, newValue) => setActiveTab(newValue)}
          variant="fullWidth"
        >
          <Tab label="All Assets" />
          {exchanges.map((exchange, index) => (
            <Tab key={exchange.id} label={exchange.label || exchange.exchangeName} />
          ))}
        </Tabs>
      </Box>

      <Box sx={{ mb: 2 }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Search assets..."
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

      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>
                <Typography 
                  variant="subtitle2"
                  sx={{ cursor: 'pointer' }}
                  onClick={() => requestSort('asset')}
                >
                  Asset
                  {sortConfig.key === 'asset' && (
                    sortConfig.direction === 'asc' ? ' ↑' : ' ↓'
                  )}
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography 
                  variant="subtitle2"
                  sx={{ cursor: 'pointer' }}
                  onClick={() => requestSort('balance')}
                >
                  Balance
                  {sortConfig.key === 'balance' && (
                    sortConfig.direction === 'asc' ? ' ↑' : ' ↓'
                  )}
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography 
                  variant="subtitle2"
                  sx={{ cursor: 'pointer' }}
                  onClick={() => requestSort('price')}
                >
                  Price
                  {sortConfig.key === 'price' && (
                    sortConfig.direction === 'asc' ? ' ↑' : ' ↓'
                  )}
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography 
                  variant="subtitle2"
                  sx={{ cursor: 'pointer' }}
                  onClick={() => requestSort('usdValue')}
                >
                  Value
                  {sortConfig.key === 'usdValue' && (
                    sortConfig.direction === 'asc' ? ' ↑' : ' ↓'
                  )}
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography 
                  variant="subtitle2"
                  sx={{ cursor: 'pointer' }}
                  onClick={() => requestSort('change24h')}
                >
                  24h
                  {sortConfig.key === 'change24h' && (
                    sortConfig.direction === 'asc' ? ' ↑' : ' ↓'
                  )}
                </Typography>
              </TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <CircularProgress size={32} sx={{ my: 3 }} />
                </TableCell>
              </TableRow>
            ) : sortedAssets.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography variant="body2" sx={{ py: 3 }}>
                    {searchQuery ? 'No assets found matching your search' : 'No assets found'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              sortedAssets
                // Filter by exchange if not on "All Assets" tab
                .filter(asset => {
                  if (activeTab === 0) return true;
                  const exchange = exchanges[activeTab - 1];
                  return asset.exchanges.some(e => e.name === exchange.exchangeName);
                })
                .map((asset) => (
                  <TableRow key={asset.asset}>
                    <TableCell>
                      <Typography variant="body2">{asset.asset}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {asset.exchanges.map(e => e.label || e.name).join(', ')}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        {asset.balance.toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 8
                        })}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        ${asset.price.toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 6
                        })}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        ${asset.usdValue.toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2
                        })}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Box display="flex" alignItems="center" justifyContent="flex-end">
                        {asset.change24h > 0 ? (
                          <ArrowUpIcon color="success" fontSize="small" />
                        ) : (
                          <ArrowDownIcon color="error" fontSize="small" />
                        )}
                        <Typography 
                          variant="body2" 
                          color={asset.change24h >= 0 ? "success.main" : "error.main"}
                        >
                          {Math.abs(asset.change24h).toFixed(2)}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title="View Chart">
                        <IconButton size="small">
                          <ShowChartIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default PortfolioOverview;
