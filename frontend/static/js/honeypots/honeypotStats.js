/**
 * Honeypot Statistics Module
 * 
 * Handles honeypot statistics and enforces limits
 */

class HoneypotStats {
  constructor(honeypotsList) {
    this.honeypotsList = honeypotsList;
    this.maxHoneypots = 5;
    this.statsContainer = document.getElementById('honeypot-stats');
    this.createButton = document.querySelector('a[href="/honeypot-builder"]');
    
    // Bind methods
    this.updateStats = this.updateStats.bind(this);
    this.checkLimits = this.checkLimits.bind(this);
    
    // Initialize stats when honeypots are loaded
    document.addEventListener('honeypots-loaded', this.updateStats);
    document.addEventListener('honeypots-filtered', (e) => {
      this.updateFilteredStats(e.detail.visibleCount);
    });
  }
  
  /**
   * Initialize the honeypot statistics
   */
  static init(honeypotsList) {
    return new HoneypotStats(honeypotsList);
  }
  
  /**
   * Update honeypot statistics
   */
  updateStats() {
    if (!this.statsContainer) {
      this.createStatsContainer();
    }
    
    const totalCount = this.honeypotsList.honeypots.length;
    const runningCount = this.honeypotsList.honeypots.filter(h => h.status === 'running').length;
    
    this.statsContainer.innerHTML = `
      <div class="flex items-center text-white/70 text-base font-medium"> <!-- Changed text-sm to text-base and added font-medium -->
        <span class="mr-2">Total Honeypots:</span>
        <span class="text-accent font-bold text-lg mr-4">${totalCount}</span> <!-- Added text-lg and mr-4 for more spacing -->
        <span class="mx-2 text-white/40 hidden md:inline">|</span>
        <span class="mr-2">Running:</span>
        <span class="text-green-400 font-bold text-lg mr-4">${runningCount}</span> <!-- Added text-lg and mr-4 for more spacing -->
        <span class="mx-2 text-white/40 hidden md:inline">|</span>
        <span class="mr-2">Limit:</span>
        <span class="${totalCount >= this.maxHoneypots ? 'text-red-400' : 'text-white/70'} font-bold text-lg">${totalCount}/${this.maxHoneypots}</span> <!-- Added text-lg -->
      </div>
    `;
    
    this.checkLimits();
  }
  
  /**
   * Update filtered honeypot statistics
   * @param {number} visibleCount - Number of visible honeypots
   */
  updateFilteredStats(visibleCount) {
    const totalCount = this.honeypotsList.honeypots.length;
    
    if (visibleCount !== totalCount && this.statsContainer) {
      const filterCountEl = this.statsContainer.querySelector('.filtered-count');
      
      if (filterCountEl) {
        filterCountEl.textContent = visibleCount;
      } else {
        // Add filtered count if it doesn't exist
        const countDiv = document.createElement('div');
        countDiv.className = 'text-white/70 text-sm mt-1';
        countDiv.innerHTML = `
          <span class="mr-2 font-medium">Filtered:</span>
          <span class="filtered-count text-accent font-bold">${visibleCount}</span>
          <span class="mx-1">of</span>
          <span class="text-white font-bold">${totalCount}</span>
          <span class="mx-1">shown</span>
        `;
        this.statsContainer.appendChild(countDiv);
      }
    } else if (this.statsContainer) {
      // Remove filtered count if all honeypots are visible
      const filterCountEl = this.statsContainer.querySelector('.filtered-count')?.closest('div');
      if (filterCountEl) {
        filterCountEl.remove();
      }
    }
  }
  
  /**
   * Create stats container if it doesn't exist
   */
  createStatsContainer() {
    if (!this.statsContainer) {
      this.statsContainer = document.createElement('div');
      this.statsContainer.id = 'honeypot-stats';
      this.statsContainer.className = 'mb-2 bg-black/20 rounded-lg p-2';
      
      // Find control bar to insert stats before
      const controlBar = document.querySelector('.control-bar');
      if (controlBar) {
        controlBar.parentNode.insertBefore(this.statsContainer, controlBar);
      } else {
        // Fallback - insert at the beginning of the main container
        const mainContainer = document.querySelector('.max-w-7xl');
        if (mainContainer) {
          mainContainer.insertBefore(this.statsContainer, mainContainer.firstChild);
        }
      }
    }
  }
  
  /**
   * Check if honeypot limit is reached and update UI accordingly
   */
  checkLimits() {
    if (!this.createButton) return;
    
    const totalCount = this.honeypotsList.honeypots.length;
    
    if (totalCount >= this.maxHoneypots) {
      // Disable create button
      this.createButton.classList.add('opacity-50', 'cursor-not-allowed', 'pointer-events-none');
      
      // Add tooltip explaining the limit
      this.createButton.setAttribute('title', `Maximum limit of ${this.maxHoneypots} honeypots reached`);
      
      // Optionally change button appearance
      this.createButton.classList.remove('bg-accent/80', 'hover:bg-accent');
      this.createButton.classList.add('bg-gray-500/50');
      
      // Replace the create button with a disabled version
      const originalHTML = this.createButton.innerHTML;
      this.createButton.innerHTML = `
        <span class="flex items-center opacity-60">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Limit Reached
        </span>
      `;
      
      // Store original HTML for later restoration if honeypots are deleted
      this.createButton.dataset.originalHtml = originalHTML;
    } else if (this.createButton.classList.contains('opacity-50')) {
      // Re-enable create button if it was previously disabled
      this.createButton.classList.remove('opacity-50', 'cursor-not-allowed', 'pointer-events-none', 'bg-gray-500/50');
      this.createButton.classList.add('bg-accent/80', 'hover:bg-accent');
      this.createButton.removeAttribute('title');
      
      // Restore original HTML if it was stored
      if (this.createButton.dataset.originalHtml) {
        this.createButton.innerHTML = this.createButton.dataset.originalHtml;
      }
    }
  }
}

// Export for module usage
window.HoneypotStats = HoneypotStats;
