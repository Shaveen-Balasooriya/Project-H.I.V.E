/**
 * Honeypot Authentication Handler Module
 * 
 * Manages the authentication credential UI for the honeypot builder
 */

class HoneypotAuthHandler {
  constructor(elements) {
    this.elements = elements;
    this.credentialCount = 0; // Start with zero and add fields in initialization
    this.bindMethods();
    
    // Initialize with 3 credential fields (minimum required)
    this.initializeCredentials();
  }
  
  static init(elements) {
    return new HoneypotAuthHandler(elements);
  }
  
  bindMethods() {
    this.addNewCredential = this.addNewCredential.bind(this);
    this.removeCredential = this.removeCredential.bind(this);
    this.loadAuthDetailsForType = this.loadAuthDetailsForType.bind(this);
    this.getCredentials = this.getCredentials.bind(this);
    this.validateCredentials = this.validateCredentials.bind(this);
    this.setupFieldValidation = this.setupFieldValidation.bind(this);
    this.updateAddCredentialButtonState = this.updateAddCredentialButtonState.bind(this);
    this.updateCredentialCounter = this.updateCredentialCounter.bind(this);
    this.disableAddCredentialButton = this.disableAddCredentialButton.bind(this);
  }
  
  /**
   * Initialize with minimum required credentials
   */
  initializeCredentials() {
    // Always start with exactly 3 credential fields (the minimum required)
    for (let i = 0; i < HoneypotAuthValidator.CONSTRAINTS.MIN_CREDENTIALS; i++) {
      this.addNewCredential();
    }
    
    // Add placeholder info to guide the user for the first credential
    const firstUsername = document.getElementById('auth_username_0');
    const firstPassword = document.getElementById('auth_password_0');
    
    if (firstUsername) firstUsername.placeholder = "admin (4-10 chars)";
    if (firstPassword) firstPassword.placeholder = "password (4-10 chars)";
    
    // Initialize credential counter
    this.updateCredentialCounter();
  }
  
  /**
   * Add a new credential field set
   */
  addNewCredential() {
    // Enhanced check for maximum credentials with more robust enforcement
    const currentCredentials = this.getCredentials();
    const maxCredentials = HoneypotAuthValidator.CONSTRAINTS.MAX_CREDENTIALS;
    
    if (currentCredentials.length >= maxCredentials) {
      const message = `Maximum ${maxCredentials} credential pairs allowed`;
      
      // Show message using tooltip or alert
      alert(message);
      
      // Force disable the add button to prevent further attempts
      this.disableAddCredentialButton(true, `Maximum ${maxCredentials} credential pairs reached`);
      
      return;
    }
    
    const index = this.credentialCount++;
    const container = this.elements.authContainer;
    
    const entryDiv = document.createElement('div');
    entryDiv.className = 'authentication-entry bg-black/20 p-4 rounded mb-3 border border-white/5 transition-all hover:border-accent/20';
    
    // Create username/password field grid with better guidance
    entryDiv.innerHTML = `
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label for="auth_username_${index}" class="block text-white font-medium mb-2 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-accent/70" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd" />
            </svg>
            Username
            <span class="ml-1 text-accent/70 text-xs">(4-10 chars)</span>
          </label>
          <input type="text" id="auth_username_${index}" name="auth_username_${index}" minlength="4" maxlength="10" placeholder="Enter username" class="w-full bg-black/60 border border-accent/30 rounded px-4 py-3 text-white focus:border-accent transition-all duration-200 focus-visible" />
          <div id="username_error_${index}" class="field-error hidden text-xs mt-1"></div>
        </div>
        <div>
          <label for="auth_password_${index}" class="block text-white font-medium mb-2 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 text-accent/70" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd" />
            </svg>
            Password
            <span class="ml-1 text-accent/70 text-xs">(4-10 chars)</span>
          </label>
          <div class="flex">
            <input type="text" id="auth_password_${index}" name="auth_password_${index}" minlength="4" maxlength="10" placeholder="Enter password" class="w-full bg-black/60 border border-accent/30 rounded-l px-4 py-3 text-white focus:border-accent transition-all duration-200 focus-visible" />
            <button type="button" class="remove-credential bg-danger/20 hover:bg-danger/40 text-danger px-3 rounded-r border border-danger/30 transition-all flex items-center" data-index="${index}">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div id="password_error_${index}" class="field-error hidden text-xs mt-1"></div>
        </div>
      </div>
    `;
    
    // Add to container
    container.appendChild(entryDiv);
    
    // Add event listener to the remove button
    const removeBtn = entryDiv.querySelector('.remove-credential');
    removeBtn.addEventListener('click', () => this.removeCredential(entryDiv, index));
    
    // Setup real-time validation for these fields
    this.setupFieldValidation(entryDiv);
    
    // Update credential counter AFTER adding the new credential
    this.updateCredentialCounter();
    
    // Update button state immediately after adding
    this.updateAddCredentialButtonState();
    
    // If we've reached the limit after adding this credential, disable the button
    if (this.getCredentials().length >= maxCredentials) {
      this.disableAddCredentialButton(true, `Maximum ${maxCredentials} credential pairs reached`);
    }
  }
  
