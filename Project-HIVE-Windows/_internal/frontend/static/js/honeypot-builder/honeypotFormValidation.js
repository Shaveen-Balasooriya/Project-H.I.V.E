/**
 * Form validation utilities specific to the Honeypot Builder
 * Provides validation for the honeypot builder form fields
 */

class HoneypotFormValidator {
  /**
   * Validates port number
   * @param {number} port - The port number to validate
   * @returns {Object} Validation result with isValid and message
   */
  static validatePort(port) {
    if (!port || isNaN(port)) {
      return { isValid: false, message: "Please enter a valid port number" };
    }

    // Check for privileged ports
    if (port < 1024) {
      return { isValid: false, message: "Privileged ports (below 1024) are not allowed" };
    }

    if (port > 65535) {
      return { isValid: false, message: "Invalid port. Maximum allowed is 65535" };
    }

    // Value is a valid port number within allowable range
    return { isValid: true };
  }
  
  /**
   * Shows status message in a status element using the unified field-error style
   * @param {HTMLElement} element - The status element to update
   * @param {string} message - The message to display
   * @param {string} type - Message type (success, danger, warning)
   */
  static showStatus(element, message, type) {
    if (!element) return;
    
    // Remove all existing classes
    element.classList.remove("hidden");
    
    // Clear existing content and create new content with icon
    let iconSvg = '';
    
    switch (type) {
      case "success":
        element.classList.add("field-error", "text-success");
        iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
        </svg>`;
        break;
      case "danger":
        element.classList.add("field-error");
        iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
        </svg>`;
        break;
      case "warning":
        element.classList.add("field-error", "text-warning");
        iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>`;
        break;
    }
    
    element.innerHTML = iconSvg + message;
  }
  
  /**
   * Enforce maximum length on an input field
   * @param {HTMLInputElement} input - The input element
   * @param {number} maxLength - Maximum allowed length
   */
  static enforceMaxLength(input, maxLength) {
    if (input.value.length > maxLength) {
      input.value = input.value.slice(0, maxLength);
    }
  }
  
  /**
   * Mark an input field as invalid
   * @param {HTMLElement} input - The input element to mark
   * @param {boolean} isInvalid - Whether the field is invalid
   */
  static setInvalid(input, isInvalid) {
    if (isInvalid) {
      input.classList.add("invalid-input");
    } else {
      input.classList.remove("invalid-input");
    }
  }
}

// Export for module usage
window.HoneypotFormValidator = HoneypotFormValidator;

// For backwards compatibility with any code that might use FormValidator
window.FormValidator = HoneypotFormValidator;
