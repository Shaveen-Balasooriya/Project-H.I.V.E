/**
 * Honeypot Visualizations Module
 * 
 * Handles CPU and Memory visualizations for the honeypot builder
 */

class HoneypotVisualizations {
  constructor() {
    this.initVisualizations();
    this.bindEvents();
  }
  
  static init() {
    return new HoneypotVisualizations();
  }
  
  initVisualizations() {
    // Initialize CPU visualizations
    this.updateCpuPeriodVisualization();
    this.updateCpuQuotaVisualization();
    
    // Initialize Memory visualizations
    this.updateMemoryVisualizations();
    
    // Set up focus/blur events for tooltips
    this.setupTooltipEvents();
  }
  
  bindEvents() {
    // CPU Period changes
    const cpuPeriodInput = document.getElementById('cpu_period');
    if (cpuPeriodInput) {
      cpuPeriodInput.addEventListener('input', () => {
        this.updateCpuPeriodVisualization();
        // Also update quota visualization as it depends on period
        this.updateCpuQuotaVisualization();
      });
      cpuPeriodInput.addEventListener('blur', () => {
        setTimeout(() => {
          cpuPeriodInput.parentElement.classList.remove('showing-tooltip');
        }, 200);
      });
    }
    
    // CPU Quota changes
    const cpuQuotaInput = document.getElementById('cpu_quota');
    if (cpuQuotaInput) {
      cpuQuotaInput.addEventListener('input', () => {
        this.updateCpuQuotaVisualization();
      });
      cpuQuotaInput.addEventListener('blur', () => {
        setTimeout(() => {
          cpuQuotaInput.parentElement.classList.remove('showing-tooltip');
        }, 200);
      });
    }
    
    // Memory Limit changes
    const memoryLimitSelect = document.getElementById('memory_limit');
    const memorySwapSelect = document.getElementById('memory_swap_limit');
    
    if (memoryLimitSelect && memorySwapSelect) {
      memoryLimitSelect.addEventListener('change', () => this.updateMemoryVisualizations());
      memorySwapSelect.addEventListener('change', () => this.updateMemoryVisualizations());
      
      memoryLimitSelect.addEventListener('blur', () => {
        setTimeout(() => {
          memoryLimitSelect.parentElement.parentElement.classList.remove('showing-tooltip');
        }, 200);
      });
      
      memorySwapSelect.addEventListener('blur', () => {
        setTimeout(() => {
          memorySwapSelect.parentElement.parentElement.classList.remove('showing-tooltip');
        }, 200);
      });
    }
  }
  
  /**
   * Set up events for managing tooltip visibility
   */
  setupTooltipEvents() {
    // Add CSS to document for controlling showing-tooltip class
    const style = document.createElement('style');
    style.textContent = `
      .form-group.showing-tooltip .cpu-info-tooltip,
      .form-group.showing-tooltip .memory-info-tooltip {
        opacity: 1;
        transform: translateY(0);
        pointer-events: auto;
        visibility: visible;
        display: block;
      }
    `;
    document.head.appendChild(style);
    
    // Close tooltips when clicking outside the form groups
    document.addEventListener('click', (event) => {
      const formGroups = document.querySelectorAll('.form-group.showing-tooltip');
      formGroups.forEach(group => {
        if (!group.contains(event.target)) {
          group.classList.remove('showing-tooltip');
        }
      });
    });
  }
  
  /**
   * Update CPU Period visualization in tooltip
   */
  updateCpuPeriodVisualization() {
    const cpuPeriodInput = document.getElementById('cpu_period');
    // Use the actual input value without defaulting
    const periodValue = cpuPeriodInput ? parseInt(cpuPeriodInput.value) : 0;
    const isValid = periodValue >= 50000 && periodValue <= 200000;
    
    // Find tooltip visualizations
    const periodBars = document.querySelectorAll('.cpu-info-tooltip .period-bar');
    
    periodBars.forEach(bar => {
      // Create or update period fill element
      let periodFill = bar.querySelector('.period-fill');
      if (!periodFill) {
        periodFill = document.createElement('div');
        periodFill.className = 'period-fill';
        bar.appendChild(periodFill);
      }
      
      // Calculate percentage fill based on period range: 50k-200k
      const minPeriod = 50000;
      const maxPeriod = 200000;
      const range = maxPeriod - minPeriod;
      
      // Calculate percentage even if invalid, but cap between 0-100%
      let percentage = 0;
      if (periodValue > 0) {
        percentage = Math.min(100, Math.max(0, ((periodValue - minPeriod) / range) * 100));
      }
      
      // Update the fill width
      periodFill.style.width = `${percentage}%`;
      
      // Show validation state visually
      if (!isValid && periodValue !== 0) {
        periodFill.classList.add('invalid-value');
      } else {
        periodFill.classList.remove('invalid-value');
      }
      
      // Update time markers if they exist
      const startMarker = bar.parentElement?.querySelector('.time-marker.start');
      const middleMarker = bar.parentElement?.querySelector('.time-marker.middle');
      const endMarker = bar.parentElement?.querySelector('.time-marker.end');
      
      if (startMarker) startMarker.textContent = `${minPeriod}μs`;
      if (middleMarker) middleMarker.textContent = `${Math.floor(minPeriod + (range/2))}μs`;
      if (endMarker) endMarker.textContent = `${maxPeriod}μs`;
      
      // Add current value indicator
      let valueIndicator = bar.parentElement?.querySelector('.current-value');
      if (!valueIndicator && periodValue > 0) {
        valueIndicator = document.createElement('div');
        valueIndicator.className = 'current-value';
        bar.parentElement?.appendChild(valueIndicator);
      }
      
      if (valueIndicator && periodValue > 0) {
        valueIndicator.textContent = `Current: ${periodValue}μs`;
        valueIndicator.classList.toggle('invalid-value', !isValid);
      }
    });
  }
  
