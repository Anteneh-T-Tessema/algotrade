import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Grid,
  Typography,
  CircularProgress,
  Card,
  CardContent,
  LinearProgress,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  ButtonGroup,
  Button,
  Tooltip,
  Chip
} from '@mui/material';
import {
  Pie,
  PieChart,
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { 
  TrendingUp, 
  TrendingDown, 
  NotificationImportant,
  LocalAtm,
  PieChart as PieChartIcon,
  BarChart as BarChartIcon,
  Timeline,
  FileDownload,
  Info
} from '@mui/icons-material';
import TradingService from '../../services/TradingService';

// Component for portfolio overview analytics
const PortfolioAnalytics = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [portfolioData, setPortfolioData] = useState(null);
  const [performanceData, setPerformanceData] = useState([]);
  const [assets, setAssets] = useState([]);
  const [timeframe, setTimeframe] = useState('1month');
  const [tabValue, setTabValue] = useState(0);
  const [riskMetrics, setRiskMetrics] = useState(null);
  
  // Fetch portfolio data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError('');
        
        // Fetch portfolio summary
        const summary = await TradingService.getPortfolioSummary();
        setPortfolioData(summary);
        
        // Fetch performance data based on timeframe
        const performance = await TradingService.getPortfolioPerformance(timeframe);
        setPerformanceData(performance.history || []);
        
        // Fetch asset allocation
        const assetData = await TradingService.getPortfolioAssets();
        setAssets(assetData.assets || []);
        
        // Calculate risk metrics
        calculateRiskMetrics(performance.history || []);
        
      } catch (err) {
        console.error("Failed to fetch portfolio data:", err);
        setError(err.message || 'Failed to load portfolio data');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, [timeframe]);
  
  // Calculate risk metrics from performance data
  const calculateRiskMetrics = (historicalData) => {
    if (!historicalData || historicalData.length < 10) {
      return;
    }
    
    try {
      // Calculate daily returns
      const returns = [];
      for (let i = 1; i < historicalData.length; i++) {
        const prevValue = historicalData[i-1].value;
        const currentValue = historicalData[i].value;
        if (prevValue > 0) {
          returns.push((currentValue - prevValue) / prevValue);
        }
      }
      
      // Calculate volatility (standard deviation of returns)
      const mean = returns.reduce((sum, val) => sum + val, 0) / returns.length;
      const squaredDiffs = returns.map(val => Math.pow(val - mean, 2));
      const variance = squaredDiffs.reduce((sum, val) => sum + val, 0) / squaredDiffs.length;
      const volatility = Math.sqrt(variance) * Math.sqrt(252); // Annualized volatility
      
      // Calculate maximum drawdown
      let maxDrawdown = 0;
      let peak = historicalData[0].value;
      
      for (const point of historicalData) {
        if (point.value > peak) {
          peak = point.value;
        }
        
        const drawdown = (peak - point.value) / peak;
        if (drawdown > maxDrawdown) {
          maxDrawdown = drawdown;
        }
      }
      
      // Calculate Sharpe ratio (assuming risk-free rate of 0.02 or 2%)
      const riskFreeRate = 0.02;
      const annualizedReturn = mean * 252; // Annualized return
      const sharpeRatio = (annualizedReturn - riskFreeRate) / volatility;
      
      // Calculate Sortino ratio (only considering negative returns)
      const negativeReturns = returns.filter(r => r < 0);
      const downside = negativeReturns.length > 0 
        ? Math.sqrt(negativeReturns.reduce((sum, r) => sum + r * r, 0) / negativeReturns.length) * Math.sqrt(252)
        : 0.001; // Avoid division by zero
      
      const sortinoRatio = (annualizedReturn - riskFreeRate) / downside;
      
      setRiskMetrics({
        volatility: volatility * 100, // As percentage
        maxDrawdown: maxDrawdown * 100, // As percentage
        sharpeRatio,
        sortinoRatio,
        winRate: returns.filter(r => r > 0).length / returns.length * 100, // Win rate as percentage
        profitFactor: Math.abs(returns.filter(r => r > 0).reduce((sum, r) => sum + r, 0) / 
                             returns.filter(r => r < 0).reduce((sum, r) => sum + r, 0) || 1)
      });
      
    } catch (error) {
      console.error('Error calculating risk metrics:', error);
    }
  };
  
  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  // Handle timeframe change
  const handleTimeframeChange = (newTimeframe) => {
    setTimeframe(newTimeframe);
  };
  
  // Format currency value
  const formatCurrency = (value, symbol = '$') => {
    if (value === undefined || value === null) return 'N/A';
    
    return `${symbol}${value.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })}`;
  };

  // Render loading state
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Render error state
  if (error) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="error" variant="h6">
          {error}
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Portfolio Overview Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3} alignItems="stretch">
          {/* Portfolio Value Card */}
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ height: '100%', backgroundColor: 'primary.dark', color: 'white' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ opacity: 0.8 }}>
                  Total Portfolio Value
                </Typography>
                <Typography variant="h4" sx={{ my: 1, fontWeight: 'bold' }}>
                  {formatCurrency(portfolioData?.totalValue)}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                  {portfolioData?.change24h >= 0 ? (
                    <TrendingUp fontSize="small" color="success" />
                  ) : (
                    <TrendingDown fontSize="small" color="error" />
                  )}
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      ml: 1, 
                      color: portfolioData?.change24h >= 0 ? 'success.light' : 'error.light' 
                    }}
                  >
                    {portfolioData?.change24h?.toFixed(2)}% (24h)
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Current Balance Card */}
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ height: '100%', bgcolor: 'background.paper' }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary">
                  Available Balance
                </Typography>
                <Typography variant="h5" sx={{ my: 1 }}>
                  {formatCurrency(portfolioData?.availableBalance)}
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={(portfolioData?.availableBalance / portfolioData?.totalValue) * 100}
                  sx={{ mt: 1, height: 8, borderRadius: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>
          
          {/* PNL Card */}
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ 
              height: '100%', 
              bgcolor: portfolioData?.totalPnl >= 0 ? 'success.dark' : 'error.dark',
              color: 'white'
            }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ opacity: 0.8 }}>
                  Total P&L
                </Typography>
                <Typography variant="h5" sx={{ my: 1 }}>
                  {formatCurrency(portfolioData?.totalPnl)}
                </Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  ROI: {portfolioData?.roi?.toFixed(2)}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Alerts Card */}
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ height: '100%', bgcolor: 'background.paper' }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center' }}>
                  <NotificationImportant fontSize="small" sx={{ mr: 1 }} />
                  Active Alerts
                </Typography>
                <Typography variant="h5" sx={{ my: 1 }}>
                  {portfolioData?.alerts?.length || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  {portfolioData?.alerts?.length > 0
                    ? `${portfolioData.alerts[0]?.message?.substring(0, 40)}...`
                    : 'No active alerts'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Timeframe Selector */}
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" component="h2">
          Portfolio Analysis
        </Typography>
        
        <ButtonGroup size="small" aria-label="timeframe selector">
          <Button 
            onClick={() => handleTimeframeChange('24h')}
            variant={timeframe === '24h' ? 'contained' : 'outlined'}
          >
            24H
          </Button>
          <Button 
            onClick={() => handleTimeframeChange('7d')}
            variant={timeframe === '7d' ? 'contained' : 'outlined'}
          >
            7D
          </Button>
          <Button 
            onClick={() => handleTimeframeChange('1month')}
            variant={timeframe === '1month' ? 'contained' : 'outlined'}
          >
            1M
          </Button>
          <Button 
            onClick={() => handleTimeframeChange('3months')}
            variant={timeframe === '3months' ? 'contained' : 'outlined'}
          >
            3M
          </Button>
          <Button 
            onClick={() => handleTimeframeChange('1year')}
            variant={timeframe === '1year' ? 'contained' : 'outlined'}
          >
            1Y
          </Button>
          <Button 
            onClick={() => handleTimeframeChange('all')}
            variant={timeframe === 'all' ? 'contained' : 'outlined'}
          >
            ALL
          </Button>
        </ButtonGroup>
      </Box>
      
      {/* Chart and Analysis Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="portfolio analysis tabs">
            <Tab icon={<Timeline />} iconPosition="start" label="Performance" />
            <Tab icon={<PieChartIcon />} iconPosition="start" label="Allocation" />
            <Tab icon={<BarChartIcon />} iconPosition="start" label="Risk Analysis" />
          </Tabs>
        </Box>
        
        {/* Performance Tab Panel */}
        {tabValue === 0 && (
          <Box p={3}>
            <Typography variant="subtitle1" gutterBottom>
              Portfolio Performance
            </Typography>
            <Box sx={{ height: 400 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={performanceData}
                  margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
                  <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 12 }}
                    tickFormatter={(val) => {
                      if (typeof val === 'string') {
                        return timeframe === '24h' 
                          ? val.substring(11, 16) 
                          : val.substring(5, 10);
                      }
                      return val;
                    }}
                  />
                  <YAxis 
                    tick={{ fontSize: 12 }}
                    tickFormatter={(val) => `$${val.toLocaleString()}`}
                  />
                  <RechartsTooltip 
                    formatter={(value) => [`$${value.toLocaleString()}`, 'Portfolio Value']}
                    labelFormatter={(label) => `Date: ${label}`}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="value" 
                    stroke="#2e7dff" 
                    fill="url(#colorValue)" 
                    strokeWidth={2}
                  />
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2e7dff" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#2e7dff" stopOpacity={0.1}/>
                    </linearGradient>
                  </defs>
                </AreaChart>
              </ResponsiveContainer>
            </Box>
            
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button 
                startIcon={<FileDownload />}
                variant="outlined" 
                size="small"
              >
                Export Data
              </Button>
            </Box>
          </Box>
        )}
        
        {/* Allocation Tab Panel */}
        {tabValue === 1 && (
          <Box p={3}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" gutterBottom>
                  Asset Allocation
                </Typography>
                <Box sx={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={assets}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {assets.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color || `hsl(${index * 45}, 70%, 50%)`} />
                        ))}
                      </Pie>
                      <RechartsTooltip 
                        formatter={(value, name, props) => [
                          `$${value.toLocaleString()}`, 
                          props.payload.symbol
                        ]}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </Box>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" gutterBottom>
                  Assets Breakdown
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Asset</TableCell>
                        <TableCell align="right">Amount</TableCell>
                        <TableCell align="right">Value</TableCell>
                        <TableCell align="right">Allocation</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {assets.map((asset) => (
                        <TableRow key={asset.symbol}>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              {asset.icon && (
                                <Box component="img" src={asset.icon} sx={{ width: 20, mr: 1 }} />
                              )}
                              <Typography variant="body2">
                                {asset.name} ({asset.symbol})
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="right">{asset.amount.toFixed(6)}</TableCell>
                          <TableCell align="right">{formatCurrency(asset.value)}</TableCell>
                          <TableCell align="right">
                            <Chip 
                              size="small"
                              label={`${(asset.percentage * 100).toFixed(2)}%`}
                              sx={{ 
                                bgcolor: asset.color || `hsl(${assets.indexOf(asset) * 45}, 70%, 50%)`,
                                color: 'white'
                              }}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
            </Grid>
          </Box>
        )}
        
        {/* Risk Analysis Tab Panel */}
        {tabValue === 2 && (
          <Box p={3}>
            <Typography variant="subtitle1" gutterBottom>
              Risk Analysis
            </Typography>
            
            <Grid container spacing={3}>
              {/* Risk Metrics Cards */}
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ height: '100%', bgcolor: 'background.paper' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Volatility
                      </Typography>
                      <Tooltip title="Annualized standard deviation of returns">
                        <Info fontSize="small" color="action" />
                      </Tooltip>
                    </Box>
                    <Typography variant="h5" sx={{ my: 1 }}>
                      {riskMetrics?.volatility.toFixed(2)}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ height: '100%', bgcolor: 'background.paper' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Max Drawdown
                      </Typography>
                      <Tooltip title="Maximum observed loss from a peak to a trough">
                        <Info fontSize="small" color="action" />
                      </Tooltip>
                    </Box>
                    <Typography variant="h5" sx={{ my: 1, color: 'error.main' }}>
                      {riskMetrics?.maxDrawdown.toFixed(2)}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ height: '100%', bgcolor: 'background.paper' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Sharpe Ratio
                      </Typography>
                      <Tooltip title="Return per unit of risk (higher is better)">
                        <Info fontSize="small" color="action" />
                      </Tooltip>
                    </Box>
                    <Typography variant="h5" sx={{ my: 1 }}>
                      {riskMetrics?.sharpeRatio.toFixed(2)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ height: '100%', bgcolor: 'background.paper' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Win Rate
                      </Typography>
                      <Tooltip title="Percentage of positive returns">
                        <Info fontSize="small" color="action" />
                      </Tooltip>
                    </Box>
                    <Typography variant="h5" sx={{ my: 1 }}>
                      {riskMetrics?.winRate.toFixed(2)}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              {/* Drawdown Chart */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Monthly Returns (%)
                </Typography>
                <Box sx={{ height: 250 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={performanceData.filter((_, idx) => idx % Math.max(1, Math.floor(performanceData.length / 12)) === 0)}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="date" 
                        tick={{ fontSize: 12 }}
                        tickFormatter={(val) => {
                          if (typeof val === 'string') {
                            return val.substring(5, 10);
                          }
                          return val;
                        }}
                      />
                      <YAxis
                        tickFormatter={(val) => `${val.toFixed(1)}%`}
                      />
                      <RechartsTooltip formatter={(value) => [`${value.toFixed(2)}%`, 'Monthly Return']} />
                      <Bar 
                        dataKey="monthlyReturn" 
                        fill="#8884d8" 
                        name="Monthly Return"
                        shape={(props) => {
                          const { x, y, width, height, monthlyReturn } = props;
                          return (
                            <rect 
                              x={x} 
                              y={y} 
                              width={width} 
                              height={height} 
                              fill={monthlyReturn >= 0 ? '#4CAF50' : '#F44336'}
                              radius={[2, 2, 0, 0]}
                            />
                          );
                        }}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </Grid>
              
              {/* Risk-Return Scatter Plot */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Risk Analysis
                </Typography>
                <Box sx={{ height: 250 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={performanceData}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="date"
                        tick={{ fontSize: 12 }}
                        tickFormatter={(val) => {
                          if (typeof val === 'string') {
                            return val.substring(5, 10);
                          }
                          return val;
                        }} 
                      />
                      <YAxis yAxisId="left" />
                      <YAxis yAxisId="right" orientation="right" />
                      <RechartsTooltip />
                      <Legend />
                      <Line 
                        yAxisId="left"
                        type="monotone" 
                        dataKey="rollingVolatility" 
                        stroke="#FF9800" 
                        name="Rolling Volatility"
                        dot={false}
                      />
                      <Line 
                        yAxisId="right"
                        type="monotone" 
                        dataKey="drawdown" 
                        stroke="#F44336" 
                        name="Drawdown"
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </Box>
              </Grid>
            </Grid>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default PortfolioAnalytics;
