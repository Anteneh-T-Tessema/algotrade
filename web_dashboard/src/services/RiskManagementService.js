// RiskManagementService.js - Handles risk management features
import api from './api';

// Base API URL
const API_BASE = '';

class RiskManagementService {
  /**
   * Get risk dashboard data
   * @returns {Promise<Object>} Risk dashboard data
   */
  async getRiskDashboard() {
    try {
      const response = await api.get(`${API_BASE}/trading/risk/dashboard`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get user's risk profile
   * @returns {Promise<Object>} Risk profile data
   */
  async getRiskProfile() {
    try {
      const response = await api.get(`${API_BASE}/trading/risk/profile`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Update user's risk profile
   * @param {Object} riskProfile - Updated risk profile
   * @returns {Promise<Object>} Updated risk profile
   */
  async updateRiskProfile(riskProfile) {
    try {
      const response = await api.put(`${API_BASE}/trading/risk/profile`, riskProfile);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get risk exposure
   * @param {string} period - Period ('1d', '7d', '30d', 'all')
   * @returns {Promise<Object>} Risk exposure data
   */
  async getRiskExposure(period = '30d') {
    try {
      const response = await api.get(`${API_BASE}/trading/risk/exposure`, {
        params: { period }
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get risk alerts
   * @returns {Promise<Array>} Risk alerts
   */
  async getRiskAlerts() {
    try {
      const response = await api.get(`${API_BASE}/trading/risk/alerts`);
      return response.data.alerts;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Configure risk limits
   * @param {Object} limits - Risk limits configuration
   * @returns {Promise<Object>} Updated risk limits
   */
  async configureRiskLimits(limits) {
    try {
      const response = await api.post(`${API_BASE}/trading/risk/limits`, limits);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get position risk analysis
   * @param {string} positionId - ID of the position
   * @returns {Promise<Object>} Position risk data
   */
  async getPositionRisk(positionId) {
    try {
      const response = await api.get(`${API_BASE}/trading/risk/positions/${positionId}`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get portfolio risk metrics
   * @returns {Promise<Object>} Portfolio risk metrics
   */
  async getPortfolioRiskMetrics() {
    try {
      const response = await api.get(`${API_BASE}/trading/risk/portfolio`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Run stress test on portfolio
   * @param {Object} scenario - Stress test scenario
   * @returns {Promise<Object>} Stress test results
   */
  async runStressTest(scenario) {
    try {
      const response = await api.post(`${API_BASE}/trading/risk/stress-test`, scenario);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }

  /**
   * Get predefined stress test scenarios
   * @returns {Promise<Array>} List of stress test scenarios
   */
  async getStressTestScenarios() {
    try {
      const response = await api.get(`${API_BASE}/trading/risk/stress-test/scenarios`);
      return response.data.scenarios;
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

export default new RiskManagementService();
