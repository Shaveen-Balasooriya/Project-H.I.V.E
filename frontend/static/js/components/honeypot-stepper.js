/**
 * Honeypot Creation Stepper Component
 * This module handles the multi-step form navigation for honeypot creation
 */

// Tracking variables for port validation
let portValidationTimeout = null;
let lastPortChecked = null;
let lastPortAvailable = null;

// Track the latest port check request
let latestPortCheckToken = 0;
let currentPortCheckController = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the stepper
    initStepper();
    
    // Initialize resource sliders and indicators
    initResourceControls();
    
    // Initialize form validation
    initFormValidation();
    
    // Initialize the summary review
    initSummaryReview();
    
    // Prevent Enter key from submitting form prematurely
    preventFormSubmissionOnEnter();

    const form = document.getElementById('create-honeypot-form');
    if (form) {
        form.addEventListener('submit', function() {
            // Removed: showLoadingOverlay();
        });
    }
});

// Prevent accidental form submission when pressing Enter
function preventFormSubmissionOnEnter() {
    const form = document.getElementById('create-honeypot-form');
    const inputs = form.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        input.addEventListener('keydown', function(event) {
            // Check if the pressed key is Enter
            if (event.key === 'Enter') {
                // Get current step
                const activeStep = document.querySelector('.step-content.active');
                if (!activeStep) return;
                
                const stepNumber = parseInt(activeStep.dataset.step);
                const totalSteps = document.querySelectorAll('.step-content').length;
                
                // If not on the last step, prevent form submission and trigger next button click
                if (stepNumber < totalSteps) {
                    event.preventDefault();
                    
                    // Validate current step before proceeding
                    if (validateStep(stepNumber)) {
                        document.getElementById('next-btn').click();
                    }
                }
            }
        });
    });
}

