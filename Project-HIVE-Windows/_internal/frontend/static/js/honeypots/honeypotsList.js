/**
 * Honeypots List Module
 * 
 * Handles fetching and rendering of honeypots list
 */

class HoneypotsList {
  constructor() {
    this.honeypots = [];
    this.listContainer = document.getElementById('honeypots-container');
    this.loadingIndicator = document.getElementById('loading-indicator');
    this.errorContainer = document.getElementById('error-container');
    this.emptyContainer = document.getElementById('empty-container');
    
    // Bind methods
    this.fetchHoneypots = this.fetchHoneypots.bind(this);
    this.renderHoneypots = this.renderHoneypots.bind(this);
    this.renderHoneypot = this.renderHoneypot.bind(this);
    this.refreshList = this.refreshList.bind(this);
    
    // Set up refresh button if it exists
    const refreshButton = document.getElementById('refresh-honeypots');
    if (refreshButton) {
      refreshButton.addEventListener('click', this.refreshList);
    }
  }
  
  /**
   * Initialize the honeypots list
   */
  static init() {
    const instance = new HoneypotsList();
    instance.fetchHoneypots();
    return instance;
  }
  
  /**
   * Fetch honeypots from API
   */
  async fetchHoneypots() {
    try {
      this.showLoading(true);
      
      // Clear any previous errors
      if (this.errorContainer) {
        this.errorContainer.classList.add('hidden');
      }
      
      // Use the ApiClient to fetch honeypots
      this.honeypots = await ApiClient.getAllHoneypots();
      this.renderHoneypots();
    } catch (error) {
      console.error('Failed to fetch honeypots:', error);
      this.showError('Failed to load honeypots. Please try again.');
    } finally {
      this.showLoading(false);
    }
  }
  
  /**
   * Refresh the honeypots list
   */
  async refreshList() {
    const refreshButton = document.getElementById('refresh-honeypots');
    if (refreshButton) {
      // Show loading state on the button without spinning animation
      const originalContent = refreshButton.innerHTML;
      refreshButton.innerHTML = `Loading...`;
      refreshButton.disabled = true;
      
      try {
        await this.fetchHoneypots();
      } finally {
        // Reset button state
        refreshButton.innerHTML = originalContent;
        refreshButton.disabled = false;
      }
    } else {
      await this.fetchHoneypots();
    }
  }
  
  /**
   * Render all honeypots to the page
   */
  renderHoneypots() {
    if (!this.listContainer) return;
    
    // Clear existing content
    this.listContainer.innerHTML = '';
    
    // Check if we have honeypots
    if (!this.honeypots || this.honeypots.length === 0) {
      this.showEmptyState(true);
      return;
    }
    
    // Hide empty state
    this.showEmptyState(false);
    
    // Sort honeypots: running first, then by name
    const sortedHoneypots = [...this.honeypots].sort((a, b) => {
      // First by status (running first)
      if (a.status === 'running' && b.status !== 'running') return -1;
      if (a.status !== 'running' && b.status === 'running') return 1;
      
      // Then by name
      return a.name.localeCompare(b.name);
    });
    
    // Create a grid container for the cards
    const gridContainer = document.createElement('div');
    gridContainer.className = 'honeypot-grid grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4';
    this.listContainer.appendChild(gridContainer);
    
    // Render each honeypot
    sortedHoneypots.forEach(honeypot => {
      const honeypotCard = this.renderHoneypot(honeypot);
      gridContainer.appendChild(honeypotCard);
    });
    
    // Dispatch event that honeypots have been loaded
    document.dispatchEvent(new CustomEvent('honeypots-loaded', {
      detail: { honeypots: this.honeypots }
    }));
  }
  
