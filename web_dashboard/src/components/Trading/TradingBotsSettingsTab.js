// TradingBotsSettingsTab.js
import React from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  FormControlLabel,
  Switch,
  Checkbox,
  TextField,
  Button,
  Alert
} from '@mui/material';
import { Save } from '@mui/icons-material';

const TradingBotsSettingsTab = ({ setError }) => {
  return (
    <Box sx={{ py: 2 }}>
      <Typography variant="h5" gutterBottom>
        Settings
      </Typography>
      
      <Grid container spacing={3}>
        {/* General Settings */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              General Settings
            </Typography>
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Theme</InputLabel>
              <Select
                value="system"
                label="Theme"
              >
                <MenuItem value="system">System Default</MenuItem>
                <MenuItem value="light">Light</MenuItem>
                <MenuItem value="dark">Dark</MenuItem>
              </Select>
            </FormControl>
            
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Enable notifications"
              sx={{ mt: 2, display: 'block' }}
            />
            
            <FormControlLabel
              control={<Switch />}
              label="Enable email alerts"
              sx={{ mt: 1, display: 'block' }}
            />
          </Paper>
        </Grid>
        
        {/* Trading Settings */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Trading Settings
            </Typography>
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Default Timeframe</InputLabel>
              <Select
                value="1h"
                label="Default Timeframe"
              >
                <MenuItem value="1m">1 Minute</MenuItem>
                <MenuItem value="5m">5 Minutes</MenuItem>
                <MenuItem value="15m">15 Minutes</MenuItem>
                <MenuItem value="1h">1 Hour</MenuItem>
                <MenuItem value="4h">4 Hours</MenuItem>
                <MenuItem value="1d">1 Day</MenuItem>
              </Select>
            </FormControl>
            
            <FormControlLabel
              control={<Switch />}
              label="Automatically start bots on application load"
              sx={{ mt: 2, display: 'block' }}
            />
            
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Confirm trades before execution"
              sx={{ mt: 1, display: 'block' }}
            />
          </Paper>
        </Grid>
        
        {/* API Configuration */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              API Configuration
            </Typography>
            
            <Alert severity="info" sx={{ mb: 2 }}>
              API keys are stored securely and encrypted. Never share your API keys with anyone.
            </Alert>
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="API Key"
                  type="password"
                  placeholder="Enter your exchange API key"
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="API Secret"
                  type="password"
                  placeholder="Enter your exchange API secret"
                  margin="normal"
                />
              </Grid>
            </Grid>
            
            <FormControlLabel
              control={<Checkbox defaultChecked />}
              label="Enable trading (uncheck for read-only API access)"
            />
          </Paper>
        </Grid>
        
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<Save />}
              onClick={() => {
                setError('Settings saved successfully!');
              }}
            >
              Save Settings
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default TradingBotsSettingsTab;
