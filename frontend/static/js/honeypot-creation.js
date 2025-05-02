// Form submission handler for the simplified create honeypot form
function initSimplifiedHoneypotForm() {
    const createHoneypotForm = document.getElementById('create-honeypot-form');
    const submitBtn = document.getElementById('submit-btn');
    
    if (!createHoneypotForm || !submitBtn) return;
    
    // Initialize default authentication credentials if auth container is empty
    const authContainer = document.getElementById('auth-container');
    if (authContainer && authContainer.children.length === 0) {
        populateDefaultCredentials(authContainer);
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