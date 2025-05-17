/**
 * Honeypot Actions Module
 * 
 * Handles actions like start, stop, restart, and delete for honeypots
 */

class HoneypotActions {
  constructor(listInstance) {
    this.listInstance = listInstance;
    this.notificationContainer = document.getElementById('notification-container');
    
    // Action mapping
    this.actionHandlers = {
      start: this.startHoneypot,
      stop: this.stopHoneypot,
      restart: this.restartHoneypot,
      delete: this.deleteHoneypot
    };
    
    // Bind methods
    this.setupActionHandlers = this.setupActionHandlers.bind(this);
    this.showNotification = this.showNotification.bind(this);
    this.startHoneypot = this.startHoneypot.bind(this);
    this.stopHoneypot = this.stopHoneypot.bind(this);
    this.restartHoneypot = this.restartHoneypot.bind(this);
    this.deleteHoneypot = this.deleteHoneypot.bind(this);
    this.handleAction = this.handleAction.bind(this);
    this.confirmAction = this.confirmAction.bind(this);
    
    this.setupActionHandlers();
  }
  
  /**
   * Initialize the honeypot actions
   * @param {HoneypotsList} listInstance - Instance of the HoneypotsList class
   */
  static init(listInstance) {
    return new HoneypotActions(listInstance);
  }
  
  /**
   * Set up event handlers for honeypot actions
   */
  setupActionHandlers() {
    // Use event delegation for action buttons
    document.addEventListener('click', event => {
      const actionButton = event.target.closest('.honeypot-action-btn');
      if (!actionButton) return;
      
      const action = actionButton.dataset.action;
      const honeypotName = actionButton.dataset.honeypot;
      
      if (action && honeypotName) {
        this.handleAction(action, honeypotName, actionButton);
      }
    });
  }
  
  /**
   * Handle honeypot action
   * @param {string} action - Action to perform
   * @param {string} honeypotName - Name of the honeypot
   * @param {HTMLElement} button - Button that triggered the action
   */
  async handleAction(action, honeypotName, button) {
    // For delete, confirm first
    if (action === 'delete') {
      if (!this.confirmAction(action, honeypotName)) {
        return;
      }
    }
    
    // Save original button content for restoration
    const originalContent = button.innerHTML;
    
    // Find the action container and disable all buttons in this card
    const actionContainer = button.closest('.action-container');
    if (actionContainer) {
      const allButtons = actionContainer.querySelectorAll('.honeypot-action-btn');
      allButtons.forEach(btn => {
        btn.disabled = true;
        btn.classList.add('opacity-50', 'cursor-not-allowed');
      });
    }
    
    // Set button to loading state
    button.innerHTML = `
      <span class="flex items-center">
        <svg class="animate-spin h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        ${action.charAt(0).toUpperCase() + action.slice(1)}ing...
      </span>
    `;
    
    try {
      // Call the appropriate action handler
      if (this.actionHandlers[action]) {
        await this.actionHandlers[action].call(this, honeypotName);
      } else {
        console.error(`Unknown action: ${action}`);
        throw new Error(`Unknown action: ${action}`);
      }
    } catch (error) {
      console.error(`Failed to ${action} honeypot:`, error);
      this.showNotification(`Failed to ${action} honeypot: ${error.message || 'Unknown error'}`, 'error');
      
      // If we don't refresh, restore original button state
      if (actionContainer) {
        const allButtons = actionContainer.querySelectorAll('.honeypot-action-btn');
        allButtons.forEach(btn => {
          btn.disabled = false;
          btn.classList.remove('opacity-50', 'cursor-not-allowed');
        });
      }
      button.innerHTML = originalContent;
    } finally {
      // Always refresh the list after a successful action
      await this.listInstance.refreshList();
      
      // If we have the stats module, update it
      if (window.honeypotStats) {
        window.honeypotStats.updateStats();
      }
    }
  }
  
  /**
   * Confirm an action with the user
   * @param {string} action - Action to confirm
   * @param {string} honeypotName - Name of the honeypot
   * @returns {boolean} - Whether the action was confirmed
   */
  confirmAction(action, honeypotName) {
    let confirmMessage = '';
    
    switch (action) {
      case 'delete':
        confirmMessage = `Are you sure you want to delete the honeypot "${honeypotName}"? This action cannot be undone.`;
        break;
      default:
        confirmMessage = `Are you sure you want to ${action} the honeypot "${honeypotName}"?`;
    }
    
    return confirm(confirmMessage);
  }
  
  /**
   * Start a honeypot
   * @param {string} honeypotName - Name of the honeypot to start
   */
  async startHoneypot(honeypotName) {
    const result = await ApiClient.startHoneypot(honeypotName);
    this.showNotification(`Honeypot "${honeypotName}" started successfully`, 'success');
    return result;
  }
  
  /**
   * Stop a honeypot
   * @param {string} honeypotName - Name of the honeypot to stop
   */
  async stopHoneypot(honeypotName) {
    const result = await ApiClient.stopHoneypot(honeypotName);
    this.showNotification(`Honeypot "${honeypotName}" stopped successfully`, 'success');
    return result;
  }
  
  /**
   * Restart a honeypot
   * @param {string} honeypotName - Name of the honeypot to restart
   */
  async restartHoneypot(honeypotName) {
    // First stop the honeypot
    await ApiClient.stopHoneypot(honeypotName);
    // Then start it again
    const result = await ApiClient.startHoneypot(honeypotName);
    this.showNotification(`Honeypot "${honeypotName}" restarted successfully`, 'success');
    return result;
  }
  
  /**
   * Delete a honeypot
   * @param {string} honeypotName - Name of the honeypot to delete
   */
  async deleteHoneypot(honeypotName) {
    const result = await ApiClient.deleteHoneypot(honeypotName);
    this.showNotification(`Honeypot "${honeypotName}" deleted successfully`, 'success');
    return result;
  }
  
  /**
   * Show a notification to the user
   * @param {string} message - Notification message
   * @param {string} type - Notification type (success, error, info)
   */
  showNotification(message, type = 'info') {
    // Create notification if container exists
    if (!this.notificationContainer) return;
    
    // Define classes based on type
    const baseClasses = 'notification p-4 rounded shadow-lg max-w-md';
    let typeClasses = '';
    
    switch (type) {
      case 'success':
        typeClasses = 'bg-green-500/20 border border-green-500/30 text-green-400';
        break;
      case 'error':
        typeClasses = 'bg-red-500/20 border border-red-500/30 text-red-400';
        break;
      case 'info':
      default:
        typeClasses = 'bg-blue-500/20 border border-blue-500/30 text-blue-400';
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `${baseClasses} ${typeClasses} notification-enter`;
    notification.innerHTML = `
      <div class="flex items-center">
        <div class="flex-shrink-0 mr-3">
          ${type === 'success' ? `
            <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          ` : type === 'error' ? `
            <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          ` : `
            <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          `}
        </div>
        <div>${message}</div>
      </div>
    `;
    
    // Add to container
    this.notificationContainer.appendChild(notification);
    
    // Auto-remove after delay
    setTimeout(() => {
      notification.classList.add('notification-exit');
      setTimeout(() => {
        notification.remove();
      }, 300); // Match transition duration
    }, 5000);
  }
}

// Export for module usage
window.HoneypotActions = HoneypotActions;