  /**
   * Remove a credential entry
   * @param {HTMLElement} entryDiv - The entry div to remove
   * @param {number} index - Index of the credential
   */
  removeCredential(entryDiv, index) {
    // Check if removing would violate minimum count
    const currentCredentials = this.getCredentials();
    if (currentCredentials.length <= HoneypotAuthValidator.CONSTRAINTS.MIN_CREDENTIALS) {
      const message = `At least ${HoneypotAuthValidator.CONSTRAINTS.MIN_CREDENTIALS} credential pairs are required`;
      // Show message using tooltip or alert
      alert(message);
      return;
    }
    
    this.elements.authContainer.removeChild(entryDiv);
    
    // Re-validate after removal
    setTimeout(() => {
      this.validateCredentials();
      
      // Update credential counter after removal
      this.updateCredentialCounter();
      
      // Re-enable the add button if we're below the max limit
      const currentCount = this.getCredentials().length;
      const maxCredentials = HoneypotAuthValidator.CONSTRAINTS.MAX_CREDENTIALS;
      
      if (currentCount < maxCredentials) {
        this.disableAddCredentialButton(false);
      }
    }, 100);
  }
  
  /**
   * Setup real-time validation for credential fields
   * @param {HTMLElement} entryDiv - The credential entry div
   */
  setupFieldValidation(entryDiv) {
    const usernameInput = entryDiv.querySelector('input[id^="auth_username_"]');
    const passwordInput = entryDiv.querySelector('input[id^="auth_password_"]');
    
    if (usernameInput) {
      const index = usernameInput.id.split('_').pop();
      const errorContainer = document.getElementById(`username_error_${index}`);
      
      usernameInput.addEventListener('input', () => {
        // Enforce character limit
        if (usernameInput.value.length > HoneypotAuthValidator.CONSTRAINTS.MAX_LENGTH) {
          usernameInput.value = usernameInput.value.slice(0, HoneypotAuthValidator.CONSTRAINTS.MAX_LENGTH);
        }
        
        // Clear validation styling
        usernameInput.classList.remove('invalid-input');
        if (errorContainer) errorContainer.classList.add('hidden');
        
        // Add validation if needed
        const result = HoneypotAuthValidator.validateInputField(usernameInput);
        if (!result.isValid) {
          usernameInput.classList.add('invalid-input');
          
          // Show error message
          if (errorContainer) {
            errorContainer.textContent = result.message;
            errorContainer.classList.remove('hidden');
          }
        }
        
        // Update add button state based on validation
        this.updateAddCredentialButtonState();
      });
      
      // Run complete validation on blur
      usernameInput.addEventListener('blur', () => {
        const result = HoneypotAuthValidator.validateInputField(usernameInput);
        if (!result.isValid) {
          usernameInput.classList.add('invalid-input');
          
          // Show error message
          if (errorContainer) {
            errorContainer.textContent = result.message;
            errorContainer.classList.remove('hidden');
          }
        }
        
        // Run full validation of all credentials on blur
        this.validateCredentials();
      });
    }
    
    if (passwordInput) {
      const index = passwordInput.id.split('_').pop();
      const errorContainer = document.getElementById(`password_error_${index}`);
      
      passwordInput.addEventListener('input', () => {
        // Enforce character limit
        if (passwordInput.value.length > HoneypotAuthValidator.CONSTRAINTS.MAX_LENGTH) {
          passwordInput.value = passwordInput.value.slice(0, HoneypotAuthValidator.CONSTRAINTS.MAX_LENGTH);
        }
        
        // Clear validation styling
        passwordInput.classList.remove('invalid-input');
        if (errorContainer) errorContainer.classList.add('hidden');
        
        // Add validation if needed
        const result = HoneypotAuthValidator.validateInputField(passwordInput);
        if (!result.isValid) {
          passwordInput.classList.add('invalid-input');
          
          // Show error message
          if (errorContainer) {
            errorContainer.textContent = result.message;
            errorContainer.classList.remove('hidden');
          }
        }
        
        // Update add button state based on validation
        this.updateAddCredentialButtonState();
      });
      
      // Run complete validation on blur
      passwordInput.addEventListener('blur', () => {
        const result = HoneypotAuthValidator.validateInputField(passwordInput);
        if (!result.isValid) {
          passwordInput.classList.add('invalid-input');
          
          // Show error message
          if (errorContainer) {
            errorContainer.textContent = result.message;
            errorContainer.classList.remove('hidden');
          }
        }
        
        // Run full validation of all credentials on blur
        this.validateCredentials();
      });
    }
    
    // Add real-time credential count check whenever a value changes
    const inputs = entryDiv.querySelectorAll('input[type="text"]');
    inputs.forEach(input => {
      input.addEventListener('input', () => {
        // Check if adding this input would exceed the limit
        const currentCount = this.getCredentials().length;
        const maxCredentials = HoneypotAuthValidator.CONSTRAINTS.MAX_CREDENTIALS;
        
        // Update the counter to reflect changes
        this.updateCredentialCounter();
        
        // Enforce add button state based on current count
        if (currentCount >= maxCredentials) {
          this.disableAddCredentialButton(true, `Maximum ${maxCredentials} credential pairs reached`);
        }
      });
    });
  }
  
