// SettingsService.js - Handles user settings and preferences
import api from './api';

// Base API URL
const API_BASE = '/v1';

class SettingsService {
  /**
   * Get user's dashboard preferences
   * @returns {Promise<Object>} User's dashboard preferences
   */
  async getDashboardPreferences() {
    try {
      const response = await api.get(`${API_BASE}/settings/dashboard-preferences`);
      return response.data;
    } catch (error) {
      this._handleError(error);
      return this._getDefaultDashboardPreferences();
    }
  }

  /**
   * Update user's dashboard preferences
   * @param {Object} preferences - Dashboard preferences to update
   * @returns {Promise<Object>} Updated preferences
   */
  async updateDashboardPreferences(preferences) {
    try {
      const response = await api.put(`${API_BASE}/settings/dashboard-preferences`, preferences);
      return response.data;
    } catch (error) {
      this._handleError(error);
      return preferences; // Return input preferences as fallback
    }
  }

  /**
   * Get user's chart preferences
   * @param {string} chartType - Type of chart (e.g., 'price', 'depth', 'volume')
   * @returns {Promise<Object>} User's chart preferences
   */
  async getChartPreferences(chartType = 'price') {
    try {
      const response = await api.get(`${API_BASE}/settings/chart-preferences`, {
        params: { chartType }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
      return this._getDefaultChartPreferences(chartType);
    }
  }

  /**
   * Update user's chart preferences
   * @param {Object} preferences - Chart preferences to update
   * @param {string} chartType - Type of chart (e.g., 'price', 'depth', 'volume')
   * @returns {Promise<Object>} Updated chart preferences
   */
  async updateChartPreferences(preferences, chartType = 'price') {
    try {
      const response = await api.put(`${API_BASE}/settings/chart-preferences`, {
        ...preferences,
        chartType
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
      return preferences; // Return input preferences as fallback
    }
  }

  /**
   * Get user's notification settings
   * @returns {Promise<Object>} User's notification settings
   */
  async getNotificationSettings() {
    try {
      const response = await api.get(`${API_BASE}/settings/notifications`);
      return response.data;
    } catch (error) {
      this._handleError(error);
      return this._getDefaultNotificationSettings();
    }
  }

  /**
   * Update user's notification settings
   * @param {Object} settings - Notification settings to update
   * @returns {Promise<Object>} Updated notification settings
   */
  async updateNotificationSettings(settings) {
    try {
      const response = await api.put(`${API_BASE}/settings/notifications`, settings);
      return response.data;
    } catch (error) {
      this._handleError(error);
      return settings; // Return input settings as fallback
    }
  }

  /**
   * Get user's API keys for different exchanges
   * @returns {Promise<Array>} List of user's API keys
   */
  async getApiKeys() {
    try {
      const response = await api.get(`${API_BASE}/settings/api-keys`);
      return response.data.apiKeys;
    } catch (error) {
      this._handleError(error);
      return [];
    }
  }

  /**
   * Add a new API key
   * @param {Object} keyData - API key data
   * @returns {Promise<Object>} Added API key
   */
  async addApiKey(keyData) {
    try {
      const response = await api.post(`${API_BASE}/settings/api-keys`, keyData);
      return response.data;
    } catch (error) {
      this._handleError(error);
      throw error;
    }
  }

  /**
   * Update an existing API key
   * @param {string} keyId - ID of the API key to update
   * @param {Object} keyData - Updated API key data
   * @returns {Promise<Object>} Updated API key
   */
  async updateApiKey(keyId, keyData) {
    try {
      const response = await api.put(`${API_BASE}/settings/api-keys/${keyId}`, keyData);
      return response.data;
    } catch (error) {
      this._handleError(error);
      throw error;
    }
  }

  /**
   * Delete an API key
   * @param {string} keyId - ID of the API key to delete
   * @returns {Promise<boolean>} Success status
   */
  async deleteApiKey(keyId) {
    try {
      await api.delete(`${API_BASE}/settings/api-keys/${keyId}`);
      return true;
    } catch (error) {
      this._handleError(error);
      return false;
    }
  }

  // Private methods for fallback data

  _getDefaultDashboardPreferences() {
    return {
      layout: "2-column",
      defaultTimeframe: "1D",
      favoriteSymbols: ["BTCUSDT", "ETHUSDT"],
      defaultExchange: "binance",
      widgetsOrder: [
        "portfolio-summary",
        "price-chart",
        "trading-history",
        "open-orders"
      ],
      theme: "dark",
      hiddenWidgets: [],
      advanced: {
        showTradingVolume: true,
        autoRefresh: true,
        refreshInterval: 30
      }
    };
  }

  _getDefaultChartPreferences(chartType) {
    if (chartType === 'price') {
      return {
        indicators: ["MA", "MACD", "RSI"],
        timeframe: "1h",
        chartStyle: "candles",
        showVolume: true,
        colorTheme: "dark"
      };
    } else if (chartType === 'depth') {
      return {
        precision: "0.01",
        showBothSides: true,
        maxDepth: 500
      };
    }
    
    return {};
  }

  _getDefaultNotificationSettings() {
    return {
      email: true,
      push: true,
      sms: false,
      telegram: false,
      notifyOn: {
        orderFilled: true,
        orderCanceled: false,
        priceAlert: true,
        strategyStartStop: true,
        loginAttempts: true,
        apiKeyUsage: false
      }
    };
  }

  _handleError(error) {
    console.error('Settings Service Error:', error);
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      console.error('Error data:', error.response.data);
      console.error('Error status:', error.response.status);
    } else if (error.request) {
      // The request was made but no response was received
      console.error('Error request:', error.request);
    } else {
      // Something happened in setting up the request that triggered an Error
      console.error('Error message:', error.message);
    }
  }
}

// Create singleton instance
const settingsService = new SettingsService();
export default settingsService;
