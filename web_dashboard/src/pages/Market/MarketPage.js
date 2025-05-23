import React from 'react';
import { Box, Typography } from '@mui/material';
import MarketOverview from '../../components/Market/MarketOverview';

const MarketPage = () => {
  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1">
          Markets
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Explore cryptocurrency markets and prices
        </Typography>
      </Box>

      <MarketOverview />
    </Box>
  );
};

export default MarketPage;
