/**
 * Honeypot Authentication Validator
 * 
 * Validates credential fields for honeypot authentication
 * Rules:
 * - Username and password must be between 4-10 characters
 * - No duplicate credential pairs allowed
 * - Minimum 3 credential pairs required
 * - Maximum 10 credential pairs allowed
 */

class HoneypotAuthValidator {
  static CONSTRAINTS = {
    MIN_LENGTH: 4,
    MAX_LENGTH: 10,
    MIN_CREDENTIALS: 3,
    MAX_CREDENTIALS: 10
  };
  
  /**
   * Validates a single credential's length
   * @param {string} username - Username value
   * @param {string} password - Password value
   * @returns {Object} Validation result with isValid and message
   */
  static validateCredentialLength(username, password) {
    const userLen = username ? username.length : 0;
    const passLen = password ? password.length : 0;
    
    // Check for empty fields first
    if (!username || userLen === 0) {
      return { 
        isValid: false, 
        field: 'username',
        message: `Username is required`
      };
    }
    
    if (!password || passLen === 0) {
      return { 
        isValid: false, 
        field: 'password',
        message: `Password is required`
      };
    }
    
    // Now check length constraints
    if (userLen < this.CONSTRAINTS.MIN_LENGTH || userLen > this.CONSTRAINTS.MAX_LENGTH) {
      return { 
        isValid: false, 
        field: 'username',
        message: `Username must be between ${this.CONSTRAINTS.MIN_LENGTH} and ${this.CONSTRAINTS.MAX_LENGTH} characters`
      };
    }
    
    if (passLen < this.CONSTRAINTS.MIN_LENGTH || passLen > this.CONSTRAINTS.MAX_LENGTH) {
      return { 
        isValid: false, 
        field: 'password',
        message: `Password must be between ${this.CONSTRAINTS.MIN_LENGTH} and ${this.CONSTRAINTS.MAX_LENGTH} characters`
      };
    }
    
    return { isValid: true };
  }
  
  /**
   * Validates that no duplicate credentials exist
   * @param {Array} credentials - Array of credential objects (username, password)
   * @returns {Object} Validation result with isValid, index, and message
   */
  static validateNoDuplicates(credentials) {
    // Track all duplicates - using a map to store all indexes for each credential pair
    const occurrences = new Map();
    
    for (let i = 0; i < credentials.length; i++) {
      const cred = credentials[i];
      const key = `${cred.username}:${cred.password}`;
      
      if (!occurrences.has(key)) {
        occurrences.set(key, [i]); // Start a new array of indexes
      } else {
        // Add this index to the list of occurrences
        occurrences.get(key).push(i);
      }
    }
    
    // Check if any credential has multiple occurrences
    for (const [key, indexes] of occurrences.entries()) {
      if (indexes.length > 1) {
        // Return the last two occurrences (most recent duplicates)
        const lastIndex = indexes[indexes.length - 1];
        const prevIndex = indexes[indexes.length - 2];
        const username = key.split(':')[0];
        
        return {
          isValid: false,
          index: lastIndex,           // The most recent duplicate
          prevIndex: prevIndex,       // The previous occurrence
          message: `Duplicate credential for username "${username}" at positions ${prevIndex + 1} and ${lastIndex + 1}`
        };
      }
    }
    
    return { isValid: true };
  }
  
  /**
   * Validates the number of credentials against min/max constraints
   * @param {Array} credentials - Array of credential objects 
   * @returns {Object} Validation result with isValid, message and count
   */
  static validateCredentialCount(credentials) {
    const count = credentials.length;
    
    if (count < this.CONSTRAINTS.MIN_CREDENTIALS) {
      return {
        isValid: false,
        count: count,
        message: `At least ${this.CONSTRAINTS.MIN_CREDENTIALS} credential pairs are required (currently have ${count})`
      };
    }
    
    if (count > this.CONSTRAINTS.MAX_CREDENTIALS) {
      return {
        isValid: false,
        count: count,
        message: `Maximum ${this.CONSTRAINTS.MAX_CREDENTIALS} credential pairs allowed (currently have ${count})`
      };
    }
    
    return { isValid: true, count: count };
  }
  
