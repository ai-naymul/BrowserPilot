/**
 * EntityStore - Single source of truth for all entity data
 *
 * Uses React Context + useReducer (no external deps)
 * All views read from here; edits propagate instantly
 */

import React, { createContext, useContext, useReducer, useCallback, useMemo } from 'react';
import { Entity, Attribute } from '@/lib/api';

interface EntityState {
  entities: Record<string, Entity>;
  deletedEntityIds: Set<string>; // Soft-delete: track deleted IDs
  deleteUndoStack: Array<{ entityIds: string[] }>; // Stack for undo
  history: Array<{
    action: string;
    timestamp: number;
    payload: any;
  }>;
  dependencyGraph: Record<string, string[]>; // parent -> children mapping
  version: number; // Increments on every mutation for React re-renders
}

type EntityAction =
  | { type: 'SET_ENTITIES'; payload: Entity[] }
  | { type: 'UPSERT_ENTITIES'; payload: Entity[] }
  | { type: 'UPDATE_ATTRIBUTE'; payload: { entityId: string; attrName: string; value: any } }
  | { type: 'DELETE_ENTITY'; payload: string }
  | { type: 'DELETE_CASCADE'; payload: { entityIds: string[] } } // Soft-delete multiple entities
  | { type: 'UNDO_DELETE'; payload: null } // Restore last deleted group
  | { type: 'RESTORE_ENTITY'; payload: Entity }
  | { type: 'SET_DEPENDENCY_GRAPH'; payload: Record<string, string[]> };

// Reducer
function entityReducer(state: EntityState, action: EntityAction): EntityState {
  switch (action.type) {
    case 'SET_ENTITIES': {
      const entities: Record<string, Entity> = {};
      action.payload.forEach(entity => {
        entities[entity.id] = entity;
      });
      return {
        ...state,
        entities,
        deletedEntityIds: new Set(), // Clear deleted IDs when setting fresh entity list
        deleteUndoStack: [], // Clear undo stack as well
        history: [...state.history, {
          action: 'SET_ENTITIES',
          timestamp: Date.now(),
          payload: action.payload.length,
        }],
      };
    }

    case 'UPSERT_ENTITIES': {
      const entities = { ...state.entities };
      action.payload.forEach(entity => {
        entities[entity.id] = entity;
      });
      console.log(`[EntityStore] UPSERT_ENTITIES: Updated ${action.payload.length} entities:`, action.payload.map(e => e.id));
      return {
        ...state,
        entities,
        version: state.version + 1, // Increment version to trigger re-renders
        history: [...state.history, {
          action: 'UPSERT_ENTITIES',
          timestamp: Date.now(),
          payload: action.payload.map(e => e.id),
        }],
      };
    }

    case 'UPDATE_ATTRIBUTE': {
      const { entityId, attrName, value } = action.payload;
      const entity = state.entities[entityId];
      if (!entity) return state;

      const updatedEntity = { ...entity };
      const attrIndex = updatedEntity.attributes.findIndex(a => a.name === attrName);

      if (attrIndex >= 0) {
        updatedEntity.attributes = [...updatedEntity.attributes];
        updatedEntity.attributes[attrIndex] = {
          ...updatedEntity.attributes[attrIndex],
          value,
        };
      } else {
        updatedEntity.attributes = [
          ...updatedEntity.attributes,
          { name: attrName, value },
        ];
      }

      return {
        ...state,
        entities: {
          ...state.entities,
          [entityId]: updatedEntity,
        },
        version: state.version + 1, // Increment version to trigger re-renders
        history: [...state.history, {
          action: 'UPDATE_ATTRIBUTE',
          timestamp: Date.now(),
          payload: { entityId, attrName, value },
        }],
      };
    }

    case 'DELETE_ENTITY': {
      // Soft-delete: mark as deleted but keep entity
      const newDeleted = new Set(state.deletedEntityIds);
      newDeleted.add(action.payload);

      return {
        ...state,
        deletedEntityIds: newDeleted,
        deleteUndoStack: [...state.deleteUndoStack, { entityIds: [action.payload] }],
        version: state.version + 1, // CRITICAL: Increment version to trigger re-renders
        history: [...state.history, {
          action: 'DELETE_ENTITY',
          timestamp: Date.now(),
          payload: action.payload,
        }],
      };
    }

    case 'DELETE_CASCADE': {
      // Soft-delete multiple entities (cascade)
      const newDeleted = new Set(state.deletedEntityIds);
      action.payload.entityIds.forEach(id => newDeleted.add(id));

      return {
        ...state,
        deletedEntityIds: newDeleted,
        deleteUndoStack: [...state.deleteUndoStack, { entityIds: action.payload.entityIds }],
        version: state.version + 1, // CRITICAL: Increment version to trigger re-renders
        history: [...state.history, {
          action: 'DELETE_CASCADE',
          timestamp: Date.now(),
          payload: action.payload.entityIds,
        }],
      };
    }

    case 'UNDO_DELETE': {
      if (state.deleteUndoStack.length === 0) return state;

      const lastDelete = state.deleteUndoStack[state.deleteUndoStack.length - 1];
      const newDeleted = new Set(state.deletedEntityIds);
      lastDelete.entityIds.forEach(id => newDeleted.delete(id));

      return {
        ...state,
        deletedEntityIds: newDeleted,
        deleteUndoStack: state.deleteUndoStack.slice(0, -1),
        version: state.version + 1, // CRITICAL: Increment version to trigger re-renders
        history: [...state.history, {
          action: 'UNDO_DELETE',
          timestamp: Date.now(),
          payload: lastDelete.entityIds,
        }],
      };
    }

    case 'SET_DEPENDENCY_GRAPH': {
      return {
        ...state,
        dependencyGraph: action.payload,
      };
    }

    case 'RESTORE_ENTITY': {
      return {
        ...state,
        entities: {
          ...state.entities,
          [action.payload.id]: action.payload,
        },
        history: [...state.history, {
          action: 'RESTORE_ENTITY',
          timestamp: Date.now(),
          payload: action.payload.id,
        }],
      };
    }

    default:
      return state;
  }
}

