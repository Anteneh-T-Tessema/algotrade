import React, { useState, useEffect } from 'react';
import { Grid, Typography, Box, Paper, Card, CardContent, CardHeader, Button } from '@mui/material';
import {
  ArrowUpward as ArrowUpwardIcon,
  ArrowDownward as ArrowDownwardIcon,
  TrendingUp as TrendingUpIcon,
  AccessTime as AccessTimeIcon,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import TradingService from '../../services/TradingService';

// Component for statistics cards
const StatCard = ({ title, value, icon, color, subtitle, trending }) => {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={8}>
            <Typography variant="subtitle2" color="text.secondary">
              {title}
            </Typography>
            <Typography variant="h4" sx={{ my: 1, fontWeight: 500 }}>
              {value}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              {trending && trending !== 0 && (
                <Box 
                  component="span" 
                  sx={{ 
                    mr: 1, 
                    display: 'flex',
                    alignItems: 'center',
                    color: trending > 0 ? 'success.main' : 'error.main'
                  }}
                >
                  {trending > 0 ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />}
                  {Math.abs(trending)}%
                </Box>
              )}
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={4} sx={{ textAlign: 'right' }}>
            <Box 
              sx={{ 
                p: 1.5, 
                borderRadius: '50%', 
                display: 'inline-flex',
                bgcolor: `${color}.light`,
                color: `${color}.main`
              }}
            >
              {icon}
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

const Dashboard = () => {
  const [statistics, setStatistics] = useState({
    activeStrategies: 0,
    totalProfit: 0,
    profitTrending: 0,
    winRate: 0,
    totalTrades: 0,
  });

  const [performanceData, setPerformanceData] = useState([]);
  const [strategyPerformance, setStrategyPerformance] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setIsLoading(true);
        // In production, you would fetch data from your API
        // const data = await TradingService.getDashboardData();
        
        // For demonstration purposes, we'll use mock data
        setTimeout(() => {
          // Mock statistics
          setStatistics({
            activeStrategies: 3,
            totalProfit: '$1,258.32',
            profitTrending: 5.2,
            winRate: '67%',
            totalTrades: 34,
          });

          // Mock chart data
          const mockPerformanceData = [];
          const today = new Date();
          for (let i = 30; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(today.getDate() - i);
            mockPerformanceData.push({
              date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
              value: 1000 + Math.floor(Math.random() * 200) + (30 - i) * 10,
            });
          }
          setPerformanceData(mockPerformanceData);

          // Mock strategy performance
          setStrategyPerformance([
            { name: 'DCA Strategy', profit: 8.2, trades: 12 },
            { name: 'Grid Trading', profit: 5.4, trades: 67 },
            { name: 'Mean Reversion', profit: 3.8, trades: 24 },
          ]);

          setIsLoading(false);
        }, 1000);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1">
          Trading Dashboard
        </Typography>
        <Button variant="contained" color="primary" startIcon={<TrendingUpIcon />}>
          New Strategy
        </Button>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Strategies"
            value={statistics.activeStrategies}
            icon={<TrendingUpIcon />}
            color="primary"
            subtitle="Running"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Profit"
            value={statistics.totalProfit}
            icon={<TrendingUpIcon />}
            color="success"
            trending={statistics.profitTrending}
            subtitle="vs. last month"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Win Rate"
            value={statistics.winRate}
            icon={<TrendingUpIcon />}
            color="info"
            subtitle="From all trades"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Trades"
            value={statistics.totalTrades}
            icon={<AccessTimeIcon />}
            color="warning"
            subtitle="Last 30 days"
          />
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Portfolio Performance
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={performanceData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value) => [`$${value}`, 'Balance']}
                    labelFormatter={(label) => `Date: ${label}`}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#3f51b5"
                    activeDot={{ r: 8 }}
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Strategy Performance
            </Typography>
            <Box sx={{ mb: 2 }}>
              {strategyPerformance.map((strategy, index) => (
                <Box key={index} sx={{ mb: 2, pb: 2, borderBottom: index < strategyPerformance.length - 1 ? '1px solid #eee' : 'none' }}>
                  <Grid container alignItems="center" justifyContent="space-between">
                    <Grid item>
                      <Typography variant="body1">{strategy.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {strategy.trades} trades
                      </Typography>
                    </Grid>
                    <Grid item>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          color: strategy.profit > 0 ? 'success.main' : 'error.main',
                          fontWeight: 500
                        }}
                      >
                        {strategy.profit > 0 ? '+' : ''}{strategy.profit}%
                      </Typography>
                    </Grid>
                  </Grid>
                </Box>
              ))}
            </Box>
            <Box sx={{ mt: 2 }}>
              <Button fullWidth variant="outlined">View All Strategies</Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
