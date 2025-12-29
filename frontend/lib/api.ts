import axios from 'axios';
import { TenantCreate, TenantResponse, TenantInfo, ApiError } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const createTenant = async (data: TenantCreate): Promise<TenantResponse> => {
  try {
    const response = await apiClient.post<TenantResponse>('/super-admin/create-tenant', data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response) {
        // Server responded with error status
        const apiError = error.response.data as ApiError;
        throw new Error(apiError.detail || `Server error: ${error.response.status}`);
      } else if (error.request) {
        // Request was made but no response received
        throw new Error('Backend service is not responding. Please ensure the FastAPI server is running on ' + API_URL);
      }
    }
    throw new Error('Network error occurred');
  }
};

export const healthCheck = async (): Promise<{ status: string }> => {
  try {
    const response = await apiClient.get<{ status: string }>('/health');
    return response.data;
  } catch (error) {
    throw new Error('Service is unavailable');
  }
};

export const getTenants = async (): Promise<TenantInfo[]> => {
  try {
    const response = await apiClient.get<TenantInfo[]>('/super-admin/tenants');
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response) {
        const apiError = error.response.data as ApiError;
        throw new Error(apiError.detail || `Server error: ${error.response.status}`);
      } else if (error.request) {
        throw new Error('Backend service is not responding. Please ensure the FastAPI server is running on ' + API_URL);
      }
    }
    throw new Error('Network error occurred');
  }
};

export const deleteTenant = async (tenantId: number): Promise<{ message: string; tenant_id: number; db_name: string }> => {
  try {
    const response = await apiClient.delete(`/super-admin/tenants/${tenantId}`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response) {
        const apiError = error.response.data as ApiError;
        throw new Error(apiError.detail || `Server error: ${error.response.status}`);
      } else if (error.request) {
        throw new Error('Backend service is not responding. Please ensure the FastAPI server is running on ' + API_URL);
      }
    }
    throw new Error('Network error occurred');
  }
};

export const toggleTenantStatus = async (tenantId: number): Promise<TenantInfo> => {
  try {
    const response = await apiClient.patch<TenantInfo>(`/super-admin/tenants/${tenantId}/toggle-status`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response) {
        const apiError = error.response.data as ApiError;
        throw new Error(apiError.detail || `Server error: ${error.response.status}`);
      } else if (error.request) {
        throw new Error('Backend service is not responding. Please ensure the FastAPI server is running on ' + API_URL);
      }
    }
    throw new Error('Network error occurred');
  }
};

