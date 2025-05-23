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
  CircularProgress,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Card,
  CardContent,
  Divider,
  Chip,
  TextField,
  InputAdornment,
  IconButton,
  Tooltip,
  Tab,
  Tabs,
} from '@mui/material';
import {
  ArrowUpward as ArrowUpwardIcon,
  ArrowDownward as ArrowDownwardIcon,
  Search as SearchIcon,
  CalendarToday as CalendarIcon,
  FilterList as FilterListIcon,
  Download as DownloadIcon,
  Print as PrintIcon,
  Share as ShareIcon,
} from '@mui/icons-material';
import { 
  ComposedChart, 
  Line, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Sector,
} from 'recharts';
import TradingService from '../../services/TradingService';

// Colors for the pie chart
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

// Component to render active pie sector
const renderActiveShape = (props) => {
  const {
    cx, cy, innerRadius, outerRadius, startAngle, endAngle,
    fill, payload, percent, value
  } = props;

  return (
    <g>
      <text x={cx} y={cy} dy={-4} textAnchor="middle" fill="#333">
        {payload.name}
      </text>
      <text x={cx} y={cy} dy={20} textAnchor="middle" fill="#999">
        {`$${value.toFixed(2)} (${(percent * 100).toFixed(0)}%)`}
      </text>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
      />
      <Sector
        cx={cx}
        cy={cy}
        startAngle={startAngle}
        endAngle={endAngle}
        innerRadius={outerRadius + 6}
        outerRadius={outerRadius + 10}
        fill={fill}
      />
    </g>
  );
};

