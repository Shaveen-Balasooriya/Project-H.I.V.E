/**
 * Service Filters
 * Handles filtering and sorting of services
 */

class ServiceFilters {
    constructor() {
        // Filter elements
        this.typeFilter = document.getElementById('type-filter');
        this.statusFilter = document.getElementById('status-filter');
        this.sortFilter = document.getElementById('service-sort');
        
        // Current filters
        this.currentFilters = {
            type: 'all',
            status: 'all',
            sort: 'status'
        };
        
        // Available service types for filtering (will be populated)
        this.serviceTypes = [];
    }
    
    /**
     * Initialize filters
     */
    init() {
        // Add event listeners
        if (this.typeFilter) {
            this.typeFilter.addEventListener('change', () => this.applyFilters());
        }
        
        if (this.statusFilter) {
            this.statusFilter.addEventListener('change', () => this.applyFilters());
        }
        
        if (this.sortFilter) {
            this.sortFilter.addEventListener('change', () => this.applyFilters());
        }
    }
    
    /**
     * Update type filter options based on available service types
     */
    updateTypeOptions(services) {
        if (!this.typeFilter) return;
        
        // Extract unique service types
        const types = [...new Set(services.map(service => service.type))];
        this.serviceTypes = types;
        
        // Save current selection
        const currentSelection = this.typeFilter.value;
        
        // Clear existing options (except "All Types")
        while (this.typeFilter.options.length > 1) {
            this.typeFilter.remove(1);
        }
        
        // Add type options
        types.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type.charAt(0).toUpperCase() + type.slice(1);
            this.typeFilter.appendChild(option);
        });
        
        // Restore selection if it exists
        if (types.includes(currentSelection)) {
            this.typeFilter.value = currentSelection;
        } else {
            this.typeFilter.value = 'all';
        }
    }
    
    /**
     * Apply filters and sorting to services
     */
    applyFilters() {
        if (!window.servicesList) return;
        
        // Get current filter values
        this.currentFilters.type = this.typeFilter ? this.typeFilter.value : 'all';
        this.currentFilters.status = this.statusFilter ? this.statusFilter.value : 'all';
        this.currentFilters.sort = this.sortFilter ? this.sortFilter.value : 'status';
        
        const services = window.servicesList.services;
        if (!services || !services.length) return;
        
        // Filter services
        let filtered = [...services];
        
        // Apply type filter
        if (this.currentFilters.type !== 'all') {
            filtered = filtered.filter(service => 
                service.type === this.currentFilters.type
            );
        }
        
        // Apply status filter
        if (this.currentFilters.status !== 'all') {
            filtered = filtered.filter(service => {
                if (this.currentFilters.status === 'running') {
                    return service.status.toLowerCase() === 'running';
                } else if (this.currentFilters.status === 'created') {
                    return service.status.toLowerCase() === 'created';
                } else if (this.currentFilters.status === 'exited') {
                    return service.status.toLowerCase() === 'exited' || 
                           service.status.toLowerCase() === 'not found';
                }
                return true;
            });
        }
        
        // Apply sorting
        switch (this.currentFilters.sort) {
            case 'status':
                // Running first, then created, then exited/not found
                filtered.sort((a, b) => {
                    const statusOrder = {
                        'running': 0,
                        'created': 1,
                        'exited': 2,
                        'not found': 3
                    };
                    return statusOrder[a.status.toLowerCase()] - statusOrder[b.status.toLowerCase()];
                });
                break;
                
            case 'name-asc':
                filtered.sort((a, b) => a.name.localeCompare(b.name));
                break;
                
            case 'name-desc':
                filtered.sort((a, b) => b.name.localeCompare(a.name));
                break;
                
            case 'type-asc':
                filtered.sort((a, b) => a.type.localeCompare(b.type));
                break;
                
            case 'type-desc':
                filtered.sort((a, b) => b.type.localeCompare(a.type));
                break;
        }
        
        // Render the filtered list
        window.servicesList.renderServicesList(filtered);
    }
}

// Expose to window
window.serviceFilters = new ServiceFilters();
