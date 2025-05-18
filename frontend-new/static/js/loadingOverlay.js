/**
 * Global Loading Overlay System
 * Provides a full-screen loading indicator with customizable messages
 */

class LoadingOverlay {
  constructor() {
    this.overlay = document.getElementById('loading-overlay');
    this.messageElement = this.overlay ? this.overlay.querySelector('.loading-message') : null;
    this.activeRequests = 0;
    this.defaultMessage = 'Loading...';
    this.timeoutId = null;
    this.minDisplayTime = 500; // Minimum time to show overlay in ms
    this.showStartTime = 0;
    
    // Initialize global AJAX interceptor
    this.setupAjaxInterceptor();
    
    console.log('Loading overlay system initialized');
  }

  /**
   * Shows the loading overlay with a custom message
   * @param {string} message - Optional custom message to display
   * @param {boolean} forceShow - Force showing even if there are other active requests
   */
  show(message = this.defaultMessage, forceShow = false) {
    if (!this.overlay) return;
    
    // Check if the overlay is already visible with the same message
    if (this.activeRequests > 0 && this.messageElement && 
        this.messageElement.textContent === message && !forceShow) {
        console.log(`Loading overlay already showing same message: "${message}"`);
        this.activeRequests++; // Still increment counter for tracking
        return () => this.hide();
    }
    
    // Increment active requests counter
    this.activeRequests++;
    
    // Clear any pending hide timeout
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
    
    // Update message
    if (this.messageElement) {
      this.messageElement.textContent = message;
    }
    
    // Show overlay
    this.overlay.classList.remove('hidden');
    
    // Record the time we showed the overlay
    this.showStartTime = Date.now();
    
    // Prevent scrolling on body
    document.body.style.overflow = 'hidden';
    
    console.log(`Loading overlay shown: "${message}" (${this.activeRequests} active requests)`);
    
    // Return a function that can be called to hide this specific request
    return () => this.hide();
  }

  /**
   * Hides the loading overlay
   * @param {boolean} force - Force hide even if there are other active requests
   */
  hide(force = false) {
    if (!this.overlay) return;
    
    // Decrement active requests counter
    this.activeRequests = Math.max(0, this.activeRequests - 1);
    
    // Only hide if no active requests or forced
    if (this.activeRequests === 0 || force) {
      // Reset counter if forced
      if (force) this.activeRequests = 0;
      
      // Calculate how long the overlay has been shown
      const elapsedTime = Date.now() - this.showStartTime;
      const remainingTime = Math.max(0, this.minDisplayTime - elapsedTime);
      
      // Add delay before hiding to ensure minimum display time
      this.timeoutId = setTimeout(() => {
        this.overlay.classList.add('hidden');
        document.body.style.overflow = '';
        console.log('Loading overlay hidden');
        this.timeoutId = null;
      }, remainingTime);
    } else {
      console.log(`Loading request completed, but ${this.activeRequests} still active`);
    }
  }

  /**
   * Updates the loading message without affecting visibility
   * @param {string} message - New message to display
   */
  updateMessage(message) {
    if (this.messageElement) {
      this.messageElement.textContent = message;
      console.log(`Loading message updated: "${message}"`);
    }
  }

  /**
   * Force resets the overlay state (use in case of errors)
   */
  reset() {
    this.activeRequests = 0;
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
    if (this.overlay) {
      this.overlay.classList.add('hidden');
      document.body.style.overflow = '';
    }
    console.log('Loading overlay reset');
  }
  
  /**
   * Executes a promise while showing the loading overlay
   * @param {Promise} promise - The promise to execute
   * @param {string} message - Message to display during loading
   * @returns {Promise} The original promise
   */
  async withLoader(promise, message = this.defaultMessage) {
    if (!promise || typeof promise.then !== 'function') {
      console.error('Invalid promise provided to withLoader');
      return Promise.reject(new Error('Invalid promise'));
    }
    
    this.show(message);
    
    try {
      const result = await promise;
      this.hide();
      return result;
    } catch (error) {
      this.hide();
      throw error;
    }
  }
  
