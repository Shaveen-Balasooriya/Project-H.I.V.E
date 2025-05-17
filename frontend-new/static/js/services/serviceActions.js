/**
 * Service Actions
 * Handles all service-related actions: start all, stop all, restart all, delete all
 */

class ServiceActions {
    constructor() {
        // Initialize on class creation
        this.bindGlobalActions();
    }

    /**
     * Bind event listeners to global action buttons
     */
    bindGlobalActions() {
        // Start all services button
        const startAllBtn = document.getElementById('start-all-btn');
        if (startAllBtn) {
            startAllBtn.addEventListener('click', () => this.startServices());
        }
        
        // Stop all services button
        const stopAllBtn = document.getElementById('stop-all-btn');
        if (stopAllBtn) {
            stopAllBtn.addEventListener('click', () => this.stopServices());
        }
        
        // Restart all services button
        const restartAllBtn = document.getElementById('restart-all-btn');
        if (restartAllBtn) {
            restartAllBtn.addEventListener('click', () => this.restartServices());
        }
        
        // Delete all services button
        const deleteAllBtn = document.getElementById('delete-all-btn');
        if (deleteAllBtn) {
            deleteAllBtn.addEventListener('click', () => this.deleteServices());
        }
        
        console.log("Service action buttons initialized");
    }
    
    /**
     * Create services using the admin password
     * @param {string} adminPassword - Admin password for services
     */
    async createServices(adminPassword) {
        if (!adminPassword || adminPassword.trim().length === 0) {
            if (window.serviceUI) {
                window.serviceUI.showNotification('Admin password is required', 'error');
            }
            return;
        }
        
        try {
            // Show loading notification
            if (window.serviceUI) {
                window.serviceUI.showNotification('Creating services...', 'info');
            }
            
            // Send API request 
            await ApiClient.createServices(adminPassword);
            
            // Show success notification
            if (window.serviceUI) {
                window.serviceUI.showNotification('Services created successfully', 'success');
            }
            
            // Refresh the services list after a short delay
            setTimeout(() => {
                if (window.servicesList && typeof window.servicesList.refreshList === 'function') {
                    window.servicesList.refreshList();
                }
            }, 1000);
            
        } catch (error) {
            console.error('Error creating services:', error);
            
            // Show error notification
            if (window.serviceUI) {
                const errorMsg = error.message || "Failed to create services";
                window.serviceUI.showNotification(errorMsg, 'error');
            }
        }
    }
    
    /**
     * Start all services
     */
    async startServices() {
        if (!confirm('Are you sure you want to start all services?')) return;
        
        try {
            // Show loading notification
            if (window.serviceUI) {
                window.serviceUI.showNotification('Starting all services...', 'info');
            }
            
            // Send API request 
            await ApiClient.startServices();
            
            // Show success notification
            if (window.serviceUI) {
                window.serviceUI.showNotification('Services started successfully', 'success');
            }
            
            // Refresh the services list after a short delay
            setTimeout(() => {
                if (window.servicesList && typeof window.servicesList.refreshList === 'function') {
                    window.servicesList.refreshList();
                }
            }, 1000);
            
        } catch (error) {
            console.error('Error starting services:', error);
            
            // Show error notification
            if (window.serviceUI) {
                const errorMsg = error.message || "Failed to start services";
                window.serviceUI.showNotification(errorMsg, 'error');
            }
        }
    }
    
    /**
     * Stop all services
     */
    async stopServices() {
        if (!confirm('Are you sure you want to stop all services?')) return;
        
        try {
            // Show loading notification
            if (window.serviceUI) {
                window.serviceUI.showNotification('Stopping all services...', 'info');
            }
            
            // Send API request 
            await ApiClient.stopServices();
            
            // Show success notification
            if (window.serviceUI) {
                window.serviceUI.showNotification('Services stopped successfully', 'success');
            }
            
            // Refresh the services list after a short delay
            setTimeout(() => {
                if (window.servicesList && typeof window.servicesList.refreshList === 'function') {
                    window.servicesList.refreshList();
                }
            }, 1000);
            
        } catch (error) {
            console.error('Error stopping services:', error);
            
            // Show error notification
            if (window.serviceUI) {
                const errorMsg = error.message || "Failed to stop services";
                window.serviceUI.showNotification(errorMsg, 'error');
            }
        }
    }
    
    /**
     * Restart all services (stop then start)
     */
    async restartServices() {
        if (!confirm('Are you sure you want to restart all services?')) return;
        
        try {
            // Show loading notification
            if (window.serviceUI) {
                window.serviceUI.showNotification('Restarting all services...', 'info');
            }
            
            // Stop services
            await ApiClient.stopServices();
            
            // Wait a bit before starting
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Start services
            await ApiClient.startServices();
            
            // Show success notification
            if (window.serviceUI) {
                window.serviceUI.showNotification('Services restarted successfully', 'success');
            }
            
            // Refresh the services list after a short delay
            setTimeout(() => {
                if (window.servicesList && typeof window.servicesList.refreshList === 'function') {
                    window.servicesList.refreshList();
                }
            }, 1000);
            
        } catch (error) {
            console.error('Error restarting services:', error);
            
            // Show error notification
            if (window.serviceUI) {
                const errorMsg = error.message || "Failed to restart services";
                window.serviceUI.showNotification(errorMsg, 'error');
            }
        }
    }
    
    /**
     * Delete all services
     */
    async deleteServices() {
        if (!confirm('Are you sure you want to delete all services? This action cannot be undone.')) return;
        
        try {
            // Show loading notification
            if (window.serviceUI) {
                window.serviceUI.showNotification('Deleting all services...', 'info');
            }
            
            // Send API request 
            await ApiClient.deleteServices();
            
            // Show success notification
            if (window.serviceUI) {
                window.serviceUI.showNotification('Services deleted successfully', 'success');
            }
            
            // Refresh the services list after a short delay
            setTimeout(() => {
                if (window.servicesList && typeof window.servicesList.refreshList === 'function') {
                    window.servicesList.refreshList();
                }
            }, 1000);
            
        } catch (error) {
            console.error('Error deleting services:', error);
            
            // Show error notification
            if (window.serviceUI) {
                const errorMsg = error.message || "Failed to delete services";
                window.serviceUI.showNotification(errorMsg, 'error');
            }
        }
    }
}

// Expose to window
window.serviceActions = new ServiceActions();
console.log("Service actions module loaded");