const CommissionTracker = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [period, setPeriod] = useState('month'); // day, week, month, year, custom
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [commissionData, setCommissionData] = useState({
    summary: {
      totalEarned: 0,
      pendingPayout: 0,
      totalPaid: 0,
      activeLayers: 0,
      totalDownlines: 0,
      activeDownlines: 0,
    },
    byTier: [],
    bySource: [],
    recentPayouts: [],
    trends: []
  });
  const [activeTab, setActiveTab] = useState(0);
  const [activePieIndex, setActivePieIndex] = useState(0);
  const [referralCode, setReferralCode] = useState('');
  const [referralLink, setReferralLink] = useState('');

  useEffect(() => {
    // Generate example referral code and link
    const code = 'REF' + Math.random().toString(36).substring(2, 8).toUpperCase();
    setReferralCode(code);
    setReferralLink(`https://crypto-platform.com/register?ref=${code}`);
    
    fetchCommissionData();
  }, []);

  const fetchCommissionData = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      // In a real app, you would get the date range from the period
      let dateRange = {};
      if (period === 'custom' && startDate && endDate) {
        dateRange = { startDate, endDate };
      }
      
      // Call API to get commission data
      const data = await TradingService.getDistributorCommissions(period, dateRange);
      setCommissionData(data || getMockCommissionData());
      
    } catch (err) {
      console.error("Failed to fetch commission data:", err);
      setError(err.message || 'Failed to load commission data');
      
      // Use mock data for demo
      setCommissionData(getMockCommissionData());
    } finally {
      setIsLoading(false);
    }
  };
  
  // Generate mock data for development
  const getMockCommissionData = () => {
    // Generate some random data for the demo
    const mockTrends = [];
    const today = new Date();
    for (let i = 30; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      mockTrends.push({
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        directCommission: Math.random() * 20 + 5,
        networkCommission: Math.random() * 30 + 10,
      });
    }
    
    return {
      summary: {
        totalEarned: 2483.56,
        pendingPayout: 847.29,
        totalPaid: 1636.27,
        activeLayers: 3,
        totalDownlines: 27,
        activeDownlines: 18,
      },
      byTier: [
        { name: 'Direct (Level 1)', value: 1203.45, commission: '10%', active: 12 },
        { name: 'Level 2', value: 825.67, commission: '5%', active: 8 },
        { name: 'Level 3', value: 454.44, commission: '2%', active: 7 },
      ],
      bySource: [
        { name: 'Trading Fees', value: 1350.23 },
        { name: 'Subscription Fees', value: 600.00 },
        { name: 'Strategy Sales', value: 422.45 },
        { name: 'Other', value: 110.88 },
      ],
      recentPayouts: [
        { id: 'PMT78956', date: '2023-05-15', amount: 532.45, status: 'completed', method: 'Bitcoin' },
        { id: 'PMT78845', date: '2023-04-14', amount: 489.32, status: 'completed', method: 'Bank Transfer' },
        { id: 'PMT78654', date: '2023-03-15', amount: 614.50, status: 'completed', method: 'Bitcoin' },
      ],
      trends: mockTrends
    };
  };
  
  const handlePeriodChange = (event) => {
    setPeriod(event.target.value);
    // In a real app, you would fetch data based on the new period
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // In a real app, you would show a notification
  };
  
  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
        <Typography variant="h4" component="h1">
          Commission Tracker
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: { xs: 2, sm: 0 } }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Period</InputLabel>
            <Select
              value={period}
              label="Period"
              onChange={handlePeriodChange}
            >
              <MenuItem value="day">Today</MenuItem>
              <MenuItem value="week">This Week</MenuItem>
              <MenuItem value="month">This Month</MenuItem>
              <MenuItem value="year">This Year</MenuItem>
              <MenuItem value="all">All Time</MenuItem>
              <MenuItem value="custom">Custom Range</MenuItem>
            </Select>
          </FormControl>
          
          {period === 'custom' && (
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                label="Start Date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                InputLabelProps={{
                  shrink: true,
                }}
                size="small"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <CalendarIcon fontSize="small" />
                    </InputAdornment>
                  ),
                }}
              />
              <TextField
                label="End Date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                InputLabelProps={{
                  shrink: true,
                }}
                size="small"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <CalendarIcon fontSize="small" />
                    </InputAdornment>
                  ),
                }}
              />
            </Box>
          )}
          
          <Button 
            variant="outlined" 
            startIcon={<DownloadIcon />}
            size="small"
          >
            Export
          </Button>
        </Box>
      </Box>

      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="div" sx={{ fontWeight: 500 }}>
                ${commissionData.summary.totalEarned.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Total Commissions Earned
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Pending:
                  </Typography>
                  <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                    ${commissionData.summary.pendingPayout.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </Typography>
                </Box>
                <Chip label="View Details" size="small" variant="outlined" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="div" sx={{ fontWeight: 500 }}>
                {commissionData.summary.activeDownlines}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Active Downlines
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Total:
                  </Typography>
                  <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                    {commissionData.summary.totalDownlines}
                  </Typography>
                </Box>
                <Chip label="View Network" size="small" variant="outlined" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="div" sx={{ fontWeight: 500 }}>
                {commissionData.summary.activeLayers}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Active Tiers
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Commission Structure:
                  </Typography>
                </Box>
                <Chip label="View Rates" size="small" variant="outlined" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Your Referral Link
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TextField
                  size="small"
                  fullWidth
                  value={referralLink}
                  InputProps={{
                    readOnly: true,
                    endAdornment: (
                      <InputAdornment position="end">
                        <Tooltip title="Copy to clipboard">
                          <IconButton edge="end" onClick={() => copyToClipboard(referralLink)}>
                            <ContentCopyIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </InputAdornment>
                    ),
                  }}
                  variant="outlined"
                />
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="caption" color="text.secondary">
                  Code: <strong>{referralCode}</strong>
                </Typography>
                <Button size="small">Share</Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mb: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={(_, newValue) => setActiveTab(newValue)}
          variant="fullWidth"
        >
          <Tab 
            label="Overview" 
            icon={<PieChartIcon />} 
            iconPosition="start" 
          />
          <Tab 
            label="Commission Details" 
            icon={<TrendingUpIcon />} 
            iconPosition="start" 
          />
          <Tab 
            label="Network" 
            icon={<AccountTreeIcon />} 
            iconPosition="start" 
          />
        </Tabs>
      </Box>

      {activeTab === 0 && (
        <>
          {/* Overview Tab */}
          <Grid container spacing={3}>
            {/* Commission Distribution Pie Chart */}
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  Commission by Source
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Box sx={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        activeIndex={activePieIndex}
                        activeShape={renderActiveShape}
                        data={commissionData.bySource}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                        onMouseEnter={(_, index) => setActivePieIndex(index)}
                      >
                        {commissionData.bySource.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </Box>
              </Paper>
            </Grid>

            {/* Commission Trends */}
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  Commission Trends
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Box sx={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart
                      data={commissionData.trends}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="date" 
                        scale="auto" 
                        tick={{ fontSize: 12 }} 
                        tickFormatter={(val) => val.substring(0, 3)}
                      />
                      <YAxis />
                      <RechartsTooltip />
                      <Legend />
                      <Bar 
                        dataKey="directCommission" 
                        name="Direct Commission" 
                        fill="#8884d8" 
                        barSize={20} 
                      />
                      <Line 
                        type="monotone" 
                        dataKey="networkCommission" 
                        name="Network Commission" 
                        stroke="#ff7300" 
                        strokeWidth={2} 
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </Box>
              </Paper>
            </Grid>

            {/* Recent Payouts */}
            <Grid item xs={12}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Recent Payouts
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>ID</TableCell>
                        <TableCell>Date</TableCell>
                        <TableCell align="right">Amount</TableCell>
                        <TableCell>Method</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {commissionData.recentPayouts.map((payout) => (
                        <TableRow key={payout.id}>
                          <TableCell>{payout.id}</TableCell>
                          <TableCell>{new Date(payout.date).toLocaleDateString()}</TableCell>
                          <TableCell align="right">
                            ${payout.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </TableCell>
                          <TableCell>{payout.method}</TableCell>
                          <TableCell>
                            <Chip 
                              label={payout.status} 
                              size="small" 
                              color={payout.status === 'completed' ? 'success' : 'warning'} 
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                {commissionData.recentPayouts.length === 0 && (
                  <Box sx={{ py: 3, textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      No recent payouts found
                    </Typography>
                  </Box>
                )}
              </Paper>
            </Grid>
          </Grid>
        </>
      )}

      {activeTab === 1 && (
        <>
          {/* Commission Details Tab */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Commission by Tier
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Tier Level</TableCell>
                    <TableCell align="right">Commission Rate</TableCell>
                    <TableCell align="right">Active Members</TableCell>
                    <TableCell align="right">Earnings</TableCell>
                    <TableCell align="right">% of Total</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {commissionData.byTier.map((tier) => (
                    <TableRow key={tier.name}>
                      <TableCell>{tier.name}</TableCell>
                      <TableCell align="right">{tier.commission}</TableCell>
                      <TableCell align="right">{tier.active}</TableCell>
                      <TableCell align="right">
                        ${tier.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </TableCell>
                      <TableCell align="right">
                        {((tier.value / commissionData.summary.totalEarned) * 100).toFixed(1)}%
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow>
                    <TableCell colSpan={3} sx={{ fontWeight: 'bold' }}>Total</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                      ${commissionData.summary.totalEarned.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                      100%
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Commission Structure
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                How You Earn
              </Typography>
              <Typography variant="body2" paragraph>
                As a distributor in our multi-tier system, you earn commissions from the activities of your direct referrals and their downlines, down to 3 levels deep.
              </Typography>
            </Box>
            
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={12} sm={4}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography variant="h5" color="primary" gutterBottom>
                      10%
                    </Typography>
                    <Typography variant="subtitle1" gutterBottom>
                      Level 1 (Direct)
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Earn 10% commission on all trading fees, subscriptions, and strategy purchases from your direct referrals.
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} sm={4}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography variant="h5" color="primary" gutterBottom>
                      5%
                    </Typography>
                    <Typography variant="subtitle1" gutterBottom>
                      Level 2
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Earn 5% commission on all trading fees, subscriptions, and strategy purchases from your level 2 downlines.
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} sm={4}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography variant="h5" color="primary" gutterBottom>
                      2%
                    </Typography>
                    <Typography variant="subtitle1" gutterBottom>
                      Level 3
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Earn 2% commission on all trading fees, subscriptions, and strategy purchases from your level 3 downlines.
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
            
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Commission Rules
              </Typography>
              <Typography variant="body2" paragraph>
                • Commissions are calculated and accumulated daily.
              </Typography>
              <Typography variant="body2" paragraph>
                • Payouts are processed once your balance reaches the minimum threshold of $50.
              </Typography>
              <Typography variant="body2" paragraph>
                • You must maintain active status by having at least 1 direct referral who is actively trading.
              </Typography>
              <Typography variant="body2">
                • Commissions are paid in USDT or can be converted to your preferred cryptocurrency.
              </Typography>
            </Box>
          </Paper>
        </>
      )}

      {activeTab === 2 && (
        <>
          {/* Network Tab */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Your Distributor Network
              </Typography>
              
              <Box>
                <Button 
                  variant="outlined" 
                  startIcon={<PeopleIcon />}
                  size="small"
                >
                  View Network Graph
                </Button>
              </Box>
            </Box>
            
            <Divider sx={{ mb: 2 }} />
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" paragraph>
                Your distributor network consists of {commissionData.summary.totalDownlines} members across {commissionData.summary.activeLayers} tiers. {commissionData.summary.activeDownlines} members are currently active.
              </Typography>
            </Box>
            
            <Box sx={{ mb: 2 }}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search members..."
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  ),
                }}
              />
            </Box>
            
            <TableContainer sx={{ maxHeight: 400 }}>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>Member</TableCell>
                    <TableCell>Level</TableCell>
                    <TableCell>Joined</TableCell>
                    <TableCell align="right">Trading Volume</TableCell>
                    <TableCell align="right">Commission Generated</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {/* This would be populated with real data from your API */}
                  {[
                    { 
                      id: 1, 
                      name: 'John Smith', 
                      email: 'john@example.com',
                      level: 'Level 1',
                      joinDate: '2023-01-15',
                      tradingVolume: 24500,
                      commission: 245.00,
                      status: 'active'
                    },
                    { 
                      id: 2, 
                      name: 'Sarah Johnson', 
                      email: 'sarah@example.com',
                      level: 'Level 1',
                      joinDate: '2023-02-10',
                      tradingVolume: 18750,
                      commission: 187.50,
                      status: 'active'
                    },
                    { 
                      id: 3, 
                      name: 'Mike Peterson', 
                      email: 'mike@example.com',
                      level: 'Level 2',
                      joinDate: '2023-02-20',
                      tradingVolume: 9300,
                      commission: 46.50,
                      status: 'active'
                    },
                    { 
                      id: 4, 
                      name: 'Jessica Lee', 
                      email: 'jessica@example.com',
                      level: 'Level 2',
                      joinDate: '2023-03-05',
                      tradingVolume: 5100,
                      commission: 25.50,
                      status: 'inactive'
                    },
                    { 
                      id: 5, 
                      name: 'David Wilson', 
                      email: 'david@example.com',
                      level: 'Level 3',
                      joinDate: '2023-03-15',
                      tradingVolume: 3200,
                      commission: 6.40,
                      status: 'active'
                    }
                  ].map((member) => (
                    <TableRow key={member.id} hover>
                      <TableCell>
                        <Typography variant="body2">{member.name}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {member.email}
                        </Typography>
                      </TableCell>
                      <TableCell>{member.level}</TableCell>
                      <TableCell>{new Date(member.joinDate).toLocaleDateString()}</TableCell>
                      <TableCell align="right">
                        ${member.tradingVolume.toLocaleString()}
                      </TableCell>
                      <TableCell align="right">
                        ${member.commission.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={member.status} 
                          size="small" 
                          color={member.status === 'active' ? 'success' : 'default'} 
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </>
      )}

    </Box>
  );
};

export default CommissionTracker;
