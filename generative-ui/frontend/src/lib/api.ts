import { ChatMessage } from '@/types/entity';

// The gen-UI backend. Defaults to :8001 so it can run alongside BrowserPilot
// (the scraper) on :8000. Override with VITE_API_BASE_URL.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

export interface CreateTaskRequest {
  user_input: string;
}

export interface CreateTaskResponse {
  success: boolean;
  data_model: DataModel;
  ui_spec: UISpec;
  error?: string;
}

export interface RefineRequest {
  user_input: string;
  current_data_model: DataModel;
  current_ui_spec: UISpec;
}

export interface RefineResponse {
  success: boolean;
  intent: string;
  updated_data_model?: DataModel;
  incremental_entities?: Entity[];
  incremental_ui_spec?: Partial<UISpec>;
  components?: any[]; // Updated component specs after refinement
  layout?: any; // Updated layout after refinement
  suggested_questions?: string[]; // Updated context-aware suggestions after refinement
  message?: string;
  error?: string;
}

export interface DataModel {
  task_description: string;
  entities: Entity[];
  dependencies: Dependency[];
  conversation_history: ConversationTurn[];
  version?: number;
  created_at?: string;
  updated_at?: string;
  metadata?: Record<string, any>;
}

export interface Entity {
  id: string;
  type: string;
  icon?: string;
  color?: string;
  public_identifier: string;
  attributes: Attribute[];
  children?: Entity[];
  tags?: string[];
}

export interface Attribute {
  name: string;
  value: any;
  data_type?: string;
  widget?: string;
  editable?: boolean;
  function?: string;
  validation?: any;
  item_widget?: string;
  metadata?: Record<string, any>;
}

export interface Dependency {
  source_entity_id: string;
  target_entity_id: string;
  relationship: string;
  mechanism?: string;
  metadata?: Record<string, any>;
}

export interface ConversationTurn {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface UISpec {
  panels: Panel[];
  layout_mode?: string;
  theme?: Record<string, any>;
  metadata?: Record<string, any>;
  available_views?: Record<string, string[]>;
}

export interface Panel {
  id: string;
  title: string;
  panel_type: string;
  entity_ids: string[];
  layout?: Record<string, any>;
  config?: {
    view_type?: string;
    available_views?: string[];
    [key: string]: any;
  };
  metadata?: Record<string, any>;
}

export async function createTask(userInput: string): Promise<CreateTaskResponse> {
  try {
    console.log('Creating task with input:', userInput);
    
    const response = await fetch(`${API_BASE_URL}/api/refine/create-task`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ user_input: userInput }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || errorData.detail || `Failed with status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Task created successfully:', data);
    return data;
  } catch (error) {
    console.error('Create task error:', error);
    throw error;
  }
}

// Scrape URLs (via BrowserPilot) and render a dashboard grounded on the real data.
// Returns the same envelope as createTask (plus components/layout).
export async function renderFromScrape(urls: string[], question: string): Promise<CreateTaskResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/refine/render-from-scrape`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ urls, question }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || errorData.detail || `Failed with status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Render-from-scrape error:', error);
    throw error;
  }
}

export async function refineUI(
  userInput: string,
  currentDataModel: DataModel,
  currentUiSpec: UISpec
): Promise<RefineResponse> {
  try {
    console.log('Refining UI with input:', userInput);
    
    const response = await fetch(`${API_BASE_URL}/api/refine`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_input: userInput,
        current_data_model: currentDataModel,
        current_ui_spec: currentUiSpec,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || errorData.detail || `Failed with status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Refinement successful:', data);
    return data;
  } catch (error) {
    console.error('Refine UI error:', error);
    throw error;
  }
}

// Generate dynamic chat suggestions based on current context
export async function generateSuggestions(
  dataModel: DataModel,
  conversationHistory: ChatMessage[]
): Promise<string[]> {
  try {
    console.log('Generating suggestions...');
    
    const response = await fetch(`${API_BASE_URL}/api/refine/suggestions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        data_model: dataModel,
        conversation_history: conversationHistory.map(msg => ({
          role: msg.role,
          content: msg.content
        }))
      }),
    });

    if (!response.ok) {
      console.warn('Failed to generate suggestions, using defaults');
      return [
        'Tell me more about this',
        'What are my options?',
        'Show me additional details'
      ];
    }

    const data = await response.json();
    return data.suggestions || [];
  } catch (error) {
    console.error('Generate suggestions error:', error);
    // Return fallback suggestions on error
    return [
      'Tell me more',
      'Show additional details',
      'What else should I know?'
    ];
  }
}

// Helper function to check if backend is healthy
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/refine/health`);
    return response.ok;
  } catch {
    return false;
  }
}

// Helper function to check if input is a URL
export function isUrl(input: string): boolean {
  try {
    new URL(input);
    return input.startsWith('http://') || input.startsWith('https://');
  } catch {
    return false;
  }
}

// Helper to build entity hierarchy
export function buildEntityHierarchy(entities: Entity[], dependencies: Dependency[]): Entity[] {
  // Return all entities flat - no hierarchy filtering
  // This ensures all entities show in sidebar
  return entities.map(e => ({ ...e, children: [] }));
}
