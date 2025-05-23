// SocialTradingService.js - Handles social trading features
import api from './api';

// Base API URL
const API_BASE = '';

class SocialTradingService {
  /**
   * Get list of top traders to follow
   * @param {Object} params - Filter parameters
   * @param {number} params.limit - Number of traders to return
   * @param {string} params.sortBy - Sort field ('performance', 'followers', etc.)
   * @param {string} params.period - Performance period ('1d', '1w', '1m', '3m', '1y')
   * @returns {Promise<Array>} List of top traders
   */
  async getTopTraders(params = { limit: 20, sortBy: 'performance', period: '1m' }) {
    try {
      const response = await api.get(`${API_BASE}/social/top-traders`, { params });
      return response.data.traders;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get detailed information about a trader
   * @param {string} traderId - ID of the trader
   * @returns {Promise<Object>} Trader details
   */
  async getTraderProfile(traderId) {
    try {
      const response = await api.get(`${API_BASE}/social/traders/${traderId}`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get a trader's performance history
   * @param {string} traderId - ID of the trader
   * @param {string} period - Performance period ('1w', '1m', '3m', '1y', 'all')
   * @returns {Promise<Object>} Trader performance data
   */
  async getTraderPerformance(traderId, period = '3m') {
    try {
      const response = await api.get(`${API_BASE}/social/traders/${traderId}/performance`, {
        params: { period }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get a trader's recent trades
   * @param {string} traderId - ID of the trader
   * @param {number} limit - Number of trades to return
   * @returns {Promise<Array>} Trader's recent trades
   */
  async getTraderTrades(traderId, limit = 50) {
    try {
      const response = await api.get(`${API_BASE}/social/traders/${traderId}/trades`, {
        params: { limit }
      });
      return response.data.trades;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Follow a trader
   * @param {string} traderId - ID of the trader to follow
   * @param {Object} config - Follow configuration
   * @param {number} config.allocation - Amount to allocate to copying this trader
   * @param {number} config.riskFactor - Risk factor (0.1 to 2.0)
   * @returns {Promise<Object>} Follow status
   */
  async followTrader(traderId, config = { allocation: 0, riskFactor: 1.0 }) {
    try {
      const response = await api.post(`${API_BASE}/social/follow`, {
        traderId,
        ...config
      });
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
      const response = await api.delete(`${API_BASE}/social/follow/${traderId}`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get list of traders the user is following
   * @returns {Promise<Array>} List of followed traders
   */
  async getFollowedTraders() {
    try {
      const response = await api.get(`${API_BASE}/social/following`);
      return response.data.following;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Update follow settings for a trader
   * @param {string} traderId - ID of the trader
   * @param {Object} config - Updated configuration
   * @returns {Promise<Object>} Updated follow status
   */
  async updateFollowSettings(traderId, config) {
    try {
      const response = await api.put(`${API_BASE}/social/follow/${traderId}`, config);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Share a trade on the social platform
   * @param {Object} tradeData - Trade data to share
   * @returns {Promise<Object>} Shared trade status
   */
  async shareTrade(tradeData) {
    try {
      const response = await api.post(`${API_BASE}/social/share-trade`, tradeData);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get social feed of trades and posts
   * @param {Object} params - Filter parameters
   * @returns {Promise<Object>} Social feed data
   */
  async getSocialFeed(params = { page: 1, limit: 20 }) {
    try {
      const response = await api.get(`${API_BASE}/social/feed`, { params });
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

export default new SocialTradingService();
