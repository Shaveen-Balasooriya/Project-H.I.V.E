/**
 * Service UI utilities
 * Handles notifications and other UI components for services
 */

class ServiceUI {
    constructor() {
        this.notificationContainer = document.getElementById('notification-container');
        this.notificationTimeout = null;
        console.log("Service UI initialized");
    }
    
    /**
     * Show a notification
     * @param {string} message - Message to display
     * @param {string} type - Type of notification (success, error, warning, info)
     * @param {number} duration - How long to show the notification (ms)
     */
    showNotification(message, type = 'info', duration = 5000) {
        if (!this.notificationContainer) return;
        
        // Get color classes based on type
        let bgColor, textColor, borderColor;
        
        switch (type) {
            case 'success':
                bgColor = 'bg-green-500/20';
                textColor = 'text-green-400';
                borderColor = 'border-green-500/30';
                break;
            case 'error':
                bgColor = 'bg-red-500/20';
                textColor = 'text-red-400';
                borderColor = 'border-red-500/30';
                break;
            case 'warning':
                bgColor = 'bg-yellow-500/20';
                textColor = 'text-yellow-400';
                borderColor = 'border-yellow-500/30';
                break;
            case 'info':
            default:
                bgColor = 'bg-blue-500/20';
                textColor = 'text-blue-400';
                borderColor = 'border-blue-500/30';
                break;
        }
        
        // Create notification element
        const notificationEl = document.createElement('div');
        notificationEl.className = `${bgColor} ${textColor} border ${borderColor} p-4 rounded shadow-lg flex items-start opacity-0 transform translate-x-full transition-all duration-300`;
        notificationEl.style.width = '380px';
        notificationEl.style.maxWidth = '90vw';
        
        // Create notification icon based on type
        let icon;
        
        switch (type) {
            case 'success':
                icon = '<svg class="w-5 h-5 mr-3 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
                break;
            case 'error':
                icon = '<svg class="w-5 h-5 mr-3 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>';
                break;
            case 'warning':
                icon = '<svg class="w-5 h-5 mr-3 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>';
                break;
            case 'info':
            default:
                icon = '<svg class="w-5 h-5 mr-3 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';
                break;
        }
        
        // Set notification content
        notificationEl.innerHTML = `
            <div class="flex-shrink-0">
                ${icon}
            </div>
            <div class="flex-grow">
                ${message}
            </div>
            <button class="ml-4 flex-shrink-0 focus:outline-none text-white hover:text-white/80" aria-label="Close" title="Dismiss">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        `;
        
        // Add notification to container
        this.notificationContainer.appendChild(notificationEl);
        
        // Close button handler
        const closeBtn = notificationEl.querySelector('button');
        closeBtn.addEventListener('click', () => this.removeNotification(notificationEl));
        
        // Trigger animation to show
        setTimeout(() => {
            notificationEl.classList.remove('opacity-0', 'translate-x-full');
        }, 10);
        
        // Auto-hide after duration
        if (duration > 0) {
            setTimeout(() => {
                this.removeNotification(notificationEl);
            }, duration);
        }
    }
    
    /**
     * Remove a notification with animation
     */
    removeNotification(notificationEl) {
        notificationEl.classList.add('opacity-0', 'translate-x-full');
        setTimeout(() => {
            if (notificationEl.parentNode === this.notificationContainer) {
                this.notificationContainer.removeChild(notificationEl);
            }
        }, 300);
    }
}

// Export to window
window.ServiceUI = ServiceUI;
