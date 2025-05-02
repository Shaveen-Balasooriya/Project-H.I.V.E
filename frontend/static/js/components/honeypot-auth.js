/**
 * Honeypot Authentication Component
 * Handles the credential management for honeypot authentication
 */

// Initialize the honeypot authentication component
function initHoneypotAuthentication() {
    // Handler for adding new credentials
    const addCredentialBtn = document.getElementById('add-credential-btn');
    if (addCredentialBtn) {
        addCredentialBtn.addEventListener('click', addNewCredential);
    }

    // Container for credentials
    const credentialsContainer = document.getElementById('auth-credentials-container');
    if (!credentialsContainer) return;

    // Fetch default credentials based on selected honeypot type
    const honeypotTypeSelect = document.getElementById('honeypot-type');
    if (honeypotTypeSelect) {
        honeypotTypeSelect.addEventListener('change', function() {
            const selectedType = this.value;
            if (selectedType) {
                fetchDefaultCredentials(selectedType, credentialsContainer);
            }
        });
        
        // If a type is already selected, fetch credentials
        if (honeypotTypeSelect.value) {
            fetchDefaultCredentials(honeypotTypeSelect.value, credentialsContainer);
        }
    }
}

/**
 * Add new credential fields to the form
 */
function addNewCredential() {
    const container = document.getElementById('auth-credentials-container');
    if (!container) return;
    
    // Get current count to determine new index
    const currentCount = container.querySelectorAll('.credential-row').length;
    
    // Check if we've reached the maximum credentials
    if (currentCount >= 20) {
        showNotification('Maximum of 20 credential pairs allowed', 'error');
        return;
    }
    
    // Create a unique ID for this credential pair
    const credentialId = `credential-${Date.now()}`;
    
    // Create the credential row
    const credentialRow = document.createElement('div');
    credentialRow.className = 'credential-row grid grid-cols-12 gap-3 bg-dark-400 rounded-md p-2';
    credentialRow.setAttribute('data-id', credentialId);
    
    // Fill the row with credential fields
    credentialRow.innerHTML = `
        <div class="col-span-5">
            <input type="text" 
                   name="username_${credentialId}" 
                   class="w-full bg-dark-300 border border-dark-400 text-white rounded-md px-2 py-1.5 text-sm focus:ring-2 focus:ring-accent focus:border-transparent"
                   placeholder="Username" 
                   required>
        </div>
        <div class="col-span-5">
            <input type="text" 
                   name="password_${credentialId}" 
                   class="w-full bg-dark-300 border border-dark-400 text-white rounded-md px-2 py-1.5 text-sm focus:ring-2 focus:ring-accent focus:border-transparent"
                   placeholder="Password" 
                   required>
        </div>
        <div class="col-span-2 flex justify-center items-center">
            <button type="button" 
                    class="delete-credential-btn bg-dark-300 hover:bg-red-800 text-white p-1.5 rounded-md transition-colors"
                    aria-label="Delete credential"
                    onclick="deleteCredential('${credentialId}')">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
    `;
    
    // Add to container
    container.appendChild(credentialRow);
    
    // Update hidden auth container for form submission
    updateAuthContainerFromRows();
    
    // Update the credential count in the summary
    updateCredentialCount();
}

/**
 * Delete a credential pair
 */
function deleteCredential(credentialId) {
    const container = document.getElementById('auth-credentials-container');
    if (!container) return;
    
    // Find and remove the credential row
    const credentialRow = container.querySelector(`.credential-row[data-id="${credentialId}"]`);
    if (credentialRow) {
        // Check if we'll have at least 3 credentials left after deletion
        const currentCount = container.querySelectorAll('.credential-row').length;
        if (currentCount <= 3) {
            showNotification('Minimum of 3 credential pairs required', 'error');
            return;
        }
        
        // Remove the row
        credentialRow.remove();
        
        // Update hidden auth container
        updateAuthContainerFromRows();
        
        // Update the credential count
        updateCredentialCount();
    }
}

