// SocialTradingHub.js - Main component for social trading features
import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Grid,
  Typography,
  Tabs,
  Tab,
  Button,
  CircularProgress,
  Avatar,
  Card,
  CardContent,
  CardActions,
  Divider,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  TextField,
  InputAdornment,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Search,
  Sort,
  FilterList,
  TrendingUp,
  TrendingDown,
  PersonAdd,
  PersonRemove,
  Star,
  StarBorder,
  Share,
  Comment,
  Favorite,
  FavoriteBorder,
  AttachMoney,
  Timeline,
  MoreVert,
  Warning
} from '@mui/icons-material';
import SocialTradingService from '../../services/SocialTradingService';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';

const SocialTradingHub = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [topTraders, setTopTraders] = useState([]);
  const [followedTraders, setFollowedTraders] = useState([]);
  const [socialFeed, setSocialFeed] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('performance');
  const [timePeriod, setTimePeriod] = useState('1m');
  const [followDialogOpen, setFollowDialogOpen] = useState(false);
  const [selectedTrader, setSelectedTrader] = useState(null);
  const [followConfig, setFollowConfig] = useState({ allocation: 0, riskFactor: 1.0 });
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // Load initial data
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch top traders
        const traders = await SocialTradingService.getTopTraders({
          limit: 20,
          sortBy: sortBy,
          period: timePeriod
        });
        setTopTraders(traders);
        
        // Fetch followed traders
        const following = await SocialTradingService.getFollowedTraders();
        setFollowedTraders(following);
        
        // Fetch social feed
        const feed = await SocialTradingService.getSocialFeed();
        setSocialFeed(feed.items || []);
        
      } catch (err) {
        console.error('Failed to load social trading data:', err);
        setError(err.message || 'Failed to load social trading data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchInitialData();
  }, [sortBy, timePeriod]);
  
  // Filter traders based on search
  const filteredTraders = topTraders.filter(trader => {
    if (!searchQuery) return true;
    
    const query = searchQuery.toLowerCase();
    return (
      trader.name.toLowerCase().includes(query) ||
      trader.username.toLowerCase().includes(query) ||
      (trader.bio && trader.bio.toLowerCase().includes(query))
    );
  });

  // Check if a trader is being followed
  const isFollowing = (traderId) => {
    return followedTraders.some(t => t.id === traderId);
  };

  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // Handle follow button click
  const handleFollowClick = (trader) => {
    setSelectedTrader(trader);
    setFollowConfig({ allocation: 0, riskFactor: 1.0 });
    setFollowDialogOpen(true);
  };

  // Handle unfollow button click
  const handleUnfollowClick = async (traderId) => {
    try {
      await SocialTradingService.unfollowTrader(traderId);
      setFollowedTraders(followedTraders.filter(t => t.id !== traderId));
      setSnackbarMessage('Trader unfollowed successfully');
      setSnackbarOpen(true);
    } catch (err) {
      console.error('Failed to unfollow trader:', err);
      setSnackbarMessage('Failed to unfollow trader: ' + err.message);
      setSnackbarOpen(true);
    }
  };

  // Confirm follow dialog
  const confirmFollow = async () => {
    try {
      await SocialTradingService.followTrader(selectedTrader.id, followConfig);
      const updatedFollowing = await SocialTradingService.getFollowedTraders();
      setFollowedTraders(updatedFollowing);
      setFollowDialogOpen(false);
      setSnackbarMessage(`You are now following ${selectedTrader.name}`);
      setSnackbarOpen(true);
    } catch (err) {
      console.error('Failed to follow trader:', err);
      setSnackbarMessage('Failed to follow trader: ' + err.message);
      setSnackbarOpen(true);
    }
  };

  // Format currency
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  // Format percentage
  const formatPercentage = (value) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  // Format date
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Social Trading
      </Typography>
      
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          <Tab label="Top Traders" />
          <Tab label="Following" />
          <Tab label="Social Feed" />
        </Tabs>
        
        {/* Top Traders Tab */}
        {tabValue === 0 && (
          <Box p={3}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
              <TextField
                placeholder="Search traders"
                variant="outlined"
                size="small"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  )
                }}
                sx={{ width: 250 }}
              />
              <Box>
                <Button
                  startIcon={<Sort />}
                  variant="outlined"
                  size="small"
                  sx={{ mr: 1 }}
                  onClick={() => {
                    const newSortBy = sortBy === 'performance' ? 'followers' : 'performance';
                    setSortBy(newSortBy);
                  }}
                >
                  Sort by: {sortBy === 'performance' ? 'Performance' : 'Followers'}
                </Button>
                <Button
                  startIcon={<Timeline />}
                  variant="outlined"
                  size="small"
                  onClick={() => {
                    const periods = ['1w', '1m', '3m', '1y', 'all'];
                    const currentIndex = periods.indexOf(timePeriod);
                    const nextIndex = (currentIndex + 1) % periods.length;
                    setTimePeriod(periods[nextIndex]);
                  }}
                >
                  Period: {timePeriod === '1w' ? '1 Week' : 
                           timePeriod === '1m' ? '1 Month' : 
                           timePeriod === '3m' ? '3 Months' : 
                           timePeriod === '1y' ? '1 Year' : 'All Time'}
                </Button>
              </Box>
            </Box>
            
            <TableContainer>
              <Table size="medium">
                <TableHead>
                  <TableRow>
                    <TableCell>Trader</TableCell>
                    <TableCell align="center">Performance</TableCell>
                    <TableCell align="center">Win Rate</TableCell>
                    <TableCell align="center">Followers</TableCell>
                    <TableCell align="center">Risk Score</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredTraders.map((trader) => (
                    <TableRow key={trader.id}>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Avatar src={trader.avatar} sx={{ width: 40, height: 40, mr: 2 }}>
                            {trader.name.charAt(0)}
                          </Avatar>
                          <Box>
                            <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                              {trader.name}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              @{trader.username}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          {trader.performance >= 0 ? (
                            <TrendingUp fontSize="small" color="success" sx={{ mr: 0.5 }} />
                          ) : (
                            <TrendingDown fontSize="small" color="error" sx={{ mr: 0.5 }} />
                          )}
                          <Typography
                            variant="body2"
                            color={trader.performance >= 0 ? 'success.main' : 'error.main'}
                            sx={{ fontWeight: 'bold' }}
                          >
                            {formatPercentage(trader.performance)}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2">{trader.winRate}%</Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2">{trader.followers.toLocaleString()}</Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={trader.riskScore.toFixed(1)}
                          size="small"
                          color={
                            trader.riskScore < 3 ? 'success' :
                            trader.riskScore < 7 ? 'warning' : 'error'
                          }
                        />
                      </TableCell>
                      <TableCell align="right">
                        {isFollowing(trader.id) ? (
                          <Button
                            variant="outlined"
                            size="small"
                            color="error"
                            startIcon={<PersonRemove />}
                            onClick={() => handleUnfollowClick(trader.id)}
                          >
                            Unfollow
                          </Button>
                        ) : (
                          <Button
                            variant="contained"
                            size="small"
                            color="primary"
                            startIcon={<PersonAdd />}
                            onClick={() => handleFollowClick(trader)}
                          >
                            Follow
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}
        
        {/* Following Tab */}
        {tabValue === 1 && (
          <Box p={3}>
            {followedTraders.length > 0 ? (
              <Grid container spacing={3}>
                {followedTraders.map((trader) => (
                  <Grid item xs={12} sm={6} md={4} key={trader.id}>
                    <Card variant="outlined">
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                          <Avatar src={trader.avatar} sx={{ width: 40, height: 40, mr: 2 }}>
                            {trader.name.charAt(0)}
                          </Avatar>
                          <Box>
                            <Typography variant="h6">{trader.name}</Typography>
                            <Typography variant="body2" color="textSecondary">
                              @{trader.username}
                            </Typography>
                          </Box>
                        </Box>
                        
                        <Box sx={{ height: 100, mb: 2 }}>
                          <ResponsiveContainer width="100%" height="100%">
                            <AreaChart
                              data={trader.performanceHistory}
                              margin={{ top: 5, right: 0, left: 0, bottom: 5 }}
                            >
                              <defs>
                                <linearGradient id={`colorPerf${trader.id}`} x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor={trader.performance >= 0 ? '#4caf50' : '#f44336'} stopOpacity={0.8}/>
                                  <stop offset="95%" stopColor={trader.performance >= 0 ? '#4caf50' : '#f44336'} stopOpacity={0.1}/>
                                </linearGradient>
                              </defs>
                              <Area
                                type="monotone"
                                dataKey="value"
                                stroke={trader.performance >= 0 ? '#4caf50' : '#f44336'}
                                fill={`url(#colorPerf${trader.id})`}
                              />
                            </AreaChart>
                          </ResponsiveContainer>
                        </Box>
                        
                        <Grid container spacing={2}>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="textSecondary">Performance</Typography>
                            <Typography variant="body1" color={trader.performance >= 0 ? 'success.main' : 'error.main'}>
                              {formatPercentage(trader.performance)}
                            </Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="textSecondary">Win Rate</Typography>
                            <Typography variant="body1">{trader.winRate}%</Typography>
                          </Grid>
                        </Grid>
                        
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="body2" color="textSecondary">Your Allocation</Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Typography variant="body1" sx={{ mr: 1 }}>
                              {formatCurrency(trader.allocation)}
                            </Typography>
                            <LinearProgress
                              variant="determinate"
                              value={(trader.allocation / trader.maxAllocation) * 100}
                              sx={{ flexGrow: 1 }}
                            />
                          </Box>
                        </Box>
                      </CardContent>
                      <Divider />
                      <CardActions>
                        <Button
                          size="small"
                          startIcon={<AttachMoney />}
                        >
                          Adjust Allocation
                        </Button>
                        <Button
                          size="small"
                          color="error"
                          startIcon={<PersonRemove />}
                          onClick={() => handleUnfollowClick(trader.id)}
                        >
                          Unfollow
                        </Button>
                      </CardActions>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            ) : (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="h6" color="textSecondary" gutterBottom>
                  You're not following any traders yet
                </Typography>
                <Typography variant="body1" color="textSecondary" paragraph>
                  Find top traders and copy their trades automatically
                </Typography>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={() => setTabValue(0)}
                >
                  Discover Traders
                </Button>
              </Box>
            )}
          </Box>
        )}
        
        {/* Social Feed Tab */}
        {tabValue === 2 && (
          <Box p={3}>
            {socialFeed.map((post) => (
              <Card key={post.id} sx={{ mb: 3 }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar src={post.user.avatar} sx={{ mr: 2 }}>
                      {post.user.name.charAt(0)}
                    </Avatar>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="subtitle1">{post.user.name}</Typography>
                      <Typography variant="body2" color="textSecondary">
                        {formatDate(post.timestamp)}
                      </Typography>
                    </Box>
                    <IconButton size="small">
                      <MoreVert />
                    </IconButton>
                  </Box>
                  
                  <Typography variant="body1" paragraph>
                    {post.content}
                  </Typography>
                  
                  {post.type === 'trade' && (
                    <Box sx={{ p: 2, bgcolor: 'action.hover', borderRadius: 1, mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" color="textSecondary">
                          {post.trade.side.toUpperCase()} {post.trade.symbol}
                        </Typography>
                        <Chip
                          label={post.trade.status}
                          size="small"
                          color={post.trade.status === 'PROFIT' ? 'success' : 'error'}
                        />
                      </Box>
                      <Typography variant="body2">
                        Entry: {formatCurrency(post.trade.entryPrice)}
                      </Typography>
                      <Typography variant="body2">
                        Exit: {formatCurrency(post.trade.exitPrice)}
                      </Typography>
                      <Typography
                        variant="body2"
                        color={post.trade.profit >= 0 ? 'success.main' : 'error.main'}
                        sx={{ fontWeight: 'bold' }}
                      >
                        P&L: {formatCurrency(post.trade.profit)} ({post.trade.profitPercentage}%)
                      </Typography>
                    </Box>
                  )}
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Box>
                      <IconButton size="small" color="primary">
                        {post.liked ? <Favorite /> : <FavoriteBorder />}
                      </IconButton>
                      <Typography variant="body2" component="span" color="textSecondary">
                        {post.likes}
                      </Typography>
                    </Box>
                    <Box>
                      <IconButton size="small">
                        <Comment />
                      </IconButton>
                      <Typography variant="body2" component="span" color="textSecondary">
                        {post.comments}
                      </Typography>
                    </Box>
                    <IconButton size="small">
                      <Share />
                    </IconButton>
                  </Box>
                </CardContent>
              </Card>
            ))}
          </Box>
        )}
      </Paper>
      
      {/* Follow Trader Dialog */}
      <Dialog open={followDialogOpen} onClose={() => setFollowDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Follow {selectedTrader?.name}</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            When you follow a trader, your account will automatically copy their trades based on your settings.
          </Alert>
          
          <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
            Allocation Amount
          </Typography>
          <TextField
            fullWidth
            type="number"
            variant="outlined"
            InputProps={{
              startAdornment: <InputAdornment position="start">$</InputAdornment>
            }}
            value={followConfig.allocation}
            onChange={(e) => setFollowConfig({ ...followConfig, allocation: Number(e.target.value) })}
            helperText="The amount you want to allocate to copying this trader's positions"
            sx={{ mb: 3 }}
          />
          
          <Typography variant="subtitle2" gutterBottom>
            Risk Factor
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Typography variant="body2" color="textSecondary">Low Risk</Typography>
            <Box sx={{ flexGrow: 1, mx: 2 }}>
              <Slider
                value={followConfig.riskFactor}
                min={0.1}
                max={2.0}
                step={0.1}
                valueLabelDisplay="auto"
                onChange={(e, value) => setFollowConfig({ ...followConfig, riskFactor: value })}
              />
            </Box>
            <Typography variant="body2" color="textSecondary">High Risk</Typography>
          </Box>
          <Typography variant="caption" color="textSecondary">
            Adjust the position sizes relative to the trader (1.0 = same size)
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFollowDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            color="primary" 
            onClick={confirmFollow}
            disabled={followConfig.allocation <= 0}
          >
            Follow Trader
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={5000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Box>
  );
};

export default SocialTradingHub;