// Main stepper initialization function
function initStepper() {
    const form = document.getElementById('create-honeypot-form');
    const nextBtn = document.getElementById('next-btn');
    const backBtn = document.getElementById('back-btn');
    const submitBtn = document.getElementById('submit-btn');
    const stepContents = document.querySelectorAll('.step-content');
    const stepItems = document.querySelectorAll('.step-item');
    const stepIndicator = document.getElementById('step-indicator');
    
    if (!form || !nextBtn || !backBtn || !submitBtn) return;
    
    let currentStep = 1;
    const totalSteps = stepContents.length;
    
    // Initialize step titles for the indicator
    const stepTitles = [
        'Basic Settings',
        'Resources',
        'Authentication',
        'Review'
    ];
    
    // Override the default form submit behavior
    form.addEventListener('submit', function(e) {
        // Only allow submission on the last step
        if (currentStep !== totalSteps) {
            e.preventDefault();
            return false;
        }
        
        // On last step, let the form submission proceed normally
        return true;
    });
    
    // Handle next button click
    nextBtn.addEventListener('click', function() {
        // Validate current step
        if (!validateStep(currentStep)) {
            return;
        }
        
        if (currentStep < totalSteps) {
            currentStep++;
            updateStepVisibility();
        }
    });
    
    // Handle back button click
    backBtn.addEventListener('click', function() {
        if (currentStep > 1) {
            currentStep--;
            updateStepVisibility();
        }
    });
    
    // Update which step is visible
    function updateStepVisibility() {
        // Update step contents
        stepContents.forEach(content => {
            const step = parseInt(content.dataset.step);
            content.classList.toggle('hidden', step !== currentStep);
            content.classList.toggle('active', step === currentStep);
        });
        
        // Update step indicators
        stepItems.forEach(item => {
            const step = parseInt(item.dataset.step);
            
            // Remove active class from all
            item.classList.remove('active');
            
            // Update the step circle
            const circle = item.querySelector('.step-circle');
            if (circle) {
                circle.classList.remove('bg-accent', 'bg-dark-300', 'text-white', 'text-gray-400');
                
                if (step < currentStep) {
                    // Completed step
                    circle.classList.add('bg-accent', 'text-white');
                    
                    // Replace number with checkmark
                    circle.innerHTML = `
                        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                    `;
                } else if (step === currentStep) {
                    // Current step
                    item.classList.add('active');
                    circle.classList.add('bg-accent', 'text-white');
                    circle.textContent = step;
                } else {
                    // Future step
                    circle.classList.add('bg-dark-300', 'text-gray-400');
                    circle.textContent = step;
                }
            }
        });
        
        // Update button visibility
        backBtn.classList.toggle('hidden', currentStep === 1);
        nextBtn.classList.toggle('hidden', currentStep === totalSteps);
        submitBtn.classList.toggle('hidden', currentStep !== totalSteps);
        
        // Update step indicator text
        if (stepIndicator) {
            stepIndicator.textContent = `Step ${currentStep} of ${totalSteps}: ${stepTitles[currentStep - 1]}`;
        }
        
        // If on the last step, update the summary
        if (currentStep === totalSteps) {
            updateSummary();
        }
        
        // Dispatch a custom event when the step changes
        // This allows other components to react to step changes
        const stepChangedEvent = new CustomEvent('stepChanged', { 
            detail: { 
                step: currentStep,
                totalSteps: totalSteps,
                stepName: stepTitles[currentStep - 1]
            }
        });
        document.dispatchEvent(stepChangedEvent);
    }
    
    // Validate the current step
    function validateStep(step) {
        switch (step) {
            case 1:
                // Validate basic settings
                const honeypotType = document.getElementById('honeypot-type').value;
                const honeypotPort = document.getElementById('honeypot-port').value;
                const banner = document.getElementById('honeypot-banner').value;
                
                if (!honeypotType || honeypotType === '') {
                    showNotification('Please select a honeypot type', 'error');
                    return false;
                }
                
                if (!honeypotPort || isNaN(honeypotPort) || honeypotPort < 1 || honeypotPort > 65535) {
                    showNotification('Please enter a valid port number (1-65535)', 'error');
                    return false;
                }
                
                // Check if port has red border (indicating unavailability)
                const portInput = document.getElementById('honeypot-port');
                if (portInput) {
                    // If the port is not available, block the stepper
                    if (
                        !lastPortChecked ||
                        lastPortChecked !== portInput.value.trim() ||
                        lastPortAvailable !== true
                    ) {
                        showNotification('Please select an available port before proceeding.', 'error');
                        portInput.classList.add('border-red-500');
                        showFieldError(portInput, 'Port is not available or has not been checked.');
                        return false;
                    }
                }
                
                if (!banner || !banner.trim()) {
                    showNotification('Please enter a banner message', 'error');
                    return false;
                }
                
                return true;
            
            case 2:
                // Validate resource settings
                const cpuPeriod = document.getElementById('honeypot-cpu-limit');
                const cpuQuota = document.getElementById('honeypot-cpu-quota');
                const memoryLimit = document.getElementById('honeypot-memory-limit');
                const memorySwap = document.getElementById('honeypot-memory-swap');
                
                // Force validation on all fields before proceeding
                if (cpuPeriod) validateNumericInputOnBlur(cpuPeriod, 50000, 1000000);
                if (cpuQuota) validateNumericInputOnBlur(cpuQuota, 25000, 100000);
                if (memoryLimit) validateNumericInputOnBlur(memoryLimit, 100, 4096);
                if (memorySwap) validateNumericInputOnBlur(memorySwap, 100, 4096);
                
                // Validate CPU Period
                if (!validateResourceInput(cpuPeriod, 50000, 1000000, 'CPU Period')) {
                    return false;
                }
                
                // Validate CPU Quota
                if (!validateResourceInput(cpuQuota, 25000, 100000, 'CPU Quota')) {
                    return false;
                }
                
                // Validate Memory Limit
                if (!validateResourceInput(memoryLimit, 100, 4096, 'Memory Limit')) {
                    return false;
                }
                
                // Validate Memory Swap
                if (!validateResourceInput(memorySwap, 100, 4096, 'Memory Swap')) {
                    return false;
                }
                
                // Additional validation: Ensure CPU Quota is not greater than CPU Period
                const periodValue = parseInt(cpuPeriod.value);
                const quotaValue = parseInt(cpuQuota.value);
                if (quotaValue > periodValue) {
                    showNotification('CPU Quota cannot be greater than CPU Period', 'error');
                    return false;
                }
                
                return true;
                
            case 3:
                // Validate authentication credentials using the new function
                // Ensure the function is available globally or imported
                if (typeof window.validateAllCredentialRows === 'function') {
                    if (!window.validateAllCredentialRows()) {
                        showNotification('Please ensure all credential fields meet the requirements (3-32 characters) and are not empty.', 'error');
                        return false;
                    }
                } else {
                    console.warn('validateAllCredentialRows function not found for step 3 validation.');
                    // Fallback or default validation if needed
                    const credentialsContainer = document.getElementById('auth-credentials-container');
                    if (!credentialsContainer) return true; // No container, assume valid

                    const rows = credentialsContainer.querySelectorAll('.credential-row');
                    if (rows.length < 3) {
                        showNotification('You need at least 3 credential pairs', 'error');
                        return false;
                    }
                    // Basic check for empty fields as fallback
                    let hasEmptyFields = false;
                    rows.forEach(row => {
                        row.querySelectorAll('input').forEach(input => {
                            if (!input.value.trim()) {
                                hasEmptyFields = true;
                                input.classList.add('border-red-500');
                            }
                        });
                    });
                    if (hasEmptyFields) {
                         showNotification('All credential fields must be filled', 'error');
                         return false;
                    }
                }
                return true; // Passed validation
                
            case 4:
                // Review - no validation needed
                return true;
                
            default:
                return true;
        }
        
        // Helper function for final validation
        function validateNumericInputOnBlur(input, min, max) {
            if (!input) return;
            
            // Check if the value is a valid number
            const value = parseInt(input.value);
            
            // If empty or not a number, set to minimum
            if (isNaN(value) || input.value === '') {
                input.value = min;
            } 
            // If below minimum, set to minimum
            else if (value < min) {
                input.value = min;
            } 
            // If above maximum, set to maximum
            else if (value > max) {
                input.value = max;
            }
            
            // Remove validation styling - this removes the red bars
            input.classList.remove('border-red-500');
        }
    }
    
    // Validate resource input fields (CPU and Memory)
    function validateResourceInput(inputElement, min, max, fieldName) {
        if (!inputElement) return true;
        
        // Remove previous validation styling
        inputElement.classList.remove('border-red-500');
        
        const value = inputElement.value.trim();
        
        // Check if empty
        if (!value) {
            showNotification(`${fieldName} is required`, 'error');
            return false;
        }
        
        // Check if it's a valid number
        if (!/^\d+$/.test(value)) {
            showNotification(`${fieldName} must be a valid integer`, 'error');
            return false;
        }
        
        // Check range
        const numValue = parseInt(value);
        if (numValue < min || numValue > max) {
            showNotification(`${fieldName} must be between ${min} and ${max}`, 'error');
            return false;
        }
        
        return true;
    }
    
    // Trigger initial step setup
    updateStepVisibility();
}

