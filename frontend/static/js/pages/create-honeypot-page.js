/**
 * Create Honeypot Page
 * Initializes all components required for the honeypot creation workflow
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the multi-step form with stepper navigation
    if (typeof window.initStepper === 'function') {
        window.initStepper();
    }
    
    // Initialize the authentication component
    if (typeof window.initHoneypotAuthentication === 'function') {
        window.initHoneypotAuthentication();
    }
    
    // Initialize the main form functionality
    if (typeof window.initHoneypotCreationForm === 'function') {
        window.initHoneypotCreationForm();
    }
    
    // Initialize form validation
    initValidation();
    
    // Set initial default values
    setDefaultValues();
    
    // Handle empty-state create button if it exists
    const emptyCreateBtn = document.getElementById('empty-create-btn');
    if (emptyCreateBtn) {
        emptyCreateBtn.addEventListener('click', function() {
            window.location.href = '/create-honeypot';
        });
    }
    
    // Update CPU quota maximum to be 100000
    const cpuQuotaInput = document.getElementById('honeypot-cpu-quota');
    if (cpuQuotaInput) {
        cpuQuotaInput.setAttribute('max', '100000');
    }
});

// Add debounce function at the top level
let portCheckTimeout = null;

/**
 * Initialize form validation for all inputs
 */
function initValidation() {
    // Port validation
    const portInput = document.getElementById('honeypot-port');
    if (portInput) {
        portInput.addEventListener('input', function() {
            validatePortWithDebounce(this);
        });
        
        // Keep blur event as a backup
        portInput.addEventListener('blur', function() {
            if (validatePortInput(this)) {
                checkPortAvailability(this.value);
            }
        });
    }
    
    // Banner validation
    const bannerInput = document.getElementById('honeypot-banner');
    if (bannerInput) {
        // Enhanced banner validation
        initBannerValidation(bannerInput);
    }
    
    // Honeypot type selection
    const typeSelect = document.getElementById('honeypot-type');
    if (typeSelect) {
        // Remove tracking of last selected type - always fetch on change
        typeSelect.addEventListener('change', function() {
            validateSelectInput(this, 'Please select a honeypot type');
            
            // Get the selected honeypot type
            const selectedType = this.value;
            
            // Always fetch banner when type changes (even if same type is selected)
            if (selectedType) {
                console.log(`Fetching banner for ${selectedType} honeypot type`);
                // Auto-fetch banner template from the API
                fetchBannerFromAPI(selectedType);
            }
        });
        
        // If type is already selected on page load, fetch the banner
        if (typeSelect.value) {
            console.log(`Initial banner fetch for ${typeSelect.value} honeypot type`);
            fetchBannerFromAPI(typeSelect.value);
        }
    }
}

/**
 * Check if the entered port is available
 * @param {string} port The port to check
 */
async function checkPortAvailability(port) {
    if (!port) return;
    
    const portInput = document.getElementById('honeypot-port');
    if (!portInput) return;
    
    // Show checking status
    portInput.classList.add('border-yellow-500');
    portInput.classList.remove('border-green-500', 'border-red-500');
    
    try {
        // Use the correct endpoint
        const response = await fetch(`/api/honeypot/port-check/${port}`);
        const data = await response.json();
        if (data.available) {
            // Port is available
            portInput.classList.remove('border-yellow-500', 'border-red-500');
            portInput.classList.add('border-green-500');
            
            // Remove error message if exists
            const errorMessage = portInput.parentNode.querySelector('.port-error-message');
            if (errorMessage) {
                errorMessage.remove();
            }
            
            // Optional: Show success notification
            if (typeof showNotification === 'function') {
                showNotification(data.message || `Port ${port} is available`, 'success');
            }
        } else {
            // Port is NOT available
            portInput.classList.remove('border-yellow-500', 'border-green-500');
            portInput.classList.add('border-red-500');
            
            // Clear the port input
            portInput.value = '';
            
            // Show error message
            if (typeof showNotification === 'function') {
                showNotification(data.message || `Port ${port} is already in use`, 'error');
            }
            
            // Add inline error message
            const errorMessage = portInput.parentNode.querySelector('.port-error-message');
            if (!errorMessage) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'text-red-500 text-xs mt-1 port-error-message';
                errorDiv.textContent = data.message || `Port ${port} is already in use`;
                portInput.parentNode.appendChild(errorDiv);
            } else {
                errorMessage.textContent = data.message || `Port ${port} is already in use`;
            }
        }
    } catch (error) {
        console.error('Error checking port availability:', error);
        
        // Remove checking status
        portInput.classList.remove('border-yellow-500');
        
        // Optional: Show error notification
        if (typeof showNotification === 'function') {
            showNotification(`Error checking port availability: ${error.message}. Please verify manually.`, 'error');
        }
    }
}