  /**
   * Update CPU Quota visualization in tooltip
   * Now using a bar graph similar to CPU Period
   */
  updateCpuQuotaVisualization() {
    const cpuQuotaInput = document.getElementById('cpu_quota');
    const cpuPeriodInput = document.getElementById('cpu_period');
    
    // Use actual input values without defaulting
    const quotaValue = cpuQuotaInput ? parseInt(cpuQuotaInput.value) : 0;
    const periodValue = cpuPeriodInput ? parseInt(cpuPeriodInput.value) : 100000;
    
    // Check if values are valid
    const isQuotaValid = quotaValue >= 10000 && quotaValue <= 100000;
    const isPeriodValid = periodValue >= 50000 && periodValue <= 200000;
    const isRatioValid = quotaValue <= periodValue;
    
    // Calculate percentage for visualization
    let percentage = 0;
    if (quotaValue > 0 && periodValue > 0) {
      percentage = Math.min(100, (quotaValue / periodValue) * 100);
    }
    
    // Find quota visualizations and update to bars instead of pie charts
    const quotaBars = document.querySelectorAll('.cpu-info-tooltip .quota-bar');
    
    quotaBars.forEach(bar => {
      // Create or update quota fill element
      let quotaFill = bar.querySelector('.quota-fill');
      if (!quotaFill) {
        quotaFill = document.createElement('div');
        quotaFill.className = 'quota-fill';
        bar.appendChild(quotaFill);
      }
      
      // Update the fill width
      quotaFill.style.width = `${percentage}%`;
      
      // Show validation state visually
      const isValid = isQuotaValid && isRatioValid;
      if (!isValid && quotaValue !== 0) {
        quotaFill.classList.add('invalid-value');
      } else {
        quotaFill.classList.remove('invalid-value');
      }
      
      // Update the percentage label
      const quotaLabel = bar.parentElement?.querySelector('.quota-percentage');
      if (quotaLabel) {
        quotaLabel.textContent = `${Math.round(percentage)}%`;
        quotaLabel.classList.toggle('invalid-value', !isValid && quotaValue !== 0);
      }
      
      // Add current values indicator
      let valueIndicator = bar.parentElement?.querySelector('.current-values');
      if (!valueIndicator && quotaValue > 0) {
        valueIndicator = document.createElement('div');
        valueIndicator.className = 'current-values';
        bar.parentElement?.appendChild(valueIndicator);
      }
      
      if (valueIndicator && quotaValue > 0) {
        valueIndicator.textContent = `Quota: ${quotaValue}μs / Period: ${periodValue}μs`;
        valueIndicator.classList.toggle('invalid-value', !isValid);
      }
    });
  }
  
  /**
   * Update Memory visualizations
   * This updates both memory limit and memory swap visualizations
   */
  updateMemoryVisualizations() {
    const memoryLimitSelect = document.getElementById('memory_limit');
    const memorySwapSelect = document.getElementById('memory_swap_limit');
    
    if (!memoryLimitSelect || !memorySwapSelect) return;
    
    const memoryValue = memoryLimitSelect.value;
    const swapValue = memorySwapSelect.value;
    
    // Convert memory strings to numbers (MB) for calculations
    const memoryMB = this.memoryStringToMB(memoryValue);
    const swapMB = this.memoryStringToMB(swapValue);
    
    // Calculate swap space (if any)
    const actualSwapMB = Math.max(0, swapMB - memoryMB);
    
    // Update Memory Limit visualization
    this.updateMemoryLimitVisualization(memoryMB);
    
    // Update Memory Swap visualization
    this.updateMemorySwapVisualization(memoryMB, actualSwapMB, swapMB);
  }
  
  /**
   * Convert memory string format (like "512m") to number in MB
   * @param {string} memoryString - Memory string in format like "512m"
   * @returns {number} Memory in MB
   */
  memoryStringToMB(memoryString) {
    // Remove trailing 'm' and convert to number
    return parseInt(memoryString.replace('m', ''));
  }
  
