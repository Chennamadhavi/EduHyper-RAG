export interface ComponentStatus {
  status: 'ready' | 'configured' | 'healthy' | 'missing' | 'warning' | 'error';
  detail: string;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  environment: string;
  version: string;
  components: Record<string, ComponentStatus>;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}
