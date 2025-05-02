// Authentication component functionality
function initAuthenticationComponent() {
    const addAuthBtn = document.getElementById('add-auth-btn');
    const authContainer = document.getElementById('auth-container');
    const submitBtn = document.getElementById('submit-btn');
    const nextStepBtn = document.getElementById('next-step-btn');
    
    if (!addAuthBtn || !authContainer) return;
    
    let authCount = 3; // Start with 3 since we already have three pairs by default
    
    // Function to validate all auth fields and enable/disable submit button
    function validateAllAuthFields() {
        const authRows = authContainer.querySelectorAll('.flex.space-x-3');
        
        // Check if we have at least 3 credential pairs
        if (authRows.length < 3) {
            disableSubmitButton('You must have at least 3 credential pairs');
            return false;
        }
        
        // Check for empty fields
        let hasEmptyFields = false;
        authRows.forEach(row => {
            const inputs = row.querySelectorAll('input');
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    input.classList.add('border-red-500');
                    hasEmptyFields = true;
                } else {
                    input.classList.remove('border-red-500');
                }
            });
        });
        
        if (hasEmptyFields) {
            disableSubmitButton('All username and password fields must be filled');
            return false;
        }
        
        // Enable the submit button if all validations pass
        enableSubmitButton();
        return true;
    }
    
    // Function to disable submit button with a reason
    function disableSubmitButton(reason) {
        if (!submitBtn) return;
        
        submitBtn.disabled = true;
        submitBtn.setAttribute('disabled', 'disabled'); // Ensure the attribute is set
        submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
        submitBtn.classList.remove('btn-hover-effect');
        
        // Show tooltip or message
        const errorMessage = document.querySelector('.auth-error-message') || document.createElement('p');
        errorMessage.className = 'auth-error-message mt-1 text-xs text-red-500';
        errorMessage.textContent = reason;
        
        // Check if error message is already added
        if (!document.querySelector('.auth-error-message')) {
            const container = submitBtn.parentElement;
            container.insertBefore(errorMessage, submitBtn);
        } else {
            errorMessage.textContent = reason;
        }
    }
    
    // Function to enable submit button
    function enableSubmitButton() {
        if (!submitBtn) return;
        
        submitBtn.disabled = false;
        submitBtn.removeAttribute('disabled'); // Ensure the attribute is removed
        submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        submitBtn.classList.add('btn-hover-effect');
        
        // Remove error message if it exists
        const errorMessage = document.querySelector('.auth-error-message');
        if (errorMessage) {
            errorMessage.remove();
        }
    }
    
    // Add event listeners for existing remove buttons
    document.querySelectorAll('.remove-auth-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const authRow = this.closest('.flex.space-x-3');
            if (authContainer.children.length > 3) {
                authContainer.removeChild(authRow);
                setTimeout(() => {
                    validateAllAuthFields(); // Validate after DOM update
                }, 0);
            } else {
                showNotification('You must have at least 3 credential pairs', 'error');
            }
        });
    });
    
    // Add new credential pair
    addAuthBtn.addEventListener('click', function() {
        // Check for empty fields before adding new ones
        const emptyFields = Array.from(authContainer.querySelectorAll('input')).some(input => !input.value.trim());
        if (emptyFields) {
            showNotification('Please fill in all existing fields before adding new ones', 'error');
            validateAllAuthFields(); // Highlight empty fields
            return;
        }
        
        if (authCount >= 50) {
            showNotification('Maximum of 50 credential pairs allowed', 'error');
            return;
        }
        
        const newAuthRow = document.createElement('div');
        newAuthRow.className = 'flex space-x-3';
        newAuthRow.innerHTML = `
            <div class="flex-1">
                <label class="block mb-1 text-xs text-gray-300">Username</label>
                <input type="text" name="username_${authCount}" placeholder="Username" 
                    class="w-full bg-dark-300 border border-dark-400 text-white rounded-md px-3 py-2 focus:ring-2 focus:ring-accent focus:border-transparent transition-all">
            </div>
            <div class="flex-1">
                <label class="block mb-1 text-xs text-gray-300">Password</label>
                <input type="text" name="password_${authCount}" placeholder="Password" 
                    class="w-full bg-dark-300 border border-dark-400 text-white rounded-md px-3 py-2 focus:ring-2 focus:ring-accent focus:border-transparent transition-all">
            </div>
            <div class="flex items-end pb-2">
                <button type="button" class="remove-auth-btn bg-dark-300 hover:bg-dark-400 text-gray-300 hover:text-accent p-2 rounded-md transition-colors">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;
        
        authContainer.appendChild(newAuthRow);
        
        // Add event listener for remove button
        const removeBtn = newAuthRow.querySelector('.remove-auth-btn');
        removeBtn.addEventListener('click', function() {
            if (authContainer.children.length > 3) {
                authContainer.removeChild(newAuthRow);
                authCount--;
                setTimeout(() => {
                    validateAllAuthFields(); // Validate after DOM update
                }, 0);
            } else {
                showNotification('You must have at least 3 credential pairs', 'error');
            }
        });
        
        // Add validation and sanitization on blur events
        const inputs = newAuthRow.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                this.value = sanitizeInput(this.value);
                validateAllAuthFields();
            });
            
            // Also validate on input to provide real-time feedback
            input.addEventListener('input', function() {
                if (this.value.trim()) {
                    this.classList.remove('border-red-500');
                } else {
                    this.classList.add('border-red-500');
                }
            });
        });
        
        authCount++;
        setTimeout(() => {
            validateAllAuthFields(); // Validate after DOM update
        }, 0);
    });
    
    // Add sanitization and validation to all existing credential fields
    authContainer.querySelectorAll('input').forEach(input => {
        input.addEventListener('blur', function() {
            this.value = sanitizeInput(this.value);
            validateAllAuthFields();
        });
        
        // Also validate on input
        input.addEventListener('input', function() {
            if (this.value.trim()) {
                this.classList.remove('border-red-500');
            } else {
                this.classList.add('border-red-500');
            }
        });
    });
    
    // Initial validation when component loads
    setTimeout(() => {
        validateAllAuthFields();
    }, 100);
    
    // Prevent form submission if validation fails
    const createHoneypotForm = document.getElementById('create-honeypot-form');
    if (createHoneypotForm) {
        createHoneypotForm.addEventListener('submit', function(e) {
            if (!validateAllAuthFields()) {
                e.preventDefault();
                e.stopPropagation();
                showNotification('Please fix all validation errors before submitting', 'error');
                return false;
            }
        });
    }
    
    // Intercept submit button click
    if (submitBtn) {
        submitBtn.addEventListener('click', function(e) {
            if (!validateAllAuthFields()) {
                e.preventDefault();
                e.stopPropagation();
                showNotification('Please fix all validation errors before submitting', 'error');
                return false;
            }
        });
    }
}

// Input sanitization function
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

// Show notification function if it doesn't exist
if (typeof showNotification !== 'function') {
    function showNotification(message, type = 'info') {
        // Simple notification implementation if none exists
        console.log(`${type.toUpperCase()}: ${message}`);
        
        // You can replace this with a more sophisticated notification system
        const notification = document.createElement('div');
        notification.className = `notification ${type} fixed top-5 right-5 p-4 rounded-md z-50 shadow-lg`;
        notification.style.backgroundColor = type === 'error' ? '#f44336' : 
                                           type === 'success' ? '#4caf50' : 
                                           type === 'warning' ? '#ff9800' : '#2196f3';
        notification.style.color = 'white';
        notification.innerHTML = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Initialize authentication component
document.addEventListener('DOMContentLoaded', function() {
    initAuthenticationComponent();
    
    // Modify stepper button to glow without changing color
    const nextStepBtn = document.getElementById('next-step-btn');
    if (nextStepBtn) {
        // Remove hover effect that changes background color
        nextStepBtn.classList.remove('hover:bg-red-600');
        
        // Add glow effect class
        nextStepBtn.classList.add('stepper-btn-glow');
    }
});

/**
 * Honeypot Manager JS
 * Handles lifecycle operations for honeypots (start, stop, restart, delete)
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeHoneypotManager();
});

function initializeHoneypotManager() {
    // Initialize all event listeners for honeypot cards
    addHoneypotCardListeners();
    
    // Setup filter form handling
    initializeFilters();
}

function initializeFilters() {
    // Reset filters button
    const resetButton = document.getElementById('reset-filters');
    if (resetButton) {
        resetButton.addEventListener('click', function() {
            window.location.href = '/honeypot_manager';
        });
    }

    // Auto-submit on filter change
    const filterSelects = document.querySelectorAll('#type-filter, #status-filter');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            document.getElementById('filter-form').submit();
        });
    });
}

function addHoneypotCardListeners() {
    // Start buttons
    document.querySelectorAll('.start-honeypot').forEach(btn => {
        btn.addEventListener('click', function() {
            const name = this.dataset.honeypotName;
            honeypotAction(name, 'start');
        });
    });
    
    // Stop buttons
    document.querySelectorAll('.stop-honeypot').forEach(btn => {
        btn.addEventListener('click', function() {
            const name = this.dataset.honeypotName;
            honeypotAction(name, 'stop');
        });
    });
    
    // Restart buttons
    document.querySelectorAll('.restart-honeypot').forEach(btn => {
        btn.addEventListener('click', function() {
            const name = this.dataset.honeypotName;
            honeypotAction(name, 'restart');
        });
    });
    
    // Delete buttons
    document.querySelectorAll('.delete-honeypot').forEach(btn => {
        btn.addEventListener('click', function() {
            const name = this.dataset.honeypotName;
            if (confirm(`Are you sure you want to delete honeypot "${name}"? This action cannot be undone.`)) {
                deleteHoneypot(name);
            }
        });
    });
}

function honeypotAction(name, action) {
    // Show loading state
    const actionButton = document.querySelector(`[data-honeypot-name="${name}"].${action}-honeypot`);
    if (actionButton) {
        const originalContent = actionButton.innerHTML;
        actionButton.disabled = true;
        actionButton.innerHTML = `
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Processing...
        `;
        
        // Perform action via API
        fetch(`/api/honeypot/${name}/${action}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.message) {
                showNotification(data.message, 'success');
                // Refresh honeypot list after action completes
                setTimeout(refreshHoneypots, 1000);
            } else if (data.detail) {
                showNotification(data.detail, 'error');
                // Restore button state
                actionButton.innerHTML = originalContent;
                actionButton.disabled = false;
            }
        })
        .catch(err => {
            showNotification(`Error performing ${action}: ${err.message}`, 'error');
            // Restore button state
            actionButton.innerHTML = originalContent;
            actionButton.disabled = false;
        });
    }
}

