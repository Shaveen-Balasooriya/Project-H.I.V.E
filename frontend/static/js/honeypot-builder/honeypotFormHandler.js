/**
 * Honeypot Form Handler Module
 * 
 * Manages form submission and validation for the honeypot builder
 */

class HoneypotFormHandler {
  constructor(elements, authHandler) {
    this.elements = elements;
    this.authHandler = authHandler;
    this.portValidated = false; // Track if port has been validated
    this.portValid = false;    // Track if port is actually valid
    this.bindMethods();
  }
  
  static init(elements, authHandler) {
    return new HoneypotFormHandler(elements, authHandler);
  }
  
  bindMethods() {
    this.handleFormSubmit = this.handleFormSubmit.bind(this);
    this.handlePortCheck = this.handlePortCheck.bind(this);
    this.validateForm = this.validateForm.bind(this);
    this.setSubmitting = this.setSubmitting.bind(this);
    this.addValidationError = this.addValidationError.bind(this);
    this.toggleValidationErrorsDisplay = this.toggleValidationErrorsDisplay.bind(this);
    this.clearPortStatus = this.clearPortStatus.bind(this);
  }
  
  /**
   * Handle port availability checking
   */
  async handlePortCheck() {
    const port = this.elements.portInput.value;
    const portStatus = this.elements.portStatus;
    const checkBtn = this.elements.checkPortBtn;
    
    if (!port) {
      HoneypotFormValidator.showStatus(portStatus, "Please enter a port number", "danger");
      return;
    }
    
    // Validate port format
    const result = HoneypotFormValidator.validatePort(port);
    if (!result.isValid) {
      HoneypotFormValidator.showStatus(portStatus, result.message, "danger");
      // Mark input as invalid
      HoneypotFormValidator.setInvalid(this.elements.portInput, true);
      return;
    }
    
    // Clear invalid state
    HoneypotFormValidator.setInvalid(this.elements.portInput, false);
    
    // Disable button and show loading state
    checkBtn.disabled = true;
    const originalText = checkBtn.innerHTML;
    checkBtn.innerHTML = `
      <svg class="animate-spin h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      Checking...
    `;
    
    try {
      const response = await ApiClient.checkPortAvailability(port);
      
      if (response.available) {
        HoneypotFormValidator.showStatus(portStatus, "Port is available ✓", "success");
        HoneypotFormValidator.setInvalid(this.elements.portInput, false);
        
        // Store validation result to prevent duplicate validation
        this.portValidated = true;
        this.portValid = true;
      } else {
        HoneypotFormValidator.showStatus(portStatus, response.message || "Port is already in use", "danger");
        HoneypotFormValidator.setInvalid(this.elements.portInput, true);
        this.portValidated = true;
        this.portValid = false;
      }
    } catch (error) {
      console.error("Port check failed:", error);
      HoneypotFormValidator.showStatus(portStatus, "Error checking port availability", "danger");
      this.portValidated = false;
      this.portValid = false;
    } finally {
      // Re-enable button and restore original text
      checkBtn.disabled = false;
      checkBtn.innerHTML = originalText;
    }
  }
  
