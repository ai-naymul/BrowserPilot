/**
 * API Response Types for Component-Based UI
 * 
 * These types match the backend models for dynamic component generation.
 */

import { Entity } from './entity';

// ============================================================================
// Component Specifications (matches backend ComponentSpec)
// ============================================================================

export interface ComponentSpec {
  type: string;
  props: Record<string, any>;
  children?: ComponentSpec[];
  key?: string;
}

// ============================================================================
// Layout Specification (matches backend LayoutSpec)
// ============================================================================

export interface LayoutSpec {
  type: 'grid' | 'stack' | 'flex';
  columns?: number;
  gap?: number;
  config?: Record<string, any>;
}

// ============================================================================
// Action System Types
// ============================================================================

export type ActionType = 
  | 'fetch_data' 
  | 'refine_query' 
  | 'expand_card' 
  | 'add_entity' 
  | 'open_url';

export interface Action {
  type: ActionType;
  params: Record<string, any>;
}

// Specific action types for better type safety
export interface FetchDataAction extends Action {
  type: 'fetch_data';
  params: {
    source: string;
    ticker?: string;
    url?: string;
    query?: string;
  };
}

export interface RefineQueryAction extends Action {
  type: 'refine_query';
  params: {
    query: string;
  };
}

export interface ExpandCardAction extends Action {
  type: 'expand_card';
  params: {
    entityId: string;
  };
}

export interface AddEntityAction extends Action {
  type: 'add_entity';
  params: {
    template: string;
    data?: Record<string, any>;
  };
}

export interface OpenUrlAction extends Action {
  type: 'open_url';
  params: {
    url: string;
  };
}

export type SpecificAction = 
  | FetchDataAction 
  | RefineQueryAction 
  | ExpandCardAction 
  | AddEntityAction 
  | OpenUrlAction;

// ============================================================================
// Data Model (backward compatibility with existing entity system)
// ============================================================================

export interface Dependency {
  source_entity_id: string;
  target_entity_id: string;
  relationship: string;
  mechanism: 'validate' | 'update' | 'reference' | 'compute';
  metadata?: Record<string, any>;
}

export interface DataModel {
  version: number;
  task_description: string;
  entities: Entity[];
  dependencies: Dependency[];
  created_at?: string;
  updated_at?: string;
  conversation_history?: Array<{
    role: string;
    content: string;
    timestamp: string;
  }>;
}

// ============================================================================
// UI Specification (backward compatibility for panel-based UI)
// ============================================================================

export interface UIPanel {
  id: string;
  title: string;
  panel_type: 'summary' | 'card_grid' | 'table' | 'graph' | 'chart';
  entity_ids: string[];
  layout: Record<string, any>;
  config?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface UISpec {
  panels: UIPanel[];
  available_views?: Record<string, string[]>;
}

// ============================================================================
// Enhanced API Response (with component support)
// ============================================================================

export interface UIResponse {
  success: boolean;
  data_model?: DataModel;
  ui_spec?: UISpec;
  components?: ComponentSpec[];  // NEW: Dynamic component specs
  layout?: LayoutSpec;           // NEW: Layout specification
  suggested_questions?: string[];
  error?: string;
}

// ============================================================================
// Type Guards
// ============================================================================

/**
 * Check if response contains new component-based UI
 */
export function hasComponents(response: UIResponse): boolean {
  return !!(response.components && response.components.length > 0);
}

/**
 * Check if response contains legacy entity-based UI
 */
export function hasEntities(response: UIResponse): boolean {
  return !!(response.data_model?.entities && response.data_model.entities.length > 0);
}

/**
 * Check if action is a specific action type
 */
export function isAction<T extends SpecificAction>(
  action: Action,
  type: T['type']
): action is T {
  return action.type === type;
}
