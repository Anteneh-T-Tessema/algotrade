import React from 'react';
import { useLocation, Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  Box,
  Drawer,
  Toolbar,
  List,
  Typography,
  Divider,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  BarChart as BarChartIcon,
  Settings as SettingsIcon,
  AccountBalance as ExchangeIcon,
  Groups as NetworkIcon,
  AttachMoney as CommissionIcon,
  AdminPanelSettings as AdminIcon,
  Person as ProfileIcon,
  Wallet as PortfolioIcon,
  TrendingUp as MarketIcon,
  SwapHoriz as TradeIcon,
} from '@mui/icons-material';

const Sidebar = ({ drawerWidth, mobileOpen, handleDrawerToggle }) => {
  const location = useLocation();
  const { user } = useAuth();
  
  // Check if user has required role
  const hasRole = (requiredRoles) => {
    if (!user || !user.roles) return false;
    return requiredRoles.some(role => user.roles.includes(role));
  };

  const isDistributor = hasRole(['DISTRIBUTOR', 'MASTER_DISTRIBUTOR', 'ADMIN']);
  const isAdmin = hasRole(['ADMIN']);
  
  const menuItems = [
    { 
      text: 'Dashboard', 
      icon: <DashboardIcon />, 
      path: '/',
      roles: [] // Everyone
    },
    { 
      text: 'Trade', 
      icon: <TradeIcon />, 
      path: '/trade',
      roles: [] // Everyone
    },
    { 
      text: 'Portfolio', 
      icon: <PortfolioIcon />, 
      path: '/portfolio',
      roles: [] // Everyone
    },
    { 
      text: 'Markets', 
      icon: <MarketIcon />, 
      path: '/markets',
      roles: [] // Everyone
    },
    { 
      text: 'Strategies', 
      icon: <BarChartIcon />, 
      path: '/strategies',
      roles: [] // Everyone
    },
    { 
      text: 'Exchanges', 
      icon: <ExchangeIcon />, 
      path: '/exchanges',
      roles: [] // Everyone
    },
    { 
      text: 'Distributor Network', 
      icon: <NetworkIcon />, 
      path: '/network',
      roles: ['DISTRIBUTOR', 'MASTER_DISTRIBUTOR', 'ADMIN'] // Only distributors and admins
    },
    { 
      text: 'Commissions', 
      icon: <CommissionIcon />, 
      path: '/commissions',
      roles: ['DISTRIBUTOR', 'MASTER_DISTRIBUTOR', 'ADMIN'] // Only distributors and admins
    },
    { 
      text: 'Admin Panel', 
      icon: <AdminIcon />, 
      path: '/admin',
      roles: ['ADMIN'] // Only admins
    },
    { 
      text: 'Profile', 
      icon: <ProfileIcon />, 
      path: '/profile',
      roles: [] // Everyone
    },
    { 
      text: 'Settings', 
      icon: <SettingsIcon />, 
      path: '/settings',
      roles: [] // Everyone
    },
  ];

  const drawer = (
    <div>
      <Toolbar sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
        <Typography variant="h6" component="div" sx={{ fontWeight: 600, color: 'primary.main' }}>
          Crypto Trading Platform
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => {
          // Check if user has required role for this menu item
          if (item.roles.length > 0) {
            if (!hasRole(item.roles)) return null;
          }
          
          const isActive = location.pathname === item.path || 
                           (item.path !== '/' && location.pathname.startsWith(item.path));
          
          return (
            <ListItem key={item.text} disablePadding>
              <ListItemButton 
                component={RouterLink} 
                to={item.path}
                selected={isActive}
                sx={{
                  borderRadius: '0 24px 24px 0',
                  mr: 1,
                  ml: 0,
                  mb: 0.5,
                  '&.Mui-selected': {
                    bgcolor: 'rgba(63, 81, 181, 0.08)',
                    '&:hover': {
                      bgcolor: 'rgba(63, 81, 181, 0.12)',
                    },
                  },
                }}
              >
                <ListItemIcon sx={{ 
                  color: isActive ? 'primary.main' : 'text.secondary',
                  minWidth: '40px'
                }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.text} 
                  primaryTypographyProps={{
                    fontWeight: isActive ? 600 : 400,
                    color: isActive ? 'primary.main' : 'text.primary'
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
      
      {(isDistributor || isAdmin) && (
        <>
          <Divider sx={{ my: 2 }} />
          <Box px={2} py={1}>
            <Typography variant="body2" color="text.secondary">
              {user?.username || 'User'}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {isAdmin ? 'Administrator' : 'Distributor'}
            </Typography>
          </Box>
        </>
      )}
    </div>
  );
  
  return (
    <Box
      component="nav"
      sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
    >
      {/* Mobile drawer */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile
        }}
        sx={{
          display: { xs: 'block', sm: 'none' },
          '& .MuiDrawer-paper': { 
            boxSizing: 'border-box', 
            width: drawerWidth,
            backgroundColor: 'background.paper',
          },
        }}
      >
        {drawer}
      </Drawer>
      
      {/* Desktop drawer */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', sm: 'block' },
          '& .MuiDrawer-paper': { 
            boxSizing: 'border-box', 
            width: drawerWidth,
            backgroundColor: 'background.paper',
            border: 'none',
            boxShadow: '0 0 10px rgba(0,0,0,0.05)'
          },
        }}
        open
      >
        {drawer}
      </Drawer>
    </Box>
  );
};

export default Sidebar;
