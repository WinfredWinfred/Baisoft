import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

// Define the base URL from environment variables or use a default
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Create a custom axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for handling cookies if using HTTP-only tokens
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // Only run this in the browser
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle common errors
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    // Handle common errors (401, 403, 500, etc.)
    if (error.response) {
      const { status } = error.response;
      
      // Handle 401 Unauthorized
      if (status === 401) {
        // Clear token and redirect to login
        if (typeof window !== 'undefined') {
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
      }
      
      // Handle 403 Forbidden
      if (status === 403) {
        // You might want to redirect to a "not authorized" page
        console.error('Access Denied');
      }
    }
    
    return Promise.reject(error);
  }
);

// Helper functions for common HTTP methods
const apiService = {
  get: <T>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => 
    api.get<T>(url, config),
  
  post: <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => 
    api.post<T>(url, data, config),
  
  put: <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => 
    api.put<T>(url, data, config),
  
  delete: <T>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => 
    api.delete<T>(url, config),
  
  patch: <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => 
    api.patch<T>(url, data, config),
};

export { api as default, apiService };
