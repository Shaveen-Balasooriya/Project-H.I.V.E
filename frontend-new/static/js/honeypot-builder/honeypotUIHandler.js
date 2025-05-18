/**
 * Honeypot UI Handler Module
 * 
 * Manages UI interactions for the honeypot builder
 */

class HoneypotUIHandler {
  constructor(elements) {
    this.elements = elements;
    this.bindMethods();
  }
  
  static init(elements) {
    return new HoneypotUIHandler(elements);
  }
  
  bindMethods() {
    this.toggleResourceFields = this.toggleResourceFields.bind(this);
    this.showStatus = this.showStatus.bind(this);
  }
  
  /**
   * Toggle resource fields visibility
   */
  toggleResourceFields() {
    const resourceFields = this.elements.resourceFields;
    const checkbox = this.elements.showResourcesCheckbox;
    
    if (checkbox.checked) {
      // Show resources
      resourceFields.classList.remove('hidden');
    } else {
      // Hide resources
      resourceFields.classList.add('hidden');
    }
  }
  
  /**
   * Show status message
   * @param {string} message - Message to display
   * @param {string} type - Message type (success, danger, warning)
   */
  showStatus(message, type = 'info') {
    if (!this.elements.formStatus) return;
    
    this.elements.formStatus.textContent = message;
    this.elements.formStatus.className = `p-4 rounded border ${type === 'success' ? 'text-success bg-success/20 border-success/30' : 
      type === 'danger' ? 'text-danger bg-danger/20 border-danger/30' : 
      'text-warning bg-warning/20 border-warning/30'}`;
    
    this.elements.formStatus.classList.remove('hidden');
  }
}

// Export for module usage
window.HoneypotUIHandler = HoneypotUIHandler;
