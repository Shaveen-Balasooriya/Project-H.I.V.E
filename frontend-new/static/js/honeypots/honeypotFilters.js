/**
 * Honeypot Filters Module
 * 
 * Handles advanced filtering and sorting of honeypots
 */

class HoneypotFilters {
  constructor(honeypotsList) {
    this.honeypotsList = honeypotsList;
    this.typeFilterSelect = document.getElementById('type-filter');
    this.statusFilterSelect = document.getElementById('status-filter');
    this.sortSelect = document.getElementById('honeypot-sort');
    this.currentTypeFilter = 'all';
    this.currentStatusFilter = 'all';
    this.currentSort = 'status';
    
    // Bind methods
    this.initFilters = this.initFilters.bind(this);
    this.createTypeFilters = this.createTypeFilters.bind(this);
    this.createStatusFilters = this.createStatusFilters.bind(this);
    this.setupSorting = this.setupSorting.bind(this);
    this.applyFilters = this.applyFilters.bind(this);
    this.applySorting = this.applySorting.bind(this);
    this.getVisibleHoneypots = this.getVisibleHoneypots.bind(this);
    
    // Initialize filters when honeypots are loaded
    document.addEventListener('honeypots-loaded', this.initFilters);
  }
  
  /**
   * Initialize the honeypot filters
   */
  static init(honeypotsList) {
    return new HoneypotFilters(honeypotsList);
  }
  
  /**
   * Initialize filters after honeypots are loaded
   */
  async initFilters() {
    // Get available honeypot types from API
    try {
      const types = await ApiClient.getHoneypotTypes();
      this.createTypeFilters(types);
    } catch (error) {
      console.error('Failed to fetch honeypot types:', error);
      // Create minimal type filter with just "All" option
      this.createTypeFilters([]);
    }
    
    // Create status filters (static values)
    this.createStatusFilters(['created', 'running', 'exited']);
    
    // Setup sorting
    this.setupSorting();
  }
  
  /**
   * Create filters for honeypot types
   * @param {Array} types - Available honeypot types
   */
  createTypeFilters(types) {
    if (!this.typeFilterSelect) return;
    
    // Clear existing options
    this.typeFilterSelect.innerHTML = '';
    
    // Add "All" option first
    const allOption = document.createElement('option');
    allOption.value = 'all';
    allOption.textContent = 'All Types';
    this.typeFilterSelect.appendChild(allOption);
    
    // Add option for each type
    types.forEach(type => {
      const option = document.createElement('option');
      option.value = type;
      option.textContent = type.toUpperCase();
      this.typeFilterSelect.appendChild(option);
    });
    
    // Add change event listener
    this.typeFilterSelect.addEventListener('change', () => {
      this.currentTypeFilter = this.typeFilterSelect.value;
      this.applyFilters();
    });
  }
  
  /**
   * Create filters for honeypot statuses
   * @param {Array} statuses - Available honeypot statuses
   */
  createStatusFilters(statuses) {
    if (!this.statusFilterSelect) return;
    
    // Clear existing options
    this.statusFilterSelect.innerHTML = '';
    
    // Add "All" option first
    const allOption = document.createElement('option');
    allOption.value = 'all';
    allOption.textContent = 'All Status';
    this.statusFilterSelect.appendChild(allOption);
    
    // Add option for each status with proper capitalization
    const statusDisplayNames = {
      'created': 'Created',
      'running': 'Running',
      'exited': 'Stopped'
    };
    
    statuses.forEach(status => {
      const displayStatus = statusDisplayNames[status] || status.charAt(0).toUpperCase() + status.slice(1);
      
      const option = document.createElement('option');
      option.value = status;
      option.textContent = displayStatus;
      this.statusFilterSelect.appendChild(option);
    });
    
    // Add change event listener
    this.statusFilterSelect.addEventListener('change', () => {
      this.currentStatusFilter = this.statusFilterSelect.value;
      this.applyFilters();
    });
  }
  
  /**
   * Setup sorting functionality
   */
  setupSorting() {
    if (!this.sortSelect) return;
    
    // Add change event listener if not already set up
    if (!this.sortSelect._hasChangeListener) {
      this.sortSelect.addEventListener('change', () => {
        this.currentSort = this.sortSelect.value;
        this.applySorting();
      });
      this.sortSelect._hasChangeListener = true;
    }
  }
  