  /**
   * Update the state of the Add Credential button based on validation
   */
  updateAddCredentialButtonState() {
    const addButton = this.elements.addCredentialBtn;
    if (!addButton) return;
    
    const credentials = this.getCredentials();
    
    // Check if we've reached maximum allowed credentials
    const reachedMaxCredentials = credentials.length >= HoneypotAuthValidator.CONSTRAINTS.MAX_CREDENTIALS;
    
    // Check if any existing credential has validation errors
    let hasValidationErrors = false;
    
    // Check each credential field for validation errors
    const entries = this.elements.authContainer.querySelectorAll('.authentication-entry');
    entries.forEach(entry => {
      const usernameInput = entry.querySelector('input[type="text"]');
      const passwordInput = entry.querySelector('input[type="text"]');
      
      if (usernameInput) {
        const usernameResult = HoneypotAuthValidator.validateInputField(usernameInput);
        if (!usernameResult.isValid) {
          hasValidationErrors = true;
        }
      }
      
      if (passwordInput) {
        const passwordResult = HoneypotAuthValidator.validateInputField(passwordInput);
        if (!passwordResult.isValid) {
          hasValidationErrors = true;
        }
      }
    });
    
    // Disable button if we have validation errors or max credentials reached
    if (hasValidationErrors || reachedMaxCredentials) {
      addButton.disabled = true;
      addButton.classList.add('opacity-50', 'cursor-not-allowed');
      
      if (hasValidationErrors) {
        addButton.title = 'Fix validation errors before adding more credentials';
      } else {
        addButton.title = `Maximum ${HoneypotAuthValidator.CONSTRAINTS.MAX_CREDENTIALS} credential pairs allowed`;
      }
    } else {
      addButton.disabled = false;
      addButton.classList.remove('opacity-50', 'cursor-not-allowed');
      addButton.title = '';
    }
  }
  
  /**
   * Directly enable/disable the add credential button
   * @param {boolean} disable - Whether to disable the button
   * @param {string} reason - Optional reason to show in tooltip
   */
  disableAddCredentialButton(disable, reason = '') {
    const addButton = this.elements.addCredentialBtn;
    if (!addButton) return;
    
    addButton.disabled = disable;
    
    if (disable) {
      addButton.classList.add('opacity-50', 'cursor-not-allowed');
      if (reason) addButton.title = reason;
    } else {
      addButton.classList.remove('opacity-50', 'cursor-not-allowed');
      addButton.title = '';
    }
  }
  
  /**
   * Validate all credentials together
   * @returns {Object} Validation result with isValid and messages
   */
  validateCredentials() {
    const credentials = this.getCredentials();
    
    // Use the validator to check all credentials
    const result = HoneypotAuthValidator.validateAllCredentials(credentials);
    
    // Highlight errors in the UI
    HoneypotAuthValidator.highlightErrors(result, this.elements.authContainer);
    
    // Check for duplicates and show specific error messages
    if (result.hasDuplicates && result.duplicateIndices) {
      result.duplicateIndices.forEach(index => {
        const usernameErrorContainer = document.getElementById(`username_error_${index}`);
        if (usernameErrorContainer) {
          usernameErrorContainer.textContent = "Duplicate credential pair";
          usernameErrorContainer.classList.remove('hidden');
        }
      });
    }
    
    // Check for empty fields and show specific error messages
    if (result.lengthErrors && result.lengthErrors.length > 0) {
      result.lengthErrors.forEach(error => {
        const errorContainer = document.getElementById(`${error.field}_error_${error.index}`);
        if (errorContainer) {
          errorContainer.textContent = error.message;
          errorContainer.classList.remove('hidden');
        }
      });
    }
    
    // Update add/remove button states based on count and validation
    this.updateAddCredentialButtonState();
    
    // Handle remove buttons (keep existing logic)
    const removeButtons = this.elements.authContainer.querySelectorAll('.remove-credential');
    if (credentials.length <= HoneypotAuthValidator.CONSTRAINTS.MIN_CREDENTIALS) {
      removeButtons.forEach(btn => {
        btn.disabled = true;
        btn.classList.add('opacity-50', 'cursor-not-allowed');
        btn.title = `At least ${HoneypotAuthValidator.CONSTRAINTS.MIN_CREDENTIALS} credential pairs required`;
      });
    } else {
      removeButtons.forEach(btn => {
        btn.disabled = false;
        btn.classList.remove('opacity-50', 'cursor-not-allowed');
        btn.title = '';
      });
    }
    
    return result;
  }
  
