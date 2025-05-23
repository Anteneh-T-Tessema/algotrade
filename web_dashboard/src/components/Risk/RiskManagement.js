// RiskManagement.js - Main component for risk management features
import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Grid,
  Typography,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Tab,
  Tabs,
  Button,
  Slider,
  TextField,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Select,
  Switch,
  Divider,
  Tooltip,
  IconButton,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip
} from '@mui/material';
import {
  Warning,
  Error,
  CheckCircle,
  Info,
  TrendingUp,
  TrendingDown,
  Refresh,
  PlayArrow,
  Help,
  BarChart,
  Security,
  Settings,
  SwapVert,
  BubbleChart,
  Timeline
} from '@mui/icons-material';
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart as RechartsBarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Scatter,
  ScatterChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import RiskManagementService from '../../services/RiskManagementService';

const RiskManagement = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [riskDashboard, setRiskDashboard] = useState(null);
  const [riskProfile, setRiskProfile] = useState(null);
  const [riskExposure, setRiskExposure] = useState(null);
  const [riskAlerts, setRiskAlerts] = useState([]);
  const [exposurePeriod, setExposurePeriod] = useState('30d');
  const [stressTestScenarios, setStressTestScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [stressTestResults, setStressTestResults] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [customScenario, setCustomScenario] = useState({
    name: 'Custom Scenario',
    description: 'User-defined stress test',
    parameters: {
      marketDrop: 20,
      volatilityIncrease: 100,
      liquidityDecrease: 30,
      correlationChanges: 'increased'
    }
  });

  // Load initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch risk dashboard
        const dashboard = await RiskManagementService.getRiskDashboard();
        setRiskDashboard(dashboard);
        
        // Fetch risk profile
        const profile = await RiskManagementService.getRiskProfile();
        setRiskProfile(profile);
        
        // Fetch risk exposure
        const exposure = await RiskManagementService.getRiskExposure(exposurePeriod);
        setRiskExposure(exposure);
        
        // Fetch risk alerts
        const alerts = await RiskManagementService.getRiskAlerts();
        setRiskAlerts(alerts);
        
        // Fetch stress test scenarios
        const scenarios = await RiskManagementService.getStressTestScenarios();
        setStressTestScenarios(scenarios);
        if (scenarios.length > 0) {
          setSelectedScenario(scenarios[0].id);
        }
        
      } catch (err) {
        console.error('Failed to load risk management data:', err);
        setError(err.message || 'Failed to load risk management data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [exposurePeriod]);
  
  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  // Run stress test
  const runStressTest = async () => {
    try {
      setLoading(true);
      
      // Find selected scenario from the list
      const scenario = stressTestScenarios.find(s => s.id === selectedScenario) || customScenario;
      
      // Run the stress test
      const results = await RiskManagementService.runStressTest(scenario);
      setStressTestResults(results);
      
    } catch (err) {
      console.error('Failed to run stress test:', err);
      setError(err.message || 'Failed to run stress test');
    } finally {
      setLoading(false);
    }
  };
  
  // Handle risk profile updates
  const updateRiskProfile = async (updatedProfile) => {
    try {
      setLoading(true);
      
      const result = await RiskManagementService.updateRiskProfile(updatedProfile);
      setRiskProfile(result);
      
    } catch (err) {
      console.error('Failed to update risk profile:', err);
      setError(err.message || 'Failed to update risk profile');
    } finally {
      setLoading(false);
    }
  };
  
  // Format percentage
  const formatPercentage = (value) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
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
  
  // Get color based on risk level
  const getRiskColor = (level) => {
    if (level < 3) return 'success.main';
    if (level < 7) return 'warning.main';
    return 'error.main';
  };
  
  if (loading && !riskDashboard) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error && !riskDashboard) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }
  
  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Risk Management
      </Typography>
      
      {/* Risk Dashboard Summary */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={3}>
            <Card sx={{ height: '100%', bgcolor: riskDashboard?.overallRisk < 5 ? 'success.dark' : riskDashboard?.overallRisk < 8 ? 'warning.dark' : 'error.dark', color: 'white' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ opacity: 0.8 }}>
                  Overall Risk Score
                </Typography>
                <Typography variant="h3" sx={{ my: 1, fontWeight: 'bold' }}>
                  {riskDashboard?.overallRisk.toFixed(1)}/10
                </Typography>
                <Typography variant="body2">
                  {riskDashboard?.overallRisk < 5 ? 'Low Risk' : riskDashboard?.overallRisk < 8 ? 'Medium Risk' : 'High Risk'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="subtitle2" color="textSecondary">
                  Portfolio Value at Risk (VaR)
                </Typography>
                <Typography variant="h5" sx={{ my: 1, color: 'error.main' }}>
                  {formatCurrency(riskDashboard?.valueAtRisk)}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  95% confidence, 1-day horizon
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="subtitle2" color="textSecondary">
                  Margin Health
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', my: 1 }}>
                  <Box sx={{ width: '100%', mr: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={riskDashboard?.marginHealth}
                      color={
                        riskDashboard?.marginHealth > 80 ? 'success' :
                        riskDashboard?.marginHealth > 50 ? 'warning' : 'error'
                      }
                      sx={{ height: 10, borderRadius: 5 }}
                    />
                  </Box>
                  <Typography variant="body2" color="textSecondary">
                    {riskDashboard?.marginHealth}%
                  </Typography>
                </Box>
                <Typography variant="body2" color="textSecondary">
                  {riskDashboard?.marginHealthStatus}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Card sx={{ height: '100%', bgcolor: 'background.paper' }}>
              <CardContent>
                <Typography variant="subtitle2" color="textSecondary" sx={{ display: 'flex', alignItems: 'center' }}>
                  <Warning fontSize="small" color="warning" sx={{ mr: 1 }} />
                  Risk Alerts
                </Typography>
                <Typography variant="h5" sx={{ my: 1 }}>
                  {riskAlerts.length}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {riskAlerts.length > 0 ? `${riskAlerts.length} issue${riskAlerts.length > 1 ? 's' : ''} need${riskAlerts.length === 1 ? 's' : ''} attention` : 'No active alerts'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Tabs Navigation */}
      <Paper sx={{ mb: 3 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="risk management tabs">
            <Tab icon={<Security />} iconPosition="start" label="Risk Exposure" />
            <Tab icon={<Settings />} iconPosition="start" label="Risk Settings" />
            <Tab icon={<BubbleChart />} iconPosition="start" label="Stress Test" />
            <Tab icon={<BarChart />} iconPosition="start" label="Risk Analytics" />
          </Tabs>
        </Box>
        
        {/* Risk Exposure Tab */}
        {tabValue === 0 && (
          <Box p={3}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6">
                Risk Exposure
              </Typography>
              
              <Box>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => setExposurePeriod('1d')}
                  color={exposurePeriod === '1d' ? 'primary' : 'inherit'}
                  sx={{ mr: 1 }}
                >
                  1D
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => setExposurePeriod('7d')}
                  color={exposurePeriod === '7d' ? 'primary' : 'inherit'}
                  sx={{ mr: 1 }}
                >
                  1W
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => setExposurePeriod('30d')}
                  color={exposurePeriod === '30d' ? 'primary' : 'inherit'}
                  sx={{ mr: 1 }}
                >
                  1M
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => setExposurePeriod('all')}
                  color={exposurePeriod === 'all' ? 'primary' : 'inherit'}
                >
                  ALL
                </Button>
              </Box>
            </Box>
            
            {/* Asset Exposure Chart */}
            <Grid container spacing={3}>
              <Grid item xs={12} md={8}>
                <Typography variant="subtitle1" gutterBottom>
                  Asset Exposure Over Time
                </Typography>
                <Box sx={{ height: 400, mb: 3 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={riskExposure?.exposureOverTime || []}
                      margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <RechartsTooltip formatter={(value) => [`${value}%`, 'Exposure']} />
                      <Legend />
                      {riskExposure?.assets?.map((asset, idx) => (
                        <Area
                          key={asset.symbol}
                          type="monotone"
                          dataKey={asset.symbol}
                          stackId="1"
                          stroke={`hsl(${idx * 40}, 70%, 50%)`}
                          fill={`hsl(${idx * 40}, 70%, 50%)`}
                        />
                      ))}
                    </AreaChart>
                  </ResponsiveContainer>
                </Box>
                
                <Typography variant="subtitle1" gutterBottom>
                  Risk Metrics
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Metric</TableCell>
                        <TableCell align="right">Value</TableCell>
                        <TableCell align="right">Change</TableCell>
                        <TableCell align="right">Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {riskExposure?.riskMetrics?.map((metric) => (
                        <TableRow key={metric.name}>
                          <TableCell>
                            <Tooltip title={metric.description}>
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                {metric.name}
                                <Info fontSize="small" color="action" sx={{ ml: 0.5, fontSize: 16 }} />
                              </Box>
                            </Tooltip>
                          </TableCell>
                          <TableCell align="right">{metric.value}</TableCell>
                          <TableCell 
                            align="right"
                            sx={{ color: metric.change >= 0 ? 'success.main' : 'error.main' }}
                          >
                            {metric.change >= 0 ? '+' : ''}{metric.change}%
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              size="small"
                              label={metric.status}
                              color={
                                metric.status === 'Good' ? 'success' :
                                metric.status === 'Warning' ? 'warning' : 'error'
                              }
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
              
              <Grid item xs={12} md={4}>
                <Typography variant="subtitle1" gutterBottom>
                  Current Asset Allocation
                </Typography>
                <Box sx={{ height: 300, mb: 3 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={riskExposure?.currentAllocation}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({name, percent}) => `${name} (${(percent * 100).toFixed(0)}%)`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {riskExposure?.currentAllocation?.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={`hsl(${index * 40}, 70%, 50%)`} />
                        ))}
                      </Pie>
                      <RechartsTooltip formatter={(value, name) => [formatCurrency(value), name]} />
                    </PieChart>
                  </ResponsiveContainer>
                </Box>
                
                <Typography variant="subtitle1" gutterBottom>
                  Risk Alerts
                </Typography>
                <List dense={true} sx={{ bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                  {riskAlerts.length > 0 ? (
                    riskAlerts.map((alert) => (
                      <ListItem key={alert.id}>
                        <ListItemIcon>
                          {alert.severity === 'high' ? (
                            <Error color="error" />
                          ) : alert.severity === 'medium' ? (
                            <Warning color="warning" />
                          ) : (
                            <Info color="info" />
                          )}
                        </ListItemIcon>
                        <ListItemText
                          primary={alert.title}
                          secondary={alert.description}
                        />
                      </ListItem>
                    ))
                  ) : (
                    <ListItem>
                      <ListItemIcon>
                        <CheckCircle color="success" />
                      </ListItemIcon>
                      <ListItemText
                        primary="No Risk Alerts"
                        secondary="Your portfolio is currently within risk parameters"
                      />
                    </ListItem>
                  )}
                </List>
              </Grid>
            </Grid>
          </Box>
        )}
        
        {/* Risk Settings Tab */}
        {tabValue === 1 && (
          <Box p={3}>
            <Typography variant="h6" gutterBottom>
              Risk Profile Settings
            </Typography>
            
            <Grid container spacing={4}>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      Risk Tolerance
                    </Typography>
                    
                    <Box sx={{ mb: 4 }}>
                      <Typography variant="body2" gutterBottom>
                        Maximum portfolio drawdown you're willing to accept
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <Typography variant="body2" color="textSecondary">Low Risk</Typography>
                        <Box sx={{ flexGrow: 1, mx: 2 }}>
                          <Slider
                            value={riskProfile?.maxDrawdown || 0}
                            min={5}
                            max={50}
                            step={5}
                            marks
                            valueLabelDisplay="auto"
                            valueLabelFormat={(value) => `${value}%`}
                            onChange={(e, value) => setRiskProfile({ ...riskProfile, maxDrawdown: value })}
                            onChangeCommitted={(e, value) => updateRiskProfile({ ...riskProfile, maxDrawdown: value })}
                          />
                        </Box>
                        <Typography variant="body2" color="textSecondary">High Risk</Typography>
                      </Box>
                      <Typography variant="caption" color="textSecondary">
                        Current setting: Maximum {riskProfile?.maxDrawdown}% drawdown
                      </Typography>
                    </Box>
                    
                    <Typography variant="subtitle1" gutterBottom>
                      Position Size Limits
                    </Typography>
                    
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="body2" gutterBottom>
                        Maximum percentage of portfolio in a single position
                      </Typography>
                      <TextField
                        type="number"
                        size="small"
                        label="Max Position Size (%)"
                        value={riskProfile?.maxPositionSize || 0}
                        onChange={(e) => setRiskProfile({ ...riskProfile, maxPositionSize: Number(e.target.value) })}
                        onBlur={() => updateRiskProfile(riskProfile)}
                        InputProps={{ endAdornment: <InputLabel>%</InputLabel> }}
                        sx={{ width: 200 }}
                      />
                    </Box>
                    
                    <Typography variant="subtitle1" gutterBottom>
                      Stop Loss Settings
                    </Typography>
                    
                    <Box sx={{ mb: 3 }}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={riskProfile?.autoStopLoss || false}
                            onChange={(e) => {
                              const updated = { ...riskProfile, autoStopLoss: e.target.checked };
                              setRiskProfile(updated);
                              updateRiskProfile(updated);
                            }}
                          />
                        }
                        label="Automatic Stop Loss"
                      />
                      <Typography variant="caption" color="textSecondary" display="block">
                        Automatically set stop loss for all positions
                      </Typography>
                      
                      <TextField
                        type="number"
                        size="small"
                        label="Default Stop Loss (%)"
                        value={riskProfile?.defaultStopLoss || 0}
                        onChange={(e) => setRiskProfile({ ...riskProfile, defaultStopLoss: Number(e.target.value) })}
                        onBlur={() => updateRiskProfile(riskProfile)}
                        disabled={!riskProfile?.autoStopLoss}
                        InputProps={{ endAdornment: <InputLabel>%</InputLabel> }}
                        sx={{ mt: 2, width: 200 }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      Risk Limits
                    </Typography>
                    
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="body2" gutterBottom>
                        Maximum daily loss limit
                      </Typography>
                      <TextField
                        type="number"
                        size="small"
                        label="Daily Loss Limit"
                        value={riskProfile?.dailyLossLimit || 0}
                        onChange={(e) => setRiskProfile({ ...riskProfile, dailyLossLimit: Number(e.target.value) })}
                        onBlur={() => updateRiskProfile(riskProfile)}
                        InputProps={{ startAdornment: <InputLabel>$</InputLabel> }}
                        sx={{ width: 200 }}
                      />
                    </Box>
                    
                    <Box sx={{ mb: 4 }}>
                      <Typography variant="body2" gutterBottom>
                        Weekly loss limit as percentage of portfolio
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <Box sx={{ width: '100%', mr: 1 }}>
                          <Slider
                            value={riskProfile?.weeklyLossLimitPercent || 0}
                            min={1}
                            max={25}
                            step={1}
                            valueLabelDisplay="auto"
                            valueLabelFormat={(value) => `${value}%`}
                            onChange={(e, value) => setRiskProfile({ ...riskProfile, weeklyLossLimitPercent: value })}
                            onChangeCommitted={(e, value) => updateRiskProfile({ ...riskProfile, weeklyLossLimitPercent: value })}
                          />
                        </Box>
                        <Typography variant="body2" color="textSecondary">
                          {riskProfile?.weeklyLossLimitPercent || 0}%
                        </Typography>
                      </Box>
                    </Box>
                    
                    <Typography variant="subtitle1" gutterBottom>
                      Leverage Settings
                    </Typography>
                    
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="body2" gutterBottom>
                        Maximum leverage allowed
                      </Typography>
                      <FormControl size="small" sx={{ width: 200 }}>
                        <InputLabel>Max Leverage</InputLabel>
                        <Select
                          value={riskProfile?.maxLeverage || 1}
                          label="Max Leverage"
                          onChange={(e) => {
                            const updated = { ...riskProfile, maxLeverage: e.target.value };
                            setRiskProfile(updated);
                            updateRiskProfile(updated);
                          }}
                        >
                          <MenuItem value={1}>1x (No Leverage)</MenuItem>
                          <MenuItem value={2}>2x</MenuItem>
                          <MenuItem value={3}>3x</MenuItem>
                          <MenuItem value={5}>5x</MenuItem>
                          <MenuItem value={10}>10x</MenuItem>
                          <MenuItem value={20}>20x</MenuItem>
                        </Select>
                      </FormControl>
                    </Box>
                    
                    <Typography variant="subtitle1" gutterBottom>
                      Risk Notifications
                    </Typography>
                    
                    <Box>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={riskProfile?.riskNotifications?.email || false}
                            onChange={(e) => {
                              const updated = {
                                ...riskProfile,
                                riskNotifications: {
                                  ...riskProfile.riskNotifications,
                                  email: e.target.checked
                                }
                              };
                              setRiskProfile(updated);
                              updateRiskProfile(updated);
                            }}
                          />
                        }
                        label="Email Alerts"
                      />
                      
                      <FormControlLabel
                        control={
                          <Switch
                            checked={riskProfile?.riskNotifications?.push || false}
                            onChange={(e) => {
                              const updated = {
                                ...riskProfile,
                                riskNotifications: {
                                  ...riskProfile.riskNotifications,
                                  push: e.target.checked
                                }
                              };
                              setRiskProfile(updated);
                              updateRiskProfile(updated);
                            }}
                          />
                        }
                        label="Push Notifications"
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}
        
        {/* Stress Test Tab */}
        {tabValue === 2 && (
          <Box p={3}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6">
                Portfolio Stress Testing
              </Typography>
              
              <Box>
                <Button
                  variant="outlined"
                  startIcon={<BubbleChart />}
                  onClick={() => setDialogOpen(true)}
                  sx={{ mr: 1 }}
                >
                  Custom Scenario
                </Button>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<PlayArrow />}
                  onClick={runStressTest}
                >
                  Run Test
                </Button>
              </Box>
            </Box>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Typography variant="subtitle1" gutterBottom>
                  Choose Scenario
                </Typography>
                
                <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel id="scenario-select-label">Stress Test Scenario</InputLabel>
                    <Select
                      labelId="scenario-select-label"
                      id="scenario-select"
                      value={selectedScenario || ''}
                      label="Stress Test Scenario"
                      onChange={(e) => setSelectedScenario(e.target.value)}
                    >
                      {stressTestScenarios.map((scenario) => (
                        <MenuItem key={scenario.id} value={scenario.id}>
                          {scenario.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  
                  {selectedScenario && (
                    <Box>
                      <Typography variant="body2" gutterBottom>
                        {stressTestScenarios.find(s => s.id === selectedScenario)?.description}
                      </Typography>
                      
                      <List dense>
                        {Object.entries(stressTestScenarios.find(s => s.id === selectedScenario)?.parameters || {}).map(([key, value]) => (
                          <ListItem key={key}>
                            <ListItemText
                              primary={key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                              secondary={typeof value === 'string' ? value : `${value}%`}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  )}
                </Paper>
                
                <Typography variant="subtitle1" gutterBottom>
                  Historical Scenarios
                </Typography>
                
                <List dense sx={{ bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                  {stressTestScenarios
                    .filter(s => s.type === 'historical')
                    .map((scenario) => (
                    <ListItem 
                      key={scenario.id} 
                      button
                      selected={selectedScenario === scenario.id}
                      onClick={() => setSelectedScenario(scenario.id)}
                    >
                      <ListItemText
                        primary={scenario.name}
                        secondary={scenario.description}
                      />
                    </ListItem>
                  ))}
                </List>
              </Grid>
              
              <Grid item xs={12} md={8}>
                <Typography variant="subtitle1" gutterBottom>
                  Stress Test Results
                </Typography>
                
                {stressTestResults ? (
                  <Box>
                    <Alert 
                      severity={
                        stressTestResults.portfolioImpact < 10 ? 'success' : 
                        stressTestResults.portfolioImpact < 25 ? 'warning' : 'error'
                      }
                      sx={{ mb: 2 }}
                    >
                      <AlertTitle>Impact Assessment</AlertTitle>
                      This scenario would result in a {stressTestResults.portfolioImpact.toFixed(2)}% loss to your portfolio
                    </Alert>
                    
                    <Grid container spacing={2} sx={{ mb: 3 }}>
                      <Grid item xs={12} sm={4}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography variant="subtitle2" color="textSecondary">
                              Portfolio Value After Stress
                            </Typography>
                            <Typography variant="h6" color="error">
                              {formatCurrency(stressTestResults.valueAfterTest)}
                            </Typography>
                            <Typography variant="body2" color="error">
                              {formatCurrency(stressTestResults.lossDollar)} loss
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      
                      <Grid item xs={12} sm={4}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography variant="subtitle2" color="textSecondary">
                              Drawdown
                            </Typography>
                            <Typography variant="h6" color="error">
                              {stressTestResults.maxDrawdown.toFixed(2)}%
                            </Typography>
                            <Typography variant="body2" color={stressTestResults.exceedsRiskTolerance ? 'error' : 'textSecondary'}>
                              {stressTestResults.exceedsRiskTolerance ? 'Exceeds risk tolerance' : 'Within risk tolerance'}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      
                      <Grid item xs={12} sm={4}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography variant="subtitle2" color="textSecondary">
                              Recovery Time (Est.)
                            </Typography>
                            <Typography variant="h6">
                              {stressTestResults.recoveryTimeMonths} months
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              Based on historical data
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>
                    
                    <Typography variant="subtitle2" gutterBottom>
                      Asset Impact Analysis
                    </Typography>
                    
                    <TableContainer sx={{ mb: 3 }}>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Asset</TableCell>
                            <TableCell align="right">Current Value</TableCell>
                            <TableCell align="right">Stressed Value</TableCell>
                            <TableCell align="right">Change</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {stressTestResults.assetImpacts.map((asset) => (
                            <TableRow key={asset.symbol}>
                              <TableCell>{asset.name} ({asset.symbol})</TableCell>
                              <TableCell align="right">{formatCurrency(asset.currentValue)}</TableCell>
                              <TableCell align="right">{formatCurrency(asset.stressedValue)}</TableCell>
                              <TableCell 
                                align="right"
                                sx={{ color: 'error.main' }}
                              >
                                {formatPercentage(asset.percentChange)}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                    
                    <Typography variant="subtitle2" gutterBottom>
                      Recommendations
                    </Typography>
                    
                    <List>
                      {stressTestResults.recommendations.map((rec, idx) => (
                        <ListItem key={idx}>
                          <ListItemIcon>
                            {rec.type === 'warning' ? (
                              <Warning color="warning" />
                            ) : rec.type === 'danger' ? (
                              <Error color="error" />
                            ) : (
                              <Info color="info" />
                            )}
                          </ListItemIcon>
                          <ListItemText
                            primary={rec.title}
                            secondary={rec.description}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                ) : (
                  <Box sx={{ 
                    height: 400, 
                    bgcolor: 'action.hover', 
                    borderRadius: 1,
                    display: 'flex', 
                    flexDirection: 'column',
                    alignItems: 'center', 
                    justifyContent: 'center',
                    textAlign: 'center',
                    p: 3
                  }}>
                    <BubbleChart sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="textSecondary" gutterBottom>
                      No Stress Test Results Yet
                    </Typography>
                    <Typography variant="body2" color="textSecondary" sx={{ maxWidth: 400, mb: 3 }}>
                      Select a scenario and run the stress test to see how your portfolio would perform under different market conditions
                    </Typography>
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<PlayArrow />}
                      onClick={runStressTest}
                    >
                      Run Stress Test
                    </Button>
                  </Box>
                )}
              </Grid>
            </Grid>
          </Box>
        )}
        
        {/* Risk Analytics Tab */}
        {tabValue === 3 && (
          <Box p={3}>
            <Typography variant="h6" gutterBottom>
              Advanced Risk Analytics
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" gutterBottom>
                  Value at Risk (VaR) Analysis
                </Typography>
                
                <Box sx={{ height: 300, mb: 3 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={riskDashboard?.varAnalysis || []}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="confidenceLevel" />
                      <YAxis tickFormatter={(value) => `$${value.toLocaleString()}`} />
                      <RechartsTooltip formatter={(value) => [formatCurrency(value), 'Value at Risk']} />
                      <Bar dataKey="var" fill="#8884d8" name="Value at Risk" />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
                
                <Typography variant="subtitle1" gutterBottom>
                  Risk Contribution by Asset
                </Typography>
                
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Asset</TableCell>
                        <TableCell align="right">Allocation</TableCell>
                        <TableCell align="right">Risk Contribution</TableCell>
                        <TableCell align="right">Risk/Reward</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {riskDashboard?.riskContribution?.map((asset) => (
                        <TableRow key={asset.symbol}>
                          <TableCell>{asset.name} ({asset.symbol})</TableCell>
                          <TableCell align="right">{asset.allocation}%</TableCell>
                          <TableCell align="right">{asset.riskContribution}%</TableCell>
                          <TableCell align="right">
                            <Chip
                              size="small"
                              label={asset.riskRewardRatio.toFixed(2)}
                              color={
                                asset.riskRewardRatio > 1.5 ? 'success' :
                                asset.riskRewardRatio > 0.8 ? 'warning' : 'error'
                              }
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" gutterBottom>
                  Correlation Matrix
                </Typography>
                
                <Box sx={{ height: 300, mb: 3 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart
                      margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
                    >
                      <CartesianGrid />
                      <XAxis type="number" dataKey="x" name="volatility" unit="%" />
                      <YAxis type="number" dataKey="y" name="return" unit="%" />
                      <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} />
                      <Scatter name="Assets" data={riskDashboard?.riskReturnScatter || []} fill="#8884d8">
                        {(riskDashboard?.riskReturnScatter || []).map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color || '#8884d8'} />
                        ))}
                      </Scatter>
                    </ScatterChart>
                  </ResponsiveContainer>
                </Box>
                
                <Typography variant="subtitle1" gutterBottom>
                  Risk Factor Exposure
                </Typography>
                
                <Box sx={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart outerRadius={90} data={riskDashboard?.riskFactors || []}>
                      <PolarGrid />
                      <PolarAngleAxis dataKey="factor" />
                      <PolarRadiusAxis angle={30} domain={[0, 10]} />
                      <Radar name="Portfolio" dataKey="score" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
                      <Radar name="Benchmark" dataKey="benchmark" stroke="#82ca9d" fill="#82ca9d" fillOpacity={0.6} />
                      <Legend />
                    </RadarChart>
                  </ResponsiveContainer>
                </Box>
              </Grid>
            </Grid>
          </Box>
        )}
      </Paper>
      
      {/* Custom Scenario Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Custom Stress Test Scenario</DialogTitle>
        <DialogContent>
          <Typography variant="subtitle2" gutterBottom sx={{ mt: 1 }}>
            Scenario Name
          </Typography>
          <TextField
            fullWidth
            size="small"
            value={customScenario.name}
            onChange={(e) => setCustomScenario({ ...customScenario, name: e.target.value })}
            sx={{ mb: 3 }}
          />
          
          <Typography variant="subtitle2" gutterBottom>
            Market Drop Percentage
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <Slider
              value={customScenario.parameters.marketDrop}
              min={5}
              max={90}
              step={5}
              valueLabelDisplay="auto"
              valueLabelFormat={(value) => `${value}%`}
              onChange={(e, value) => setCustomScenario({
                ...customScenario,
                parameters: { ...customScenario.parameters, marketDrop: value }
              })}
              sx={{ flexGrow: 1, mr: 2 }}
            />
            <Typography variant="body2">
              {customScenario.parameters.marketDrop}%
            </Typography>
          </Box>
          
          <Typography variant="subtitle2" gutterBottom>
            Volatility Increase
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <Slider
              value={customScenario.parameters.volatilityIncrease}
              min={0}
              max={300}
              step={25}
              valueLabelDisplay="auto"
              valueLabelFormat={(value) => `${value}%`}
              onChange={(e, value) => setCustomScenario({
                ...customScenario,
                parameters: { ...customScenario.parameters, volatilityIncrease: value }
              })}
              sx={{ flexGrow: 1, mr: 2 }}
            />
            <Typography variant="body2">
              {customScenario.parameters.volatilityIncrease}%
            </Typography>
          </Box>
          
          <Typography variant="subtitle2" gutterBottom>
            Liquidity Decrease
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <Slider
              value={customScenario.parameters.liquidityDecrease}
              min={0}
              max={100}
              step={10}
              valueLabelDisplay="auto"
              valueLabelFormat={(value) => `${value}%`}
              onChange={(e, value) => setCustomScenario({
                ...customScenario,
                parameters: { ...customScenario.parameters, liquidityDecrease: value }
              })}
              sx={{ flexGrow: 1, mr: 2 }}
            />
            <Typography variant="body2">
              {customScenario.parameters.liquidityDecrease}%
            </Typography>
          </Box>
          
          <Typography variant="subtitle2" gutterBottom>
            Correlation Changes
          </Typography>
          <FormControl fullWidth size="small" sx={{ mb: 2 }}>
            <InputLabel>Correlation Changes</InputLabel>
            <Select
              value={customScenario.parameters.correlationChanges}
              label="Correlation Changes"
              onChange={(e) => setCustomScenario({
                ...customScenario,
                parameters: { ...customScenario.parameters, correlationChanges: e.target.value }
              })}
            >
              <MenuItem value="increased">Increased (Assets move together)</MenuItem>
              <MenuItem value="decreased">Decreased (Assets move independently)</MenuItem>
              <MenuItem value="mixed">Mixed (Some correlations increase, others decrease)</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => {
              setDialogOpen(false);
              setSelectedScenario(null);  // Deselect any predefined scenario
              setTimeout(() => runStressTest(), 100);  // Run with custom scenario
            }}
          >
            Create & Run Test
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RiskManagement;