  /**
   * Apply current filters to honeypots
   */
  applyFilters() {
    const cards = document.querySelectorAll('.honeypot-card');
    let visibleCount = 0;
    
    cards.forEach(card => {
      // Get card data
      const cardType = card.querySelector('.honeypot-type').textContent.toLowerCase();
      const cardStatus = card.dataset.honeypotStatus;
      
      // Check type filter
      const typeMatch = this.currentTypeFilter === 'all' || cardType === this.currentTypeFilter.toLowerCase();
      
      // Check status filter
      const statusMatch = this.currentStatusFilter === 'all' || 
                          (this.currentStatusFilter === 'running' && cardStatus === 'running') ||
                          (this.currentStatusFilter === 'created' && cardStatus === 'created') ||
                          (this.currentStatusFilter === 'exited' && cardStatus === 'exited');
      
      // Show or hide card
      if (typeMatch && statusMatch) {
        card.classList.remove('hidden');
        visibleCount++;
      } else {
        card.classList.add('hidden');
      }
    });
    
    // Show empty state if no visible cards
    const emptyContainer = document.getElementById('empty-filtered-container');
    if (emptyContainer) {
      if (visibleCount === 0) {
        emptyContainer.classList.remove('hidden');
        
        // Update message based on filters
        const emptyMessage = emptyContainer.querySelector('.empty-message');
        if (emptyMessage) {
          if (this.currentTypeFilter !== 'all' && this.currentStatusFilter !== 'all') {
            emptyMessage.textContent = `No ${this.currentStatusFilter} honeypots of type ${this.currentTypeFilter.toUpperCase()} found.`;
          } else if (this.currentTypeFilter !== 'all') {
            emptyMessage.textContent = `No honeypots of type ${this.currentTypeFilter.toUpperCase()} found.`;
          } else if (this.currentStatusFilter !== 'all') {
            const statusDisplay = this.currentStatusFilter === 'running' ? 'running' :
                               this.currentStatusFilter === 'created' ? 'created' :
                               this.currentStatusFilter === 'exited' ? 'stopped' : 
                               this.currentStatusFilter;
            emptyMessage.textContent = `No ${statusDisplay} honeypots found.`;
          } else {
            emptyMessage.textContent = 'No honeypots match your current filters.';
          }
        }
      } else {
        emptyContainer.classList.add('hidden');
      }
    }
    
    // Apply sorting after filtering
    this.applySorting();
    
    // Dispatch event that filters have been applied
    document.dispatchEvent(new CustomEvent('honeypots-filtered', { 
      detail: { visibleCount } 
    }));
  }
  
  /**
   * Apply current sorting to honeypots
   */
  applySorting() {
    const container = document.querySelector('.honeypot-grid');
    if (!container) return;
    
    // Get all cards
    const cards = Array.from(container.querySelectorAll('.honeypot-card:not(.hidden)'));
    
    // Sort cards based on selected option
    cards.sort((a, b) => {
      switch (this.currentSort) {
        case 'status':
          // Running first, then by name
          const statusA = a.dataset.honeypotStatus;
          const statusB = b.dataset.honeypotStatus;
          if (statusA === 'running' && statusB !== 'running') return -1;
          if (statusA !== 'running' && statusB === 'running') return 1;
          return a.dataset.honeypotName.localeCompare(b.dataset.honeypotName);
          
        case 'type-asc':
          const typeA = a.querySelector('.honeypot-type').textContent.toLowerCase();
          const typeB = b.querySelector('.honeypot-type').textContent.toLowerCase();
          return typeA.localeCompare(typeB);
          
        case 'type-desc':
          const typeADesc = a.querySelector('.honeypot-type').textContent.toLowerCase();
          const typeBDesc = b.querySelector('.honeypot-type').textContent.toLowerCase();
          return typeBDesc.localeCompare(typeADesc);
          
        case 'name-asc':
          return a.dataset.honeypotName.localeCompare(b.dataset.honeypotName);
          
        case 'name-desc':
          return b.dataset.honeypotName.localeCompare(a.dataset.honeypotName);
          
        default:
          return 0;
      }
    });
    
    // Remove all cards
    cards.forEach(card => card.remove());
    
    // Re-append in sorted order
    cards.forEach(card => container.appendChild(card));
  }
  
  /**
   * Get number of visible honeypots
   * @returns {number} Number of visible honeypots
   */
  getVisibleHoneypots() {
    return document.querySelectorAll('.honeypot-card:not(.hidden)').length;
  }
}

// Export for module usage
window.HoneypotFilters = HoneypotFilters;