  /**
   * Update Memory Limit visualization
   * @param {number} memoryMB - Memory amount in MB
   */
  updateMemoryLimitVisualization(memoryMB) {
    // Find all memory limit tooltips
    const memoryLimitTooltips = document.querySelectorAll('.form-group:has(#memory_limit) .memory-info-tooltip');
    
    memoryLimitTooltips.forEach(tooltip => {
      // Update RAM usage label
      const ramUsageLabel = tooltip.querySelector('.ram-usage-label');
      if (ramUsageLabel) {
        ramUsageLabel.textContent = `${memoryMB} MB`;
      }
      
      // Adjust RAM chips visualization based on memory size
      const ramChips = tooltip.querySelectorAll('.ram-chip');
      
      // Show appropriate number of RAM chips based on memory size
      if (ramChips.length > 0) {
        const maxChips = ramChips.length;
        const ramSizes = [64, 128, 256, 512, 768, 1024];
        
        // Find where this memory size fits in our scale
        let activeChips = 1; // At least 1 chip always active
        for (let i = 0; i < ramSizes.length; i++) {
          if (memoryMB >= ramSizes[i]) {
            activeChips = Math.min(Math.ceil((i + 1) * maxChips / ramSizes.length), maxChips);
          }
        }
        
        // Update chip visibility
        ramChips.forEach((chip, index) => {
          chip.style.opacity = index < activeChips ? "1" : "0.3";
        });
      }
      
      // Update any other elements that mention the memory value
      const memoryValueElements = tooltip.querySelectorAll('.memory-value');
      memoryValueElements.forEach(el => {
        el.textContent = `${memoryMB} MB`;
      });
    });
  }
  
  /**
   * Update Memory Swap visualization
   * @param {number} memoryMB - Memory amount in MB
   * @param {number} swapMB - Swap amount in MB
   * @param {number} totalMB - Total memory+swap in MB
   */
  updateMemorySwapVisualization(memoryMB, swapMB, totalMB) {
    // Find all memory swap tooltips
    const memorySwapTooltips = document.querySelectorAll('.form-group:has(#memory_swap_limit) .memory-info-tooltip');
    
    memorySwapTooltips.forEach(tooltip => {
      // Update RAM block value
      const ramBlockValue = tooltip.querySelector('.ram-block .block-value');
      if (ramBlockValue) {
        ramBlockValue.textContent = `${memoryMB} MB`;
      }
      
      // Update Swap block value
      const swapBlockValue = tooltip.querySelector('.swap-block .block-value');
      if (swapBlockValue) {
        swapBlockValue.textContent = `${swapMB} MB`;
      }
      
      // Update total memory+swap value
      const totalValue = tooltip.querySelector('.total-value');
      if (totalValue) {
        totalValue.textContent = `${totalMB} MB`;
      }
      
      // Update block sizes to represent proportions
      const ramBlock = tooltip.querySelector('.ram-block');
      const swapBlock = tooltip.querySelector('.swap-block');
      
      if (ramBlock && swapBlock && totalMB > 0) {
        // Calculate percentage with minimum thresholds to avoid too small blocks
        let ramPercentage = (memoryMB / totalMB) * 100;
        let swapPercentage = (swapMB / totalMB) * 100;
        
        // Ensure minimal visual width even for small values
        if (swapMB > 0 && swapPercentage < 10) {
          swapPercentage = 10;
          ramPercentage = 90;
        } else if (memoryMB > 0 && ramPercentage < 10) {
          ramPercentage = 10;
          swapPercentage = 90;
        }
        
        ramBlock.style.flex = `${ramPercentage} 0 0`; // Use flex grow/shrink/basis
        swapBlock.style.flex = `${swapPercentage} 0 0`;
        
        // Set minimum width for each block based on its proportion
        ramBlock.style.minWidth = swapMB > 0 ? "30%" : "100%";
        swapBlock.style.minWidth = swapMB > 0 ? "30%" : "0%";
        
        // Show or hide swap block based on swap value
        swapBlock.style.display = swapMB > 0 ? "flex" : "none";
      }
      
      // Update visual styles based on swap being used or not
      if (swapMB <= 0) {
        tooltip.querySelectorAll('.swap-block').forEach(el => {
          el.classList.add('opacity-50');
        });
      } else {
        tooltip.querySelectorAll('.swap-block').forEach(el => {
          el.classList.remove('opacity-50');
        });
      }
      
      // Update memory and swap values in equation
      const memoryValueElements = tooltip.querySelectorAll('.memory-value');
      const swapValueElements = tooltip.querySelectorAll('.swap-value');
      
      memoryValueElements.forEach(el => {
        el.textContent = `${memoryMB} MB`;
      });
      
      swapValueElements.forEach(el => {
        if (el.closest('.swap-equation')) {
          el.textContent = `${totalMB} MB`;
        }
      });
    });
  }
}

// Initialize visualizations when document is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.honeypotVisualizations = HoneypotVisualizations.init();
});