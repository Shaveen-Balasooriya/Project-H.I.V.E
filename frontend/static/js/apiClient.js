/**
 * API client for Project H.I.V.E backend services
 * Centralized API client for all API calls including honeypot functionality
 */

class ApiClient {
  /**
   * Fetches available honeypot types
   * @returns {Promise<Array>} Array of honeypot types
   */
  static async getHoneypotTypes() {
    const response = await fetch('/api/honeypot/types');
    if (!response.ok) {
      throw new Error('Failed to fetch honeypot types');
    }
    return await response.json();
  }
  
  /**
   * Checks if a port is available
   * @param {number} port - Port to check
   * @returns {Promise<Object>} Port availability information
   */
  static async checkPortAvailability(port) {
    const response = await fetch(`/api/honeypot/port-check/${port}`);
    return await response.json();
  }
  
  /**
   * Creates a new honeypot
   * @param {Object} honeypotData - Honeypot configuration
   * @returns {Promise<Object>} Created honeypot data
   */
  static async createHoneypot(honeypotData) {
    console.log("Sending honeypot data:", honeypotData);
    
    const response = await fetch("/api/honeypot/create", {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(honeypotData)
    });
    
    console.log("Response status:", response.status);
    const result = await response.json();
    console.log("Response data:", result);
    
    if (!response.ok) {
      const errorMsg = result.detail || result.error || "Failed to deploy honeypot";
      throw new Error(errorMsg);
    }
    
    return result;
  }
  
  /**
   * Gets configuration for a specific honeypot type
   * @param {string} type - Honeypot type
   * @returns {Promise<Object>} Type configuration
   */
  static async getTypeConfig(type) {
    try {
      console.log(`Fetching config for type: ${type}`);
      // Update endpoint to use the correct path pattern that matches backend route
      const endpoint = `/api/honeypot/types/${type}/auth-details`;
      console.log(`API endpoint: ${endpoint}`);
      
      const response = await fetch(endpoint);
      console.log(`Response status: ${response.status}`);
      
      if (!response.ok) {
        console.warn(`Got non-OK response: ${response.status}`);
        // Try to read error message from response
        try {
          const errorData = await response.json();
          console.error("Error response:", errorData);
        } catch (e) {
          console.error("Could not parse error response");
        }
        return null;
      }
      
      const data = await response.json();
      console.log("Config data successfully retrieved:", data);
      return data;
    } catch (err) {
      console.error("Error fetching type config:", err);
      return null;
    }
  }
  
  /**
   * Fetch all honeypots
   * @returns {Promise<Array>} List of honeypots
   */
  static async getAllHoneypots() {
    try {
      // Corrected endpoint to match the controller routes
      const response = await fetch('/api/honeypot/');
      if (!response.ok) {
        throw new Error(`Failed to fetch honeypots: ${response.status} ${response.statusText}`);
      }
      return await response.json();
    } catch (err) {
      console.error("Error fetching honeypots:", err);
      throw err;
    }
  }
  
  /**
   * Start a honeypot
   * @param {string} name - Honeypot name
   * @returns {Promise<Object>} Result of operation
   */
  static async startHoneypot(name) {
    try {
      // Corrected endpoint to match the controller routes
      const response = await fetch(`/api/honeypot/${name}/start`, {
        method: 'POST'
      });
      
      // Check for success or our special handled case
      const result = await response.json();
      
      // Allow both standard success and our custom handled response
      if (response.ok || (result && result.message && result.message.includes('successfully'))) {
        return result;
      }
      
      throw new Error(result.detail || result.error || `Failed to start honeypot: ${response.status} ${response.statusText}`);
    } catch (err) {
      console.error(`Error starting honeypot ${name}:`, err);
      throw err;
    }
  }
  
  /**
   * Stop a honeypot
   * @param {string} name - Honeypot name
   * @returns {Promise<Object>} Result of operation
   */
  static async stopHoneypot(name) {
    try {
      // Corrected endpoint to match the controller routes
      const response = await fetch(`/api/honeypot/${name}/stop`, {
        method: 'POST'
      });
      
      // Check for success or our special handled case
      const result = await response.json();
      
      // Allow both standard success and our custom handled response
      if (response.ok || (result && result.message && result.message.includes('successfully'))) {
        return result;
      }
      
      throw new Error(result.detail || result.error || `Failed to stop honeypot: ${response.status} ${response.statusText}`);
    } catch (err) {
      console.error(`Error stopping honeypot ${name}:`, err);
      throw err;
    }
  }
  
  /**
   * Delete a honeypot
   * @param {string} name - Honeypot name
   * @returns {Promise<Object>} Result of operation
   */
  static async deleteHoneypot(name) {
    try {
      // Corrected endpoint to match the controller routes
      const response = await fetch(`/api/honeypot/${name}`, {
        method: 'DELETE'
      });
      if (!response.ok) {
        throw new Error(`Failed to delete honeypot: ${response.status} ${response.statusText}`);
      }
      return await response.json();
    } catch (err) {
      console.error(`Error deleting honeypot ${name}:`, err);
      throw err;
    }
  }
  
  /**
   * Gets the status of all services
   * @returns {Promise<Object>} Services status information
   */
  static async getServicesStatus() {
    const response = await fetch('/api/service/status');
    if (!response.ok) {
      throw new Error(`Failed to fetch services status: ${response.status} ${response.statusText}`);
    }
    return await response.json();
  }
  
  /**
   * Creates services with admin password
   * @param {string} adminPassword - Admin password for services
   * @returns {Promise<Object>} Create operation result
   */
  static async createServices(adminPassword) {
    const response = await fetch('/api/service/create', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ admin_password: adminPassword })
    });
    
    const result = await response.json();
    
    if (!response.ok) {
      const errorMsg = result.detail || result.error || "Failed to create services";
      throw new Error(errorMsg);
    }
    
    return result;
  }
  
  /**
   * Starts all services
   * @returns {Promise<Object>} Start operation result
   */
  static async startServices() {
    const response = await fetch('/api/service/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    const result = await response.json();
    
    if (!response.ok) {
      const errorMsg = result.detail || result.error || "Failed to start services";
      throw new Error(errorMsg);
    }
    
    return result;
  }
  
  /**
   * Stops all services
   * @returns {Promise<Object>} Stop operation result
   */
  static async stopServices() {
    const response = await fetch('/api/service/stop', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    const result = await response.json();
    
    if (!response.ok) {
      const errorMsg = result.detail || result.error || "Failed to stop services";
      throw new Error(errorMsg);
    }
    
    return result;
  }
  
  /**
   * Deletes all services
   * @returns {Promise<Object>} Delete operation result
   */
  static async deleteServices() {
    const response = await fetch('/api/service/delete', {
      method: 'DELETE'
    });
    
    const result = await response.json();
    
    if (!response.ok) {
      const errorMsg = result.detail || result.error || "Failed to delete services";
      throw new Error(errorMsg);
    }
    
    return result;
  }
  
  /**
   * Restarts all services
   * @returns {Promise<Object>} Restart operation result
   */
  static async restartServices() {
    const response = await fetch('/api/service/restart', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    const result = await response.json();
    
    if (!response.ok) {
      const errorMsg = result.detail || result.error || "Failed to restart services";
      throw new Error(errorMsg);
    }
    
    return result;
  }
}

// Export for module usage
window.ApiClient = ApiClient;
