import api from './api';

// Base API URL
const API_BASE = '/v1';

class ExchangeService {
  async getAllSupportedExchanges() {
    try {
      const response = await api.get(`${API_BASE}/exchanges/supported`);
      return response.data.exchanges;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getUserExchanges() {
    try {
      const response = await api.get(`${API_BASE}/exchanges/user`);
      return response.data.exchanges;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async addExchangeApi(exchangeData) {
    try {
      const response = await api.post(`${API_BASE}/exchanges/api-keys`, exchangeData);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async updateExchangeApi(keyId, exchangeData) {
    try {
      const response = await api.put(`${API_BASE}/exchanges/api-keys/${keyId}`, exchangeData);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async deleteExchangeApi(keyId) {
    try {
      await api.delete(`${API_BASE}/exchanges/api-keys/${keyId}`);
      return true;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async verifyExchangeApi(exchangeData) {
    try {
      const response = await api.post(`${API_BASE}/exchanges/verify`, exchangeData);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getBalances(exchangeId) {
    try {
      const response = await api.get(`${API_BASE}/exchanges/${exchangeId}/balances`);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getOrderHistory(exchangeId, params = {}) {
    try {
      const response = await api.get(`${API_BASE}/exchanges/${exchangeId}/orders`, { params });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async placeOrder(exchangeId, orderData) {
    try {
      const response = await api.post(`${API_BASE}/exchanges/${exchangeId}/orders`, orderData);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async cancelOrder(exchangeId, orderId) {
    try {
      await api.delete(`${API_BASE}/exchanges/${exchangeId}/orders/${orderId}`);
      return true;
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
      } else if (status === 400) {
        errorMessage = 'Invalid exchange data provided.';
      } else if (status === 401) {
        errorMessage = 'Invalid API credentials.';
      } else if (status === 403) {
        errorMessage = 'API key does not have required permissions.';
      } else if (status === 404) {
        errorMessage = 'Exchange not found.';
      } else if (status === 429) {
        errorMessage = 'Rate limit exceeded. Please try again later.';
      } else if (status === 502) {
        errorMessage = 'Exchange API is currently unavailable.';
      }
    } else if (error.request) {
      errorMessage = 'No response received from server. Please check your connection.';
    }
    
    throw new Error(errorMessage);
  }
}

export default new ExchangeService();
