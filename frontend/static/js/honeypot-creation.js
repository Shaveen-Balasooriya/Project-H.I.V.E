// Centralized API base path for Honeypot Manager endpoints
const HONEYPOT_MANAGER_API_BASE = '/honeypot_manager';

// Form submission handler for the simplified create honeypot form
let portValidationTimer = null;

// Track the latest port check request
let latestPortCheckToken = 0;
let currentPortCheckController = null;

function initSimplifiedHoneypotForm() {
    const createHoneypotForm = document.getElementById('create-honeypot-form');
    const submitBtn = document.getElementById('submit-btn');
    
    if (!createHoneypotForm || !submitBtn) return;
    
    // Initialize default authentication credentials if auth container is empty
    const authContainer = document.getElementById('auth-container');
    if (authContainer && authContainer.children.length === 0) {
        populateDefaultCredentials(authContainer);
    }
    
    // Initialize the banner input field enhancements
    initBannerField();
    
    // Add port availability checking
    const portInput = document.getElementById('honeypot-port');
    if (portInput) {
        // Validate and check port on every input (no debounce)
        portInput.addEventListener('input', function() {
            checkPortAvailability(this);
        });
        // Optionally, still check on blur for completeness
        portInput.addEventListener('blur', function() {
            checkPortAvailability(this);
        });
    }
    
    createHoneypotForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        try {
            // Show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating...
            `;
            
            // Get form data
            const honeypotType = document.getElementById('honeypot-type')?.value;
            const honeypotPort = document.getElementById('honeypot-port')?.value;
            const banner = document.getElementById('honeypot-banner')?.value;
            
            if (!honeypotType || !honeypotPort || !banner) {
                showNotification('Missing required honeypot information', 'error');
                resetSubmitButton();
                return false;
            }
            
            // Build request payload
            const payload = {
                honeypot_type: honeypotType,
                honeypot_port: parseInt(honeypotPort),
                banner: banner
            };
            
            // Process authentication credentials from hidden fields
            const authContainer = document.getElementById('auth-container');
            if (authContainer) {
                // Clear any existing authentication data to prevent duplicates
                const authData = { allowed_users: [] };
                
                // Get all username fields
                const usernameFields = authContainer.querySelectorAll('input[name^="username_"]');
                const processedIndexes = new Set(); // Keep track of processed indexes to prevent duplicates
                
                usernameFields.forEach((usernameField) => {
                    // Extract the index from the field name (username_X)
                    const fieldNameParts = usernameField.name.split('_');
                    const index = fieldNameParts[fieldNameParts.length - 1];
                    
                    // Skip if we've already processed this index
                    if (processedIndexes.has(index)) return;
                    
                    const passwordField = authContainer.querySelector(`input[name="password_${index}"]`);
                    
                    if (usernameField && passwordField && 
                        usernameField.value.trim() && 
                        passwordField.value.trim()) {
                        
                        // Add to processed set
                        processedIndexes.add(index);
                        
                        // Add to auth data
                        authData.allowed_users.push({
                            username: sanitizeInput(usernameField.value),
                            password: sanitizeInput(passwordField.value)
                        });
                    }
                });
                
                // Add authentication if credentials provided
                if (authData.allowed_users.length > 0) {
                    console.log(`Adding ${authData.allowed_users.length} credential pairs to payload`);
                    payload.authentication = authData;
                } else {
                    // If no credentials were found, add default ones
                    payload.authentication = {
                        allowed_users: [
                            { username: "admin", password: "admin123" },
                            { username: "root", password: "toor" },
                            { username: "user", password: "password" }
                        ]
                    };
                    console.log("Using default credential pairs");
                }
            }
            
            console.log('Submitting payload:', payload);
            
            // Submit via AJAX
            const response = await fetch('/api/honeypot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.detail || 'Failed to create honeypot');
            }
            
            // Show success and reset
            showNotification('Honeypot created successfully', 'success');
            createHoneypotForm.reset();
            
            // Clear auth container to prevent duplicates on next submission
            if (authContainer) {
                authContainer.innerHTML = '';
            }
            
            // Close modal and reload page after delay
            const closeModalBtn = document.getElementById('close-modal-btn');
            if (closeModalBtn) {
                closeModalBtn.click();
            }
            
            setTimeout(() => {
                window.location.reload();
            }, 2000);
            
        } catch (error) {
            console.error('Error creating honeypot:', error);
            showNotification(`Error: ${error.message}`, 'error');
            resetSubmitButton();
        }
    });
    
    // Function to reset submit button to original state
    function resetSubmitButton() {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `
                <svg class="w-5 h-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                Create Honeypot
            `;
        }
    }
}

/**
 * Validate port input format
 */
function validatePortInput(input) {
    if (!input) return false;
    
    const value = input.value.trim();
    
    // Remove validation classes except checking state
    if (!input.classList.contains('border-yellow-500')) {
        input.classList.remove('border-red-500', 'border-green-500', 'border-yellow-500');
    }
    
    // Basic validation
    if (!value) {
        input.classList.add('border-red-500');
        return false;
    }
    
    const port = parseInt(value);
    if (isNaN(port) || port < 1 || port > 65535) {
        input.classList.add('border-red-500');
        return false;
    }
    
    return true;
}

/**
 * Check port availability using API
 */
function checkPortAvailability(input) {
    if (!input || !input.value) return;

    const port = input.value.trim();
    const thisToken = ++latestPortCheckToken;

    // Abort any previous request
    if (currentPortCheckController) {
        currentPortCheckController.abort();
    }
    currentPortCheckController = new AbortController();
    const signal = currentPortCheckController.signal;

    input.dataset.checkingPort = port;

    if (typeof showNotification === 'function') {
        showNotification('Checking port availability...', 'info');
    }

    input.classList.add('border-yellow-500');
    input.classList.remove('border-red-500', 'border-green-500');

    fetch(`/api/honeypot/port-check/${port}`, { signal })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to check port availability (HTTP ${response.status})`);
            }
            return response.json();
        })
        .then(data => {
            if (thisToken !== latestPortCheckToken || input.value.trim() !== port) {
                return;
            }
            input.classList.remove('border-yellow-500');
            if (data.available) {
                input.classList.remove('border-red-500');
                input.classList.add('border-green-500');
                if (typeof showNotification === 'function') {
                    showNotification(data.message || `Port ${port} is available`, 'success');
                }
            } else {
                input.classList.remove('border-green-500', 'border-yellow-500');
                input.classList.add('border-red-500');
                if (typeof showNotification === 'function') {
                    showNotification(data.message || `Port ${port} is already in use`, 'error');
                }
            }
        })
        .catch(error => {
            if (error.name === 'AbortError') return;
            if (thisToken !== latestPortCheckToken || input.value.trim() !== port) return;
            input.classList.remove('border-yellow-500');
            if (typeof showNotification === 'function') {
                showNotification(`Error checking port: ${error.message}. Please verify manually.`, 'error');
            }
        })
        .finally(() => {
            if (thisToken === latestPortCheckToken) {
                delete input.dataset.checkingPort;
                currentPortCheckController = null;
            }
        });
}

