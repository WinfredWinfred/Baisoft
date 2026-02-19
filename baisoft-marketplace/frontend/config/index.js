// Application configuration
const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  siteName: process.env.NEXT_PUBLIC_SITE_NAME || 'Baisoft Marketplace',
  
  features: {
    enableSearch: true,
    enableFilters: true,
    enableNotifications: true,
  },
  
  ui: {
    itemsPerPage: 10,
    notificationDuration: 5000,
    debounceDelay: 300,
  },
  
  api: {
    timeout: 30000,
    retryAttempts: 3,
    retryDelay: 1000,
  },
};

export default config;