// Update summary for review step
function updateSummary() {
    // Basic settings summary
    updateSummaryField('summary-type', 'honeypot-type', value => value.toUpperCase());
    updateSummaryField('summary-port', 'honeypot-port');
    updateSummaryField('summary-banner', 'honeypot-banner');
    
    // Resource settings summary
    updateSummaryField('summary-cpu-period', 'honeypot-cpu-limit', value => `${value} µs`);
    updateSummaryField('summary-cpu-quota', 'honeypot-cpu-quota', value => `${value} µs`);
    
    // Calculate CPU percentage
    const cpuPeriod = document.getElementById('honeypot-cpu-limit')?.value;
    const cpuQuota = document.getElementById('honeypot-cpu-quota')?.value;
    const cpuPercentage = document.getElementById('summary-cpu-percentage');
    
    if (cpuPeriod && cpuQuota && cpuPercentage) {
        const percentage = Math.round((parseInt(cpuQuota) / parseInt(cpuPeriod)) * 100);
        cpuPercentage.textContent = `${percentage}%`;
    }
    
    updateSummaryField('summary-memory', 'honeypot-memory-limit', value => `${value} MB`);
    updateSummaryField('summary-memory-swap', 'honeypot-memory-swap', value => `${value} MB`);
    
    // Auth credentials summary
    updateCredentialSummary();
}

