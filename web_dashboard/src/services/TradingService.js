import api from './api';

// Base API URL (already included in api.js baseURL)
const API_BASE = '';

class TradingService {
  async getAllStrategies() {
    try {
      const response = await api.get(`${API_BASE}/trading/strategies`);
      return response.data.strategies;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getUserStrategies() {
    try {
      const response = await api.get(`${API_BASE}/trading/user-strategies`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getStrategyById(strategyId) {
    try {
      const response = await api.get(`${API_BASE}/trading/user-strategies/${strategyId}`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async createUserStrategy(strategyData) {
    try {
      const response = await api.post(`${API_BASE}/trading/user-strategies`, strategyData);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async updateUserStrategy(strategyId, strategyData) {
    try {
      const response = await api.put(`${API_BASE}/trading/user-strategies/${strategyId}`, strategyData);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async deleteUserStrategy(strategyId) {
    try {
      await api.delete(`${API_BASE}/trading/user-strategies/${strategyId}`);
      return true;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async startStrategy(strategyId) {
    try {
      const response = await api.post(`${API_BASE}/trading/user-strategies/${strategyId}/start`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async stopStrategy(strategyId) {
    try {
      const response = await api.post(`${API_BASE}/trading/user-strategies/${strategyId}/stop`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async backtestStrategy(backtestData) {
    try {
      const response = await api.post(`${API_BASE}/trading/backtest`, backtestData);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getBacktestResult(backtestId) {
    try {
      const response = await api.get(`${API_BASE}/trading/backtest/${backtestId}`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getTradingHistory(filters = {}) {
    try {
      const response = await api.get(`${API_BASE}/trading/history`, { params: filters });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getStrategyPerformance(strategyId) {
    try {
      const response = await api.get(`${API_BASE}/trading/user-strategies/${strategyId}/performance`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getDistributorCommissions(period, dateRange = null, tier = null) {
    try {
      const params = { period };
      
      if (dateRange) {
        params.startDate = dateRange.startDate;
        params.endDate = dateRange.endDate;
      }
      
      if (tier !== null) {
        params.tier = tier;
      }
      
      const response = await api.get(`${API_BASE}/distributor/commissions`, { params });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getDistributorNetwork(depth = 3, userId = null) {
    try {
      const params = { depth };
      if (userId) {
        params.userId = userId;
      }
      
      const response = await api.get(`${API_BASE}/distributor/network`, { params });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getDistributorStats(period = '1month', userId = null) {
    try {
      const params = { period };
      if (userId) {
        params.userId = userId;
      }
      
      const response = await api.get(`${API_BASE}/distributor/stats`, { params });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getDistributorReferrals(status = 'all', page = 1, limit = 20) {
    try {
      const params = { status, page, limit };
      const response = await api.get(`${API_BASE}/distributor/referrals`, { params });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getDashboardData(period = '24h') {
    try {
      const response = await api.get(`${API_BASE}/trading/dashboard`, { params: { period } });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getDashboardPerformance(period = '1month') {
    try {
      const response = await api.get(`${API_BASE}/trading/dashboard/performance`, { params: { period } });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getDashboardAlerts() {
    try {
      const response = await api.get(`${API_BASE}/trading/dashboard/alerts`);
      return response.data.alerts;
    } catch (error) {
      this._handleError(error);
    }
  }

  async getMarketData(limit = 100, sortBy = 'marketCap', order = 'desc') {
    try {
      const response = await api.get(`${API_BASE}/trading/market-data`, { 
        params: { limit, sortBy, order } 
      });
      return response.data.cryptocurrencies;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getExchangeMarketData(exchangeId, symbol) {
    try {
      const response = await api.get(`${API_BASE}/exchanges/${exchangeId}/market-data`, {
        params: { symbol }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getPortfolioSummary() {
    try {
      const response = await api.get(`${API_BASE}/trading/portfolio/summary`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getPortfolioPerformance(period = '1month') {
    try {
      const response = await api.get(`${API_BASE}/trading/portfolio/performance`, {
        params: { period }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getPortfolioAssets() {
    try {
      const response = await api.get(`${API_BASE}/trading/portfolio/assets`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getOrderBookData(symbol, depth = 10) {
    try {
      const response = await api.get(`${API_BASE}/trading/orderbook`, {
        params: { symbol, depth }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getRecentTrades(symbol, limit = 50) {
    try {
      const response = await api.get(`${API_BASE}/trading/recent-trades`, {
        params: { symbol, limit }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getTechnicalIndicators(symbol, timeframe = '1d', indicators = ['sma', 'ema', 'rsi']) {
    try {
      const response = await api.get(`${API_BASE}/trading/technical-indicators`, {
        params: { symbol, timeframe, indicators: indicators.join(',') }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getAvailableTimeframes() {
    try {
      const response = await api.get(`${API_BASE}/trading/timeframes`);
      return response.data.timeframes;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getAvailableIndicators() {
    try {
      const response = await api.get(`${API_BASE}/trading/indicators`);
      return response.data.indicators;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getChartData(symbol, timeframe = '1h', from = null, to = null) {
    try {
      const params = { symbol, timeframe };
      
      if (from) params.from = from;
      if (to) params.to = to;
      
      const response = await api.get(`${API_BASE}/trading/chart-data`, { params });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getMultiExchangePairs() {
    try {
      const response = await api.get(`${API_BASE}/trading/exchange-pairs`);
      return response.data.pairs;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getArbitrageOpportunities(minSpreadPercentage = 0.5) {
    try {
      const response = await api.get(`${API_BASE}/trading/arbitrage`, { 
        params: { minSpreadPercentage } 
      });
      return response.data.opportunities;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getCommissionTiers() {
    try {
      const response = await api.get(`${API_BASE}/distributor/commission-tiers`);
      return response.data.tiers;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getCommissionCalculator(amount, tier = null) {
    try {
      const params = { amount };
      if (tier !== null) params.tier = tier;
      
      const response = await api.get(`${API_BASE}/distributor/commission-calculator`, { params });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async generateReferralLink() {
    try {
      const response = await api.post(`${API_BASE}/distributor/referral-link`);
      return response.data.referralLink;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  _handleError(error) {
    let errorMessage = 'An unexpected error occurred';
    
    if (error.response) {
      const { status, data } = error.response;
      
      if (data.message) {
        errorMessage = data.message;
      } else if (status === 404) {
        errorMessage = 'The requested resource was not found.';
      } else if (status === 403) {
        errorMessage = 'You do not have permission to perform this action.';
      }
    } else if (error.request) {
      errorMessage = 'No response received from server. Please check your connection.';
    }
    
    throw new Error(errorMessage);
  }
}

export default new TradingService();