/**
 * Fetch default credentials based on honeypot type
 */
function fetchDefaultCredentials(honeypotType, container) {
    if (!container) return;
    
    // Show loading state
    container.innerHTML = `
        <div class="flex justify-center items-center py-6">
            <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-accent"></div>
            <span class="ml-2 text-gray-300">Loading credentials...</span>
        </div>
    `;
    
    // Fetch from API
    fetch(`/api/honeypot/type/${honeypotType}/auth-details`)
        .then(response => response.json())
        .then(data => {
            // Clear container
            container.innerHTML = '';
            
            // Check if we have authentication data
            if (data.authentication && Array.isArray(data.authentication.allowed_users)) {
                const credentials = data.authentication.allowed_users;
                
                credentials.forEach((cred, index) => {
                    addCredentialToUI(cred.username, cred.password, container);
                });
                
                // Make sure we have at least 3 credentials
                const currentCount = container.querySelectorAll('.credential-row').length;
                if (currentCount < 3) {
                    // Add additional default credentials
                    const defaultCredentials = [
                        { username: 'admin', password: 'admin123' },
                        { username: 'root', password: 'toor' },
                        { username: 'user', password: 'password' }
                    ];
                    
                    for (let i = currentCount; i < 3; i++) {
                        const cred = defaultCredentials[i % defaultCredentials.length];
                        addCredentialToUI(cred.username, cred.password, container);
                    }
                }
            } else {
                // Add default credentials if none were returned
                const defaultCredentials = [
                    { username: 'admin', password: 'admin123' },
                    { username: 'root', password: 'toor' },
                    { username: 'user', password: 'password' }
                ];
                
                defaultCredentials.forEach((cred) => {
                    addCredentialToUI(cred.username, cred.password, container);
                });
            }
            
            // Update the auth container for form submission
            updateAuthContainerFromRows();
            
            // Update credential count
            updateCredentialCount();
        })
        .catch(error => {
            console.error('Error fetching default credentials:', error);
            
            // Add default credentials on error
            container.innerHTML = '';
            
            const defaultCredentials = [
                { username: 'admin', password: 'admin123' },
                { username: 'root', password: 'toor' },
                { username: 'user', password: 'password' }
            ];
            
            defaultCredentials.forEach((cred) => {
                addCredentialToUI(cred.username, cred.password, container);
            });
            
            // Update auth container
            updateAuthContainerFromRows();
            
            // Update count
            updateCredentialCount();
        });
}

/**
 * Add a credential to the UI
 */
