import api from './api';

class AuthService {
  async login(email, password, twoFactorCode = null) {
    try {
      const payload = {
        email,
        password,
      };
      
      if (twoFactorCode) {
        payload.twoFactorCode = twoFactorCode;
      }
      
      const response = await api.post('/auth/login', payload);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async register(userData) {
    try {
      const response = await api.post('/auth/register', userData);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async logout() {
    try {
      await api.post('/auth/logout');
      return true;
    } catch (error) {
      console.error('Logout error:', error);
      // Even if API call fails, we still want to clear local storage
      return true;
    }
  }
  
  async refreshToken(refreshToken) {
    try {
      const response = await api.post('/auth/refresh-token', { refreshToken });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getCurrentUser() {
    try {
      const response = await api.get('/users/me');
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async updateProfile(profileData) {
    try {
      const response = await api.put('/users/me', profileData);
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async requestPasswordReset(email) {
    try {
      await api.post('/auth/reset-password-request', { email });
      return true;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async resetPassword(token, newPassword) {
    try {
      await api.post('/auth/reset-password', { token, newPassword });
      return true;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async updatePassword(currentPassword, newPassword) {
    try {
      await api.put('/users/me/password', { currentPassword, newPassword });
      return true;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async enable2FA() {
    try {
      const response = await api.post('/users/me/2fa/enable');
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async verify2FA(code) {
    try {
      await api.post('/users/me/2fa/verify', { code });
      return true;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async disable2FA(code) {
    try {
      await api.post('/users/me/2fa/disable', { code });
      return true;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  _handleError(error) {
    let errorMessage = 'An unexpected error occurred';
    
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const { status, data } = error.response;
      
      if (status === 400 && data.message) {
        errorMessage = data.message;
      } else if (status === 401) {
        errorMessage = 'Authentication failed. Please log in again.';
      } else if (status === 403) {
        errorMessage = 'You do not have permission to perform this action.';
      } else if (status === 404) {
        errorMessage = 'The requested resource was not found.';
      } else if (status === 422 && data.errors) {
        // Validation errors
        errorMessage = Object.values(data.errors)
          .flat()
          .join('. ');
      } else if (data.message) {
        errorMessage = data.message;
      }
    } else if (error.request) {
      // The request was made but no response was received
      errorMessage = 'No response received from server. Please check your connection.';
    }
    
    throw new Error(errorMessage);
  }
}

export default new AuthService();
