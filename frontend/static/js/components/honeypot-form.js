/**
 * Honeypot Creation Form - handles the multi-step form for creating honeypots
 */

// Track the current step of the form
let currentStep = 1;
const totalSteps = 4;
let authenticationData = {
    allowed_users: []
};

/**
 * Initialize the honeypot creation form
 */
function initHoneypotCreationForm() {
    setupStepNavigation();
    setupFormValidation();
    setupCredentialManagement();
    setupSummaryGeneration();
    loadAuthenticationDefaults();
}

/**
 * Load default authentication credentials for selected honeypot type
 */
async function loadAuthenticationDefaults() {
    const honeypotTypeSelect = document.getElementById('honeypot-type');
    
    honeypotTypeSelect.addEventListener('change', async function() {
        const selectedType = this.value;
        if (!selectedType) return;
        
        // Clear existing credentials
        authenticationData.allowed_users = [];
        
        try {
            // Use the correct endpoint
            const response = await fetch(`/api/honeypot/types/${selectedType}/auth-details`);
            const data = await response.json();
            console.log("Loaded auth details:", data);
            
            // Set authentication data
            if (data.authentication && data.authentication.allowed_users) {
                authenticationData.allowed_users = data.authentication.allowed_users;
                
                // If we're on the auth step, update the UI
                if (currentStep === 3) {
                    renderCredentials();
                }
            }
        } catch (error) {
            console.error("Error loading authentication defaults:", error);
            // Set fallback defaults
            authenticationData.allowed_users = [
                { username: "admin", password: "admin123" },
                { username: "root", password: "toor" },
                { username: "user", password: "password" }
            ];
            
            if (currentStep === 3) {
                renderCredentials();
            }
        }
    });
}

/**
 * Setup step navigation for the multi-step form
 */
function setupStepNavigation() {
    const nextBtn = document.getElementById('next-btn');
    const backBtn = document.getElementById('back-btn');
    const submitBtn = document.getElementById('submit-btn');
    
    nextBtn.addEventListener('click', function() {
        if (validateCurrentStep()) {
            goToStep(currentStep + 1);
        }
    });
    
    backBtn.addEventListener('click', function() {
        goToStep(currentStep - 1);
    });
    
    // Handle form submission
    document.getElementById('create-honeypot-form').addEventListener('submit', function(e) {
        e.preventDefault();
        submitHoneypotForm();
    });
}

/**
 * Validate the current form step
 * @returns {boolean} True if validation passes
 */
function validateCurrentStep() {
    if (currentStep === 1) {
        // Validate basic settings
        const type = document.getElementById('honeypot-type').value;
        const port = document.getElementById('honeypot-port').value;
        const banner = document.getElementById('honeypot-banner').value;
        
        if (!type) {
            showNotification('Please select a honeypot type', 'error');
            return false;
        }
        
        if (!port || port < 1 || port > 65535) {
            showNotification('Please enter a valid port number (1-65535)', 'error');
            return false;
        }
        
        return true;
    } 
    else if (currentStep === 3) {
        // Validate authentication - ensure we have at least 3 credentials
        if (authenticationData.allowed_users.length < 3) {
            showNotification('Please add at least 3 credential pairs', 'error');
            return false;
        }
        
        return true;
    }
    
    return true;
}

/**
 * Navigate to a specific step in the form
 * @param {number} step The step number to go to
 */
function goToStep(step) {
    if (step < 1 || step > totalSteps) return;
    
    // Hide all steps
    document.querySelectorAll('.step-content').forEach(el => {
        el.classList.add('hidden');
        el.classList.remove('active');
    });
    
    // Show the target step
    const targetStep = document.querySelector(`.step-content[data-step="${step}"]`);
    targetStep.classList.remove('hidden');
    targetStep.classList.add('active');
    
    // Update stepper circles
    document.querySelectorAll('.step-item').forEach(el => {
        const stepNum = parseInt(el.getAttribute('data-step'));
        const stepCircle = el.querySelector('.step-circle');
        
        if (stepNum === step) {
            el.classList.add('active');
            stepCircle.classList.remove('bg-dark-300', 'text-gray-400');
            stepCircle.classList.add('bg-accent', 'text-white');
        } else if (stepNum < step) {
            el.classList.add('completed');
            stepCircle.classList.remove('bg-dark-300', 'text-gray-400');
            stepCircle.classList.add('bg-accent', 'text-white');
        } else {
            el.classList.remove('active', 'completed');
            stepCircle.classList.add('bg-dark-300', 'text-gray-400');
            stepCircle.classList.remove('bg-accent', 'text-white');
        }
    });
    
    // Update back button visibility
    const backBtn = document.getElementById('back-btn');
    if (step === 1) {
        backBtn.classList.add('hidden');
    } else {
        backBtn.classList.remove('hidden');
    }
    
    // Update next/submit button
    const nextBtn = document.getElementById('next-btn');
    const submitBtn = document.getElementById('submit-btn');
    
    if (step === totalSteps) {
        nextBtn.classList.add('hidden');
        submitBtn.classList.remove('hidden');
        updateSummary(); // Update summary before showing the final step
    } else {
        nextBtn.classList.remove('hidden');
        submitBtn.classList.add('hidden');
    }
    
    // Update step indicator text
    let stepText = "";
    switch (step) {
        case 1: stepText = "Step 1 of 4: Basic Settings"; break;
        case 2: stepText = "Step 2 of 4: Resources"; break;
        case 3: stepText = "Step 3 of 4: Authentication"; break;
        case 4: stepText = "Step 4 of 4: Review"; break;
    }
    
    document.getElementById('step-indicator').textContent = stepText;
    
    // If we're on the authentication step, render credentials
    if (step === 3) {
        renderCredentials();
    }
    
    // Update current step
    currentStep = step;
}

