/**
 * Centralized application configuration
 * All environment variables and app constants in one place
 */

const config = {
  // API Configuration
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  
  // Site Configuration
  siteName: process.env.NEXT_PUBLIC_SITE_NAME || 'Baisoft Marketplace',
  
  // Feature Flags
  features: {
    enableSearch: true,
    enableFilters: true,
    enableNotifications: true,
  },
  
  // UI Configuration
  ui: {
    itemsPerPage: 10,
    notificationDuration: 5000, // 5 seconds
    debounceDelay: 300, // 300ms for search
  },
  
  // API Configuration
  api: {
    timeout: 30000, // 30 seconds
    retryAttempts: 3,
    retryDelay: 1000, // 1 second
  },
};

export default config;