  /**
   * Setup interceptor for fetch API
   */
  setupAjaxInterceptor() {
    // Store original fetch function
    const originalFetch = window.fetch;
    
    // Override fetch with our intercepted version
    window.fetch = async (...args) => {
      const [resource, config] = args;
      
      // Determine if this is an API call that should show the loader
      const shouldShowLoader = typeof resource === 'string' && 
        (resource.startsWith('/api/') || resource.includes('api'));
        
      // Show loader for API calls
      if (shouldShowLoader) {
        const message = `Loading data${resource.includes('honeypot') ? ' for honeypot' : ''}...`;
        this.show(message);
      }
      
      try {
        // Call original fetch
        const response = await originalFetch(resource, config);
        
        // Clone response before reading it
        const clone = response.clone();
        
        // For API calls, hide loader after processing response
        if (shouldShowLoader) {
          try {
            // Try to parse JSON to see if there's an error message
            const data = await clone.json();
            if (data && data.message) {
              // Show the message briefly before hiding
              this.updateMessage(data.message);
            }
          } catch (e) {
            // JSON parsing failed, but that's okay
          }
          
          // Hide loader with slight delay to ensure minimum display time
          setTimeout(() => this.hide(), 300);
        }
        
        return response;
      } catch (error) {
        // Handle error and hide loader
        if (shouldShowLoader) {
          this.updateMessage(`Error: ${error.message}`);
          setTimeout(() => this.hide(true), 1000);
        }
        throw error;
      }
    };
    
    console.log('Fetch API interceptor configured');
    
    // Add interceptor for button clicks that show "loading" text
    document.addEventListener('click', (event) => {
      const button = event.target.closest('button:not([disabled])');
      if (button && !button.classList.contains('no-loader')) {
        // Check if this button has loading text or spinner
        const hasLoadingState = button.dataset.loading || 
                              button.querySelector('.spinner') ||
                              button.innerHTML.includes('Loading') ||
                              button.innerHTML.includes('Please wait');
                              
        if (hasLoadingState) {
          // Show loading overlay for button actions with loading states
          const action = button.textContent.trim() || 'Action';
          this.show(`Processing ${action}...`);
          
          // Add a timeout to hide the loader if it wasn't hidden by a fetch call
          setTimeout(() => {
            if (this.activeRequests > 0) {
              this.hide();
            }
          }, 5000);
        }
      }
    });
  }
}

// Create global instance
window.loadingOverlay = new LoadingOverlay();