function addCredentialToUI(username, password, container) {
    if (!container) return;
    
    // Create a unique ID for this credential pair
    const credentialId = `credential-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    
    // Create the credential row
    const credentialRow = document.createElement('div');
    credentialRow.className = 'credential-row grid grid-cols-12 gap-3 bg-dark-400 rounded-md p-2';
    credentialRow.setAttribute('data-id', credentialId);
    
    // Fill the row with credential fields
    credentialRow.innerHTML = `
        <div class="col-span-5">
            <input type="text" 
                   name="username_${credentialId}" 
                   value="${escapeHtml(username)}"
                   class="w-full bg-dark-300 border border-dark-400 text-white rounded-md px-2 py-1.5 text-sm focus:ring-2 focus:ring-accent focus:border-transparent"
                   placeholder="Username" 
                   required>
        </div>
        <div class="col-span-5">
            <input type="text" 
                   name="password_${credentialId}" 
                   value="${escapeHtml(password)}"
                   class="w-full bg-dark-300 border border-dark-400 text-white rounded-md px-2 py-1.5 text-sm focus:ring-2 focus:ring-accent focus:border-transparent"
                   placeholder="Password" 
                   required>
        </div>
        <div class="col-span-2 flex justify-center items-center">
            <button type="button" 
                    class="delete-credential-btn bg-dark-300 hover:bg-red-800 text-white p-1.5 rounded-md transition-colors"
                    aria-label="Delete credential"
                    onclick="deleteCredential('${credentialId}')">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
    `;
    
    // Add to container
    container.appendChild(credentialRow);
    
    // Return a slight delay so that multiple credentials don't get the same timestamp
    return new Promise(resolve => setTimeout(resolve, 5));
}

/**
 * Update the hidden auth container with current credentials
 */
function updateAuthContainerFromRows() {
    const authContainer = document.getElementById('auth-container');
    const credentialsContainer = document.getElementById('auth-credentials-container');
    if (!authContainer || !credentialsContainer) return;
    
    // Clear auth container
    authContainer.innerHTML = '';
    
    // Get all credential rows
    const credentialRows = credentialsContainer.querySelectorAll('.credential-row');
    
    credentialRows.forEach((row, index) => {
        const usernameInput = row.querySelector('input[name^="username_"]');
        const passwordInput = row.querySelector('input[name^="password_"]');
        
        if (usernameInput && passwordInput) {
            // Create hidden fields for form submission
            const hiddenUsername = document.createElement('input');
            hiddenUsername.type = 'hidden';
            hiddenUsername.name = `username_${index}`;
            hiddenUsername.value = usernameInput.value;
            
            const hiddenPassword = document.createElement('input');
            hiddenPassword.type = 'hidden';
            hiddenPassword.name = `password_${index}`;
            hiddenPassword.value = passwordInput.value;
            
            authContainer.appendChild(hiddenUsername);
            authContainer.appendChild(hiddenPassword);
        }
    });
    
    // Also update the summary view if we're on the summary step
    updateCredentialSummary();
}

/**
 * Update credential count in the UI
 */
function updateCredentialCount() {
    const container = document.getElementById('auth-credentials-container');
    const countElement = document.getElementById('summary-credential-count');
    if (!container) return;
    
    const count = container.querySelectorAll('.credential-row').length;
    
    // Update count in summary
    if (countElement) {
        countElement.textContent = count;
    }
}

/**
 * Update the credential summary in the review step
 */
function updateCredentialSummary() {
    const summaryContainer = document.getElementById('summary-credentials');
    const credentialsContainer = document.getElementById('auth-credentials-container');
    if (!summaryContainer || !credentialsContainer) return;
    
    // Clear the summary
    summaryContainer.innerHTML = '';
    
    // Get all credential rows
    const credentialRows = credentialsContainer.querySelectorAll('.credential-row');
    
    // Show a sample of up to 3 credentials
    const sampleRows = Array.from(credentialRows).slice(0, 3);
    
    sampleRows.forEach(row => {
        const usernameInput = row.querySelector('input[name^="username_"]');
        const passwordInput = row.querySelector('input[name^="password_"]');
        
        if (usernameInput && passwordInput) {
            const credDiv = document.createElement('div');
            credDiv.className = 'flex justify-between bg-dark-400 rounded-md p-2';
            
            credDiv.innerHTML = `
                <div class="text-white text-sm font-mono">${escapeHtml(usernameInput.value)}</div>
                <div class="text-white text-sm font-mono">${escapeHtml(passwordInput.value)}</div>
            `;
            
            summaryContainer.appendChild(credDiv);
        }
    });
    
    // Add ellipsis if there are more credentials
    if (credentialRows.length > 3) {
        const moreDiv = document.createElement('div');
        moreDiv.className = 'text-center text-gray-400 mt-2';
        moreDiv.textContent = `...and ${credentialRows.length - 3} more`;
        
        summaryContainer.appendChild(moreDiv);
    }
}

/**
 * Helper function to escape HTML for security
 */
function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') return '';
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Make functions available globally
window.initHoneypotAuthentication = initHoneypotAuthentication;
window.addNewCredential = addNewCredential;
window.deleteCredential = deleteCredential;
window.updateAuthContainerFromRows = updateAuthContainerFromRows;