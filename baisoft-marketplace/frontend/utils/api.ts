import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import config from '../config';

const API_BASE_URL = config.apiUrl;

/**
 * Axios instance configured for API requests
 * Automatically adds JWT token, handles common errors, and implements retry logic
 */
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: config.api.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
});

/**
 * Request interceptor to add authentication token to all requests
 */
api.interceptors.request.use(
  (requestConfig: InternalAxiosRequestConfig) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      if (token && requestConfig.headers) {
        requestConfig.headers.Authorization = `Bearer ${token}`;
      }
    }
    return requestConfig;
  },
  (error) => Promise.reject(error)
);

/**
 * Response interceptor with retry logic and error handling
 */
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: number };
    
    if (error.response) {
      const { status } = error.response;
      
      // Handle authentication errors
      if (status === 401 && typeof window !== 'undefined') {
        localStorage.removeItem('token');
        window.location.href = '/login';
        return Promise.reject(error);
      }
      
      // Handle authorization errors
      if (status === 403) {
        console.error('Access Denied');
        return Promise.reject(error);
      }

      // Don't retry client errors (4xx except 429 Too Many Requests)
      if (status >= 400 && status < 500 && status !== 429) {
        return Promise.reject(error);
      }
    }

    // Retry logic for network errors, 5xx errors, and 429 (rate limiting)
    if (
      originalRequest &&
      (!originalRequest._retry || originalRequest._retry < config.api.retryAttempts) &&
      (!error.response || error.response.status >= 500 || error.response.status === 429)
    ) {
      originalRequest._retry = (originalRequest._retry || 0) + 1;
      
      // Exponential backoff: 1s, 2s, 4s
      const delay = config.api.retryDelay * Math.pow(2, originalRequest._retry - 1);
      
      console.log(`Retrying request (attempt ${originalRequest._retry}/${config.api.retryAttempts}) after ${delay}ms`);
      
      await new Promise(resolve => setTimeout(resolve, delay));
      
      return api(originalRequest);
    }
    
    return Promise.reject(error);
  }
);

/**
 * Helper functions for common HTTP methods with type safety
 */
export const apiService = {
  get: <T>(url: string, requestConfig?: InternalAxiosRequestConfig): Promise<AxiosResponse<T>> => 
    api.get<T>(url, requestConfig),
  
  post: <T>(url: string, data?: any, requestConfig?: InternalAxiosRequestConfig): Promise<AxiosResponse<T>> => 
    api.post<T>(url, data, requestConfig),
  
  put: <T>(url: string, data?: any, requestConfig?: InternalAxiosRequestConfig): Promise<AxiosResponse<T>> => 
    api.put<T>(url, data, requestConfig),
  
  delete: <T>(url: string, requestConfig?: InternalAxiosRequestConfig): Promise<AxiosResponse<T>> => 
    api.delete<T>(url, requestConfig),
  
  patch: <T>(url: string, data?: any, requestConfig?: InternalAxiosRequestConfig): Promise<AxiosResponse<T>> => 
    api.patch<T>(url, data, requestConfig),
};

export default api;
