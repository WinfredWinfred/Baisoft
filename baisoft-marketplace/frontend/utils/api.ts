import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

/**
 * Axios instance configured for API requests
 * Automatically adds JWT token and handles common errors
 */
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
});

/**
 * Request interceptor to add authentication token to all requests
 */
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Response interceptor to handle authentication and authorization errors
 */
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response) {
      const { status } = error.response;
      
      if (status === 401 && typeof window !== 'undefined') {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
      
      if (status === 403) {
        console.error('Access Denied');
      }
    }
    
    return Promise.reject(error);
  }
);

/**
 * Helper functions for common HTTP methods with type safety
 */
export const apiService = {
  get: <T>(url: string, config?: InternalAxiosRequestConfig): Promise<AxiosResponse<T>> => 
    api.get<T>(url, config),
  
  post: <T>(url: string, data?: any, config?: InternalAxiosRequestConfig): Promise<AxiosResponse<T>> => 
    api.post<T>(url, data, config),
  
  put: <T>(url: string, data?: any, config?: InternalAxiosRequestConfig): Promise<AxiosResponse<T>> => 
    api.put<T>(url, data, config),
  
  delete: <T>(url: string, config?: InternalAxiosRequestConfig): Promise<AxiosResponse<T>> => 
    api.delete<T>(url, config),
  
  patch: <T>(url: string, data?: any, config?: InternalAxiosRequestConfig): Promise<AxiosResponse<T>> => 
    api.patch<T>(url, data, config),
};

export default api;
