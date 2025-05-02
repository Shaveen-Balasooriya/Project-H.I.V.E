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

/**
 * Initialize form validation for all inputs
 */
function initValidation() {
    // Port validation
    const portInput = document.getElementById('honeypot-port');
    if (portInput) {
        portInput.addEventListener('input', function() {
            validatePortInput(this);
        });
    }
    
    // Banner validation
    const bannerInput = document.getElementById('honeypot-banner');
    if (bannerInput) {
        bannerInput.addEventListener('input', function() {
            validateTextInput(this, 'Banner text is required');
        });
    }
    
    // Honeypot type selection
    const typeSelect = document.getElementById('honeypot-type');
    if (typeSelect) {
        typeSelect.addEventListener('change', function() {
            validateSelectInput(this, 'Please select a honeypot type');
            
            // Load banner template for this type
            updateBannerTemplate(this.value);
        });
    }
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
 * Update default port based on honeypot type - FUNCTION KEPT FOR REFERENCE BUT NOT USED
 * This function is intentionally not called anymore to prevent automatic port assignment
 */
function updateDefaultPort(honeypotType) {
    const portInput = document.getElementById('honeypot-port');
    if (!portInput || !honeypotType) return;
    
    // Only update if user hasn't already set a value
    if (portInput.value.trim()) return;
    
    // Default ports for common honeypot types
    const defaultPorts = {
        'ssh': '2222',
        'ftp': '2121',
        'telnet': '2323',
        'http': '8080',
        'mysql': '3306',
        'smtp': '2525'
    };
    
    if (defaultPorts[honeypotType]) {
        portInput.value = defaultPorts[honeypotType];
        validatePortInput(portInput);
    }
}

/**
 * Update banner template based on honeypot type
 */
function updateBannerTemplate(honeypotType) {
    const bannerInput = document.getElementById('honeypot-banner');
    if (!bannerInput || !honeypotType) return;
    
    // Only update if user hasn't already set a value
    if (bannerInput.value.trim()) return;
    
    // Show loading state
    bannerInput.value = 'Loading banner template...';
    bannerInput.disabled = true;
    
    // Attempt to fetch banner template from API
    fetch(`/api/honeypot/type/${honeypotType}/auth-details`)
        .then(response => response.json())
        .then(data => {
            if (data.banner) {
                bannerInput.value = data.banner;
            } else {
                // Default banners if API doesn't provide one
                const defaultBanners = {
                    'ssh': 'SSH-2.0-OpenSSH_7.4p1 Debian-10',
                    'ftp': '220 FTP Server Ready',
                    'telnet': '\nWelcome to TelnetD\nLogin:',
                    'http': 'Apache/2.4.41 (Unix)',
                    'mysql': '5.7.30-MySQL Community Server',
                    'smtp': '220 SMTP Service Ready'
                };
                
                bannerInput.value = defaultBanners[honeypotType] || `Welcome to ${honeypotType.toUpperCase()} server`;
            }
        })
        .catch(error => {
            console.error('Error fetching banner template:', error);
            bannerInput.value = `Welcome to ${honeypotType.toUpperCase()} server`;
        })
        .finally(() => {
            bannerInput.disabled = false;
            validateTextInput(bannerInput);
        });
}