// Visual roles for entity types
export type EntityRole = 'primary' | 'breakdown' | 'derived';

// Context
interface EntityContextValue {
  entities: Record<string, Entity>;
  version: number; // For triggering re-renders when entities change
  setEntities: (entities: Entity[]) => void;
  upsertEntities: (entities: Entity[]) => void;
  updateAttr: (entityId: string, attrName: string, value: any) => void;
  getAttr: (entityId: string, attrName: string) => any;
  deleteEntity: (entityId: string) => void;
  deleteCascade: (entityId: string) => string[]; // Returns list of deleted IDs
  undoDelete: () => void;
  restoreEntity: (entity: Entity) => void;
  getEntity: (entityId: string) => Entity | undefined;
  getAllEntities: () => Entity[]; // Returns only non-deleted entities
  getVisibleEntities: () => Entity[]; // Explicit: only non-deleted
  setDependencyGraph: (graph: Record<string, string[]>) => void;
  // NEW: Role-aware selectors
  getEntitiesByType: (entityType: string) => Entity[];
  getPrimaryEntities: (primaryType: string) => Entity[];
  getBreakdownEntities: (primaryType: string) => Entity[];
  classifyEntity: (entityId: string, primaryType: string) => EntityRole;
}

const EntityContext = createContext<EntityContextValue | null>(null);

// Helper: Compute cascade delete set (BFS traversal)
function computeCascadeDeletes(rootId: string, dependencyGraph: Record<string, string[]>): string[] {
  const toDelete = new Set<string>([rootId]);
  const queue = [rootId];

  while (queue.length > 0) {
    const current = queue.shift()!;
    const children = dependencyGraph[current] || [];

    children.forEach(childId => {
      if (!toDelete.has(childId)) {
        toDelete.add(childId);
        queue.push(childId);
      }
    });
  }

  return Array.from(toDelete);
}

