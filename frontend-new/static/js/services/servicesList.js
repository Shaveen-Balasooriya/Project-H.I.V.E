/**
 * Services List Manager
 * Responsible for fetching, displaying, and managing services
 */

class ServicesList {
    constructor() {
        // The services data
        this.services = [];
        this.refreshing = false;
        
        // References to DOM elements
        this.servicesContainer = document.getElementById('services-container');
        this.loadingIndicator = document.getElementById('loading-indicator');
        this.errorContainer = document.getElementById('error-container');
        this.emptyContainer = document.getElementById('empty-container');
        this.emptyFilteredContainer = document.getElementById('empty-filtered-container');
        
        // Bind refresh button
        const refreshBtn = document.getElementById('refresh-services');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshList());
        }
        
        console.log("Services list manager initialized");
    }
    
    /**
     * Fetches services status from the API
     */
    async fetchServices() {
        try {
            console.log("Fetching services status...");
            
            // Use a timeout to avoid infinite API calls
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Request timed out')), 10000);
            });
            
            const fetchPromise = fetch('/api/service/status');
            
            // Race between fetch and timeout
            const response = await Promise.race([fetchPromise, timeoutPromise]);
            console.log("Fetch finished loading:", response);
            
            if (!response.ok) {
                throw new Error(`API returned ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log("Received services data:", data);
            
            // Make sure we have the expected fields
            if (!data || typeof data !== 'object') {
                throw new Error("Invalid response format from API");
            }
            
            // Transform the data into an array of service objects with all four services
            // This matches the StatusResponse model from log_manager_router.py
            const services = [
                {
                    name: 'OpenSearch Node',
                    id: 'hive-opensearch-node',
                    status: data.open_search_node || 'not found',
                    type: 'data-storage',
                    description: 'Search and analytics engine for logs'
                },
                {
                    name: 'NATS Server',
                    id: 'hive-nats-server',
                    status: data.nats_server || 'not found',
                    type: 'messaging',
                    description: 'Message broker for log collection'
                },
                {
                    name: 'Log Collector',
                    id: 'hive-log-collector', 
                    status: data.log_collector || 'not found',
                    type: 'collector',
                    description: 'Collects logs from honeypots'
                },
                {
                    name: 'OpenSearch Dashboard',
                    id: 'hive-opensearch-dash',
                    status: data.open_search_dashboard || 'not found', 
                    type: 'visualization',
                    description: 'Web interface for analyzing logs and metrics'
                }
            ];
            
            this.services = services;
            return services;
            
        } catch (error) {
            console.error('Error fetching services:', error);
            throw error;
        }
    }
    
    /**
     * Refreshes the services list
     */
    async refreshList() {
        // Prevent multiple simultaneous refreshes
        if (this.refreshing) {
            console.log("Refresh already in progress, skipping");
            return;
        }
        
        this.refreshing = true;
        this.showLoading();
        
        try {
            await this.fetchServices();
            this.renderServicesList();
            
            // Show notification for successful refresh
            if (window.serviceUI) {
                window.serviceUI.showNotification('Services refreshed successfully', 'success', 3000);
            }
        } catch (error) {
            console.error('Error refreshing services:', error);
            this.showError("Could not retrieve service status. Please try again.");
        } finally {
            this.refreshing = false;
        }
    }
    
    /**
     * Shows the loading indicator
     */
    showLoading() {
        if (this.loadingIndicator) this.loadingIndicator.classList.remove('hidden');
        if (this.servicesContainer) this.servicesContainer.classList.add('hidden');
        if (this.errorContainer) this.errorContainer.classList.add('hidden');
        if (this.emptyContainer) this.emptyContainer.classList.add('hidden');
        if (this.emptyFilteredContainer) this.emptyFilteredContainer.classList.add('hidden');
    }
    
    /**
     * Shows an error message
     */
    showError(message) {
        if (this.loadingIndicator) this.loadingIndicator.classList.add('hidden');
        if (this.servicesContainer) this.servicesContainer.classList.add('hidden');
        if (this.errorContainer) this.errorContainer.classList.remove('hidden');
        if (this.emptyContainer) this.emptyContainer.classList.add('hidden');
        if (this.emptyFilteredContainer) this.emptyFilteredContainer.classList.add('hidden');
        
        // Set error message
        const errorMessageEl = document.querySelector('.error-message');
        if (errorMessageEl) {
            errorMessageEl.textContent = message || 'Failed to load services. Please try again.';
        }
    }
    
    /**
     * Shows the services container
     */
    showServices() {
        if (this.loadingIndicator) this.loadingIndicator.classList.add('hidden');
        if (this.servicesContainer) this.servicesContainer.classList.remove('hidden');
        if (this.errorContainer) this.errorContainer.classList.add('hidden');
        if (this.emptyContainer) this.emptyContainer.classList.add('hidden');
        if (this.emptyFilteredContainer) this.emptyFilteredContainer.classList.add('hidden');
    }
    
    /**
     * Shows the empty state
     */
    showEmpty() {
        if (this.loadingIndicator) this.loadingIndicator.classList.add('hidden');
        if (this.servicesContainer) this.servicesContainer.classList.add('hidden');
        if (this.errorContainer) this.errorContainer.classList.add('hidden');
        if (this.emptyContainer) this.emptyContainer.classList.remove('hidden');
        if (this.emptyFilteredContainer) this.emptyFilteredContainer.classList.add('hidden');
    }
    
    /**
     * Shows the empty filtered state
     */
    showEmptyFiltered(message) {
        if (this.loadingIndicator) this.loadingIndicator.classList.add('hidden');
        if (this.servicesContainer) this.servicesContainer.classList.add('hidden');
        if (this.errorContainer) this.errorContainer.classList.add('hidden');
        if (this.emptyContainer) this.emptyContainer.classList.add('hidden');
        if (this.emptyFilteredContainer) this.emptyFilteredContainer.classList.remove('hidden');
        
        // Set message if provided
        if (message) {
            const emptyMessage = this.emptyFilteredContainer.querySelector('.empty-message');
            if (emptyMessage) {
                emptyMessage.textContent = message;
            }
        }
    }
    
    /**
     * Renders the services list
     */
    renderServicesList() {
        if (!this.servicesContainer) return;
        
        // Clear any existing services
        this.servicesContainer.innerHTML = '';
        
        // Check if we have any services
        if (!this.services || this.services.length === 0) {
            this.showEmpty();
            return;
        }
        
        // Create service cards
        this.services.forEach(service => {
            const serviceCard = this.createServiceCard(service);
            this.servicesContainer.appendChild(serviceCard);
        });
        
        this.showServices();
    }
    
    /**
     * Creates a service card element
     */
    createServiceCard(service) {
        // Create card container
        const card = document.createElement('div');
        card.className = 'service-card mb-6 bg-black/30 backdrop-blur-sm border border-accent/10 rounded-lg overflow-hidden transition-shadow hover:shadow-lg hover:shadow-accent/5';
        card.dataset.id = service.id;
        card.dataset.name = service.name;
        card.dataset.type = service.type;
        card.dataset.status = service.status;
        
        // Determine status class and label (removed icons)
        let statusClass, statusLabel;
        
        switch (service.status.toLowerCase()) {
            case 'running':
                statusClass = 'bg-green-500/20 text-green-400';
                statusLabel = 'Running';
                break;
            case 'not found':
                statusClass = 'bg-red-500/20 text-red-400';
                statusLabel = 'Not Found';
                break;
            case 'created':
                statusClass = 'bg-blue-500/20 text-blue-400';
                statusLabel = 'Created';
                break;
            case 'exited':
            default:
                statusClass = 'bg-yellow-500/20 text-yellow-400';
                statusLabel = 'Stopped';
        }
        
        // Determine the type icon
        let typeIcon;
        switch (service.type) {
            case 'data-storage':
                typeIcon = `<svg class="w-5 h-5 mr-2 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"></path>
                </svg>`;
                break;
            case 'messaging':
                typeIcon = `<svg class="w-5 h-5 mr-2 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                </svg>`;
                break;
            case 'collector':
                typeIcon = `<svg class="w-5 h-5 mr-2 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                </svg>`;
                break;
            case 'visualization':
                typeIcon = `<svg class="w-5 h-5 mr-2 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                </svg>`;
                break;
            default:
                typeIcon = `<svg class="w-5 h-5 mr-2 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path>
                </svg>`;
        }
        
        // Card content HTML - with status icons removed
        card.innerHTML = `
            <div class="p-5">
                <div class="flex flex-wrap justify-between items-start mb-4">
                    <div class="flex items-center mb-2 sm:mb-0">
                        <h3 class="text-xl font-display text-white">${service.name}</h3>
                        <span class="service-status ml-3 px-2 py-1 rounded-full text-xs font-medium flex items-center ${statusClass}">
                            ${statusLabel}
                        </span>
                    </div>
                </div>
                
                <div class="mb-4">
                    <div class="flex items-center text-sm text-white/80 mb-2">
                        ${typeIcon}
                        <span class="service-type">${service.type.charAt(0).toUpperCase() + service.type.slice(1)}</span>
                    </div>
                    <p class="text-white/70 mt-2">
                        ${service.description}
                    </p>
                </div>
            </div>
        `;
        
        return card;
    }
}

// Expose to window
window.servicesList = new ServicesList();
console.log("ServicesList module loaded");