  /**
   * Validate form before submission
   * @returns {boolean} Whether form is valid
   */
  validateForm() {
    const { typeSelect, portInput, cpuPeriod, cpuQuota, memoryLimit, memorySwapLimit, bannerTextarea } = this.elements;
    let isValid = true;
    
    // Basic validation
    if (!typeSelect.value) {
      // Instead of adding to central error list, we focus on the field and highlight it
      HoneypotFormValidator.setInvalid(typeSelect, true);
      typeSelect.focus();
      isValid = false;
    } else {
      HoneypotFormValidator.setInvalid(typeSelect, false);
    }
    
    // Validate port only if not previously validated successfully
    if (!this.portValidated || !this.portValid) {
      // Check if port-status already has an error displayed
      const portStatus = document.getElementById('port-status');
      const portStatusVisible = portStatus && !portStatus.classList.contains('hidden');
      
      if (!portInput.value) {
        // Ensure port-status is showing the correct message
        HoneypotFormValidator.showStatus(portStatus, "Please enter a port number", "danger");
        HoneypotFormValidator.setInvalid(portInput, true);
        if (isValid) {
          portInput.focus();
        }
        isValid = false;
      }
      
      // Validate port format but don't show duplicate errors
      if (portInput.value) {
        const portResult = HoneypotFormValidator.validatePort(portInput.value);
        if (!portResult.isValid) {
          // Show in port-status
          HoneypotFormValidator.showStatus(portStatus, portResult.message, "danger");
          HoneypotFormValidator.setInvalid(portInput, true);
          if (isValid) {
            portInput.focus();
          }
          isValid = false;
        } else if (portStatusVisible) {
          // Hide port-status if port is valid and port-status is visible
          portStatus.classList.add('hidden');
        }
      }
      
      // If port is still valid at this point but not checked with API
      if (isValid && portInput.value && !this.portValidated) {
        HoneypotFormValidator.showStatus(portStatus, "Please check if the port is available", "warning");
        isValid = false;
      }
    }
    
    // Validate banner if it exists
    if (bannerTextarea) {
      const bannerResult = BannerValidator.validate(bannerTextarea.value);
      if (!bannerResult.isValid) {
        this.addValidationError(bannerResult.message);
        HoneypotFormValidator.setInvalid(bannerTextarea, true);
        if (isValid) {
          bannerTextarea.focus();
        }
        isValid = false;
      } else {
        HoneypotFormValidator.setInvalid(bannerTextarea, false);
        
        // Sanitize banner content before submission if valid
        bannerTextarea.value = BannerValidator.sanitize(bannerTextarea.value);
      }
    }
    
    // Validate CPU settings if resources are enabled
    if (this.elements.showResourcesCheckbox.checked && cpuPeriod && cpuQuota) {
      // Validate period
      const periodResult = ResourceValidator.validateCPUPeriod(parseInt(cpuPeriod.value));
      if (!periodResult.isValid) {
        this.addValidationError(periodResult.message);
        HoneypotFormValidator.setInvalid(cpuPeriod, true);
        if (isValid) {
          cpuPeriod.focus();
        }
        isValid = false;
      } else {
        HoneypotFormValidator.setInvalid(cpuPeriod, false);
      }
      
      // Validate quota
      const quotaResult = ResourceValidator.validateCPUQuota(
        parseInt(cpuQuota.value), 
        parseInt(cpuPeriod.value)
      );
      
      if (!quotaResult.isValid) {
        this.addValidationError(quotaResult.message);
        HoneypotFormValidator.setInvalid(cpuQuota, true);
        if (isValid && periodResult.isValid) {
          cpuQuota.focus();
        }
        isValid = false;
      } else {
        HoneypotFormValidator.setInvalid(cpuQuota, false);
      }
    }
    
    // Validate memory settings if resources are enabled
    if (this.elements.showResourcesCheckbox.checked && memoryLimit && memorySwapLimit) {
      const memResult = ResourceValidator.validateMemorySwap(
        memorySwapLimit.value,
        memoryLimit.value
      );
      
      if (!memResult.isValid) {
        this.addValidationError(memResult.message);
        HoneypotFormValidator.setInvalid(memorySwapLimit, true);
        if (isValid) {
          memorySwapLimit.focus();
        }
        isValid = false;
      } else {
        HoneypotFormValidator.setInvalid(memorySwapLimit, false);
      }
    }
    
    // Enhanced validation for credential fields - executed earlier in the validation flow
    const authResult = this.authHandler.validateCredentials();
    
    // Check specifically for empty fields in credentials
    const credentials = this.authHandler.getCredentials();
    let hasEmptyCredentials = false;
    
    // Check each credential for empty fields
    credentials.forEach((cred, idx) => {
      if (!cred.username || cred.username.trim() === '' || 
          !cred.password || cred.password.trim() === '') {
        hasEmptyCredentials = true;
        
        // Get the field elements
        const usernameField = document.getElementById(`auth_username_${idx}`);
        const passwordField = document.getElementById(`auth_password_${idx}`);
        
        // Mark empty fields as invalid
        if (usernameField && (!cred.username || cred.username.trim() === '')) {
          HoneypotFormValidator.setInvalid(usernameField, true);
          const errorContainer = document.getElementById(`username_error_${idx}`);
          if (errorContainer) {
            errorContainer.textContent = "Username is required";
            errorContainer.classList.remove('hidden');
          }
        }
        
        if (passwordField && (!cred.password || cred.password.trim() === '')) {
          HoneypotFormValidator.setInvalid(passwordField, true);
          const errorContainer = document.getElementById(`password_error_${idx}`);
          if (errorContainer) {
            errorContainer.textContent = "Password is required";
            errorContainer.classList.remove('hidden');
          }
        }
      }
    });
    
    if (!authResult.isValid || hasEmptyCredentials) {
      isValid = false;
      
      // Add a global form error about credentials if needed
      if (this.elements.formStatus && authResult.messages.length > 0) {
        const errorMsg = authResult.messages.join('; ');
        HoneypotFormValidator.showStatus(
          this.elements.formStatus,
          `Authentication issues: ${errorMsg}`,
          "danger"
        );
      } else if (hasEmptyCredentials) {
        // Add message about empty credential fields
        this.addValidationError("All username and password fields are required");
      }
      
      // Scroll to the auth section if it contains errors
      if (this.elements.authContainer) {
        this.elements.authContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
    
    return isValid;
  }
  
  /**
   * Add a validation error to the centralized error list
   * @param {string} message - Error message to display
   */
  addValidationError(message) {
    // This function is now a no-op since we're not showing centralized errors
    // but we keep it to avoid breaking existing code
    console.log("Validation error (not shown to user):", message);
  }
  
  /**
   * Toggle the display of the validation errors container
   * @param {boolean} show - Whether to show the container
   */
  toggleValidationErrorsDisplay(show) {
    // This function is now a no-op since we're not showing centralized errors
    // but we keep it to avoid breaking existing code
  }
  
  /**
   * Toggle submit button state during submission
   * @param {boolean} isSubmitting - Whether form is submitting
   */
  setSubmitting(isSubmitting) {
    const { deployBtn, deployText, deploySpinner } = this.elements;
    
    deployBtn.disabled = isSubmitting;
    deployText.textContent = isSubmitting ? "DEPLOYING..." : "DEPLOY HONEYPOT";
    
    // Add visual styling for disabled state
    if (isSubmitting) {
      deploySpinner.classList.remove("hidden");
      deployBtn.classList.add("opacity-60", "cursor-not-allowed");
      // Prevent multiple submissions by adding a data attribute
      deployBtn.setAttribute("data-submitting", "true");
    } else {
      deploySpinner.classList.add("hidden");
      deployBtn.classList.remove("opacity-60", "cursor-not-allowed");
      deployBtn.removeAttribute("data-submitting");
    }
  }
  
  /**
   * Handle form submission
   * @param {Event} event - Form submission event
   */
  async handleFormSubmit(event) {
    event.preventDefault();
    
    // Prevent multiple submissions
    if (this.elements.deployBtn.hasAttribute("data-submitting")) {
      return;
    }
    
    if (!this.validateForm()) {
      return;
    }
    
    // Show submitting state
    this.setSubmitting(true);
    
    try {
      // Build payload from form
      const formData = new FormData(event.target);
    
      // Sanitize banner content again just to be sure
      const bannerContent = formData.get('banner') || "";
      const sanitizedBanner = BannerValidator.sanitize(bannerContent);
    
      const payload = {
        type: formData.get('type'),
        port: parseInt(formData.get('port')),
        cpu_period: parseInt(formData.get('cpu_period')),
        cpu_quota: parseInt(formData.get('cpu_quota')),
        memory_limit: formData.get('memory_limit'),
        memory_swap_limit: formData.get('memory_swap_limit'),
        banner: sanitizedBanner,
        authentication: {
          allowed_users: this.authHandler.getCredentials()
        }
      };
    
      // Send to API
      const result = await ApiClient.createHoneypot(payload);
    
      // ✅ Clear inline port errors
      if (this.elements.portStatus) {
        this.elements.portStatus.classList.add("hidden");
        this.elements.portStatus.textContent = "";
      }
    
      // ✅ Reset validation state
      this.portValidated = false;
      this.portValid = false;
    
      // ✅ Redirect to honeypots page
      setTimeout(() => {
        window.location.href = "/honeypots";
      }, 1500);
    
    } catch (error) {
      console.error("Deploy error:", error);
      
      // Show error via alert instead of status message
      alert(`Deployment failed: ${error.message || "Unknown error"}`);
    
      // Reset submit button
      this.setSubmitting(false);
    }    
  }
  
  /**
   * Clear port status when port input changes
   */
  clearPortStatus() {
    // Only clear validation state if the form is NOT in the process of submitting
    if (!this.formSubmittedSuccessfully) {
      this.portValidated = false;
      this.portValid = false;
    }
  
    const portStatus = this.elements.portStatus;
    if (portStatus) {
      portStatus.classList.add("hidden");
      portStatus.textContent = "";
    }
  }  
}

// Export for module usage
window.HoneypotFormHandler = HoneypotFormHandler;