// Provider
export function EntityProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(entityReducer, {
    entities: {},
    deletedEntityIds: new Set(),
    deleteUndoStack: [],
    history: [],
    dependencyGraph: {},
    version: 0, // Start at version 0
  });

  const setEntities = useCallback((entities: Entity[]) => {
    dispatch({ type: 'SET_ENTITIES', payload: entities });
  }, []);

  const upsertEntities = useCallback((entities: Entity[]) => {
    dispatch({ type: 'UPSERT_ENTITIES', payload: entities });
  }, []);

  const updateAttr = useCallback((entityId: string, attrName: string, value: any) => {
    dispatch({ type: 'UPDATE_ATTRIBUTE', payload: { entityId, attrName, value } });
  }, []);

  const getAttr = useCallback((entityId: string, attrName: string): any => {
    const entity = state.entities[entityId];
    if (!entity) return undefined;
    const attr = entity.attributes.find(a => a.name === attrName);
    return attr?.value;
  }, [state.entities]);

  const deleteEntity = useCallback((entityId: string) => {
    dispatch({ type: 'DELETE_ENTITY', payload: entityId });
  }, []);

  const restoreEntity = useCallback((entity: Entity) => {
    dispatch({ type: 'RESTORE_ENTITY', payload: entity });
  }, []);

  const getEntity = useCallback((entityId: string) => {
    return state.entities[entityId];
  }, [state.entities]);

  const deleteCascade = useCallback((entityId: string): string[] => {
    const idsToDelete = computeCascadeDeletes(entityId, state.dependencyGraph);
    dispatch({ type: 'DELETE_CASCADE', payload: { entityIds: idsToDelete } });
    console.log('[EntityStore] Cascade deleted:', idsToDelete);
    return idsToDelete;
  }, [state.dependencyGraph]);

  const undoDelete = useCallback(() => {
    dispatch({ type: 'UNDO_DELETE', payload: null });
    console.log('[EntityStore] Undo delete');
  }, []);

  const setDependencyGraph = useCallback((graph: Record<string, string[]>) => {
    dispatch({ type: 'SET_DEPENDENCY_GRAPH', payload: graph });
    console.log('[EntityStore] Dependency graph set:', Object.keys(graph).length, 'nodes');
  }, []);

  const getAllEntities = useCallback(() => {
    // Filter out deleted entities
    return Object.values(state.entities).filter(e => !state.deletedEntityIds.has(e.id));
  }, [state.entities, state.deletedEntityIds]);

  const getVisibleEntities = useCallback(() => {
    // Explicit: only non-deleted entities
    return Object.values(state.entities).filter(e => !state.deletedEntityIds.has(e.id));
  }, [state.entities, state.deletedEntityIds]);

  // NEW: Get entities by type
  const getEntitiesByType = useCallback((entityType: string) => {
    return Object.values(state.entities).filter(
      e => !state.deletedEntityIds.has(e.id) && e.type === entityType
    );
  }, [state.entities, state.deletedEntityIds]);

  // NEW: Get primary entities (entities of the hero type)
  const getPrimaryEntities = useCallback((primaryType: string) => {
    return Object.values(state.entities).filter(
      e => !state.deletedEntityIds.has(e.id) && e.type === primaryType
    );
  }, [state.entities, state.deletedEntityIds]);

  // NEW: Get breakdown/derived entities (all non-primary types)
  const getBreakdownEntities = useCallback((primaryType: string) => {
    return Object.values(state.entities).filter(
      e => !state.deletedEntityIds.has(e.id) && e.type !== primaryType
    );
  }, [state.entities, state.deletedEntityIds]);

  // NEW: Classify entity role based on type and dependency graph
  const classifyEntity = useCallback((entityId: string, primaryType: string): EntityRole => {
    const entity = state.entities[entityId];
    if (!entity || state.deletedEntityIds.has(entityId)) {
      return 'derived';
    }

    // Primary entities: match the primary type
    if (entity.type === primaryType) {
      return 'primary';
    }

    // Check if this entity is a child of a primary entity in the dependency graph
    // If so, it's a breakdown (e.g., seasonal variant of a destination)
    const isBreakdown = Object.entries(state.dependencyGraph).some(([parentId, childIds]) => {
      const parent = state.entities[parentId];
      return parent?.type === primaryType && childIds.includes(entityId);
    });

    if (isBreakdown) {
      return 'breakdown';
    }

    // Everything else is derived
    return 'derived';
  }, [state.entities, state.deletedEntityIds, state.dependencyGraph]);

  const value = useMemo(() => ({
    entities: state.entities,
    version: state.version, // Expose version for re-render subscriptions
    setEntities,
    upsertEntities,
    updateAttr,
    getAttr,
    deleteEntity,
    deleteCascade,
    undoDelete,
    restoreEntity,
    getEntity,
    getAllEntities,
    getVisibleEntities,
    setDependencyGraph,
    getEntitiesByType,
    getPrimaryEntities,
    getBreakdownEntities,
    classifyEntity,
  }), [
    state.entities,
    state.version, // Include version in dependencies
    setEntities,
    upsertEntities,
    updateAttr,
    getAttr,
    deleteEntity,
    deleteCascade,
    undoDelete,
    restoreEntity,
    getEntity,
    getAllEntities,
    getVisibleEntities,
    setDependencyGraph,
    getEntitiesByType,
    getPrimaryEntities,
    getBreakdownEntities,
    classifyEntity,
  ]);

  return (
    <EntityContext.Provider value={value}>
      {children}
    </EntityContext.Provider>
  );
}

// Hook
export function useEntityStore() {
  const context = useContext(EntityContext);
  if (!context) {
    throw new Error('useEntityStore must be used within EntityProvider');
  }
  return context;
}

// Convenience hook for single entity
export function useEntity(entityId: string | undefined): Entity | undefined {
  const { entities } = useEntityStore();
  return entityId ? entities[entityId] : undefined;
}
