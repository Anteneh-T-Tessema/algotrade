import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Alert,
  Card,
  CardContent,
  CardActions,
  Switch,
  FormControlLabel,
  Chip,
  CircularProgress,
  Divider
} from '@mui/material';
import { 
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import ExchangeService from '../../services/ExchangeService';

const Exchanges = () => {
  const [exchanges, setExchanges] = useState([]);
  const [supportedExchanges, setSupportedExchanges] = useState([]);
  const [selectedExchange, setSelectedExchange] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    exchangeName: '',
    apiKey: '',
    apiSecret: '',
    label: '',
    permissions: []
  });

  // Fetch exchanges on component mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [userExchanges, supported] = await Promise.all([
          ExchangeService.getUserExchanges(),
          ExchangeService.getAllSupportedExchanges()
        ]);
        setExchanges(userExchanges || []);
        setSupportedExchanges(supported || []);
      } catch (err) {
        setError(err.message || 'Failed to load exchanges');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  const handleDialogOpen = (exchange = null) => {
    if (exchange) {
      // Edit mode
      setIsEditing(true);
      setSelectedExchange(exchange);
      setFormData({
        exchangeName: exchange.exchangeName,
        apiKey: '••••••••••••••••••••••••••',
        apiSecret: '••••••••••••••••••••••••••',
        label: exchange.label,
        permissions: exchange.permissions
      });
    } else {
      // Add mode
      setIsEditing(false);
      setSelectedExchange(null);
      setFormData({
        exchangeName: supportedExchanges.length > 0 ? supportedExchanges[0].name : '',
        apiKey: '',
        apiSecret: '',
        label: '',
        permissions: []
      });
    }
    setOpenDialog(true);
  };

  const handleDialogClose = () => {
    setOpenDialog(false);
    setError('');
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handlePermissionToggle = (permission) => {
    const currentPermissions = [...formData.permissions];
    const index = currentPermissions.indexOf(permission);
    if (index === -1) {
      currentPermissions.push(permission);
    } else {
      currentPermissions.splice(index, 1);
    }
    setFormData({ ...formData, permissions: currentPermissions });
  };

  const handleSubmit = async () => {
    try {
      setError('');
      const exchangeData = {
        ...formData
      };
      
      let result;
      if (isEditing) {
        // Don't send apiKey and apiSecret if they haven't been changed
        if (exchangeData.apiKey === '••••••••••••••••••••••••••') {
          delete exchangeData.apiKey;
        }
        
        if (exchangeData.apiSecret === '••••••••••••••••••••••••••') {
          delete exchangeData.apiSecret;
        }
        
        result = await ExchangeService.updateExchangeApi(selectedExchange.id, exchangeData);
        
        // Update the exchanges list
        setExchanges(exchanges.map(exchange => 
          exchange.id === selectedExchange.id 
            ? { ...exchange, ...result } 
            : exchange
        ));
      } else {
        result = await ExchangeService.addExchangeApi(exchangeData);
        setExchanges([...exchanges, result]);
      }
      
      handleDialogClose();
    } catch (err) {
      setError(err.message || 'Failed to save exchange API');
    }
  };

  const handleDelete = async (exchangeId) => {
    if (window.confirm('Are you sure you want to delete this exchange API?')) {
      try {
        await ExchangeService.deleteExchangeApi(exchangeId);
        setExchanges(exchanges.filter(exchange => exchange.id !== exchangeId));
      } catch (err) {
        setError(err.message || 'Failed to delete exchange API');
      }
    }
  };

  const refreshBalances = async (exchangeId) => {
    try {
      // This would trigger a balance refresh on the server
      // and then fetch updated balances
      const updatedExchange = await ExchangeService.getBalances(exchangeId);
      
      // Update the exchanges list with fresh balance data
      setExchanges(exchanges.map(exchange => 
        exchange.id === exchangeId 
          ? { ...exchange, balances: updatedExchange.balances } 
          : exchange
      ));
    } catch (err) {
      setError(err.message || 'Failed to refresh balances');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1">
          Exchange Connections
        </Typography>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />}
          onClick={() => handleDialogOpen()}
        >
          Add Exchange
        </Button>
      </Box>
      
      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
      
      {exchanges.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            No exchanges connected yet
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Connect your exchange accounts to start trading
          </Typography>
          <Button 
            variant="outlined" 
            startIcon={<AddIcon />}
            onClick={() => handleDialogOpen()}
          >
            Add Your First Exchange
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {exchanges.map(exchange => (
            <Grid item xs={12} md={6} key={exchange.id}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                    <Typography variant="h6">{exchange.exchangeName}</Typography>
                    <Chip 
                      label={exchange.isActive ? "Active" : "Inactive"} 
                      color={exchange.isActive ? "success" : "default"}
                      size="small"
                    />
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {exchange.label || "Unlabeled"}
                  </Typography>
                  
                  <Typography variant="caption" color="text.secondary" component="div" sx={{ mb: 1 }}>
                    API Key: {exchange.apiKey.substring(0, 4)}••••{exchange.apiKey.substring(exchange.apiKey.length - 4)}
                  </Typography>
                  
                  <Box mt={2}>
                    <Typography variant="subtitle2">Permissions:</Typography>
                    <Box display="flex" flexWrap="wrap" gap={0.5} mt={0.5}>
                      {exchange.permissions.map(permission => (
                        <Chip key={permission} label={permission} size="small" />
                      ))}
                    </Box>
                  </Box>
                  
                  {exchange.balances && (
                    <>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="subtitle2" sx={{ mb: 1 }}>Balances:</Typography>
                      <Box display="flex" flexWrap="wrap" gap={1}>
                        {Object.entries(exchange.balances)
                          .filter(([_, value]) => parseFloat(value) > 0)
                          .slice(0, 5) // Show only top 5 balances
                          .map(([currency, balance]) => (
                            <Chip 
                              key={currency}
                              label={`${currency}: ${parseFloat(balance).toFixed(4)}`}
                              size="small"
                              variant="outlined"
                            />
                          ))}
                        {Object.keys(exchange.balances).filter(key => parseFloat(exchange.balances[key]) > 0).length > 5 && (
                          <Chip label="..." size="small" variant="outlined" />
                        )}
                      </Box>
                    </>
                  )}
                </CardContent>
                <CardActions>
                  <Button 
                    size="small" 
                    startIcon={<EditIcon />}
                    onClick={() => handleDialogOpen(exchange)}
                  >
                    Edit
                  </Button>
                  <Button 
                    size="small" 
                    startIcon={<RefreshIcon />}
                    onClick={() => refreshBalances(exchange.id)}
                  >
                    Refresh Balances
                  </Button>
                  <Box sx={{ flexGrow: 1 }} />
                  <IconButton 
                    size="small" 
                    color="error"
                    onClick={() => handleDelete(exchange.id)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
      
      {/* Add/Edit Exchange Dialog */}
      <Dialog open={openDialog} onClose={handleDialogClose} maxWidth="sm" fullWidth>
        <DialogTitle>{isEditing ? 'Edit Exchange' : 'Add New Exchange'}</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          <DialogContentText sx={{ mb: 2 }}>
            {isEditing 
              ? 'Update your exchange API credentials or permissions.' 
              : 'Enter your exchange API credentials to connect your account.'}
          </DialogContentText>
          
          <FormControl fullWidth margin="normal">
            <InputLabel id="exchange-name-label">Exchange</InputLabel>
            <Select
              labelId="exchange-name-label"
              id="exchangeName"
              name="exchangeName"
              value={formData.exchangeName}
              onChange={handleInputChange}
              label="Exchange"
              disabled={isEditing}
            >
              {supportedExchanges.map((exchange) => (
                <MenuItem key={exchange.name} value={exchange.name}>
                  {exchange.displayName || exchange.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <TextField
            margin="normal"
            id="label"
            name="label"
            label="Label (Optional)"
            fullWidth
            value={formData.label}
            onChange={handleInputChange}
            placeholder="e.g., Trading Account, Main Account"
          />
          
          <TextField
            margin="normal"
            required
            id="apiKey"
            name="apiKey"
            label="API Key"
            type="password"
            fullWidth
            value={formData.apiKey}
            onChange={handleInputChange}
          />
          
          <TextField
            margin="normal"
            required
            id="apiSecret"
            name="apiSecret"
            label="API Secret"
            type="password"
            fullWidth
            value={formData.apiSecret}
            onChange={handleInputChange}
          />
          
          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Permissions
          </Typography>
          
          <FormControlLabel
            control={
              <Switch
                checked={formData.permissions.includes('READ')}
                onChange={() => handlePermissionToggle('READ')}
                name="READ"
              />
            }
            label="Read (View balances and orders)"
          />
          
          <FormControlLabel
            control={
              <Switch
                checked={formData.permissions.includes('TRADE')}
                onChange={() => handlePermissionToggle('TRADE')}
                name="TRADE"
              />
            }
            label="Trade (Place and cancel orders)"
          />
          
          <FormControlLabel
            control={
              <Switch
                checked={formData.permissions.includes('WITHDRAW')}
                onChange={() => handlePermissionToggle('WITHDRAW')}
                name="WITHDRAW"
              />
            }
            label="Withdraw (Not recommended for most strategies)"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {isEditing ? 'Update' : 'Connect'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Exchanges;