/**
 * Initialize and enhance the banner input field with validation,
 * counters, preview, and warnings
 */
function initBannerField() {
    const bannerInput = document.getElementById('honeypot-banner');
    if (!bannerInput) return;
    
    // Create and append UI elements for banner enhancement
    createBannerEnhancementUI(bannerInput);
    
    // Get references to the newly created elements
    const charCounter = document.getElementById('banner-char-counter');
    const lineCounter = document.getElementById('banner-line-counter');
    const bannerPreview = document.getElementById('banner-preview');
    const restoreDefaultBtn = document.getElementById('restore-default-btn');
    const securityWarning = document.getElementById('security-warning');
    
    // Constants
    const MAX_CHARS = 300;
    const MAX_LINES = 3;
    const MAX_CHARS_PER_LINE = 100;
    const MIN_CHARS = 20;
    const MAX_REPEATING_CHARS = 10;
    const SECURITY_TERMS = ['unauthorized', 'access', 'prohibited', 'monitored', 'warning', 'notice', 'security', 'private'];
    
    // Set initial empty state for the preview (no loading message)
    if (bannerPreview) {
        bannerPreview.innerHTML = '<span class="text-gray-500">Enter banner text above</span>';
    }
    
    // Event listeners
    bannerInput.addEventListener('input', function() {
        // Sanitize input
        this.value = sanitizeBannerInput(this.value);
        
        // Update counters, preview, and warnings
        updateBannerCounters(this.value, charCounter, lineCounter);
        updateBannerPreview(this.value, bannerPreview);
        checkSecurityPhrases(this.value, securityWarning);
    });
    
    // Restore default button functionality - only when explicitly clicked
    if (restoreDefaultBtn) {
        restoreDefaultBtn.addEventListener('click', function() {
            const honeypotType = document.getElementById('honeypot-type')?.value;
            restoreDefaultBanner(honeypotType, bannerInput);
        });
    }
    
    // Initial updates with existing value (if any)
    updateBannerCounters(bannerInput.value, charCounter, lineCounter);
    updateBannerPreview(bannerInput.value, bannerPreview);
    checkSecurityPhrases(bannerInput.value, securityWarning);
    
    // Add automatic fetching when honeypot type changes
    const honeypotTypeSelect = document.getElementById('honeypot-type');
    if (honeypotTypeSelect) {
        // Remove tracking of last selected type - always fetch on change
        honeypotTypeSelect.addEventListener('change', function() {
            const selectedType = this.value;
            
            // Always fetch banner when type changes (even if same type is selected)
            if (selectedType) {
                console.log(`Fetching banner for ${selectedType} honeypot type (from honeypot-creation.js)`);
                autoFetchBanner(selectedType, bannerInput);
            }
        });
        
        // If a type is already selected on load, fetch the banner
        if (honeypotTypeSelect.value && !bannerInput.value) {
            console.log(`Initial banner fetch for ${honeypotTypeSelect.value} honeypot type (from honeypot-creation.js)`);
            autoFetchBanner(honeypotTypeSelect.value, bannerInput);
        }
    }
}

