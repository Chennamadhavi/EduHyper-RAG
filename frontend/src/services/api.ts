import axios, { AxiosInstance, AxiosError } from 'axios';
import { HealthResponse } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Response interceptor for consistent error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Graceful error logging without exposing secrets or breaking application flow
    if (error.response) {
      console.warn(`[API] Server responded with status ${error.response.status}`);
    } else if (error.request) {
      console.warn('[API] No response received from server. Backend may be offline.');
    } else {
      console.warn('[API] Request initialization error:', error.message);
    }
    return Promise.reject(error);
  }
);

/**
 * Checks FastAPI backend health status
 */
export async function getBackendHealth(): Promise<HealthResponse | null> {
  try {
    const response = await apiClient.get<HealthResponse>('/api/health');
    return response.data;
  } catch (error) {
    return null;
  }
}

export default apiClient;
