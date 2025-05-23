import React from 'react';
import { Box, Grid, Paper, Typography } from '@mui/material';
import PortfolioOverview from '../../components/Portfolio/PortfolioOverview';
import MarketOverview from '../../components/Market/MarketOverview';

const PortfolioPage = () => {
  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1">
          Portfolio
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Manage your crypto assets across multiple exchanges
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <PortfolioOverview />
        </Grid>
      </Grid>
    </Box>
  );
};

export default PortfolioPage;