/**
 * Setup form validation handlers
 */
function setupFormValidation() {
    // Add any specific validation handlers here
}

/**
 * Setup credential management for the authentication step
 */
function setupCredentialManagement() {
    const addBtn = document.getElementById('add-credential-btn');
    addBtn.addEventListener('click', function handler(e) {
        // Prevent double click/add
        if (addBtn.disabled) return;
        // Prevent adding if any existing credential is invalid
        if (!validateAllCredentialInputs()) {
            showNotification('Please fill in all existing credential fields correctly before adding new ones.', 'warning');
            return;
        }
        // Check if we've reached the maximum number of credentials
        if (authenticationData.allowed_users.length >= 20) {
            showNotification('Maximum number of credentials (20) reached', 'error');
            return;
        }
        // Disable button immediately to prevent double add
        addBtn.disabled = true;
        // Add a new credential
        authenticationData.allowed_users.push({ username: "", password: "" });
        renderCredentials();
        // Button will be re-enabled by updateAddCredentialButtonState after render
    });

    // Initial rendering
    renderCredentials();
}

/**
 * Enable/disable the add credential button based on validity and count
 */
function updateAddCredentialButtonState() {
    const addBtn = document.getElementById('add-credential-btn');
    if (!addBtn) return;
    const container = document.getElementById('auth-credentials-container');
    if (!container) {
        addBtn.disabled = false;
        return;
    }
    const count = authenticationData.allowed_users.length;
    if (count >= 20 || !validateAllCredentialInputs()) {
        addBtn.disabled = true;
    } else {
        addBtn.disabled = false;
    }
}

/**
 * Validate all credential input fields in the UI
 * Returns true if all are valid, false otherwise
 */
function validateAllCredentialInputs() {
    const container = document.getElementById('auth-credentials-container');
    if (!container) return true;
    let allValid = true;
    container.querySelectorAll('input[data-field]').forEach(input => {
        const value = input.value.trim();
        if (value.length < 4 || value.length > 15) {
            input.classList.add('border-red-500');
            allValid = false;
        } else {
            input.classList.remove('border-red-500');
        }
    });
    return allValid;
}

/**
 * Render the credential list in the UI
 */
