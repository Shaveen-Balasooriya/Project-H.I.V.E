/**
 * Service Actions
 * Handles all service-related actions: start all, stop all, restart all, delete all
 */

class ServiceActions {
    constructor() {
        // Initialize on class creation
        this.bindGlobalActions();
        this.actionInProgress = false;
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
     * Disable all action buttons during an operation
     */
    disableActionButtons() {
        const buttons = [
            document.getElementById('start-all-btn'),
            document.getElementById('stop-all-btn'),
            document.getElementById('restart-all-btn'),
            document.getElementById('delete-all-btn'),
            document.getElementById('create-service-btn'),
            document.getElementById('refresh-services')
        ];
        
        buttons.forEach(button => {
            if (button) {
                button.disabled = true;
                button.classList.add('opacity-50', 'cursor-not-allowed');
            }
        });
    }
    
    /**
     * Enable all action buttons after an operation
     */
    enableActionButtons() {
        const buttons = [
            document.getElementById('start-all-btn'),
            document.getElementById('stop-all-btn'),
            document.getElementById('restart-all-btn'),
            document.getElementById('delete-all-btn'),
            document.getElementById('create-service-btn'),
            document.getElementById('refresh-services')
        ];
        
        buttons.forEach(button => {
            if (button) {
                button.disabled = false;
                button.classList.remove('opacity-50', 'cursor-not-allowed');
            }
        });
        
        // Also update button states based on current service status
        this.updateButtonStates();
    }
    
    /**
     * Create services using the admin password
     * @param {string} adminPassword - Admin password for services
     */
    async createServices(adminPassword) {
        if (this.actionInProgress) return;
        this.actionInProgress = true;
        
        if (!adminPassword || adminPassword.trim().length === 0) {
            if (window.serviceUI) {
                window.serviceUI.showNotification('Admin password is required', 'error');
            }
            this.actionInProgress = false;
            return;
        }
        
        try {
            // Disable buttons during operation
            this.disableActionButtons();
            
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
            
            // Refresh the services list immediately
            await this.refreshServicesList();
            
        } catch (error) {
            console.error('Error creating services:', error);
            
            // Show error notification
            if (window.serviceUI) {
                const errorMsg = error.message || "Failed to create services";
                window.serviceUI.showNotification(errorMsg, 'error');
            }
        } finally {
            // Re-enable buttons
            this.enableActionButtons();
            this.actionInProgress = false;
        }
    }
    
    /**
     * Start all services
     */
    async startServices() {
        if (this.actionInProgress) return;
        this.actionInProgress = true;
        
        if (!confirm('Are you sure you want to start all services?')) {
            this.actionInProgress = false;
            return;
        }
        
        try {
            // Disable buttons during operation
            this.disableActionButtons();
            
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
            
            // Refresh the services list - JUST ONCE
            await this.refreshServicesList(1);
            
        } catch (error) {
            console.error('Error starting services:', error);
            
            // Show error notification
            if (window.serviceUI) {
                const errorMsg = error.message || "Failed to start services";
                window.serviceUI.showNotification(errorMsg, 'error');
            }
            
            // Still try to refresh to get updated status - JUST ONCE
            await this.refreshServicesList(1);
        } finally {
            // Re-enable buttons
            this.enableActionButtons();
            this.actionInProgress = false;
        }
    }
    
    /**
     * Stop all services
     */
    async stopServices() {
        if (this.actionInProgress) return;
        this.actionInProgress = true;
        
        if (!confirm('Are you sure you want to stop all services?')) {
            this.actionInProgress = false;
            return;
        }
        
        try {
            // Disable buttons during operation
            this.disableActionButtons();
            
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
            
            // Refresh the services list - JUST ONCE
            await this.refreshServicesList(1);
            
        } catch (error) {
            console.error('Error stopping services:', error);
            
            // Show error notification
            if (window.serviceUI) {
                const errorMsg = error.message || "Failed to stop services";
                window.serviceUI.showNotification(errorMsg, 'error');
            }
            
            // Still try to refresh to get updated status - JUST ONCE
            await this.refreshServicesList(1);
        } finally {
            // Re-enable buttons
            this.enableActionButtons();
            this.actionInProgress = false;
        }
    }
    
    /**
     * Restart all services (using dedicated restart endpoint)
     */
    async restartServices() {
        if (this.actionInProgress) return;
        this.actionInProgress = true;
        
        if (!confirm('Are you sure you want to restart all services?')) {
            this.actionInProgress = false;
            return;
        }
        
        try {
            // Disable buttons during operation
            this.disableActionButtons();
            
            // Show loading notification
            if (window.serviceUI) {
                window.serviceUI.showNotification('Restarting all services...', 'info');
            }
            
            // Use the dedicated restart endpoint
            await ApiClient.restartServices();
            
            // Show success notification
            if (window.serviceUI) {
                window.serviceUI.showNotification('Services restarted successfully', 'success');
            }
            
            // Refresh the services list - JUST ONCE
            await this.refreshServicesList(1);
            
        } catch (error) {
            console.error('Error restarting services:', error);
            
            // Show error notification
            if (window.serviceUI) {
                const errorMsg = error.message || "Failed to restart services";
                window.serviceUI.showNotification(errorMsg, 'error');
            }
            
            // Still try to refresh to get updated status - JUST ONCE
            await this.refreshServicesList(1);
        } finally {
            // Re-enable buttons
            this.enableActionButtons();
            this.actionInProgress = false;
        }
    }
    
    /**
     * Delete all services
     */
    async deleteServices() {
        if (this.actionInProgress) return;
        this.actionInProgress = true;
        
        if (!confirm('Are you sure you want to delete all services? This action cannot be undone.')) {
            this.actionInProgress = false;
            return;
        }
        
        try {
            // Disable buttons during operation
            this.disableActionButtons();
            
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
            
            // Refresh the services list - JUST ONCE
            await this.refreshServicesList(1);
            
        } catch (error) {
            console.error('Error deleting services:', error);
            
            // Show error notification
            if (window.serviceUI) {
                const errorMsg = error.message || "Failed to delete services";
                window.serviceUI.showNotification(errorMsg, 'error');
            }
            
            // Still try to refresh to get updated status - JUST ONCE
            await this.refreshServicesList(1);
        } finally {
            // Re-enable buttons
            this.enableActionButtons();
            this.actionInProgress = false;
        }
    }
    
    /**
     * Refresh the services list with multiple attempts
     * @param {number} attempts - Number of refresh attempts to make
     * @param {number} delay - Delay between attempts in ms
     */
    async refreshServicesList(attempts = 1, delay = 1500) {
        if (!window.servicesList || typeof window.servicesList.refreshList !== 'function') {
            console.error('ServicesList not available for refresh');
            return;
        }
        
        // Only make a single refresh attempt by default
        // This prevents multiple loading screens
        try {
            await window.servicesList.refreshList();
        } catch (error) {
            console.error(`Error refreshing services:`, error);
        }
    }
    
    /**
     * Update button states based on current service status
     */
    updateButtonStates() {
        if (!window.servicesList || !window.servicesList.services) {
            return;
        }
        
        const services = window.servicesList.services;
        const allRunning = services.every(service => service.status.toLowerCase() === 'running');
        const allStopped = services.every(service => 
            service.status.toLowerCase() === 'exited' || 
            service.status.toLowerCase() === 'not found' || 
            service.status.toLowerCase() === 'created'
        );
        const noServices = services.length === 0 || 
            services.every(service => service.status.toLowerCase() === 'not found');
        
        // Get references to all buttons
        const startAllBtn = document.getElementById('start-all-btn');
        const stopAllBtn = document.getElementById('stop-all-btn');
        const restartAllBtn = document.getElementById('restart-all-btn');
        const deleteAllBtn = document.getElementById('delete-all-btn');
        const createServiceBtn = document.getElementById('create-service-btn');
        
        if (startAllBtn && stopAllBtn && restartAllBtn && deleteAllBtn) {
            if (allRunning) {
                // When all services are running, show Stop and Restart buttons
                startAllBtn.style.display = 'none';
                stopAllBtn.style.display = 'flex';
                restartAllBtn.style.display = 'flex';
                deleteAllBtn.style.display = 'none';
            } else if (allStopped) {
                // When all services are stopped, show Start and Delete buttons
                startAllBtn.style.display = 'flex';
                stopAllBtn.style.display = 'none';
                restartAllBtn.style.display = 'none';
                deleteAllBtn.style.display = 'flex';
            } else if (noServices) {
                // When no services exist, only show Start button
                startAllBtn.style.display = 'flex';
                stopAllBtn.style.display = 'none';
                restartAllBtn.style.display = 'none';
                deleteAllBtn.style.display = 'none';
            } else {
                // Mixed state, show all buttons
                startAllBtn.style.display = 'flex';
                stopAllBtn.style.display = 'flex';
                restartAllBtn.style.display = 'flex';
                deleteAllBtn.style.display = 'flex';
            }
        }
        
        // Control the "New Service" button - only enable when no services exist
        if (createServiceBtn) {
            if (noServices) {
                // Enable the button when no services exist
                createServiceBtn.disabled = false;
                createServiceBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                createServiceBtn.title = 'Create new services';
            } else {
                // Disable the button when services already exist
                createServiceBtn.disabled = true;
                createServiceBtn.classList.add('opacity-50', 'cursor-not-allowed');
                createServiceBtn.title = 'Services already exist. Delete them first to create new ones.';
            }
        }
    }
}

// Expose to window
window.serviceActions = new ServiceActions();
console.log("Service actions module loaded");
