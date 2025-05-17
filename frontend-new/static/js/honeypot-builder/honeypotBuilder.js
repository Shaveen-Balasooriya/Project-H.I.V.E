/**
 * Honeypot Builder - Main Controller
 * Project H.I.V.E
 * 
 * This is the main entry point for the honeypot builder functionality.
 * It initializes the modules and coordinates their interactions.
 */

document.addEventListener("DOMContentLoaded", function() {
  // Form and UI elements
  const elements = {
    form: document.getElementById("honeypot-form"),
    typeSelect: document.getElementById("type"),
    typeStatus: document.getElementById("type-status"),
    typeLoading: document.getElementById("type-loading"),
    portInput: document.getElementById("port"),
    portStatus: document.getElementById("port-status"),
    checkPortBtn: document.getElementById("check-port"),
    formStatus: document.getElementById("form-status").querySelector("div"),
    deployBtn: document.getElementById("deploy-btn"),
    deployText: document.getElementById("deploy-text"),
    deploySpinner: document.getElementById("deploy-spinner"),
    showResourcesCheckbox: document.getElementById("show-resources"),
    resourceFields: document.getElementById("resource-fields"),
    addCredentialBtn: document.getElementById("add-credential"),
    authContainer: document.getElementById("authentication-container"),
    // Resource allocation elements
    cpuPeriod: document.getElementById("cpu_period"),
    cpuQuota: document.getElementById("cpu_quota"),
    cpuPeriodStatus: document.getElementById("cpu-period-status"),
    cpuQuotaStatus: document.getElementById("cpu-quota-status"),
    memoryLimit: document.getElementById("memory_limit"),
    swapLimit: document.getElementById("memory_swap_limit"),
    memoryStatus: document.getElementById("memory-status")
  };
  
  // Initialize the modules with shared elements
  const authHandler = HoneypotAuthHandler.init(elements);
  const formHandler = HoneypotFormHandler.init(elements, authHandler);
  const uiHandler = HoneypotUIHandler.init(elements);
  
  // Timer for debouncing input events
  let cpuPeriodTimer;
  let cpuQuotaTimer;
  
  // Setup controllers
  initializeApp();
  
  /**
   * Initialize the application
   */
  function initializeApp() {
    loadHoneypotTypes();
    setupEventListeners();
    applyResourceConstraints();
    
    // Add elements needed by BannerValidator to the form handler
    elements.bannerTextarea = document.getElementById('banner');
    elements.bannerError = document.getElementById('banner-error');
    elements.bannerStats = document.getElementById('banner-stats');
  }
  
  /**
   * Apply constraints to resource fields from ResourceValidator
   */
  function applyResourceConstraints() {
    if (elements.cpuPeriod) {
      elements.cpuPeriod.min = ResourceValidator.CONSTRAINTS.CPU_PERIOD.min;
      elements.cpuPeriod.max = ResourceValidator.CONSTRAINTS.CPU_PERIOD.max;
    }
    
    if (elements.cpuQuota) {
      elements.cpuQuota.min = ResourceValidator.CONSTRAINTS.CPU_QUOTA.min;
      elements.cpuQuota.max = ResourceValidator.CONSTRAINTS.CPU_QUOTA.max;
    }
  }
  
  /**
   * Load and display available honeypot types
   */
  async function loadHoneypotTypes() {
    try {
      const types = await ApiClient.getHoneypotTypes();
      
      elements.typeLoading.classList.add("hidden");

      // Clear any existing options except the placeholder
      while (elements.typeSelect.options.length > 1) {
        elements.typeSelect.remove(1);
      }

      // Ensure the placeholder is properly disabled
      elements.typeSelect.options[0].disabled = true;

      // Add animation for options appearing
      let delay = 100;

      // Populate dropdown with available types
      types.forEach((type, index) => {
        setTimeout(() => {
          const option = document.createElement("option");
          option.value = type;
          option.textContent = type.toUpperCase();
          elements.typeSelect.appendChild(option);

          // Briefly highlight the option as it appears
          option.classList.add("animate-pulse");
          setTimeout(() => option.classList.remove("animate-pulse"), 300);
        }, delay * index);
      });

      // Show a nice animation on the select itself
      elements.typeSelect.classList.add("border-accent");
      setTimeout(() => elements.typeSelect.classList.remove("border-accent"), 800);
    } catch (error) {
      console.error("Error loading honeypot types:", error);
      elements.typeLoading.textContent = "Failed to load honeypot types";
      elements.typeLoading.classList.remove("text-white/50");
      elements.typeLoading.classList.add("text-danger");
    }
  }
  
  /**
   * Setup main event listeners
   */
  function setupEventListeners() {
    // Resource allocation toggle - simple checkbox handler
    elements.showResourcesCheckbox.addEventListener("change", uiHandler.toggleResourceFields);
    
    // Type selection change - Enhanced with loading indicator
    elements.typeSelect.addEventListener("change", async function() {
      const selectedType = this.value;
      
      // If empty value is somehow selected, reset selection
      if (!selectedType) {
        this.selectedIndex = 0;
        return;
      }
      
      // Show loading indicator
      if (elements.typeStatus) {
        elements.typeStatus.textContent = "Loading configuration...";
        elements.typeStatus.classList.remove("hidden");
      }
      
      try {
        // Load auth details for selected type - now with await to catch errors
        await authHandler.loadAuthDetailsForType(selectedType);
        
        // Hide loading indicator after successful load
        if (elements.typeStatus) {
          elements.typeStatus.classList.add("hidden");
        }
      } catch (error) {
        console.error("Error loading type configuration:", error);
        if (elements.typeStatus) {
          elements.typeStatus.textContent = "Failed to load configuration";
          elements.typeStatus.classList.remove("hidden");
          
          // Auto-hide error after delay
          setTimeout(() => {
            elements.typeStatus.classList.add("hidden");
          }, 3000);
        }
      }
      
      // Reset port status
      elements.portStatus.classList.add("hidden");
    });
    
    // Port availability check
    elements.checkPortBtn.addEventListener("click", formHandler.handlePortCheck);
    
    // Port input validation - clear port status when port changes
    elements.portInput.addEventListener("input", function() {
      HoneypotFormValidator.enforceMaxLength(this, 5);
      formHandler.clearPortStatus(); // Clear validation state when input changes
    });
    
    // Credential management
    elements.addCredentialBtn.addEventListener("click", authHandler.addNewCredential);
    
    // Form submission
    elements.form.addEventListener("submit", formHandler.handleFormSubmit);
    
    // CPU validation events - Debounced input events for real-time validation
    if (elements.cpuPeriod && elements.cpuQuota) {
      // CPU Period input with debouncing
      elements.cpuPeriod.addEventListener("input", function() {
        clearTimeout(cpuPeriodTimer);
        cpuPeriodTimer = setTimeout(function() {
          validateCPUPeriod();
          // After period validation, also check if quota is still valid with the new period
          if (elements.cpuQuota.value) {
            validateCPUQuota();
          }
        }, 500); // 500ms delay for debouncing
      });
      
      // CPU Quota input with debouncing
      elements.cpuQuota.addEventListener("input", function() {
        clearTimeout(cpuQuotaTimer);
        cpuQuotaTimer = setTimeout(validateCPUQuota, 500); // 500ms delay for debouncing
      });
      
      // Also validate on blur (when user clicks away)
      elements.cpuPeriod.addEventListener("blur", function() {
        validateCPUPeriod();
        if (elements.cpuQuota.value) {
          validateCPUQuota();
        }
      });
      
      elements.cpuQuota.addEventListener("blur", validateCPUQuota);
    }
    
    // Memory validation and auto-adjustment
    if (elements.memoryLimit && elements.swapLimit && elements.memoryStatus) {
      elements.memoryLimit.addEventListener("change", validateMemorySettings);
      elements.swapLimit.addEventListener("change", validateMemorySettings);
    }
    
    // Banner validation
    const bannerTextarea = document.getElementById('banner');
    const bannerError = document.getElementById('banner-error');
    const bannerStats = document.getElementById('banner-stats');
    
    if (bannerTextarea && bannerError) {
      // Setup prevention of disallowed characters
      BannerValidator.setupPreventDisallowedChars(bannerTextarea);
      
      // Real-time validation as user types
      bannerTextarea.addEventListener('input', () => {
        // Debounce validation for better performance
        clearTimeout(bannerTextarea._validationTimer);
        bannerTextarea._validationTimer = setTimeout(() => {
          BannerValidator.updateValidationUI(bannerTextarea, bannerError, bannerStats);
        }, 300);
      });
      
      // Final validation on blur
      bannerTextarea.addEventListener('blur', () => {
        BannerValidator.updateValidationUI(bannerTextarea, bannerError, bannerStats);
      });
      
      // Initialize stats display
      BannerValidator.updateValidationUI(bannerTextarea, bannerError, bannerStats);
    }
  }
  
  /**
   * Validate CPU Period only
   */
  function validateCPUPeriod() {
    const period = parseInt(elements.cpuPeriod.value);
    
    // First validate period
    const periodResult = ResourceValidator.validateCPUPeriod(period);
    if (!periodResult.isValid) {
      HoneypotFormValidator.showStatus(elements.cpuPeriodStatus, periodResult.message, "danger");
      HoneypotFormValidator.setInvalid(elements.cpuPeriod, true);
      return false;
    }
    
    // Valid period
    HoneypotFormValidator.setInvalid(elements.cpuPeriod, false);
    elements.cpuPeriodStatus.classList.add("hidden");
    return true;
  }
  
  /**
   * Validate CPU Quota only (and its relation to period)
   */
  function validateCPUQuota() {
    const period = parseInt(elements.cpuPeriod.value);
    const quota = parseInt(elements.cpuQuota.value);
    
    // First make sure period is valid
    if (!validateCPUPeriod()) {
      return false;
    }
    
    // Then validate quota against period
    const quotaResult = ResourceValidator.validateCPUQuota(quota, period);
    if (!quotaResult.isValid) {
      HoneypotFormValidator.showStatus(elements.cpuQuotaStatus, quotaResult.message, "danger");
      HoneypotFormValidator.setInvalid(elements.cpuQuota, true);
      return false;
    }
    
    // All is valid
    HoneypotFormValidator.setInvalid(elements.cpuQuota, false);
    elements.cpuQuotaStatus.classList.add("hidden");
    return true;
  }
  
  /**
   * Validate CPU settings - Combined validation
   */
  function validateCPUSettings() {
    validateCPUPeriod();
    validateCPUQuota();
  }
  
  /**
   * Validate memory settings and auto-adjust if needed
   */
  function validateMemorySettings() {
    const memLimit = elements.memoryLimit.value;
    const swapLimit = elements.swapLimit.value;
    
    // Validate memory swap against memory limit
    const result = ResourceValidator.validateMemorySwap(swapLimit, memLimit);
    
    if (!result.isValid) {
      // Auto-adjust swap limit if it's lower than memory limit
      if (ResourceValidator.memoryToBytes(swapLimit) < ResourceValidator.memoryToBytes(memLimit)) {
        // Set swap limit to at least memory limit
        const newSwapLimit = memLimit;
        elements.swapLimit.value = newSwapLimit;
        
        HoneypotFormValidator.showStatus(
          elements.memoryStatus, 
          `Swap limit automatically adjusted to ${newSwapLimit} to match memory limit`, 
          "warning"
        );
        
        // Clear message after delay
        setTimeout(() => {
          elements.memoryStatus.classList.add("hidden");
          HoneypotFormValidator.setInvalid(elements.swapLimit, false);
        }, 3000);
      } else {
        // Show error for other validation issues
        HoneypotFormValidator.showStatus(elements.memoryStatus, result.message, "danger");
        HoneypotFormValidator.setInvalid(elements.swapLimit, true);
      }
    } else {
      // All is valid
      HoneypotFormValidator.setInvalid(elements.memoryLimit, false);
      HoneypotFormValidator.setInvalid(elements.swapLimit, false);
      elements.memoryStatus.classList.add("hidden");
    }
  }
});
