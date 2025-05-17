/**
 * Honeypot API - Utility for making API calls to the honeypot backend
 * This file centralizes all backend communication through the Flask proxy
 */

// Create the global HoneypotAPI object
window.HoneypotAPI = {
    // Base path for all API requests
    basePath: '/api/honeypot',
    
    /**
     * Check if a port is available
     * @param {number|string} port - The port number to check
     * @returns {Promise<Object>} - Response with available status and message
     */
    async checkPort(port) {
        try {
            const response = await fetch(`${this.basePath}/port-check/${port}`);
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || `Error checking port: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error("Port check error:", error);
            // Return a structured error response
            return {
                available: false,
                message: `Error checking port: ${error.message}. Please verify manually.`
            };
        }
    },
    
    /**
     * Get available honeypot types
     * @returns {Promise<Array<string>>} - List of honeypot types
     */
    async getTypes() {
        try {
            const response = await fetch(`${this.basePath}/types`);
            
            if (!response.ok) {
                throw new Error(`Error fetching honeypot types: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error getting honeypot types:', error);
            // Return default types as fallback
            return ["ssh", "ftp", "http"];
        }
    },
    
    /**
     * Get authentication details for a honeypot type
     * @param {string} type - The honeypot type
     * @returns {Promise<Object>} - Authentication details and banner
     */
    async getTypeAuthDetails(type) {
        try {
            console.log(`Fetching auth details for ${type}...`);
            const response = await fetch(`${this.basePath}/types/${type}/auth-details`);
            
            if (!response.ok) {
                console.warn(`Auth details response not OK: ${response.status}`);
                // Return default values
                return this._getDefaultAuthDetails(type);
            }
            
            const data = await response.json();
            console.log('Auth details received:', data);
            return data;
        } catch (error) {
            console.error(`Error getting auth details for ${type}:`, error);
            // Return fallback default values when backend is unavailable
            return this._getDefaultAuthDetails(type);
        }
    },
    
    /**
     * Create a new honeypot
     * @param {Object} data - Honeypot configuration
     * @returns {Promise<Object>} - Created honeypot details
     */
    async createHoneypot(data) {
        try {
            const response = await fetch(`${this.basePath}`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json' 
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: `Failed to create honeypot: ${response.status}` }));
                throw new Error(errorData.detail || `Failed to create honeypot: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error("Create honeypot error:", error);
            throw error;
        }
    },
    
    /**
     * Get default authentication details for a honeypot type
     * @private
     * @param {string} type - The honeypot type
     * @returns {Object} - Default authentication details and banner
     */
    _getDefaultAuthDetails(type) {
        let banner = "";
        
        // Default banners based on honeypot type
        switch(type.toLowerCase()) {
            case "ssh":
                banner = "SSH-2.0-OpenSSH_7.6p1 Ubuntu-4ubuntu0.3";
                break;
            case "ftp":
                banner = "220 ProFTPD 1.3.5e Server [ftp.example.com] FTP server ready";
                break;
            case "http":
                banner = "Apache/2.4.41 (Ubuntu)";
                break;
            default:
                banner = `Welcome to ${type.toUpperCase()} Server`;
        }
        
        // Default credentials
        return {
            authentication: {
                allowed_users: [
                    { username: "admin", password: "admin123" },
                    { username: "root", password: "toor" },
                    { username: "user", password: "password" }
                ]
            },
            banner: banner
        };
    }
};

console.log('HoneypotAPI utility loaded successfully');