// Helper function to update summary fields
function updateSummaryField(summaryId, inputId, transform = null) {
    const summaryElement = document.getElementById(summaryId);
    const inputElement = document.getElementById(inputId);
    
    if (summaryElement && inputElement) {
        let value = inputElement.value;
        
        if (inputElement.tagName === 'SELECT') {
            const selectedOption = inputElement.options[inputElement.selectedIndex];
            value = selectedOption.text || value;
        }
        
        if (transform && typeof transform === 'function') {
            value = transform(value);
        }
        
        summaryElement.textContent = value || '—';
    }
}

// Update the credentials summary
function updateCredentialSummary() {
    const credentialsContainer = document.getElementById('auth-credentials-container');
    const summaryContainer = document.getElementById('summary-credentials');
    const countElement = document.getElementById('summary-credential-count');
    
    if (!credentialsContainer || !summaryContainer) return;
    
    // Clear existing summary
    summaryContainer.innerHTML = '';
    
    // Get all credential rows
    const rows = credentialsContainer.querySelectorAll('.credential-row');
    const count = rows.length;
    
    // Update count
    if (countElement) countElement.textContent = count;
    
    // Display sample credentials (up to 5)
    const sampleCount = Math.min(5, count);
    for (let i = 0; i < sampleCount; i++) {
        const row = rows[i];
        const usernameInput = row.querySelector('input[name^="username_"]');
        const passwordInput = row.querySelector('input[name^="password_"]');
        
        if (usernameInput && passwordInput) {
            const credBadge = document.createElement('div');
            credBadge.className = 'bg-dark-300 text-xs p-2 rounded text-gray-200';
            credBadge.innerHTML = `
                <span class="font-medium text-accent">${usernameInput.value}</span>:<span class="opacity-75">${passwordInput.value}</span>
            `;
            summaryContainer.appendChild(credBadge);
        }
    }
    
    // Add "and more" badge if there are more credentials
    if (count > sampleCount) {
        const moreBadge = document.createElement('div');
        moreBadge.className = 'bg-dark-300 text-xs p-2 rounded text-gray-300';
        moreBadge.textContent = `+ ${count - sampleCount} more`;
        summaryContainer.appendChild(moreBadge);
    }
}

// Make functions available globally
window.initStepper = initStepper;
window.updateSummary = updateSummary;