/**
 * Automatically fetch banner from API when honeypot type changes
 */
function autoFetchBanner(honeypotType, bannerInput) {
    if (!bannerInput || !honeypotType) return;
    
    // Show loading state
    bannerInput.value = 'Loading Existing Banner...';
    
    // Show loading state in the banner preview
    const bannerPreview = document.getElementById('banner-preview');
    if (bannerPreview) {
        bannerPreview.innerHTML = '<span class="text-gray-500">Loading Existing Banner...</span>';
    }
    
    console.log(`Fetching banner for ${honeypotType} from API...`);
    
    // Use the correct endpoint
    fetch(`/api/honeypot/types/${honeypotType}/auth-details`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load banner (HTTP ${response.status})`);
            }
            return response.json();
        })
        .then(data => {
            if (data && data.banner) {
                bannerInput.value = data.banner;
                console.log('Banner successfully loaded from API');
            } else {
                // Leave empty if API doesn't provide banner
                bannerInput.value = "";
                console.log('No banner available from API');
                // Show notification
                if (typeof showNotification === 'function') {
                    showNotification('No default banner available for this honeypot type', 'info');
                }
            }
        })
        .catch(error => {
            console.error('Error auto-fetching banner from API:', error);
            // Show error via notification
            if (typeof showNotification === 'function') {
                showNotification(`Error loading banner: ${error.message}`, 'error');
            }
            
            // Leave field empty
            bannerInput.value = "";
        })
        .finally(() => {
            // Update the preview based on the current value (empty or from API)
            bannerInput.dispatchEvent(new Event('input'));
        });
}

/**
 * Create and append UI elements for banner field enhancement
 */
function createBannerEnhancementUI(bannerInput) {
    if (!bannerInput) return;
    
    const parentContainer = bannerInput.closest('div');
    if (!parentContainer) return;
    
    // Add maxlength and data attributes to the textarea
    bannerInput.setAttribute('maxlength', '300');
    bannerInput.setAttribute('data-max-lines', '3');
    
    // Create counter elements if they don't exist
    if (!document.getElementById('banner-counter-container')) {
        const counterContainer = document.createElement('div');
        counterContainer.id = 'banner-counter-container';
        counterContainer.className = 'flex justify-end space-x-4 text-xs text-gray-400 mt-1';
        counterContainer.innerHTML = `
            <span id="banner-line-counter">0/3 lines</span>
            <span id="banner-char-counter">0/300 chars</span>
        `;
        
        // Insert after the banner input
        insertAfter(counterContainer, bannerInput);
    }
    
    // Create security warning if it doesn't exist
    if (!document.getElementById('security-warning')) {
        const securityWarning = document.createElement('div');
        securityWarning.id = 'security-warning';
        securityWarning.className = 'text-xs text-yellow-500 mt-1 hidden';
        securityWarning.innerHTML = `
            <svg class="inline-block w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>Consider adding security terms like "Unauthorized", "Access", or "Monitored"</span>
        `;
        
        // Insert after the counter container
        const counterContainer = document.getElementById('banner-counter-container');
        if (counterContainer) {
            insertAfter(securityWarning, counterContainer);
        } else {
            insertAfter(securityWarning, bannerInput);
        }
    }
    
    // Create banner preview if it doesn't exist
    if (!document.getElementById('banner-preview-container')) {
        const previewContainer = document.createElement('div');
        previewContainer.id = 'banner-preview-container';
        previewContainer.className = 'mt-3';
        previewContainer.innerHTML = `
            <div class="flex justify-between items-center mb-1">
                <span class="text-xs font-medium text-gray-300">Preview:</span>
                <button type="button" id="restore-default-btn" class="text-xs text-accent hover:underline">
                    Restore Default
                </button>
            </div>
            <div id="banner-preview" class="bg-dark-400 border border-dark-500 rounded p-2 font-mono text-xs text-green-400 h-20 overflow-auto">
            </div>
        `;
        
        // Insert after the security warning
        const securityWarning = document.getElementById('security-warning');
        if (securityWarning) {
            insertAfter(previewContainer, securityWarning);
        } else {
            const counterContainer = document.getElementById('banner-counter-container');
            if (counterContainer) {
                insertAfter(previewContainer, counterContainer);
            } else {
                insertAfter(previewContainer, bannerInput);
            }
        }
    }
    
    // Create constraints info if it doesn't exist
    if (!document.getElementById('banner-constraints')) {
        const constraintsContainer = document.createElement('div');
        constraintsContainer.id = 'banner-constraints';
        constraintsContainer.className = 'mt-2 p-2 bg-dark-300 rounded text-xs text-gray-400';
        constraintsContainer.innerHTML = `
            <strong>Requirements:</strong> 20-300 characters, max 3 lines, only printable ASCII and line breaks.
            Unsafe characters (;|&$\\<>\`) will be removed.
        `;
        
        // Insert after the preview container
        const previewContainer = document.getElementById('banner-preview-container');
        if (previewContainer) {
            insertAfter(constraintsContainer, previewContainer);
        }
    }
    
    // Helper function to insert an element after another
    function insertAfter(newNode, referenceNode) {
        referenceNode.parentNode.insertBefore(newNode, referenceNode.nextSibling);
    }
}

/**
 * Sanitize banner input according to the security requirements
 */
function sanitizeBannerInput(input) {
    if (!input) return '';
    
    // Remove terminal escape sequences
    input = input.replace(/\x1b\[[0-9;]*[a-zA-Z]/g, '');
    
    // Keep only printable ASCII (32-126) and newlines
    input = input.replace(/[^\x20-\x7E\n]/g, '');
    
    // Remove unsafe characters
    input = input.replace(/[;|&$\\<>`]/g, '');
    
    // Split into lines and process each line
    let lines = input.split('\n');
    
    // Limit to max 3 lines
    if (lines.length > 3) {
        lines = lines.slice(0, 3);
    }
    
    // Limit length to 100 chars per line (preserve spaces)
    lines = lines.map(line => {
        // Explicitly preserve spaces (no trim call)
        return line.slice(0, 100);
    });
    
    // Limit repeating characters (e.g., no more than 10 of the same character in a row)
    lines = lines.map(line => {
        return line.replace(/(.)(\1{9,})/g, (match, char, repeats) => {
            return char + repeats.slice(0, 9);
        });
    });
    
    // Combine lines and limit to 300 chars total
    input = lines.join('\n').slice(0, 300);
    
    return input;
}

/**
 * Update character and line counters for banner input
 */
function updateBannerCounters(value, charCounter, lineCounter) {
    if (!charCounter || !lineCounter) return;
    
    const charCount = value ? value.length : 0;
    const lineCount = value ? (value.match(/\n/g) || []).length + 1 : 0;
    
    charCounter.textContent = `${charCount}/300 chars`;
    lineCounter.textContent = `${lineCount}/3 lines`;
    
    // Visual indication when approaching limits
    if (charCount > 270) { // >90% of limit
        charCounter.classList.add('text-yellow-500');
    } else {
        charCounter.classList.remove('text-yellow-500');
    }
    
    if (lineCount === 3) {
        lineCounter.classList.add('text-yellow-500');
    } else {
        lineCounter.classList.remove('text-yellow-500');
    }
}

/**
 * Update banner preview with formatted content
 */
function updateBannerPreview(value, previewElement) {
    if (!previewElement) return;
    
    // Show empty state if no value
    if (!value) {
        previewElement.innerHTML = '<span class="text-gray-500">Enter banner text above</span>';
        return;
    }
    
    // Escape HTML to prevent XSS
    const escapedValue = value
        ? value
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
        : '';
    
    // Format with newlines as <br> tags
    const formattedValue = escapedValue.replace(/\n/g, '<br>');
    
    // Add a blinking cursor at the end
    previewElement.innerHTML = formattedValue + '<span class="inline-block bg-green-400 w-1.5 h-4 ml-0.5 animate-pulse"></span>';
}

/**
 * Check if banner contains security-related phrases
 * and show warning if missing
 */
function checkSecurityPhrases(value, warningElement) {
    if (!warningElement) return;
    
    const lowerValue = (value || '').toLowerCase();
    
    // Check for minimum length
    if (lowerValue.length < 20) {
        warningElement.classList.remove('hidden');
        warningElement.querySelector('span').textContent = 
            'Banner should be at least 20 characters long for security purposes';
        return;
    }
    
    // Check for all symbols/gibberish
    if (lowerValue.length > 0 && !/[a-zA-Z0-9]/.test(lowerValue)) {
        warningElement.classList.remove('hidden');
        warningElement.querySelector('span').textContent = 
            'Banner should contain some text, not just symbols';
        return;
    }
    
    // Security terms to check for
    const securityTerms = ['unauthorized', 'access', 'prohibited', 'monitored', 'warning', 'notice', 'security', 'private'];
    
    // Check if any security term is present
    const hasSecurityTerm = securityTerms.some(term => lowerValue.includes(term));
    if (!hasSecurityTerm && lowerValue.length > 0) {
        warningElement.classList.remove('hidden');
        warningElement.querySelector('span').textContent = 
            'Consider adding security terms like "Unauthorized", "Access", or "Monitored"';
        return;
    }
    
    // No warnings needed
    warningElement.classList.add('hidden');
}

/**
 * Restore default banner based on honeypot type - Only when explicitly requested
 */
function restoreDefaultBanner(honeypotType, bannerInput) {
    if (!bannerInput) return;
    
    // If no type is selected, show a notification
    if (!honeypotType) {
        if (typeof showNotification === 'function') {
            showNotification('Please select a honeypot type first', 'warning');
        }
        return;
    }
    
    // Show loading state in the banner preview
    const bannerPreview = document.getElementById('banner-preview');
    if (bannerPreview) {
        bannerPreview.innerHTML = '<span class="text-gray-500">Loading Existing Banner...</span>';
    }
    
    // Use the correct endpoint
    fetch(`/api/honeypot/types/${honeypotType}/auth-details`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load banner (HTTP ${response.status})`);
            }
            return response.json();
        })
        .then(data => {
            if (data && data.banner) {
                bannerInput.value = data.banner;
                console.log('Banner loaded from API');
                showNotification('Default banner loaded successfully', 'success');
            } else {
                // If API doesn't provide a banner, leave it empty
                if (typeof showNotification === 'function') {
                    showNotification('No default banner available for this honeypot type', 'info');
                }
                bannerInput.value = ""; // Leave empty, don't use default values
                console.log('No banner available from API');
            }
        })
        .catch(error => {
            console.error('Error fetching banner from API:', error);
            
            // Show error notification and leave field empty
            if (typeof showNotification === 'function') {
                showNotification(`Failed to load banner: ${error.message}`, 'error');
            }
            bannerInput.value = ""; // Leave empty, don't use default values
        })
        .finally(() => {
            // Update the preview based on the current value (empty or from API)
            bannerInput.dispatchEvent(new Event('input'));
        });
}

/**
 * Populate default authentication credentials in the auth container
 */
function populateDefaultCredentials(authContainer) {
    if (!authContainer) return;
    
    // Clear existing content
    authContainer.innerHTML = '';
    
    // Add default credential pairs
    const defaultCredentials = [
        { username: 'admin', password: 'admin123' },
        { username: 'root', password: 'toor' },
        { username: 'user', password: 'password' }
    ];
    
    defaultCredentials.forEach((cred, index) => {
        const usernameInput = document.createElement('input');
        usernameInput.type = 'hidden';
        usernameInput.name = `username_${index}`;
        usernameInput.value = cred.username;
        
        const passwordInput = document.createElement('input');
        passwordInput.type = 'hidden';
        passwordInput.name = `password_${index}`;
        passwordInput.value = cred.password;
        
        authContainer.appendChild(usernameInput);
        authContainer.appendChild(passwordInput);
    });
    
    console.log(`Added ${defaultCredentials.length} default credential pairs`);
}

// Helper function for input sanitization
function sanitizeInput(input) {
    if (typeof input === 'string') {
        return input
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;')
            .trim();
    }
    return input;
}

// Initialize the form when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initSimplifiedHoneypotForm();
});