/**
 * Validate port input with debounce to avoid too many API calls
 */
function validatePortWithDebounce(input) {
    // Clear any existing timeout
    if (portCheckTimeout) {
        clearTimeout(portCheckTimeout);
    }
    
    // Do basic validation immediately
    const isValid = validatePortInput(input);
    
    // Only check port availability via API if the port is valid
    if (isValid) {
        // Show "typing" state
        input.classList.add('border-yellow-500');
        
        // Set a delay before making the API call
        portCheckTimeout = setTimeout(() => {
            checkPortAvailability(input.value);
        }, 600); // 600ms debounce
    }
}

/**
 * Fetch banner template from the honeypot manager API
 * @param {string} honeypotType The selected honeypot type
 */
async function fetchBannerFromAPI(honeypotType) {
    const bannerInput = document.getElementById('honeypot-banner');
    if (!bannerInput || !honeypotType) return;
    
    // Show loading state
    bannerInput.value = 'Loading Existing Banner...';
    bannerInput.placeholder = 'Loading Existing Banner...';
    
    console.log(`Fetching banner for ${honeypotType} from API`);
    
    try {
        // Use the correct endpoint
        const response = await fetch(`/api/honeypot/types/${honeypotType}/auth-details`);
        const data = await response.json();
        if (data && data.banner) {
            // Always update the banner field with the new value
            bannerInput.value = data.banner;
            console.log('Banner automatically loaded from API for', honeypotType);
            
            // Trigger input event to update preview and validation
            bannerInput.dispatchEvent(new Event('input'));
        } else {
            console.log('No banner available from API for this honeypot type');
            // Clear the banner field and set appropriate placeholder
            bannerInput.value = '';
            bannerInput.placeholder = 'Enter banner text that will be shown to users';
        }
    } catch (error) {
        console.error('Error fetching banner from API:', error);
        // Use notification system for errors
        if (typeof showNotification === 'function') {
            showNotification(`Error loading banner: ${error.message}`, 'error');
        }
        
        // Clear the banner field on error
        bannerInput.value = '';
        bannerInput.placeholder = 'Enter banner text (API fetch failed)';
    }
}

/**
 * Initialize enhanced banner validation and UI
 */