  /**
   * Update the credential counter display
   */
  updateCredentialCounter() {
    const counter = document.getElementById('credential-counter');
    if (counter) {
      const count = this.getCredentials().length;
      const max = HoneypotAuthValidator.CONSTRAINTS.MAX_CREDENTIALS;
      counter.textContent = `${count}/${max} pairs`;
      
      // Enhanced visual indicators based on how close to the limit
      if (count >= max) {
        // At the limit - use danger color
        counter.classList.add('text-danger');
        counter.classList.remove('text-warning');
      } else if (count >= max * 0.8) {
        // Approaching the limit (80% or more) - use warning color
        counter.classList.add('text-warning');
        counter.classList.remove('text-danger');
      } else {
        // Well below limit - normal color
        counter.classList.remove('text-warning', 'text-danger');
      }
    }
  }
  
  /**
   * Load authentication details for selected honeypot type
   * @param {string} type - Honeypot type
   */
  async loadAuthDetailsForType(type) {
    try {
      console.log(`Loading config for honeypot type: ${type}`);
      const response = await ApiClient.getTypeConfig(type);
      console.log("Type config response:", response);
      
      // If we got authentication defaults, pre-fill the form
      if (response && response.authentication && response.authentication.allowed_users) {
        console.log("Found authentication config with users:", response.authentication.allowed_users);
        const users = response.authentication.allowed_users;
        
        // Clear existing entries first
        const entries = Array.from(this.elements.authContainer.querySelectorAll('.authentication-entry'));
        for (let i = 0; i < entries.length; i++) {
          this.elements.authContainer.removeChild(entries[i]);
        }
        
        // Reset counter
        this.credentialCount = 0;
        
        // Add users from the response
        for (let i = 0; i < users.length; i++) {
          this.addNewCredential();
          
          const usernameField = document.getElementById(`auth_username_${i}`);
          const passwordField = document.getElementById(`auth_password_${i}`);
          
          if (usernameField) usernameField.value = users[i].username || '';
          if (passwordField) passwordField.value = users[i].password || '';
        }
        
        // If we have fewer than minimum, add more
        while (this.getCredentials().length < HoneypotAuthValidator.CONSTRAINTS.MIN_CREDENTIALS) {
          this.addNewCredential();
        }
        
        // Validate after loading
        this.validateCredentials();
        
        // Update credential counter after loading
        this.updateCredentialCounter();
      } else {
        console.log("No authentication config found in response or missing allowed_users");
      }
      
      // If we got banner defaults, pre-fill the banner field
      if (response && response.banner) {
        console.log("Found banner text in response:", response.banner);
        const bannerField = document.getElementById('banner');
        if (bannerField) {
          bannerField.value = response.banner || '';
          console.log("Updated banner field value");
        } else {
          console.warn("Banner field element not found in the DOM");
        }
      } else {
        console.log("No banner text found in response");
      }
      
      // After loading credentials, check if we're at the limit
      const currentCount = this.getCredentials().length;
      const maxCredentials = HoneypotAuthValidator.CONSTRAINTS.MAX_CREDENTIALS;
      
      // Update counter and button state
      this.updateCredentialCounter();
      
      // Disable add button if at or over limit after loading
      if (currentCount >= maxCredentials) {
        this.disableAddCredentialButton(true, `Maximum ${maxCredentials} credential pairs reached`);
      } else {
        this.disableAddCredentialButton(false);
      }
    } catch (error) {
      console.error('Error loading auth details:', error);
    }
  }
  
  /**
   * Gets all credential pairs from the form
   * @returns {Array} Array of username/password objects
   */
  getCredentials() {
    const credentials = [];
    const entries = this.elements.authContainer.querySelectorAll('.authentication-entry');
    
    entries.forEach((entry, index) => {
      const usernameField = entry.querySelector('input[type="text"]');
      const passwordField = entry.querySelector('input[type="text"]');
      
      if (usernameField && passwordField) {
        credentials.push({
          username: usernameField.value,
          password: passwordField.value
        });
      }
    });
    
    return credentials;
  }
}

// Export for module usage
window.HoneypotAuthHandler = HoneypotAuthHandler;
