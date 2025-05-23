import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, Container, Typography, AppBar, Toolbar, Button } from '@mui/material';
import MarketOverview from './components/Market/MarketOverview';
import TradingInterface from './components/Trading/TradingInterface';
import StrategyAnalysisPage from './pages/AnalysisPage';

// Simple Layout component
const Layout = ({ children }) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Crypto Trading Platform
          </Typography>
          <Button color="inherit" component="a" href="/">Market</Button>
          <Button color="inherit" component="a" href="/trading">Trading</Button>
          <Button color="inherit" component="a" href="/analysis">Analysis</Button>
        </Toolbar>
      </AppBar>
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4, flexGrow: 1 }}>
        {children}
      </Container>
    </Box>
  );
};

// Simple pages
const MarketPage = () => (
  <Layout>
    <Typography variant="h4" gutterBottom>Market Overview</Typography>
    <MarketOverview />
  </Layout>
);

const TradePage = () => (
  <Layout>
    <Typography variant="h4" gutterBottom>Trading Interface</Typography>
    <TradingInterface />
  </Layout>
);

const HomePage = () => <Navigate to="/market" replace />;

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/market" element={<MarketPage />} />
      <Route path="/trading" element={<TradePage />} />
      <Route path="/analysis" element={<StrategyAnalysisPage />} />
      <Route path="*" element={
        <Layout>
          <Box sx={{ textAlign: 'center', py: 5 }}>
            <Typography variant="h4">404 - Page Not Found</Typography>
            <Button variant="contained" color="primary" href="/" sx={{ mt: 3 }}>
              Return Home
            </Button>
          </Box>
        </Layout>
      } />
    </Routes>
  );
}

export default App;