function initResourceControls() {
    const cpuPeriod = document.getElementById('honeypot-cpu-limit');
    const cpuQuota = document.getElementById('honeypot-cpu-quota');
    const cpuPercentage = document.getElementById('cpu-percentage');
    const memoryLimit = document.getElementById('honeypot-memory-limit');
    const memorySwap = document.getElementById('honeypot-memory-swap');
    
    // Add input validation for all resource fields
    if (cpuPeriod) {
        cpuPeriod.addEventListener('input', function() {
            // Only strip non-numeric characters during input
            this.value = this.value.replace(/[^\d]/g, '');
            updateCpuPercentage();
        });
        
        // Apply min/max constraints only when focus is lost
        cpuPeriod.addEventListener('blur', function() {
            validateNumericInputOnBlur(this, 50000, 1000000);
            updateCpuPercentage();
        });
    }
    
    if (cpuQuota) {
        cpuQuota.addEventListener('input', function() {
            // Only strip non-numeric characters during input
            this.value = this.value.replace(/[^\d]/g, '');
            updateCpuPercentage();
        });
        
        // Apply min/max constraints only when focus is lost
        cpuQuota.addEventListener('blur', function() {
            validateNumericInputOnBlur(this, 25000, 100000);
            updateCpuPercentage();
        });
    }
    
    if (memoryLimit) {
        memoryLimit.addEventListener('input', function() {
            // Only strip non-numeric characters during input
            this.value = this.value.replace(/[^\d]/g, '');
        });
        
        // Apply min/max constraints only when focus is lost
        memoryLimit.addEventListener('blur', function() {
            validateNumericInputOnBlur(this, 100, 4096);
        });
    }
    
    if (memorySwap) {
        memorySwap.addEventListener('input', function() {
            // Only strip non-numeric characters during input
            this.value = this.value.replace(/[^\d]/g, '');
        });
        
        // Apply min/max constraints only when focus is lost
        memorySwap.addEventListener('blur', function() {
            validateNumericInputOnBlur(this, 100, 4096);
        });
    }
    
    // Validate numeric inputs only when focus is lost
    function validateNumericInputOnBlur(input, min, max) {
        // Check if the value is a valid number
        const value = parseInt(input.value);
        
        // If empty or not a number, set to minimum
        if (isNaN(value) || input.value === '') {
            input.value = min;
        } 
        // If below minimum, set to minimum
        else if (value < min) {
            input.value = min;
        } 
        // If above maximum, set to maximum
        else if (value > max) {
            input.value = max;
        }
        
        // Remove validation styling - this removes the red bars
        input.classList.remove('border-red-500');
    }
    
    // Update CPU percentage when period or quota changes
    function updateCpuPercentage() {
        if (cpuPeriod && cpuQuota && cpuPercentage) {
            const period = parseInt(cpuPeriod.value);
            const quota = parseInt(cpuQuota.value);
            
            if (!isNaN(period) && !isNaN(quota) && period > 0) {
                const percentage = Math.round((quota / period) * 100);
                cpuPercentage.textContent = `${percentage}%`;
                
                // Visual feedback if quota > period (invalid configuration)
                // We only add warning class but don't prevent typing
                if (quota > period) {
                    cpuQuota.classList.add('border-yellow-500');
                } else {
                    cpuQuota.classList.remove('border-yellow-500');
                }
            }
        }
    }
    
    // Initial calculation
    updateCpuPercentage();
}

function initFormValidation() {
    // Validate honeypot type
    const honeypotType = document.getElementById('honeypot-type');
    if (honeypotType) {
        honeypotType.addEventListener('change', function() {
            const selectedType = this.value;
            if (!selectedType) return;
            
            // Fetch authentication details and banner for this honeypot type
            fetchHoneypotTypeDetails(selectedType);
        });
    }
    
    // Validate port field
    const portInput = document.getElementById('honeypot-port');
    if (portInput) {
        // Validate and check port on every input (no debounce)
        portInput.addEventListener('input', function() {
            checkPortAvailabilityAPI(this);
        });
        // Optionally, still check on blur for completeness
        portInput.addEventListener('blur', function() {
            checkPortAvailabilityAPI(this);
        });
    }
    
    // Banner validation
    const bannerInput = document.getElementById('honeypot-banner');
    if (bannerInput) {
        bannerInput.addEventListener('input', function() {
            validateBannerField(this);
        });
        
        // Also validate on blur
        bannerInput.addEventListener('blur', function() {
            validateBannerField(this, true);
        });
    }
}

/**
 * Check if the entered port is available via API
 */