  /**
   * Validates all credential fields and returns comprehensive results
   * @param {Array} credentials - Array of credential objects
   * @returns {Object} Validation result with overall status and specific issues
   */
  static validateAllCredentials(credentials) {
    const result = {
      isValid: true,
      lengthErrors: [],
      hasDuplicates: false,
      countValid: true,
      messages: []
    };
    
    // Validate individual credential lengths
    credentials.forEach((cred, index) => {
      const lengthCheck = this.validateCredentialLength(cred.username, cred.password);
      if (!lengthCheck.isValid) {
        result.isValid = false;
        result.lengthErrors.push({
          index: index,
          field: lengthCheck.field,
          message: lengthCheck.message
        });
        result.messages.push(lengthCheck.message + ` (credential #${index + 1})`);
      }
    });
    
    // Check for duplicates
    const dupeCheck = this.validateNoDuplicates(credentials);
    if (!dupeCheck.isValid) {
      result.isValid = false;
      result.hasDuplicates = true;
      result.duplicateIndices = [dupeCheck.prevIndex, dupeCheck.index];
      result.messages.push(dupeCheck.message);
    }
    
    // Check credential count
    const countCheck = this.validateCredentialCount(credentials);
    if (!countCheck.isValid) {
      result.isValid = false;
      result.countValid = false;
      result.count = countCheck.count;
      result.messages.push(countCheck.message);
    }
    
    return result;
  }
  
  /**
   * Highlights errors on credential fields based on validation results
   * @param {Object} validationResult - Result from validateAllCredentials
   * @param {HTMLElement} container - Container element for credentials
   */
  static highlightErrors(validationResult, container) {
    // Clear previous error styling
    const allInputs = container.querySelectorAll('input[type="text"], input[type="password"]');
    allInputs.forEach(input => {
      input.classList.remove('invalid-input');
    });
    
    // No errors to highlight
    if (validationResult.isValid) {
      return;
    }
    
    // Highlight length errors
    validationResult.lengthErrors.forEach(error => {
      const inputField = document.getElementById(`auth_${error.field}_${error.index}`);
      if (inputField) {
        inputField.classList.add('invalid-input');
      }
    });
    
    // Highlight duplicate fields
    if (validationResult.hasDuplicates && validationResult.duplicateIndices) {
      validationResult.duplicateIndices.forEach(index => {
        const usernameField = document.getElementById(`auth_username_${index}`);
        const passwordField = document.getElementById(`auth_password_${index}`);
        
        if (usernameField) usernameField.classList.add('invalid-input');
        if (passwordField) passwordField.classList.add('invalid-input');
      });
    }
  }

  /**
   * Updates centralized error message display
   * @param {Object} validationResult - Validation result with messages
   * @param {HTMLElement} errorsContainer - Container for error messages
   * @returns {boolean} Whether there were errors displayed
   */
  static updateCentralizedErrors(validationResult, errorsContainer = document.getElementById('validation-errors-list')) {
    if (!errorsContainer) return false;
    
    if (validationResult.isValid) {
      // Hide the parent container if no errors
      const parentContainer = document.getElementById('form-validation-errors');
      if (parentContainer) {
        parentContainer.classList.add('hidden');
      }
      return false;
    }

    // Show the parent container
    const parentContainer = document.getElementById('form-validation-errors');
    if (parentContainer) {
      parentContainer.classList.remove('hidden');
    }
    
    // Add error messages to the list
    if (validationResult.messages && validationResult.messages.length > 0) {
      // Create error items
      const errorItems = validationResult.messages.map(msg => 
        `<li class="text-sm">Authentication: ${msg}</li>`
      ).join('');
      
      // Add to existing error items
      const currentErrors = errorsContainer.innerHTML;
      if (!currentErrors.includes(errorItems)) {
        errorsContainer.innerHTML += errorItems;
      }
      
      return true;
    }
    
    return false;
  }
  
  /**
   * Real-time validation for a credential field
   * @param {HTMLInputElement} input - Input field being validated
   * @returns {Object} Validation result
   */
  static validateInputField(input) {
    const fieldType = input.id.includes('username') ? 'username' : 'password';
    const value = input.value;
    
    // Check for empty values first
    if (!value || value.trim() === '') {
      return {
        isValid: false,
        message: `${fieldType.charAt(0).toUpperCase() + fieldType.slice(1)} is required`
      };
    }
    
    const len = value.length;
    
    if (len < this.CONSTRAINTS.MIN_LENGTH) {
      return {
        isValid: false,
        message: `${fieldType.charAt(0).toUpperCase() + fieldType.slice(1)} must be at least ${this.CONSTRAINTS.MIN_LENGTH} characters`
      };
    }
    
    if (len > this.CONSTRAINTS.MAX_LENGTH) {
      return {
        isValid: false,
        message: `${fieldType.charAt(0).toUpperCase() + fieldType.slice(1)} cannot exceed ${this.CONSTRAINTS.MAX_LENGTH} characters`
      };
    }
    
    return { isValid: true };
  }
}

// Export for module usage
window.HoneypotAuthValidator = HoneypotAuthValidator;
