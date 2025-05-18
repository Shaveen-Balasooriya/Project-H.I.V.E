/**
 * Honeypots Main Controller
 * Project H.I.V.E
 * 
 * This is the main entry point for the honeypots page functionality.
 * It initializes the modules and coordinates their interactions.
 */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize the honeypot list
  const honeypotsList = HoneypotsList.init();
  
  // Initialize actions with the list instance
  const honeypotActions = HoneypotActions.init(honeypotsList);
  
  // Initialize statistics
  const honeypotStats = HoneypotStats.init(honeypotsList);
  
  // Initialize filters
  const honeypotFilters = HoneypotFilters.init(honeypotsList);
  
  // Expose instances to window for debugging if needed
  window.honeypotsList = honeypotsList;
  window.honeypotActions = honeypotActions;
  window.honeypotStats = honeypotStats;
  window.honeypotFilters = honeypotFilters;
});