async function checkPortAvailabilityAPI(portField) {
    if (!portField || !portField.value) return;

    const port = portField.value.trim();
    const thisToken = ++latestPortCheckToken;

    // Abort any previous request
    if (currentPortCheckController) {
        currentPortCheckController.abort();
    }
    currentPortCheckController = new AbortController();
    const signal = currentPortCheckController.signal;

    portField.dataset.checkingPort = port;

    if (typeof showNotification === 'function') {
        showNotification('Checking port availability...', 'info');
    }

    portField.classList.add('border-yellow-500');
    clearFieldError(portField);

    try {
        const response = await fetch(`/api/honeypot/port-check/${port}`, { signal });
        const data = await response.json();

        // Only update if this is the latest request and the value hasn't changed
        if (thisToken !== latestPortCheckToken || portField.value.trim() !== port) {
            return;
        }
        portField.classList.remove('border-yellow-500');

        lastPortChecked = port;
        if (data.available) {
            portField.classList.remove('border-red-500');
            portField.classList.add('border-green-500');
            lastPortAvailable = true;
            if (typeof showNotification === 'function') {
                showNotification(data.message || `Port ${port} is available`, 'success');
            }
        } else {
            portField.classList.remove('border-green-500', 'border-yellow-500');
            portField.classList.add('border-red-500');
            lastPortAvailable = false;
            if (typeof showNotification === 'function') {
                showNotification(data.message || `Port ${port} is already in use`, 'error');
            }
        }
    } catch (error) {
        // Ignore abort errors
        if (error.name === 'AbortError') return;
        if (thisToken !== latestPortCheckToken || portField.value.trim() !== port) return;
        portField.classList.remove('border-yellow-500');
        lastPortAvailable = null;
        if (typeof showNotification === 'function') {
            showNotification(`Error checking port: ${error.message}. Please verify manually.`, 'error');
        }
    } finally {
        if (thisToken === latestPortCheckToken) {
            delete portField.dataset.checkingPort;
            currentPortCheckController = null;
        }
    }
}

function validatePortField(field, showError = false) {
    if (!field) return true;
    
    const value = field.value.trim();
    field.classList.remove('border-red-500', 'border-green-500');
    
    // Empty check
    if (!value) {
        if (showError) {
            field.classList.add('border-red-500');
            showFieldError(field, 'Port number is required');
        }
        return false;
    }
    
    // Validate port range
    const port = parseInt(value);
    if (isNaN(port) || port < 1 || port > 65535) {
        field.classList.add('border-red-500');
        showFieldError(field, 'Port must be between 1-65535');
        return false;
    }
    
    // Warn about privileged ports
    if (port < 1024) {
        field.classList.add('border-red-500');
        showFieldError(field, 'Privileged port: Requires root access');
        return true; // We allow it but with warning
    }
    
    // Valid port
    field.classList.add('border-green-500');
    clearFieldError(field);
    return true;
}

function validateBannerField(field, showError = false) {
    if (!field) return true;
    
    const value = field.value.trim();
    field.classList.remove('border-red-500', 'border-green-500');
    
    if (!value) {
        if (showError) {
            field.classList.add('border-red-500');
            showFieldError(field, 'Banner message is required');
        }
        return false;
    }
    
    field.classList.add('border-green-500');
    clearFieldError(field);
    return true;
}

function showFieldError(field, message) {
    // Remove any existing error/status messages (but do not show new ones)
    clearFieldError(field);
    // No DOM error message shown
}

function clearFieldError(field) {
    const parent = field.parentNode;
    if (!parent) return;
    parent.querySelectorAll('.field-error, .port-status, .field-message').forEach(el => el.remove());
}

async function fetchHoneypotTypeDetails(selectedType) {
    const bannerInput = document.getElementById('honeypot-banner');
    if (!bannerInput) return;
    
    try {
        bannerInput.placeholder = "Enter banner text that will be shown to users";
        
        // Use the correct endpoint
        const response = await fetch(`/api/honeypot/types/${selectedType}/auth-details`);
        const data = await response.json();
        
        // Update banner if provided
        if (data && data.banner) {
            bannerInput.value = data.banner;
            bannerInput.dispatchEvent(new Event('input')); // Trigger validation
        }
    } catch (error) {
        console.error('Error fetching honeypot details:', error);
    } finally {
        bannerInput.removeAttribute('disabled');
        bannerInput.placeholder = "Enter the banner text that will be shown to users";
    }
}

function initSummaryReview() {
    // This will be called when reaching the last step
    // We'll implement the logic to update all summary fields
}