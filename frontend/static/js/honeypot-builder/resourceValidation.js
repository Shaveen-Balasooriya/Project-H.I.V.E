/**
 * Resource Validation Module
 * 
 * Validates CPU and memory resource allocations for honeypot containers.
 */

class ResourceValidator {
  // Resource constraints
  static CONSTRAINTS = {
    CPU_PERIOD: { min: 50000, max: 200000, default: 100000 },
    CPU_QUOTA:  { min: 10000, max: 100000, default: 50000 },
    
    // Memory values in bytes (used for validation)
    MEMORY: {
      // Converting MB values to bytes for comparison
      "64m":    64 * 1024 * 1024,
      "128m":   128 * 1024 * 1024,
      "256m":   256 * 1024 * 1024,
      "512m":   512 * 1024 * 1024,
      "768m":   768 * 1024 * 1024,
      "1024m":  1024 * 1024 * 1024,
      "1536m":  1536 * 1024 * 1024,
      "2048m":  2048 * 1024 * 1024
    }
  };
  
  /**
   * Validates CPU quota against period
   * @param {number} quota - CPU quota value
   * @param {number} period - CPU period value
   * @returns {Object} Validation result with isValid and message
   */
  static validateCPUQuota(quota, period) {
    // Check if quota is within its own constraints
    if (isNaN(quota) || quota === null || quota === '') {
      return { 
        isValid: false, 
        message: "CPU Quota must be a number"
      };
    }
    
    if (quota < this.CONSTRAINTS.CPU_QUOTA.min) {
      return { 
        isValid: false, 
        message: `CPU Quota must be at least ${this.CONSTRAINTS.CPU_QUOTA.min}`
      };
    }
    
    if (quota > this.CONSTRAINTS.CPU_QUOTA.max) {
      return { 
        isValid: false, 
        message: `CPU Quota cannot exceed ${this.CONSTRAINTS.CPU_QUOTA.max}`
      };
    }
    
    // CPU Quota must be less than or equal to CPU Period
    if (quota > period) {
      return { 
        isValid: false, 
        message: "CPU Quota must be less than or equal to CPU Period"
      };
    }
    
    return { isValid: true };
  }
  
  /**
   * Validates CPU period value
   * @param {number} period - CPU period value
   * @returns {Object} Validation result with isValid and message
   */
  static validateCPUPeriod(period) {
    if (isNaN(period) || period === null || period === '') {
      return { 
        isValid: false, 
        message: "CPU Period must be a number"
      };
    }
    
    if (period < this.CONSTRAINTS.CPU_PERIOD.min) {
      return { 
        isValid: false, 
        message: `CPU Period must be at least ${this.CONSTRAINTS.CPU_PERIOD.min}`
      };
    }
    
    if (period > this.CONSTRAINTS.CPU_PERIOD.max) {
      return { 
        isValid: false, 
        message: `CPU Period cannot exceed ${this.CONSTRAINTS.CPU_PERIOD.max}`
      };
    }
    
    return { isValid: true };
  }
  
  /**
   * Helper function to convert memory string to bytes
   * @param {string} memoryStr - Memory value as string (e.g., "512m")
   * @returns {number} Value in bytes
   */
  static memoryToBytes(memoryStr) {
    return this.CONSTRAINTS.MEMORY[memoryStr] || 0;
  }
  
  /**
   * Validates memory swap against memory limit
   * @param {string} swapLimit - Memory swap limit (e.g., "1024m")
   * @param {string} memLimit - Memory limit (e.g., "512m")
   * @returns {Object} Validation result with isValid and message
   */
  static validateMemorySwap(swapLimit, memLimit) {
    const swapBytes = this.memoryToBytes(swapLimit);
    const memBytes = this.memoryToBytes(memLimit);
    
    if (!swapBytes || !memBytes) {
      return { 
        isValid: false, 
        message: "Invalid memory value format" 
      };
    }
    
    // Memory Swap must be greater than or equal to Memory Limit
    if (swapBytes < memBytes) {
      return { 
        isValid: false, 
        message: "Swap limit must be greater than or equal to memory limit"
      };
    }
    
    return { isValid: true };
  }
  
  /**
   * Get the next higher memory option
   * @param {string} currentLimit - Current memory value (e.g., "512m")
   * @returns {string} Next higher memory value or same if at max
   */
  static getNextMemoryOption(currentLimit) {
    const memoryOptions = Object.keys(this.CONSTRAINTS.MEMORY).sort(
      (a, b) => this.memoryToBytes(a) - this.memoryToBytes(b)
    );
    
    const currentIndex = memoryOptions.indexOf(currentLimit);
    if (currentIndex === -1 || currentIndex === memoryOptions.length - 1) {
      return currentLimit; // Return same if not found or already at max
    }
    
    return memoryOptions[currentIndex + 1];
  }
}

// Export for module usage
window.ResourceValidator = ResourceValidator;