function deleteHoneypot(name) {
    // Show loading state on delete button
    const deleteButton = document.querySelector(`[data-honeypot-name="${name}"].delete-honeypot`);
    if (deleteButton) {
        const originalContent = deleteButton.innerHTML;
        deleteButton.disabled = true;
        deleteButton.innerHTML = `
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Deleting...
        `;
        
        fetch(`/api/honeypot/${name}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.message) {
                showNotification(data.message, 'success');
                // Refresh honeypot list after deletion
                setTimeout(refreshHoneypots, 1000);
            } else if (data.detail) {
                showNotification(data.detail, 'error');
                // Restore button state
                deleteButton.innerHTML = originalContent;
                deleteButton.disabled = false;
            }
        })
        .catch(err => {
            showNotification(`Error deleting honeypot: ${err.message}`, 'error');
            // Restore button state
            deleteButton.innerHTML = originalContent;
            deleteButton.disabled = false;
        });
    }
}

function refreshHoneypots() {
    // Get current filter values
    const typeFilter = document.getElementById('type-filter')?.value || '';
    const statusFilter = document.getElementById('status-filter')?.value || '';
    
    // Build query string
    let queryParams = new URLSearchParams();
    if (typeFilter) queryParams.append('type', typeFilter);
    if (statusFilter) queryParams.append('status', statusFilter);
    const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
    
    // Show loading state
    const honeypotGrid = document.getElementById('honeypot-grid');
    if (honeypotGrid) {
        honeypotGrid.innerHTML = `
            <div class="col-span-1 md:col-span-2 lg:col-span-3 flex justify-center items-center p-12">
                <div class="flex flex-col items-center justify-center">
                    <svg class="animate-spin h-12 w-12 text-accent mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span class="text-gray-400">Refreshing honeypots...</span>
                </div>
            </div>
        `;
    }
    
    fetch(`/honeypot_cards${queryString}`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.text();
    })
    .then(html => {
        if (honeypotGrid) {
            honeypotGrid.innerHTML = html;
            addHoneypotCardListeners();
        }
    })
    .catch(err => {
        showNotification('Error refreshing honeypot data: ' + err.message, 'error');
        // Restore previous state or show error state
        if (honeypotGrid) {
            honeypotGrid.innerHTML = `
                <div class="col-span-1 md:col-span-2 lg:col-span-3 flex justify-center items-center p-12">
                    <div class="flex flex-col items-center justify-center">
                        <svg class="h-12 w-12 text-red-500 mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        <span class="text-red-400">Failed to load honeypots</span>
                        <button class="mt-4 bg-accent text-white px-4 py-2 rounded-md" onclick="refreshHoneypots()">Try Again</button>
                    </div>
                </div>
            `;
        }
    });
}

// Function to show notifications
function showNotification(message, type = 'info', duration = 5000) {
    // Use global notification function if available
    if (window.showNotification) {
        window.showNotification(message, type, duration);
        return;
    }
    
    // Fallback notification implementation
    console.log(`${type.toUpperCase()}: ${message}`);
    
    // You can replace this with a more sophisticated notification system
    const notification = document.createElement('div');
    notification.className = `notification ${type} fixed top-5 right-5 p-4 rounded-md z-50 shadow-lg`;
    notification.style.backgroundColor = type === 'error' ? '#f44336' : 
                                       type === 'success' ? '#4caf50' : 
                                       type === 'warning' ? '#ff9800' : '#2196f3';
    notification.style.color = 'white';
    notification.innerHTML = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, duration);
}

// Make functions globally available
window.honeypotAction = honeypotAction;
window.deleteHoneypot = deleteHoneypot;
window.refreshHoneypots = refreshHoneypots;
window.addHoneypotCardListeners = addHoneypotCardListeners;