function renderCredentials() {
    const container = document.getElementById('auth-credentials-container');
    if (!container) return;
    
    // Clear container
    container.innerHTML = '';
    
    // Add credential rows
    authenticationData.allowed_users.forEach((cred, index) => {
        const row = document.createElement('div');
        row.className = 'grid grid-cols-12 gap-3 items-center';
        row.dataset.index = index;
        
        row.innerHTML = `
            <div class="col-span-5">
                <input type="text" 
                    class="w-full bg-dark-300 border border-dark-400 text-white rounded-md px-2 py-1.5 text-sm focus:ring-2 focus:ring-accent focus:border-transparent" 
                    placeholder="Username (4-15 chars)" 
                    value="${cred.username || ''}"
                    data-field="username"
                    data-index="${index}"
                    minlength="4"
                    maxlength="15">
            </div>
            <div class="col-span-5">
                <input type="text" 
                    class="w-full bg-dark-300 border border-dark-400 text-white rounded-md px-2 py-1.5 text-sm focus:ring-2 focus:ring-accent focus:border-transparent" 
                    placeholder="Password (4-15 chars)" 
                    value="${cred.password || ''}"
                    data-field="password"
                    data-index="${index}"
                    minlength="4"
                    maxlength="15">
            </div>
            <div class="col-span-2 flex justify-end">
                <button type="button" class="delete-credential-btn bg-dark-400 hover:bg-red-600 text-white p-1.5 rounded-md transition-colors" data-index="${index}">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;
        
        container.appendChild(row);
        
        // Add event listeners for this row
        row.querySelectorAll('input').forEach(input => {
            input.addEventListener('change', function() {
                const index = parseInt(this.dataset.index);
                const field = this.dataset.field;
                authenticationData.allowed_users[index][field] = this.value;
                validateAllCredentialInputs();
                updateAddCredentialButtonState();
            });
            input.addEventListener('input', function() {
                validateAllCredentialInputs();
                updateAddCredentialButtonState();
            });
        });
        
        // Delete button
        const deleteBtn = row.querySelector('.delete-credential-btn');
        deleteBtn.addEventListener('click', function() {
            const index = parseInt(this.dataset.index);
            // Don't allow deleting if we have only 3 credentials
            if (authenticationData.allowed_users.length <= 3) {
                showNotification('At least 3 credentials are required', 'error');
                return;
            }
            authenticationData.allowed_users.splice(index, 1);
            renderCredentials();
            updateAddCredentialButtonState();
        });
    });

    // Always update the add button state after rendering
    updateAddCredentialButtonState();
}

/**
 * Setup summary generation for the review step
 */
function setupSummaryGeneration() {
    // Nothing to set up, summary is generated when navigating to the last step
}

/**
 * Update the summary page with current form values
 */
function updateSummary() {
    // Basic settings
    document.getElementById('summary-type').textContent = 
        document.getElementById('honeypot-type').value || '—';
    
    document.getElementById('summary-port').textContent = 
        document.getElementById('honeypot-port').value || '—';
    
    document.getElementById('summary-banner').textContent = 
        document.getElementById('honeypot-banner').value || '—';
    
    // Resource settings
    document.getElementById('summary-cpu-period').textContent = 
        `${document.getElementById('honeypot-cpu-limit').value || '100000'} µs`;
    
    document.getElementById('summary-cpu-quota').textContent = 
        `${document.getElementById('honeypot-cpu-quota').value || '50000'} µs`;
    
    // Calculate CPU percentage
    const cpuPeriod = parseInt(document.getElementById('honeypot-cpu-limit').value || '100000');
    const cpuQuota = parseInt(document.getElementById('honeypot-cpu-quota').value || '50000');
    const cpuPercentage = Math.round((cpuQuota / cpuPeriod) * 100);
    document.getElementById('summary-cpu-percentage').textContent = `${cpuPercentage}%`;
    
    document.getElementById('summary-memory').textContent = 
        `${document.getElementById('honeypot-memory-limit').value || '512'} MB`;
    
    document.getElementById('summary-memory-swap').textContent = 
        `${document.getElementById('honeypot-memory-swap').value || '512'} MB`;
    
    // Authentication
    document.getElementById('summary-credential-count').textContent = 
        authenticationData.allowed_users.length;
    
    // Sample credentials
    const credentialsContainer = document.getElementById('summary-credentials');
    credentialsContainer.innerHTML = '';
    
    // Show up to 5 credentials
    const sampleCount = Math.min(5, authenticationData.allowed_users.length);
    for (let i = 0; i < sampleCount; i++) {
        const cred = authenticationData.allowed_users[i];
        const credItem = document.createElement('div');
        credItem.className = 'flex justify-between py-1 px-2 bg-dark-300 rounded text-xs';
        
        credItem.innerHTML = `
            <span class="text-gray-300">${cred.username}</span>
            <span class="text-gray-400">${cred.password}</span>
        `;
        
        credentialsContainer.appendChild(credItem);
    }
    
    // Add "and more..." if there are more credentials
    if (authenticationData.allowed_users.length > 5) {
        const moreItem = document.createElement('div');
        moreItem.className = 'text-center text-xs text-gray-400 mt-1';
        moreItem.textContent = `and ${authenticationData.allowed_users.length - 5} more...`;
        credentialsContainer.appendChild(moreItem);
    }
}

/**
 * Submit the honeypot creation form
 */
async function submitHoneypotForm() {
    // Gather form data
    const honeypotType = document.getElementById('honeypot-type').value;
    const honeypotPort = document.getElementById('honeypot-port').value;
    const honeypotBanner = document.getElementById('honeypot-banner').value;
    const cpuPeriod = document.getElementById('honeypot-cpu-limit').value || '100000';
    const cpuQuota = document.getElementById('honeypot-cpu-quota').value || '50000';
    const memoryLimit = document.getElementById('honeypot-memory-limit').value || '512';
    const memorySwap = document.getElementById('honeypot-memory-swap').value || '512';
    
    // Prepare form data
    const formData = {
        type: honeypotType,
        port: parseInt(honeypotPort),
        banner: honeypotBanner,
        cpu_period: parseInt(cpuPeriod),
        cpu_quota: parseInt(cpuQuota),
        memory_limit: parseInt(memoryLimit),
        memory_swap_limit: parseInt(memorySwap),
        authentication: {
            allowed_users: authenticationData.allowed_users
        }
    };
    
    console.log("Submitting honeypot form data:", formData);
    
    // Disable the submit button to prevent multiple submissions
    const submitBtn = document.getElementById('submit-btn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = `
        <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Creating...
    `;
    
    try {
        // Use the global HoneypotAPI utility
        await HoneypotAPI.createHoneypot(formData);
        showNotification('Honeypot created successfully!', 'success');
        setTimeout(() => { window.location.href = '/'; }, 1500);
    } catch (error) {
        console.error("Error creating honeypot:", error);
        showNotification(error.message || 'Failed to create honeypot', 'error');
        
        // Re-enable submit button
        submitBtn.disabled = false;
        submitBtn.innerHTML = `
            <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            Deploy Honeypot
        `;
    }
}

// Export for usage in other files
window.initHoneypotCreationForm = initHoneypotCreationForm;