function initBannerValidation(bannerInput) {
    // Elements
    const charCounter = document.getElementById('banner-char-counter');
    const lineCounter = document.getElementById('banner-line-counter');
    const bannerPreview = document.getElementById('banner-preview');
    const restoreDefaultBtn = document.getElementById('restore-default-banner');
    const bannerWarnings = document.getElementById('banner-warnings');
    const bannerWarningText = document.getElementById('banner-warning-text');
    
    // Constants
    const MAX_CHARS = 300;
    const MAX_LINES = 3;
    const MIN_CHARS = 20;
    const MAX_REPEATED_CHARS = 10;
    const SECURITY_TERMS = ['unauthorized', 'access', 'monitored', 'security', 'warning', 'legal', 'notice', 'private'];
    
    // Initialize counters
    updateCounters();
    
    // Event listeners
    bannerInput.addEventListener('input', function() {
        // Sanitize input
        this.value = sanitizeBannerInput(this.value);
        
        // Update counters and preview
        updateCounters();
        updatePreview();
        checkForWarnings();
        
        // Basic validation
        validateTextInput(this, 'Banner text is required');
    });
    
    // Restore default button
    if (restoreDefaultBtn) {
        restoreDefaultBtn.addEventListener('click', function() {
            const honeypotType = document.getElementById('honeypot-type').value;
            if (honeypotType) {
                // Show loading state
                bannerInput.value = "Loading default banner...";
                updateBannerTemplate(honeypotType);
            } else {
                // No default banner anymore - leave it blank
                bannerInput.value = "";
                showNotification('Please select a honeypot type first', 'warning');
            }
        });
    }
    
    /**
     * Sanitize banner input
     */
    function sanitizeBannerInput(input) {
        if (!input) return '';
        
        // Remove terminal escape sequences
        input = input.replace(/\x1b\[[0-9;]*[mK]/g, '');
        
        // Keep only printable ASCII (32-126) and newlines
        input = input.replace(/[^\x20-\x7E\n]/g, '');
        
        // Remove unsafe characters
        input = input.replace(/[;|&$\\<>`]/g, '');
        
        // Limit to max lines
        let lines = input.split('\n');
        if (lines.length > MAX_LINES) {
            lines = lines.slice(0, MAX_LINES);
        }
        
        // Preserve spaces and limit length
        lines = lines.map(line => {
            return line.slice(0, 100); // Max 100 chars per line, preserve spaces
        });
        
        // Limit repeated characters
        lines = lines.map(line => {
            return line.replace(new RegExp(`(.)\\1{${MAX_REPEATED_CHARS},}`, 'g'), 
                match => match.slice(0, MAX_REPEATED_CHARS));
        });
        
        // Combine lines
        input = lines.join('\n');
        
        // Enforce total max length
        return input.slice(0, MAX_CHARS);
    }
    
    /**
     * Update character and line counters
     */
    function updateCounters() {
        if (!charCounter || !lineCounter) return;
        
        const text = bannerInput.value || '';
        const chars = text.length;
        const lines = text ? (text.match(/\n/g) || []).length + 1 : 0;
        
        charCounter.textContent = `${chars}/${MAX_CHARS} chars`;
        lineCounter.textContent = `${lines}/${MAX_LINES} lines`;
        
        // Visual warning when approaching limits
        if (chars > MAX_CHARS * 0.9) {
            charCounter.classList.add('text-yellow-500');
        } else {
            charCounter.classList.remove('text-yellow-500');
        }
        
        if (lines >= MAX_LINES) {
            lineCounter.classList.add('text-yellow-500');
        } else {
            lineCounter.classList.remove('text-yellow-500');
        }
    }
    
    /**
     * Update banner preview
     */
    function updatePreview() {
        if (!bannerPreview) return;
        
        let previewText = bannerInput.value || '';
        
        // Escape HTML for safety
        previewText = previewText
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        // Convert newlines to <br> tags
        previewText = previewText.replace(/\n/g, '<br>');
        
        // Show in preview area with terminal-style cursor
        bannerPreview.innerHTML = `${previewText}<span class="animate-pulse">▌</span>`;
    }
    
    /**
     * Check for security term warnings
     */
    function checkForWarnings() {
        if (!bannerWarnings || !bannerWarningText) return;
        
        const text = bannerInput.value.toLowerCase();
        
        // Check minimum length
        if (text.length < MIN_CHARS) {
            bannerWarnings.classList.remove('hidden');
            bannerWarningText.textContent = `Banner should be at least ${MIN_CHARS} characters long`;
            return;
        }
        
        // Check for all symbols/gibberish
        if (/^[^a-zA-Z0-9]+$/.test(text)) {
            bannerWarnings.classList.remove('hidden');
            bannerWarningText.textContent = 'Banner should contain some text, not just symbols';
            return;
        }
        
        // Check for security terms
        const hasSecurityTerm = SECURITY_TERMS.some(term => text.includes(term));
        if (!hasSecurityTerm) {
            bannerWarnings.classList.remove('hidden');
            bannerWarningText.textContent = 'Consider adding security-related terms like "Unauthorized", "Access", or "Monitored"';
            return;
        }
        
        // No warnings needed
        bannerWarnings.classList.add('hidden');
    }
    
    // Initialize preview on load
    updatePreview();
}

/**
 * Set default values for form fields
 */
function setDefaultValues() {
    // Set default CPU values if they exist
    const cpuPeriodInput = document.getElementById('honeypot-cpu-limit');
    const cpuQuotaInput = document.getElementById('honeypot-cpu-quota');
    
    if (cpuPeriodInput && !cpuPeriodInput.value) {
        cpuPeriodInput.value = '100000';
    }
    
    if (cpuQuotaInput && !cpuQuotaInput.value) {
        cpuQuotaInput.value = '50000';
    }
    
    // Set default memory values
    const memoryLimitInput = document.getElementById('honeypot-memory-limit');
    const memorySwapInput = document.getElementById('honeypot-memory-swap');
    
    if (memoryLimitInput && !memoryLimitInput.value) {
        memoryLimitInput.value = '512';
    }
    
    if (memorySwapInput && !memorySwapInput.value) {
        memorySwapInput.value = '512';
    }
}

/**
 * Validate port input
 */
function validatePortInput(input) {
    if (!input) return false;
    
    const value = input.value.trim();
    const minPort = 1;
    const maxPort = 65535;
    
    // Remove previous validation classes
    input.classList.remove('border-red-500', 'border-green-500');
    
    // Empty check
    if (!value) {
        input.classList.add('border-red-500');
        return false;
    }
    
    // Range check
    const portNum = parseInt(value);
    if (isNaN(portNum) || portNum < minPort || portNum > maxPort) {
        input.classList.add('border-red-500');
        return false;
    }
    
    // Add success class
    input.classList.add('border-green-500');
    return true;
}

/**
 * Validate text input
 */
function validateTextInput(input, errorMessage) {
    if (!input) return false;
    
    const value = input.value.trim();
    
    // Remove previous validation classes
    input.classList.remove('border-red-500', 'border-green-500');
    
    // Empty check
    if (!value) {
        input.classList.add('border-red-500');
        return false;
    }
    
    // Add success class
    input.classList.add('border-green-500');
    return true;
}

/**
 * Validate select input
 */
function validateSelectInput(input, errorMessage) {
    if (!input) return false;
    
    const value = input.value;
    
    // Remove previous validation classes
    input.classList.remove('border-red-500', 'border-green-500');
    
    // Empty selection check
    if (!value) {
        input.classList.add('border-red-500');
        return false;
    }
    
    // Add success class
    input.classList.add('border-green-500');
    return true;
}

/**
 * Update banner template based on honeypot type
 * Only called when explicitly requested via the "Restore Default" button
 */
async function updateBannerTemplate(honeypotType) {
    const bannerInput = document.getElementById('honeypot-banner');
    if (!bannerInput || !honeypotType) return;
    
    // Show loading state
    bannerInput.value = 'Loading Existing Banner...';
    bannerInput.disabled = true;
    
    try {
        // Use the correct endpoint
        const response = await fetch(`/api/honeypot/types/${honeypotType}/auth-details`);
        const data = await response.json();
        if (data && data.banner) {
            bannerInput.value = data.banner;
            console.log('Loaded banner template from API');
        } else {
            // Leave empty if API doesn't provide banner
            bannerInput.value = '';
            console.log('No banner template available from API');
            // Show notification for clarity
            if (typeof showNotification === 'function') {
                showNotification('No default banner available for this honeypot type', 'info');
            }
        }
        
        // Trigger validation and UI updates
        bannerInput.dispatchEvent(new Event('input'));
    } catch (error) {
        console.error('Error fetching banner template:', error);
        // Show error via notification
        if (typeof showNotification === 'function') {
            showNotification(`Failed to load banner template: ${error.message}`, 'error');
        }
        
        // Don't set a default value, just clear and show error
        bannerInput.value = '';
    } finally {
        bannerInput.disabled = false;
        validateTextInput(bannerInput);
    }
}