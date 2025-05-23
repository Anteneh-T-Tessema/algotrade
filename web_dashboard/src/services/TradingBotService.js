// TradingBotService.js - Handles automated trading bot functionality
import api from './api';

// Base API URL
const API_BASE = '';

class TradingBotService {
  /**
   * Get all available bot templates
   * @returns {Promise<Array>} List of bot templates
   */
  async getBotTemplates() {
    try {
      const response = await api.get(`${API_BASE}/trading/bots/templates`);
      return response.data.templates;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get user's active bots
   * @returns {Promise<Array>} List of user's active bots
   */
  async getUserBots() {
    try {
      const response = await api.get(`${API_BASE}/trading/bots`);
      return response.data.bots;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get detailed information about a specific bot
   * @param {string} botId - ID of the bot
   * @returns {Promise<Object>} Bot details
   */
  async getBotDetails(botId) {
    try {
      const response = await api.get(`${API_BASE}/trading/bots/${botId}`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Create a new trading bot
   * @param {Object} botConfig - Bot configuration
   * @returns {Promise<Object>} Created bot
   */
  async createBot(botConfig) {
    try {
      const response = await api.post(`${API_BASE}/trading/bots`, botConfig);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Update an existing bot
   * @param {string} botId - ID of the bot to update
   * @param {Object} botConfig - Updated bot configuration
   * @returns {Promise<Object>} Updated bot
   */
  async updateBot(botId, botConfig) {
    try {
      const response = await api.put(`${API_BASE}/trading/bots/${botId}`, botConfig);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Delete a trading bot
   * @param {string} botId - ID of the bot to delete
   * @returns {Promise<boolean>} Success indicator
   */
  async deleteBot(botId) {
    try {
      await api.delete(`${API_BASE}/trading/bots/${botId}`);
      return true;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Start a trading bot
   * @param {string} botId - ID of the bot to start
   * @returns {Promise<Object>} Started bot status
   */
  async startBot(botId) {
    try {
      const response = await api.post(`${API_BASE}/trading/bots/${botId}/start`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Stop a trading bot
   * @param {string} botId - ID of the bot to stop
   * @returns {Promise<Object>} Stopped bot status
   */
  async stopBot(botId) {
    try {
      const response = await api.post(`${API_BASE}/trading/bots/${botId}/stop`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get bot performance history
   * @param {string} botId - ID of the bot
   * @param {string} period - Period for performance data
   * @returns {Promise<Object>} Bot performance data
   */
  async getBotPerformance(botId, period = '1m') {
    try {
      const response = await api.get(`${API_BASE}/trading/bots/${botId}/performance`, {
        params: { period }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get bot trade history
   * @param {string} botId - ID of the bot
   * @param {Object} params - Query parameters
   * @returns {Promise<Object>} Bot trade history
   */
  async getBotTradeHistory(botId, params = { limit: 50 }) {
    try {
      const response = await api.get(`${API_BASE}/trading/bots/${botId}/trades`, {
        params
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get bot statistics
   * @param {string} botId - ID of the bot
   * @returns {Promise<Object>} Bot statistics
   */
  async getBotStats(botId) {
    try {
      const response = await api.get(`${API_BASE}/trading/bots/${botId}/stats`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Backtest a bot configuration
   * @param {Object} config - Bot configuration for backtesting
   * @returns {Promise<Object>} Backtest results
   */
  async backtestBot(config) {
    try {
      const response = await api.post(`${API_BASE}/trading/bots/backtest`, config);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get available indicators for bot configuration
   * @returns {Promise<Array>} List of available indicators
   */
  async getAvailableIndicators() {
    try {
      const response = await api.get(`${API_BASE}/trading/bots/indicators`);
      return response.data.indicators;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get sample bot strategies
   * @returns {Promise<Array>} List of sample strategies
   */
  async getSampleStrategies() {
    try {
      const response = await api.get(`${API_BASE}/trading/bots/sample-strategies`);
      return response.data.strategies;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get portfolio performance data
   * @param {string} period - Time period for data
   * @returns {Promise<Object>} Portfolio performance data
   */
  async getPortfolioPerformance(period = '1m') {
    try {
      const response = await api.get(`${API_BASE}/trading/bots/portfolio/performance`, {
        params: { period }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get portfolio allocation recommendations
   * @param {string} riskProfile - User's risk profile (low, medium, high)
   * @returns {Promise<Object>} Portfolio allocation recommendations
   */
  async getPortfolioRecommendations(riskProfile = 'medium') {
    try {
      const response = await api.get(`${API_BASE}/trading/bots/portfolio/recommendations`, {
        params: { riskProfile }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get risk exposure analysis
   * @param {Array} botIds - Optional list of bot IDs to analyze
   * @returns {Promise<Object>} Risk exposure data
   */
  async getRiskExposure(botIds = []) {
    try {
      const response = await api.post(`${API_BASE}/trading/bots/risk-analysis`, {
        botIds
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Import bot configuration from file or exchange
   * @param {Object} importData - Import configuration
   * @returns {Promise<Object>} Imported bot configuration
   */
  async importBotConfig(importData) {
    try {
      const response = await api.post(`${API_BASE}/trading/bots/import`, importData);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Export bot configuration
   * @param {string} botId - Bot ID to export
   * @returns {Promise<Object>} Exported bot configuration
   */
  async exportBotConfig(botId) {
    try {
      const response = await api.get(`${API_BASE}/trading/bots/${botId}/export`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Configure bot alerts and notifications
   * @param {string} botId - Bot ID
   * @param {Object} alertsConfig - Alerts configuration
   * @returns {Promise<Object>} Updated alerts configuration
   */
  async configureBotAlerts(botId, alertsConfig) {
    try {
      const response = await api.post(`${API_BASE}/trading/bots/${botId}/alerts`, alertsConfig);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get correlated trading pairs for diversification
   * @param {string} baseSymbol - Base trading pair symbol
   * @returns {Promise<Object>} Correlation data for trading pairs
   */
  async getPairCorrelations(baseSymbol = 'BTCUSDT') {
    try {
      const response = await api.get(`${API_BASE}/trading/bots/correlations`, {
        params: { symbol: baseSymbol }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Optimize a bot's strategy parameters
   * @param {Object} optimizationConfig - Optimization configuration
   * @returns {Promise<Object>} Optimized parameters
   */
  async optimizeStrategy(optimizationConfig) {
    try {
      const response = await api.post(`${API_BASE}/trading/bots/optimize`, optimizationConfig);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get AI-based strategy suggestions for given market conditions
   * @param {Object} params - Market parameters to consider
   * @returns {Promise<Object>} AI suggested strategies
   */
  async getAiStrategyRecommendations(params = {}) {
    try {
      const response = await api.post(`${API_BASE}/trading/bots/ai-suggestions`, params);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get AI-based parameter optimizations for a specific strategy
   * @param {string} strategy - Strategy name to optimize
   * @param {Object} marketConditions - Current market conditions
   * @returns {Promise<Object>} Optimized strategy parameters
   */
  async getAiStrategyOptimization(strategy, marketConditions = {}) {
    try {
      const response = await api.post(`${API_BASE}/trading/bots/ai-optimization`, {
        strategy,
        marketConditions
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get popular traders based on performance metrics
   * @param {Object} params - Filter parameters (period, minProfitRate, etc.)
   * @returns {Promise<Array>} List of popular traders and their performance
   */
  async getPopularTraders(params = { period: '1m', limit: 10 }) {
    try {
      const response = await api.get(`${API_BASE}/trading/social/popular-traders`, {
        params
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get traders followed by the current user
   * @returns {Promise<Array>} List of followed traders
   */
  async getFollowedTraders() {
    try {
      const response = await api.get(`${API_BASE}/trading/social/following`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Follow a trader
   * @param {string} traderId - ID of the trader to follow
   * @param {Object} params - Follow parameters (copyTrades, allocationPercentage)
   * @returns {Promise<Object>} Follow status
   */
  async followTrader(traderId, params = { copyTrades: false, allocationPercentage: 0 }) {
    try {
      const response = await api.post(`${API_BASE}/trading/social/follow/${traderId}`, params);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Unfollow a trader
   * @param {string} traderId - ID of the trader to unfollow
   * @returns {Promise<Object>} Unfollow status
   */
  async unfollowTrader(traderId) {
    try {
      const response = await api.delete(`${API_BASE}/trading/social/follow/${traderId}`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get available signals from followed traders
   * @returns {Promise<Array>} List of available trading signals
   */
  async getTradingSignals() {
    try {
      const response = await api.get(`${API_BASE}/trading/social/signals`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Apply a trading signal from another trader
   * @param {string} signalId - ID of the signal to apply
   * @param {Object} params - Signal application parameters
   * @returns {Promise<Object>} Signal application status
   */
  async applyTradingSignal(signalId, params = { allocationPercentage: 5 }) {
    try {
      const response = await api.post(`${API_BASE}/trading/social/signals/${signalId}/apply`, params);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get user notifications related to trading bots and signals
   * @param {Object} params - Filter parameters (read, type, limit, etc.)
   * @returns {Promise<Object>} User notifications with pagination
   */
  async getUserNotifications(params = { limit: 20, page: 1 }) {
    try {
      const response = await api.get(`${API_BASE}/notifications`, {
        params
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Mark notifications as read
   * @param {Array} notificationIds - Array of notification IDs to mark as read
   * @returns {Promise<Object>} Update status
   */
  async markNotificationsRead(notificationIds = []) {
    try {
      const response = await api.post(`${API_BASE}/notifications/mark-read`, {
        notificationIds
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Configure user notification preferences
   * @param {Object} preferences - User notification preferences
   * @returns {Promise<Object>} Updated preferences
   */
  async updateNotificationPreferences(preferences = {}) {
    try {
      const response = await api.put(`${API_BASE}/notifications/preferences`, preferences);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Register device for push notifications
   * @param {Object} deviceInfo - Device information (token, platform)
   * @returns {Promise<Object>} Registration status
   */
  async registerDeviceForPushNotifications(deviceInfo) {
    try {
      const response = await api.post(`${API_BASE}/notifications/devices`, deviceInfo);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get advanced chart data for backtesting with multiple indicators
   * @param {string} symbol - Trading pair symbol
   * @param {string} timeframe - Chart timeframe
   * @param {Array} indicators - Indicators to include in chart data
   * @param {Object} params - Additional parameters (startTime, endTime, etc.)
   * @returns {Promise<Object>} Chart data with indicators
   */
  async getAdvancedChartData(symbol, timeframe, indicators = [], params = {}) {
    try {
      const response = await api.post(`${API_BASE}/trading/charts/advanced`, {
        symbol,
        timeframe,
        indicators,
        ...params
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Run advanced backtest with custom indicators and strategy parameters
   * @param {Object} config - Advanced backtest configuration
   * @returns {Promise<Object>} Advanced backtest results
   */
  async runAdvancedBacktest(config) {
    try {
      const response = await api.post(`${API_BASE}/trading/bots/advanced-backtest`, config);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Apply custom indicators to chart data
   * @param {Array} chartData - Raw chart data
   * @param {Array} indicators - Indicators to apply
   * @returns {Promise<Array>} Chart data with indicators applied
   */
  async applyIndicatorsToChart(chartData, indicators) {
    try {
      const response = await api.post(`${API_BASE}/trading/charts/apply-indicators`, {
        chartData,
        indicators
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get market sentiment analysis
   * @param {string} symbol - Trading pair symbol
   * @param {string} timeframe - Analysis timeframe
   * @returns {Promise<Object>} Market sentiment data
   */
  async getMarketSentiment(symbol, timeframe = '1d') {
    try {
      const response = await api.get(`${API_BASE}/trading/market/sentiment`, {
        params: { symbol, timeframe }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get comparative backtests for multiple strategies
   * @param {Array} configs - Array of backtest configurations to compare
   * @returns {Promise<Object>} Comparative backtest results
   */
  async compareBacktestStrategies(configs) {
    try {
      const response = await api.post(`${API_BASE}/trading/bots/compare-backtest`, {
        configs
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get market regime analysis for a given period
   * @param {string} symbol - Trading pair symbol
   * @param {Object} params - Analysis parameters
   * @returns {Promise<Object>} Market regime analysis data
   */
  async getMarketRegimeAnalysis(symbol, params = {}) {
    try {
      const response = await api.get(`${API_BASE}/trading/market/regime-analysis`, {
        params: { symbol, ...params }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get machine learning price predictions
   * @param {string} symbol - Trading pair symbol
   * @param {string} timeframe - Prediction timeframe
   * @param {string} modelType - Type of ML model to use
   * @returns {Promise<Object>} Price predictions and confidence levels
   */
  async getMlPricePredictions(symbol, timeframe = '1d', modelType = 'ensemble') {
    try {
      const response = await api.get(`${API_BASE}/trading/ml/predictions`, {
        params: { symbol, timeframe, modelType }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get market anomaly detection
   * @param {string} symbol - Trading pair symbol
   * @param {string} timeframe - Analysis timeframe
   * @returns {Promise<Object>} Detected market anomalies
   */
  async getMarketAnomalies(symbol, timeframe = '1d') {
    try {
      const response = await api.get(`${API_BASE}/trading/ml/anomalies`, {
        params: { symbol, timeframe }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get feature importance for ML models
   * @param {string} modelId - ML model ID
   * @returns {Promise<Object>} Feature importance data
   */
  async getFeatureImportance(modelId) {
    try {
      const response = await api.get(`${API_BASE}/trading/ml/feature-importance/${modelId}`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get market regime classification
   * @param {string} symbol - Trading pair symbol
   * @param {string} timeframe - Analysis timeframe
   * @returns {Promise<Object>} Market regime data (trending, ranging, volatile)
   */
  async getMarketRegime(symbol, timeframe = '1d') {
    try {
      const response = await api.get(`${API_BASE}/trading/market/regime`, {
        params: { symbol, timeframe }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get latest crypto news articles
   * @param {string} symbol - Optional symbol to filter news by
   * @param {number} limit - Number of news articles to return
   * @returns {Promise<Array>} Latest news articles
   */
  async getCryptoNews(symbol = '', limit = 10) {
    try {
      const response = await api.get(`${API_BASE}/trading/news`, {
        params: { symbol, limit }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get social media sentiment analysis for cryptocurrencies
   * @param {string} symbol - Trading pair symbol
   * @returns {Promise<Object>} Social media sentiment data
   */
  async getSocialSentiment(symbol) {
    try {
      const response = await api.get(`${API_BASE}/trading/sentiment/social`, {
        params: { symbol }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get news sentiment analysis for cryptocurrencies
   * @param {string} symbol - Trading pair symbol
   * @param {number} days - Number of days to analyze
   * @returns {Promise<Object>} News sentiment data over time
   */
  async getNewsSentiment(symbol, days = 7) {
    try {
      const response = await api.get(`${API_BASE}/trading/sentiment/news`, {
        params: { symbol, days }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get upcoming cryptocurrency events
   * @param {string} symbol - Optional symbol to filter events by
   * @returns {Promise<Array>} Upcoming crypto events
   */
  async getCryptoEvents(symbol = '') {
    try {
      const response = await api.get(`${API_BASE}/trading/events`, {
        params: { symbol }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get detailed risk analysis for portfolio
   * @param {Array} positions - Current positions or portfolio allocation
   * @returns {Promise<Object>} Comprehensive risk analysis
   */
  async getDetailedRiskAnalysis(positions) {
    try {
      const response = await api.post(`${API_BASE}/risk/analysis`, { positions });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get optimal portfolio allocation based on Modern Portfolio Theory
   * @param {Array} assets - List of assets to include
   * @param {string} riskProfile - Risk tolerance profile
   * @returns {Promise<Object>} Optimal portfolio weights
   */
  async getOptimalPortfolioAllocation(assets, riskProfile = 'medium') {
    try {
      const response = await api.post(`${API_BASE}/trading/portfolio/optimize`, { 
        assets, 
        riskProfile 
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get Value at Risk (VaR) analysis for portfolio
   * @param {Array} positions - Current positions
   * @param {number} confidenceLevel - Confidence level percentage (e.g., 95, 99)
   * @returns {Promise<Object>} VaR analysis results
   */
  async getValueAtRisk(positions, confidenceLevel = 95) {
    try {
      const response = await api.post(`${API_BASE}/risk/var`, { 
        positions, 
        confidence_level: confidenceLevel 
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get stress test results for portfolio
   * @param {Array} positions - Current positions
   * @param {string} scenario - Stress test scenario type
   * @returns {Promise<Object>} Stress test results
   */
  async getPortfolioStressTest(positions, scenario = 'bearMarket') {
    try {
      const response = await api.post(`${API_BASE}/risk/stresstest`, { 
        positions, 
        scenario 
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get hedging recommendations for current portfolio
   * @param {Array} positions - Current positions
   * @returns {Promise<Object>} Hedging recommendations
   */
  async getHedgingRecommendations(positions) {
    try {
      const response = await api.post(`${API_BASE}/risk/hedging`, { positions });
      return response.data;
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

export default new TradingBotService();