// Enhance the API client with loading overlay integration
document.addEventListener('DOMContentLoaded', function() {
  if (window.ApiClient) {
    // Keep reference to original methods
    const originalMethods = {
      getAllHoneypots: ApiClient.getAllHoneypots,
      getHoneypotTypes: ApiClient.getHoneypotTypes,
      startHoneypot: ApiClient.startHoneypot,
      stopHoneypot: ApiClient.stopHoneypot,
      deleteHoneypot: ApiClient.deleteHoneypot,
      getServicesStatus: ApiClient.getServicesStatus,
      createServices: ApiClient.createServices,
      startServices: ApiClient.startServices,
      stopServices: ApiClient.stopServices,
      deleteServices: ApiClient.deleteServices,
      restartServices: ApiClient.restartServices,
      createHoneypot: ApiClient.createHoneypot,
      checkPortAvailability: ApiClient.checkPortAvailability,
      getTypeConfig: ApiClient.getTypeConfig
    };
    
    // Override methods with loading overlay integration
    ApiClient.getAllHoneypots = function() {
      return window.loadingOverlay.withLoader(
        originalMethods.getAllHoneypots.apply(this, arguments),
        'Loading honeypots...'
      );
    };
    
    ApiClient.getHoneypotTypes = function() {
      return window.loadingOverlay.withLoader(
        originalMethods.getHoneypotTypes.apply(this, arguments),
        'Loading honeypot types...'
      );
    };
    
    ApiClient.startHoneypot = function(name) {
      return window.loadingOverlay.withLoader(
        originalMethods.startHoneypot.apply(this, arguments),
        `Starting honeypot "${name}"...`
      );
    };
    
    ApiClient.stopHoneypot = function(name) {
      return window.loadingOverlay.withLoader(
        originalMethods.stopHoneypot.apply(this, arguments),
        `Stopping honeypot "${name}"...`
      );
    };
    
    ApiClient.deleteHoneypot = function(name) {
      return window.loadingOverlay.withLoader(
        originalMethods.deleteHoneypot.apply(this, arguments),
        `Deleting honeypot "${name}"...`
      );
    };
    
    ApiClient.getServicesStatus = function() {
      return window.loadingOverlay.withLoader(
        originalMethods.getServicesStatus.apply(this, arguments),
        'Fetching services status...'
      );
    };
    
    ApiClient.createServices = function() {
      return window.loadingOverlay.withLoader(
        originalMethods.createServices.apply(this, arguments),
        'Creating services...'
      );
    };
    
    ApiClient.startServices = function() {
      return window.loadingOverlay.withLoader(
        originalMethods.startServices.apply(this, arguments),
        'Starting all services...'
      );
    };
    
    ApiClient.stopServices = function() {
      return window.loadingOverlay.withLoader(
        originalMethods.stopServices.apply(this, arguments),
        'Stopping all services...'
      );
    };
    
    ApiClient.deleteServices = function() {
      return window.loadingOverlay.withLoader(
        originalMethods.deleteServices.apply(this, arguments),
        'Deleting all services...'
      );
    };
    
    ApiClient.restartServices = function() {
      return window.loadingOverlay.withLoader(
        originalMethods.restartServices.apply(this, arguments),
        'Restarting all services...'
      );
    };
    
    ApiClient.createHoneypot = function(data) {
      return window.loadingOverlay.withLoader(
        originalMethods.createHoneypot.apply(this, arguments),
        'Deploying honeypot...'
      );
    };
    
    ApiClient.checkPortAvailability = function(port) {
      return window.loadingOverlay.withLoader(
        originalMethods.checkPortAvailability.apply(this, arguments),
        `Checking port ${port} availability...`
      );
    };
    
    ApiClient.getTypeConfig = function(type) {
      return window.loadingOverlay.withLoader(
        originalMethods.getTypeConfig.apply(this, arguments),
        `Loading configuration for ${type}...`
      );
    };
    
    // Enhance the ApiClient integration for services specifically
    const originalGetServicesStatus = ApiClient.getServicesStatus;
    
    // Add debouncing for service status requests
    let servicesStatusTimer = null;
    ApiClient.getServicesStatus = function() {
      // Clear any pending requests
      if (servicesStatusTimer) {
        clearTimeout(servicesStatusTimer);
      }
      
      return new Promise((resolve, reject) => {
        servicesStatusTimer = setTimeout(() => {
          window.loadingOverlay.withLoader(
            originalGetServicesStatus.apply(this, arguments),
            'Fetching services status...'
          ).then(resolve).catch(reject);
        }, 100); // Short debounce to prevent near-simultaneous calls
      });
    };
    
    console.log('ApiClient enhanced with loading overlay integration');
  }
});

// Add error handling for failed API calls
window.addEventListener('unhandledrejection', function(event) {
  if (window.loadingOverlay) {
    window.loadingOverlay.updateMessage(`Error: ${event.reason.message || 'Operation failed'}`);
    setTimeout(() => window.loadingOverlay.reset(), 1500);
  }
});

// Add DOM mutation observer to detect button state changes
document.addEventListener('DOMContentLoaded', function() {
  // Watch for changes to button text/disabled state
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === 'attributes' && 
          mutation.attributeName === 'disabled' && 
          mutation.target.tagName === 'BUTTON') {
        // Button was enabled after being disabled
        if (mutation.oldValue === 'true' && !mutation.target.disabled) {
          // Hide loader if it's active
          if (window.loadingOverlay && window.loadingOverlay.activeRequests > 0) {
            window.loadingOverlay.hide();
          }
        }
      }
    });
  });
  
  // Observe all buttons in the document
  document.querySelectorAll('button').forEach(button => {
    observer.observe(button, { 
      attributes: true,
      attributeFilter: ['disabled'],
      attributeOldValue: true
    });
  });
});
