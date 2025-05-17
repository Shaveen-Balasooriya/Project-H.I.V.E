/**
 * Honeypot UI Module
 * 
 * UI helpers for honeypots page
 */

class HoneypotUI {
  constructor() {
    // Bind methods
    this.createFilterHandlers = this.createFilterHandlers.bind(this);
    this.createSortHandlers = this.createSortHandlers.bind(this);
    
    // Initialize components
    this.createFilterHandlers();
    this.createSortHandlers();
  }
  
  /**
   * Initialize the honeypot UI
   */
  static init() {
    return new HoneypotUI();
  }
  
  /**
   * Set up handlers for filtering honeypots
   */
  createFilterHandlers() {
    const filterButtons = document.querySelectorAll('[data-filter]');
    if (!filterButtons.length) return;
    
    filterButtons.forEach(button => {
      button.addEventListener('click', () => {
        // Remove active class from all buttons
        filterButtons.forEach(btn => {
          btn.classList.remove('bg-accent', 'text-black');
          btn.classList.add('bg-black/50', 'text-white', 'hover:bg-accent/70');
        });
        
        // Add active class to clicked button
        button.classList.add('bg-accent', 'text-black');
        button.classList.remove('bg-black/50', 'text-white', 'hover:bg-accent/70');
        
        // Get filter value
        const filter = button.dataset.filter;
        
        // Apply filter to honeypot cards
        const cards = document.querySelectorAll('.honeypot-card');
        let visibleCount = 0;
        
        cards.forEach(card => {
          if (filter === 'all') {
            card.classList.remove('hidden');
            visibleCount++;
          } else {
            // Check if card status matches filter
            const cardStatus = card.dataset.honeypotStatus;
            if (filter === 'running' && cardStatus === 'running') {
              card.classList.remove('hidden');
              visibleCount++;
            } else if (filter === 'stopped' && cardStatus !== 'running') {
              card.classList.remove('hidden');
              visibleCount++;
            } else {
              card.classList.add('hidden');
            }
          }
        });
        
        // Check if we need to show the empty state
        const emptyContainer = document.getElementById('empty-filtered-container');
        
        if (visibleCount === 0 && emptyContainer) {
          emptyContainer.classList.remove('hidden');
          
          // Update empty message based on filter
          const emptyMessage = emptyContainer.querySelector('.empty-message');
          if (emptyMessage) {
            if (filter === 'running') {
              emptyMessage.textContent = 'No running honeypots found.';
            } else if (filter === 'stopped') {
              emptyMessage.textContent = 'No stopped honeypots found.';
            } else {
              emptyMessage.textContent = 'No honeypots found.';
            }
          }
        } else if (emptyContainer) {
          emptyContainer.classList.add('hidden');
        }
      });
    });
  }
  
  /**
   * Set up handlers for sorting honeypots
   */
  createSortHandlers() {
    const sortSelect = document.getElementById('honeypot-sort');
    if (!sortSelect) return;
    
    sortSelect.addEventListener('change', () => {
      const sortBy = sortSelect.value;
      const container = document.getElementById('honeypots-container');
      if (!container) return;
      
      // Get all cards and convert to array for sorting
      const cards = Array.from(container.querySelectorAll('.honeypot-card'));
      
      // Sort cards based on selected option
      cards.sort((a, b) => {
        switch (sortBy) {
          case 'status':
            // Running first, then by name
            const statusA = a.dataset.honeypotStatus;
            const statusB = b.dataset.honeypotStatus;
            if (statusA === 'running' && statusB !== 'running') return -1;
            if (statusA !== 'running' && statusB === 'running') return 1;
            return a.dataset.honeypotName.localeCompare(b.dataset.honeypotName);
            
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
    });
  }
}

// Export for module usage
window.HoneypotUI = HoneypotUI;