  /**
   * Render a single honeypot card
   * @param {Object} honeypot - Honeypot data
   * @returns {HTMLElement} - Honeypot card element
   */
  renderHoneypot(honeypot) {
    const isRunning = honeypot.status === 'running';
    
    // Create honeypot card with accent-colored border (secondary color)
    const card = document.createElement('div');
    card.className = 'honeypot-card bg-black/40 border-2 border-accent rounded-lg overflow-hidden shadow-md transition-all hover:shadow-accent/20 hover:shadow-lg';
    card.setAttribute('data-honeypot-id', honeypot.id);
    card.setAttribute('data-honeypot-name', honeypot.name);
    card.setAttribute('data-honeypot-status', honeypot.status);
    card.setAttribute('data-honeypot-type', honeypot.type);
    
    // Create status indicator class based on status
    let statusClass = 'bg-gray-400 text-gray-100'; // default
    let statusText = 'Unknown';
    let statusBg = 'bg-gray-500/20 border-gray-500/30';
    
    if (honeypot.status === 'running') {
      statusClass = 'bg-green-500/20 border-green-500/30 text-green-400';
      statusText = 'Running';
      statusBg = 'bg-green-500/10';
    } else if (honeypot.status === 'exited') {
      statusClass = 'bg-red-500/20 border-red-500/30 text-red-400';
      statusText = 'Stopped';
      statusBg = 'bg-red-500/10';
    } else if (honeypot.status === 'created') {
      statusClass = 'bg-yellow-500/20 border-yellow-500/30 text-yellow-400';
      statusText = 'Created';
      statusBg = 'bg-yellow-500/10';
    }
    
    // Get truncated ID (first 12 chars)
    const shortId = honeypot.id.substring(0, 12);
    
    // Compact card with vertical layout - use accent for internal elements only
    card.innerHTML = `
      <!-- Header with name and status -->
      <div class="bg-accent/20 border-b border-accent/30 p-3">
        <div class="flex items-center justify-between">
          <h3 class="font-display text-lg text-white uppercase truncate mr-2">${honeypot.name}</h3>
          <div class="text-xs font-medium px-2 py-1 rounded-full ${statusBg} border ${statusClass}">
            ${statusText}
          </div>
        </div>
        <div class="text-xs text-white/50 mt-1">ID: ${shortId}</div>
      </div>
      
      <!-- Stacked info items -->
      <div class="flex flex-col divide-y divide-accent/20">
        <div class="p-3 bg-black/20 hover:bg-black/30 transition-colors">
          <div class="text-accent text-xs uppercase font-bold">Type</div>
          <div class="honeypot-type font-medium text-white text-sm">${honeypot.type.toUpperCase()}</div>
        </div>
        <div class="p-3 bg-black/30 hover:bg-black/40 transition-colors">
          <div class="text-accent text-xs uppercase font-bold">Port</div>
          <div class="font-medium text-white text-sm">${honeypot.port}</div>
        </div>
        <div class="p-3 bg-black/20 hover:bg-black/30 transition-colors">
          <div class="text-accent text-xs uppercase font-bold">Image</div>
          <div class="font-medium text-white text-xs truncate" title="${honeypot.image}">${honeypot.image.split('/').pop()}</div>
        </div>
      </div>
      
      <!-- Footer with redesigned buttons that better match the card style -->
      <div class="action-container flex justify-between items-center p-3 bg-black/50 border-t border-accent/30" data-honeypot="${honeypot.name}">
        ${isRunning ? `
          <!-- Left side - Stop button for running honeypots -->
          <div>
            <button class="honeypot-action-btn stop-btn bg-transparent hover:bg-red-500/20 border border-red-500/30 text-white px-4 py-1.5 rounded-md text-xs font-semibold transition-colors" data-action="stop" data-honeypot="${honeypot.name}">
              Stop
            </button>
          </div>
          <!-- Right side - Restart button for running honeypots -->
          <div>
            <button class="honeypot-action-btn restart-btn bg-transparent hover:bg-yellow-500/20 border border-yellow-500/30 text-white px-4 py-1.5 rounded-md text-xs font-semibold transition-colors" data-action="restart" data-honeypot="${honeypot.name}">
              Restart
            </button>
          </div>
        ` : `
          <!-- Left side - Delete button for stopped honeypots -->
          <div>
            <button class="honeypot-action-btn delete-btn bg-transparent hover:bg-red-500/20 border border-red-500/30 text-white px-4 py-1.5 rounded-md text-xs font-semibold transition-colors" data-action="delete" data-honeypot="${honeypot.name}">
              Delete
            </button>
          </div>
          <!-- Right side - Start button for stopped honeypots -->
          <div>
            <button class="honeypot-action-btn start-btn bg-transparent hover:bg-green-500/20 border border-green-500/30 text-white px-4 py-1.5 rounded-md text-xs font-semibold transition-colors" data-action="start" data-honeypot="${honeypot.name}">
              Start
            </button>
          </div>
        `}
      </div>
    `;
    
    return card;
  }
  
  /**
   * Show or hide the loading indicator
   * @param {boolean} show - Whether to show the loading indicator
   */
  showLoading(show) {
    if (!this.loadingIndicator) return;
    
    if (show) {
      this.loadingIndicator.classList.remove('hidden');
      if (this.listContainer) {
        this.listContainer.classList.add('hidden');
      }
    } else {
      this.loadingIndicator.classList.add('hidden');
      if (this.listContainer) {
        this.listContainer.classList.remove('hidden');
      }
    }
  }
  
  /**
   * Show error message
   * @param {string} message - Error message to display
   */
  showError(message) {
    if (!this.errorContainer) return;
    
    // Show error container
    this.errorContainer.classList.remove('hidden');
    
    // Find error message element
    const errorMessage = this.errorContainer.querySelector('.error-message');
    if (errorMessage) {
      errorMessage.textContent = message;
    }
    
    // Hide loading and honeypots
    this.showLoading(false);
    if (this.listContainer) {
      this.listContainer.classList.add('hidden');
    }
  }
  
  /**
   * Show empty state when no honeypots available
   * @param {boolean} show - Whether to show empty state
   */
  showEmptyState(show) {
    if (!this.emptyContainer) return;
    
    if (show) {
      this.emptyContainer.classList.remove('hidden');
      if (this.listContainer) {
        this.listContainer.classList.add('hidden');
      }
    } else {
      this.emptyContainer.classList.add('hidden');
      if (this.listContainer) {
        this.listContainer.classList.remove('hidden');
      }
    }
  }
}

// Export for module usage
window.HoneypotsList = HoneypotsList;
