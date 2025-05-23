// WebSocketService.js - Handles WebSocket connections for real-time data
import { nanoid } from 'nanoid';

class WebSocketService {
  constructor() {
    this.connections = {};
    this.listeners = {};
    this.baseUrl = this._getWebSocketBaseUrl();
    this.clientId = nanoid();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 2000; // Start with 2 seconds delay
  }

  _getWebSocketBaseUrl() {
    // Convert HTTP API URL to WebSocket URL
    // For local development, use localhost if not explicitly set
    const apiUrl = process.env.REACT_APP_API_URL || 
      (window.location.hostname === 'localhost' ? 
        `${window.location.protocol}//${window.location.hostname}:8000/v1` : 
        'https://api.cryptotrading-platform.com/v1');
        
    return apiUrl.replace(/^http/, 'ws').replace(/^https/, 'wss');
  }

  /**
   * Connect to a specific data stream
   * @param {string} dataType - Type of data to subscribe to (e.g., 'market', 'portfolio', 'orders')
   * @returns {Promise} - Resolves when connection is established
   */
  connect(dataType) {
    return new Promise((resolve, reject) => {
      if (this.connections[dataType]) {
        resolve(this.connections[dataType]);
        return;
      }

      const url = `${this.baseUrl}/ws/${dataType}/${this.clientId}`;
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log(`WebSocket connected: ${dataType}`);
        this.connections[dataType] = ws;
        this.reconnectAttempts = 0;
        resolve(ws);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this._notifyListeners(dataType, data);
        } catch (error) {
          console.error('Failed to parse WebSocket message', error);
        }
      };

      ws.onerror = (error) => {
        console.error(`WebSocket error (${dataType}):`, error);
        if (!this.connections[dataType]) {
          reject(error);
        }
      };

      ws.onclose = () => {
        console.warn(`WebSocket closed: ${dataType}`);
        delete this.connections[dataType];
        
        // Try to reconnect if not deliberately disconnected
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1);
          console.log(`Attempting to reconnect in ${delay}ms...`);
          setTimeout(() => this.connect(dataType), delay);
        } else {
          console.error(`Maximum reconnection attempts reached for ${dataType}`);
          // Notify listeners of permanent disconnect
          this._notifyListeners(dataType, { 
            type: 'connection_error', 
            error: 'Connection lost. Please refresh the page.'
          });
        }
      };
    });
  }

  /**
   * Disconnect from a data stream
   * @param {string} dataType - Type of data to unsubscribe from
   */
  disconnect(dataType) {
    if (this.connections[dataType]) {
      this.connections[dataType].close();
      delete this.connections[dataType];
      console.log(`WebSocket disconnected: ${dataType}`);
    }
  }

  /**
   * Disconnect from all data streams
   */
  disconnectAll() {
    Object.keys(this.connections).forEach(dataType => {
      this.disconnect(dataType);
    });
    this.listeners = {};
  }

  /**
   * Add a listener for WebSocket data
   * @param {string} dataType - Type of data to listen for
   * @param {Function} callback - Function to call when data is received
   * @returns {string} - Listener ID for removal
   */
  addListener(dataType, callback) {
    if (!this.listeners[dataType]) {
      this.listeners[dataType] = {};
    }
    
    const listenerId = nanoid();
    this.listeners[dataType][listenerId] = callback;
    return listenerId;
  }

  /**
   * Remove a listener
   * @param {string} dataType - Type of data the listener was registered for
   * @param {string} listenerId - ID of the listener to remove
   */
  removeListener(dataType, listenerId) {
    if (this.listeners[dataType] && this.listeners[dataType][listenerId]) {
      delete this.listeners[dataType][listenerId];
    }
  }

  /**
   * Notify all registered listeners for a data type
   * @param {string} dataType - Type of data received
   * @param {Object} data - Data received from WebSocket
   * @private
   */
  _notifyListeners(dataType, data) {
    if (this.listeners[dataType]) {
      Object.values(this.listeners[dataType]).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in WebSocket listener callback', error);
        }
      });
    }
  }

  /**
   * Get the WebSocket connection for a specific data type
   * @param {string} dataType - Type of data to check connection for
   * @returns {WebSocket|null} - The WebSocket connection object or null if not connected
   */
  getConnection(dataType) {
    if (this.isConnected(dataType)) {
      return this.connections[dataType];
    }
    return null;
  }

  /**
   * Check if connected to a specific data stream
   * @param {string} dataType - Type of data to check connection for
   * @returns {boolean} - True if connected
   */
  isConnected(dataType) {
    return !!this.connections[dataType] && this.connections[dataType].readyState === WebSocket.OPEN;
  }
}

// Create singleton instance
const webSocketService = new WebSocketService();
export default webSocketService;
