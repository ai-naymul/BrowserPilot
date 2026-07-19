// Shared types for generative-ui-browser
// These types can be used across both frontend and backend

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  version?: string;
}

export interface ComponentConfig {
  id: string;
  name: string;
  type: string;
  props: Record<string, any>;
  children?: ComponentConfig[];
}

export interface GenerationRequest {
  prompt: string;
  componentType?: string;
  framework?: 'react' | 'vue' | 'angular' | 'html';
  styling?: 'css' | 'tailwind' | 'styled-components';
}

export interface GenerationResponse {
  success: boolean;
  component?: ComponentConfig;
  code?: string;
  error?: string;
}
