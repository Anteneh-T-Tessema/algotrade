import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Chip,
  IconButton,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Slider,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Settings as SettingsIcon,
  ExpandMore as ExpandMoreIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  DragIndicator as DragIndicatorIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
} from '@mui/icons-material';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import SettingsService from '../../services/SettingsService';

const DashboardSettings = () => {
  const [preferences, setPreferences] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [notification, setNotification] = useState({
    open: false,
    severity: 'success',
    message: ''
  });
  const [symbolDialog, setSymbolDialog] = useState({
    open: false,
    symbol: ''
  });

  // Chart preferences state
  const [chartPreferences, setChartPreferences] = useState(null);

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const dashboardPrefs = await SettingsService.getDashboardPreferences();
        setPreferences(dashboardPrefs);

        const chartPrefs = await SettingsService.getChartPreferences('price');
        setChartPreferences(chartPrefs);
      } catch (error) {
        console.error("Failed to load settings:", error);
        setNotification({
          open: true,
          severity: 'error',
          message: 'Failed to load settings. Please try again.'
        });
      } finally {
        setLoading(false);
      }
    };

    loadSettings();
  }, []);

  const handleSaveSettings = async () => {
    setSaving(true);
    try {
      await SettingsService.updateDashboardPreferences(preferences);
      
      if (chartPreferences) {
        await SettingsService.updateChartPreferences(chartPreferences, 'price');
      }
      
      setNotification({
        open: true,
        severity: 'success',
        message: 'Settings saved successfully!'
      });
    } catch (error) {
      console.error("Failed to save settings:", error);
      setNotification({
        open: true,
        severity: 'error',
        message: 'Failed to save settings. Please try again.'
      });
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (key, value) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleAdvancedChange = (key, value) => {
    setPreferences(prev => ({
      ...prev,
      advanced: {
        ...prev.advanced,
        [key]: value
      }
    }));
  };

  const handleChartChange = (key, value) => {
    setChartPreferences(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleAddFavoriteSymbol = () => {
    if (!symbolDialog.symbol) return;
    
    const updatedSymbols = [
      ...preferences.favoriteSymbols,
      symbolDialog.symbol.toUpperCase()
    ];
    
    setPreferences(prev => ({
      ...prev,
      favoriteSymbols: updatedSymbols
    }));
    
    setSymbolDialog({
      open: false,
      symbol: ''
    });
  };

  const handleRemoveFavoriteSymbol = (symbolToRemove) => {
    const updatedSymbols = preferences.favoriteSymbols.filter(
      symbol => symbol !== symbolToRemove
    );
    
    setPreferences(prev => ({
      ...prev,
      favoriteSymbols: updatedSymbols
    }));
  };

  const handleDragEnd = (result) => {
    if (!result.destination) return;
    
    const items = Array.from(preferences.widgetsOrder);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);
    
    setPreferences(prev => ({
      ...prev,
      widgetsOrder: items
    }));
  };

  const handleNotificationClose = () => {
    setNotification(prev => ({
      ...prev,
      open: false
    }));
  };

  if (loading || !preferences) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        height: '300px'
      }}>
        <Typography>Loading settings...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ pb: 4 }}>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Dashboard Settings
        </Typography>
        <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
          Customize your trading dashboard experience
        </Typography>

        <Divider sx={{ mb: 3 }} />

        <Grid container spacing={3}>
          {/* General Settings */}
          <Grid item xs={12} md={6}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Layout</InputLabel>
              <Select
                value={preferences.layout}
                label="Layout"
                onChange={(e) => handleChange('layout', e.target.value)}
              >
                <MenuItem value="2-column">2 Column</MenuItem>
                <MenuItem value="3-column">3 Column</MenuItem>
                <MenuItem value="wide">Wide</MenuItem>
                <MenuItem value="compact">Compact</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth margin="normal">
              <InputLabel>Default Exchange</InputLabel>
              <Select
                value={preferences.defaultExchange}
                label="Default Exchange"
                onChange={(e) => handleChange('defaultExchange', e.target.value)}
              >
                <MenuItem value="binance">Binance</MenuItem>
                <MenuItem value="coinbase">Coinbase</MenuItem>
                <MenuItem value="kraken">Kraken</MenuItem>
                <MenuItem value="ftx">FTX</MenuItem>
                <MenuItem value="kucoin">KuCoin</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth margin="normal">
              <InputLabel>Default Timeframe</InputLabel>
              <Select
                value={preferences.defaultTimeframe}
                label="Default Timeframe"
                onChange={(e) => handleChange('defaultTimeframe', e.target.value)}
              >
                <MenuItem value="15m">15 Minutes</MenuItem>
                <MenuItem value="1h">1 Hour</MenuItem>
                <MenuItem value="4h">4 Hours</MenuItem>
                <MenuItem value="1D">1 Day</MenuItem>
                <MenuItem value="1W">1 Week</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth margin="normal">
              <InputLabel>Theme</InputLabel>
              <Select
                value={preferences.theme}
                label="Theme"
                onChange={(e) => handleChange('theme', e.target.value)}
              >
                <MenuItem value="light">Light</MenuItem>
                <MenuItem value="dark">Dark</MenuItem>
                <MenuItem value="system">System Default</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Favorite Symbols */}
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>
              Favorite Symbols
            </Typography>
            
            <Box sx={{ 
              display: 'flex', 
              flexWrap: 'wrap', 
              mt: 1, 
              gap: 1, 
              mb: 2,
              minHeight: '40px'
            }}>
              {preferences.favoriteSymbols.map((symbol) => (
                <Chip
                  key={symbol}
                  label={symbol}
                  onDelete={() => handleRemoveFavoriteSymbol(symbol)}
                  color="primary"
                  variant="outlined"
                />
              ))}
            </Box>
            
            <Button 
              startIcon={<AddIcon />}
              variant="outlined"
              onClick={() => setSymbolDialog({ open: true, symbol: '' })}
              size="small"
            >
              Add Symbol
            </Button>
          </Grid>
        </Grid>

        {/* Widget Order */}
        <Box sx={{ mt: 4, mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Widget Order
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Drag and drop to rearrange widgets on your dashboard
          </Typography>
          
          <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="widgets">
              {(provided) => (
                <List
                  {...provided.droppableProps}
                  ref={provided.innerRef}
                  sx={{ bgcolor: 'background.paper', borderRadius: 1 }}
                >
                  {preferences.widgetsOrder.map((widgetId, index) => (
                    <Draggable key={widgetId} draggableId={widgetId} index={index}>
                      {(provided) => (
                        <ListItem
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          divider
                          sx={{ bgcolor: 'background.paper' }}
                        >
                          <DragIndicatorIcon sx={{ mr: 2, color: 'text.secondary' }} />
                          <ListItemText 
                            primary={widgetId.split('-')
                              .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                              .join(' ')} 
                          />
                          <ListItemSecondaryAction>
                            <IconButton 
                              edge="end" 
                              onClick={() => {
                                const updated = preferences.hiddenWidgets.includes(widgetId) 
                                  ? preferences.hiddenWidgets.filter(w => w !== widgetId)
                                  : [...preferences.hiddenWidgets, widgetId];
                                handleChange('hiddenWidgets', updated);
                              }}
                            >
                              {preferences.hiddenWidgets.includes(widgetId) ? (
                                <VisibilityOffIcon />
                              ) : (
                                <VisibilityIcon />
                              )}
                            </IconButton>
                          </ListItemSecondaryAction>
                        </ListItem>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </List>
              )}
            </Droppable>
          </DragDropContext>
        </Box>

        {/* Advanced Settings */}
        <Accordion sx={{ mt: 3 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>Advanced Settings</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.advanced.showTradingVolume}
                      onChange={(e) => handleAdvancedChange('showTradingVolume', e.target.checked)}
                    />
                  }
                  label="Show Trading Volume"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.advanced.autoRefresh}
                      onChange={(e) => handleAdvancedChange('autoRefresh', e.target.checked)}
                    />
                  }
                  label="Auto Refresh Data"
                />
              </Grid>
              <Grid item xs={12}>
                <Typography id="refresh-interval-slider" gutterBottom>
                  Refresh Interval: {preferences.advanced.refreshInterval} seconds
                </Typography>
                <Slider
                  aria-labelledby="refresh-interval-slider"
                  value={preferences.advanced.refreshInterval}
                  onChange={(e, newValue) => handleAdvancedChange('refreshInterval', newValue)}
                  min={5}
                  max={60}
                  step={5}
                  disabled={!preferences.advanced.autoRefresh}
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Save Button */}
        <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSaveSettings}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </Button>
        </Box>
      </Paper>

      {/* Add Symbol Dialog */}
      <Dialog open={symbolDialog.open} onClose={() => setSymbolDialog({ open: false, symbol: '' })}>
        <DialogTitle>Add Favorite Symbol</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Trading Symbol (e.g., BTCUSDT)"
            fullWidth
            variant="outlined"
            value={symbolDialog.symbol}
            onChange={(e) => setSymbolDialog(prev => ({ ...prev, symbol: e.target.value }))}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSymbolDialog({ open: false, symbol: '' })}>
            Cancel
          </Button>
          <Button onClick={handleAddFavoriteSymbol} color="primary">
            Add
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification Snackbar */}
      <Snackbar 
        open={notification.open} 
        autoHideDuration={6000} 
        onClose={handleNotificationClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleNotificationClose} 
          severity={notification.severity}
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default DashboardSettings;
