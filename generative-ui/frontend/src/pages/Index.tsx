import { useState, useEffect, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { EntitySidebar } from '@/components/layout/EntitySidebar';
import { MainPanel } from '@/components/layout/MainPanel';
import { ContextPanel } from '@/components/layout/ContextPanel';
import { ChatInterface } from '@/components/layout/ChatInterface';
import { TriPaneSkeleton, RefinementSkeleton } from '@/components/SkeletonLoader';
import { Entity, ChatMessage } from '@/types/entity';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { Loader2, AlertCircle, LayoutGrid, List } from 'lucide-react';
import { updateComputedFields } from '@/utils/computedFields';
import { syncRelatedEntities, fixObjectDisplay } from '@/utils/entitySync';
import examplesData from '@/data/examples.json';
import {
  createTask,
  refineUI,
  checkBackendHealth,
  buildEntityHierarchy,
  type DataModel,
  type UISpec
} from '@/lib/api';
import { ComponentSpec, LayoutSpec, hasComponents } from '@/types/api';
import { DynamicComponentRenderer } from '@/components/DynamicComponentRenderer';
import { DynamicEntitySections } from '@/components/DynamicEntitySections';
import { EntityTypeSummaryCard } from '@/components/EntityTypeSummaryCard';
import { ActionHandler } from '@/utils/actionHandler';
import { useTheme } from '@/hooks/useTheme';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';
import { generateComponentsFromEntities, processComponentTree } from '@/utils/componentMapper';
import { EntityProvider, useEntityStore } from '@/store/EntityStore';
import { ActionDock } from '@/components/ActionDock';
import { AppPanel } from '@/components/AppPanel';

// NEW: Interaction system imports
import { UIProvider, useUIContext } from '@/contexts/UIContext';
import { LocationPanel } from '@/components/LocationPanel';
import { buildRelationshipMap } from '@/utils/relations';
import { useKeyboardNav } from '@/hooks/useKeyboardNav';
import { bus } from '@/utils/eventBus';

/**
 * IndexContent - Main application logic (uses UI context)
 */
const IndexContent = () => {
  const { toast } = useToast();
  const { theme, setTheme } = useTheme();
  const { locationPanelCity, setLocationPanel } = useUIContext(); // Use UI context
  const entityStore = useEntityStore(); // Access entity store

  // Subscribe to entity version to trigger re-renders when entities update (e.g., computed fields)
  // This is lightweight and doesn't cause side effects like accessing entities directly
  const _ = entityStore.version;

  // API state
  const [dataModel, setDataModel] = useState<DataModel | null>(null);
  const [uiSpec, setUiSpec] = useState<UISpec | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);
  const [chatVisible, setChatVisible] = useState(true);

  // NEW: Component-based UI state
  const [components, setComponents] = useState<ComponentSpec[]>([]);
  const [layout, setLayout] = useState<LayoutSpec | null>(null);

  // UI state
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [viewMode, setViewMode] = useState<'components' | 'entities'>('components');
  const [preferredView, setPreferredView] = useState<'components' | 'entities' | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([
    'Tell me more',
    'Show additional details',
    'What else should I know?'
  ]);

  // Track the initial primary entity type (set once on task creation, never changes)
  const [initialPrimaryType, setInitialPrimaryType] = useState<string | null>(null);

  // Suggested actions for ActionDock (AI-generated, context-aware)
  const [suggestedActions, setSuggestedActions] = useState<Array<{
    label: string;
    query?: string;
    icon?: string;
  }>>([]);

  // Track which action is currently loading
  const [loadingActionId, setLoadingActionId] = useState<string | null>(null);

  // Track new entity types (for "New" indicators on summary cards)
  const [newEntityTypes, setNewEntityTypes] = useState<Set<string>>(new Set());

  // Selection context for entity inference (tracks last focused/expanded entity)
  const [selectedFocusEntityId, setSelectedFocusEntityId] = useState<string | null>(null);

  // Track analysis-only updates (for visual feedback when no UI changes)
  const [showAnalysisFeedback, setShowAnalysisFeedback] = useState(false);

  // Task ID to track when we need full re-initialization
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);

  // Undo/Redo stacks for entity operations
  const [undoStack, setUndoStack] = useState<Array<{ action: string; entity: Entity }>>([]);
  const [redoStack, setRedoStack] = useState<Array<{ action: string; entity: Entity }>>([]);

  // Convert backend suggested_questions (strings) to suggestedActions format
  // Memoized to prevent creating new array references on every render
  const convertQuestionsToActions = useCallback((questions: string[] = []) => {
    return questions.map((question, idx) => {
      // Determine icon based on question content (generic patterns)
      let icon = 'sparkles'; // default
      const lowerQ = question.toLowerCase();

      if (lowerQ.includes('find') || lowerQ.includes('search') || lowerQ.includes('look for')) {
        icon = 'search';
      } else if (lowerQ.includes('add') || lowerQ.includes('include') || lowerQ.includes('show more')) {
        icon = 'plus';
      } else if (lowerQ.includes('compare') || lowerQ.includes('analyze')) {
        icon = 'trending';
      } else if (lowerQ.includes('create') || lowerQ.includes('generate') || lowerQ.includes('build')) {
        icon = 'file';
      } else if (lowerQ.includes('filter') || lowerQ.includes('refine') || lowerQ.includes('adjust')) {
        icon = 'zap';
      }

      return {
        label: question,
        query: question,
        icon: icon,
      };
    });
  }, []); // No dependencies - pure function

  // NOTE: Suggestions are now ONLY generated by the backend
  // Do NOT generate frontend suggestions as they will overwrite backend suggestions
  // The backend provides context-aware suggestions via the /refine and /generate endpoints

  // Check backend health on mount
  useEffect(() => {
    checkBackendHealth().then(setBackendHealthy);
  }, []);

  // Initialize entity store when dataModel changes
  // This ensures that any deleted entities are properly cleared when the data updates
  useEffect(() => {
    if (dataModel?.entities) {
      console.log('[EntityStore] Initializing with', dataModel.entities.length, 'entities for task:', currentTaskId);
      entityStore.setEntities(dataModel.entities);

      // Log visible entities for debugging
      setTimeout(() => {
        const visibleEntities = entityStore.getVisibleEntities();
        console.log('[EntityStore] Visible entities after init:', visibleEntities.length, 'entities:',
                    visibleEntities.map(e => e.public_identifier).join(', '));
      }, 100);
    }
  }, [dataModel, currentTaskId]); // Re-run when dataModel OR task ID changes

  // Build entity hierarchy for sidebar (using visible entities from store)
  const entities = dataModel ? buildEntityHierarchy(entityStore.getVisibleEntities(), dataModel.dependencies) : [];

  // NEW: Build relationship map from entities and dependencies
  useEffect(() => {
    if (dataModel) {
      buildRelationshipMap(dataModel.entities, dataModel.dependencies);
      console.log('[Index] Built relationship map for', dataModel.entities.length, 'entities');

      // Build dependency graph for cascade delete (parent -> children)
      // IMPORTANT: Only include TRUE dependencies (contains, part_of, etc.)
      // EXCLUDE peer relationships (comparable_to, similar_to, etc.)
      const CASCADE_RELATIONSHIPS = [
        'contains',
        'has',
        'part_of',
        'composed_of',
        'parent_of',
        'owns'
      ];

      const dependencyGraph: Record<string, string[]> = {};
      (dataModel.dependencies || []).forEach((dep: any) => {
        const relationship = (dep.relationship || '').toLowerCase();

        // Only cascade for true dependency relationships
        if (CASCADE_RELATIONSHIPS.includes(relationship)) {
          const parentId = dep.source_entity_id;
          const childId = dep.target_entity_id;

          if (!dependencyGraph[parentId]) {
            dependencyGraph[parentId] = [];
          }
          if (!dependencyGraph[parentId].includes(childId)) {
            dependencyGraph[parentId].push(childId);
          }
        }
        // Ignore peer relationships like "comparable_to", "similar_to", etc.
      });

      entityStore.setDependencyGraph(dependencyGraph);
    }
  }, [dataModel]); // entityStore is stable from context, doesn't need to be in deps

  // NEW: Enable keyboard navigation
  useKeyboardNav({
    entities: dataModel?.entities || [],
    enabled: true,
  });

  // Track entity selection/focus for better inference
  useEffect(() => {
    const unsubscribeCardExpand = bus.on('CARD_EXPANDED', (event: any) => {
      if (event.entityId && event.expanded) {
        setSelectedFocusEntityId(event.entityId);
      }
    });

    const unsubscribeEntitySelected = bus.on('ENTITY_SELECTED', (event: any) => {
      if (event.entityId) {
        setSelectedFocusEntityId(event.entityId);
      }
    });

    return () => {
      unsubscribeCardExpand();
      unsubscribeEntitySelected();
    };
  }, []);

  // Undo delete keyboard shortcut (Cmd/Ctrl + Z)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Only handle Cmd/Ctrl + Z (no shift)
      if (!(e.metaKey || e.ctrlKey) || e.key !== 'z' || e.shiftKey) return;

      // Don't intercept if user is typing in an input/textarea
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return;

      e.preventDefault();

      // Undo last delete from EntityStore
      entityStore.undoDelete();

      toast({
        title: 'Undo delete',
        description: 'Restored deleted entities',
        duration: 2000,
      });

      console.log('[Undo] Restored last delete');
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [entityStore, toast]);

  // Handle actions from components
  const handleAction = async (action: any) => {
    console.log('[Index] Action triggered:', action);

    // Set loading state for refine actions (using query as ID)
    const actionId = action.type === 'refine_query' ? action.params.query : null;
    if (actionId) {
      setLoadingActionId(actionId);
    }

    try {
      switch (action.type) {
        case 'add_entity':
          // Trigger refinement to add new entity
          const entityType = action.params.entityType || 'item';
          await handleFollowUp(`Add another ${entityType} to compare`);
          // Note: handleFollowUp will regenerate components automatically
          break;

        case 'refine_query':
          // Trigger refinement with the query
          await handleFollowUp(action.params.query);
          // Note: handleFollowUp will regenerate components automatically
          break;

        case 'expand_card':
          // Switch to detail view and select the entity
          const entity = dataModel?.entities.find(e => e.id === action.params.entityId);
          if (entity) {
            setSelectedEntity(entity);
            setViewMode('entities');
          }
          break;

        case 'open_url':
          // Open URL in new tab
          if (action.params.url) {
            window.open(action.params.url, '_blank', 'noopener,noreferrer');
          }
          break;

        case 'delete_entity':
          // Delete entity
          if (action.params.entityId) {
            await handleDeleteEntity(action.params.entityId);
          }
          break;

        default:
          console.warn('[Index] Unknown action type:', action.type);
          toast({
            title: 'Action not supported',
            description: `The action "${action.type}" is not yet implemented`,
            variant: 'destructive',
          });
      }
    } catch (error) {
      console.error('[Index] Action handler error:', error);
      toast({
        title: 'Action failed',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    } finally {
      // Clear loading state
      setLoadingActionId(null);
    }
  };

  // Handle component deletion
  const handleDeleteComponent = (componentKey: string) => {
    console.log('[Index] Deleting component:', componentKey);
    setComponents(prev => prev.filter(c => c.key !== componentKey));

    toast({
      title: 'Component removed',
      description: 'The component has been deleted from the view',
    });
  };

  // Delete entity with cascade and undo tracking (memoized)
  const handleDeleteEntity = useCallback((entityId: string) => {
    const entity = entityStore.getEntity(entityId);
    if (!entity) {
      console.warn('[Delete] Entity not found:', entityId);
      return;
    }

    // Cascade delete from store (includes dependencies)
    const deletedIds = entityStore.deleteCascade(entityId);

    const cascadeCount = deletedIds.length - 1; // Don't count the primary entity
    const cascadeMsg = cascadeCount > 0
      ? ` and ${cascadeCount} related ${cascadeCount === 1 ? 'item' : 'items'}`
      : '';

    toast({
      title: 'Entity removed',
      description: `${entity.public_identifier || entityId}${cascadeMsg} deleted. Press Cmd+Z to undo.`,
      duration: 3000,
    });

    console.log('[Delete] Cascade deleted:', deletedIds);
  }, [entityStore, toast]);

  // Handle initial task creation
  const handleCreateTask = async (input: string) => {
    setLoading(true);
    setError(null);

    try {
      console.log('Creating task with input:', input);
      
      const response = await createTask(input) as any; // Cast to any for component support
      
      console.log('Task created:', response);

      if (response.success && response.data_model) {
        setDataModel(response.data_model);
        setUiSpec(response.ui_spec);

        // Set task ID for entity store initialization
        setCurrentTaskId(response.data_model.id || Date.now().toString());

        // Extract and set components if present, or generate dynamically from entities
        if (response.components && response.components.length > 0) {
          const componentTypes = response.components.reduce((acc: Record<string, number>, c: any) => {
            acc[c.type] = (acc[c.type] || 0) + 1;
            return acc;
          }, {});
          console.log('[Components] Rendering dynamic components:', response.components.length, 'by type:', componentTypes);
          setComponents(response.components as ComponentSpec[]);
          setLayout(response.layout as LayoutSpec || null);

          // Use user's preferred view if set, otherwise default to components
          if (preferredView) {
            setViewMode(preferredView);
          } else {
            setViewMode('components');
          }
        } else if (response.data_model && response.data_model.entities.length > 0) {
          // Backend didn't return components - generate them dynamically
          console.log('[Components] Generating components dynamically from', response.data_model.entities.length, 'entities');

          // Determine primary entity type for filtering
          const typeCounts: Record<string, number> = {};
          response.data_model.entities.forEach((e: any) => {
            const type = e.type || 'Unknown';
            typeCounts[type] = (typeCounts[type] || 0) + 1;
          });
          const primaryType = Object.entries(typeCounts)
            .sort(([, a], [, b]) => b - a)[0]?.[0];

          const generatedComponents = generateComponentsFromEntities(
            response.data_model.entities,
            primaryType || initialPrimaryType
          );
          const componentTypes = generatedComponents.reduce((acc: Record<string, number>, c) => {
            acc[c.type] = (acc[c.type] || 0) + 1;
            return acc;
          }, {});
          console.log('[Components] Generated', generatedComponents.length, 'components by type:', componentTypes, 'for primary type:', primaryType || initialPrimaryType);
          setComponents(generatedComponents);
          setLayout(null);
          setViewMode(preferredView || 'components');
        } else {
          // No entities or components
          setComponents([]);
          setLayout(null);
          setViewMode(preferredView || 'components');
        }
        
        // Add to chat history
        setMessages([
          { 
            id: Date.now().toString(), 
            role: 'user', 
            content: input,
            timestamp: new Date()
          },
          { 
            id: (Date.now() + 1).toString(), 
            role: 'assistant', 
            content: response.data_model.task_description || 'Task created successfully!',
            timestamp: new Date()
          }
        ]);

        // Select first entity by default
        if (response.data_model.entities.length > 0) {
          setSelectedEntity(response.data_model.entities[0]);

          // Set initial primary type (most common entity type at task creation)
          const typeCounts: Record<string, number> = {};
          response.data_model.entities.forEach((e: any) => {
            const type = e.type || 'Unknown';
            typeCounts[type] = (typeCounts[type] || 0) + 1;
          });
          const primaryType = Object.entries(typeCounts)
            .sort(([, a], [, b]) => b - a)[0]?.[0];

          if (primaryType) {
            console.log('[Initial] Primary entity type:', primaryType);
            setInitialPrimaryType(primaryType);
          }
        }

        // Set suggestions for ChatInterface if provided by backend
        if (response.suggested_questions && response.suggested_questions.length > 0) {
          console.log('[Suggestions] Setting initial suggestions from backend:', response.suggested_questions);
          setSuggestions(response.suggested_questions);

          // Also convert to suggested actions for backward compatibility
          const actions = convertQuestionsToActions(response.suggested_questions);
          setSuggestedActions(actions);
        }

        toast({
          title: 'Success',
          description: 'UI generated successfully!',
        });
      } else {
        setError(response.error || 'Failed to create task');
        toast({
          title: 'Error',
          description: response.error || 'Failed to create task',
          variant: 'destructive',
        });
      }
    } catch (err: any) {
      console.error('Create task error:', err);
      setError(err.message || 'An error occurred');
      toast({
        title: 'Error',
        description: err.message || 'Failed to connect to backend',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Handle follow-up refinements
  const handleFollowUp = async (input: string) => {
    if (!dataModel || !uiSpec) {
      console.warn('No existing data model for follow-up');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('Refining UI with input:', input);
      
      const response = await refineUI(input, dataModel, uiSpec);
      
      console.log('Refinement response:', response);

      // Gracefully handle failed refines
      if (!response.success) {
        console.warn('[Refine] Failed:', response.error || 'Unknown error');
        toast({
          title: "Refinement failed",
          description: response.error || "No view changes. Try a different action.",
          variant: "destructive",
        });
        setLoading(false);
        return; // Don't update UI
      }

      if (response.success) {
        // ====================================================================
        // PATCH-MERGE LOGIC: Only update what changed
        // ====================================================================

        // 1. Merge entities using upsert (don't replace entire store)
        if (response.updated_data_model?.entities) {
          // Detect if entities actually changed (not just reprioritized)
          const hasValueChanges = response.updated_data_model.entities.some((newEntity: any) => {
            const existingEntity = dataModel?.entities.find(e => e.id === newEntity.id);
            if (!existingEntity) return true; // New entity

            // Compare attribute values (deep check)
            return JSON.stringify(existingEntity.attributes) !== JSON.stringify(newEntity.attributes);
          });

          console.log('[Refine] Upserting', response.updated_data_model.entities.length, 'entities (patch-merge) - Value changes detected:', hasValueChanges);

          // Detect new entity types for visual feedback
          if (dataModel) {
            const existingTypes = new Set(dataModel.entities.map(e => e.type));
            const newTypes = new Set(
              response.updated_data_model.entities
                .map(e => e.type)
                .filter(type => !existingTypes.has(type))
            );

            if (newTypes.size > 0) {
              console.log('[Refine] New entity types detected:', Array.from(newTypes));
              setNewEntityTypes(prev => new Set([...prev, ...newTypes]));

              // Auto-scroll to first new section after a short delay (for rendering)
              const firstNewType = Array.from(newTypes)[0];
              const sectionId = `section-${firstNewType.toLowerCase().replace(/\s+/g, '-')}`;

              setTimeout(() => {
                const section = document.getElementById(sectionId);
                if (section) {
                  section.scrollIntoView({ behavior: 'smooth', block: 'start' });
                  console.log('[Refine] Auto-scrolled to new section:', sectionId);
                }
              }, 300); // Wait for animation to complete

              // Auto-clear "New" indicators after 5 seconds
              setTimeout(() => {
                setNewEntityTypes(prev => {
                  const updated = new Set(prev);
                  newTypes.forEach(type => updated.delete(type));
                  return updated;
                });
              }, 5000);
            }
          }

          entityStore.upsertEntities(response.updated_data_model.entities);
          setDataModel(response.updated_data_model);

          // Update selected entity if it still exists
          if (selectedEntity) {
            const updatedEntity = response.updated_data_model.entities.find(
              e => e.id === selectedEntity.id
            );
            if (updatedEntity) {
              setSelectedEntity(updatedEntity);
            }
          }
        }

        // 2. Handle component updates with ADD-ON-TOP strategy (merge new with existing)
        const hasNewComponents = response.components && response.components.length > 0;
        const hasEmptyComponents = response.components !== undefined && response.components.length === 0;
        const noComponentsField = response.components === undefined;

        if (hasNewComponents) {
          // Backend returned NEW components from refinement - ADD them to existing components
          console.log('[Components] Received', response.components.length, 'NEW components from refinement');

          // MERGE STRATEGY: Add new refinement components ABOVE existing components
          // This shows the new analysis while keeping the original data visible below
          const newComponents = response.components as ComponentSpec[];

          setComponents(prevComponents => {
            // If response has "add_to_top" flag or this is a refinement, prepend new components
            const mergedComponents = [...newComponents, ...prevComponents];

            const componentTypes = mergedComponents.reduce((acc: Record<string, number>, c) => {
              acc[c.type] = (acc[c.type] || 0) + 1;
              return acc;
            }, {});

            console.log('[Components] Merged components:', newComponents.length, 'new +', prevComponents.length, 'existing =', mergedComponents.length, 'total');
            console.log('[Components] Component breakdown:', componentTypes);

            return mergedComponents;
          });

          if (response.layout) {
            setLayout(response.layout as LayoutSpec);
          }

          // Show success feedback for refinement
          toast({
            title: "Analysis complete",
            description: response.message || `Added ${newComponents.length} new visualization${newComponents.length > 1 ? 's' : ''}`,
            duration: 3000,
          });
        } else if (hasEmptyComponents || noComponentsField) {
          // Backend didn't update components - regenerate from fresh entities
          console.log('[Components] No component changes - regenerating from updated entities');

          // Regenerate components from updated entity data so counts/values are fresh
          if (response.updated_data_model?.entities && response.updated_data_model.entities.length > 0) {
            // Check if new entity types were added
            const existingTypes = dataModel ? new Set(dataModel.entities.map(e => e.type)) : new Set();
            const newTypes = response.updated_data_model.entities
              .map((e: any) => e.type)
              .filter((type: string) => !existingTypes.has(type));

            // If new entity types were added, generate cards for ALL types
            // Otherwise, use the original primary type to maintain chart consistency
            const typesToGenerate = newTypes.length > 0
              ? undefined // Generate for all types
              : initialPrimaryType; // Keep using the original primary type

            console.log('[Components] Generating components:', newTypes.length > 0 ? `for ALL types (${newTypes.length} new types added)` : `for primary type: ${initialPrimaryType}`);

            const regeneratedComponents = generateComponentsFromEntities(
              response.updated_data_model.entities,
              typesToGenerate
            );
            const componentTypes = regeneratedComponents.reduce((acc: Record<string, number>, c) => {
              acc[c.type] = (acc[c.type] || 0) + 1;
              return acc;
            }, {});
            console.log('[Components] Regenerated', regeneratedComponents.length, 'components by type:', componentTypes, 'from', response.updated_data_model.entities.length, 'entities');
            setComponents(regeneratedComponents);
          }

          // Check if we actually have value changes to show
          const hasValueChanges = response.updated_data_model?.entities?.some((newEntity: any) => {
            const existingEntity = dataModel?.entities.find(e => e.id === newEntity.id);
            if (!existingEntity) return true;
            return JSON.stringify(existingEntity.attributes) !== JSON.stringify(newEntity.attributes);
          });

          // Trigger visual feedback for analysis-only actions
          setShowAnalysisFeedback(true);
          setTimeout(() => setShowAnalysisFeedback(false), 2000);

          // Show appropriate feedback based on whether data changed
          if (hasValueChanges) {
            toast({
              title: "Analysis complete",
              description: "Data has been analyzed and updated.",
              duration: 2000,
            });
          } else {
            // Backend reprioritized attributes but didn't generate new data/components
            console.log('[Refine] No value changes detected - backend returned same data');
            toast({
              title: "No new data",
              description: "The analysis didn't generate new components or data. Try a different refinement.",
              duration: 3000,
            });
          }
        }

        // Merge incremental UI changes
        if (response.incremental_ui_spec?.panels) {
          setUiSpec(prev => ({
            ...prev!,
            panels: [
              ...(prev?.panels || []),
              ...response.incremental_ui_spec!.panels
            ]
          }));
        }

        // Update suggestions if backend provided new ones
        if (response.suggested_questions && response.suggested_questions.length > 0) {
          console.log('[Suggestions] Updating with new suggestions from backend:', response.suggested_questions);
          setSuggestions(response.suggested_questions);

          // Also convert to suggested actions for ActionDock
          const actions = convertQuestionsToActions(response.suggested_questions);
          console.log('[Actions] Updating ActionDock with suggested actions:', actions);
          setSuggestedActions(actions);
        }

        // Add to chat history
        setMessages(prev => [
          ...prev,
          { 
            id: Date.now().toString(), 
            role: 'user', 
            content: input,
            timestamp: new Date()
          },
          { 
            id: (Date.now() + 1).toString(), 
            role: 'assistant', 
            content: response.message || 'Updated successfully',
            timestamp: new Date()
          }
        ]);

        toast({
          title: 'Success',
          description: response.message || 'UI updated successfully!',
        });
      } else {
        setError(response.error || 'Failed to refine UI');
        toast({
          title: 'Error',
          description: response.error || 'Failed to refine UI',
          variant: 'destructive',
        });
      }
    } catch (err: any) {
      console.error('Refine UI error:', err);
      setError(err.message || 'An error occurred');
      toast({
        title: 'Error',
        description: err.message || 'Failed to connect to backend',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Debounce timer for backend sync
  const [syncTimer, setSyncTimer] = useState<NodeJS.Timeout | null>(null);

  // Handle real-time entity attribute changes
  const handleAttributeChange = async (entityId: string, attributeName: string, newValue: any) => {
    if (!dataModel) return;

    // Update local state immediately for instant UI feedback
    let updatedEntities = dataModel.entities.map(entity => {
      if (entity.id === entityId) {
        const updatedEntity = {
          ...entity,
          attributes: entity.attributes.map(attr => 
            attr.name === attributeName 
              ? { ...attr, value: newValue }
              : attr
          )
        };
        // Recalculate computed fields (totals, percentages, etc.)
        return updateComputedFields(updatedEntity);
      }
      return entity;
    });
    
    // Sync related entities (propagate changes across relationships)
    updatedEntities = syncRelatedEntities(
      updatedEntities,
      entityId,
      attributeName,
      newValue
    );
    
    // Recalculate computed fields for ALL entities after sync
    updatedEntities = updatedEntities.map(entity => updateComputedFields(entity));
    
    // Fix any object display issues
    updatedEntities = updatedEntities.map(entity => fixObjectDisplay(entity));

    const updatedModel = {
      ...dataModel,
      entities: updatedEntities,
      updated_at: new Date().toISOString()
    };

    setDataModel(updatedModel);

    // CRITICAL: Update EntityStore so cards/charts reflect changes immediately
    entityStore.upsertEntities(updatedEntities);
    console.log('[Index] Updated EntityStore with', updatedEntities.length, 'entities after attribute change');

    // Debounced backend sync for ALL changes (not just location)
    // This ensures data persists and relationships are maintained
    if (syncTimer) {
      clearTimeout(syncTimer);
    }

    const newTimer = setTimeout(async () => {
      try {
        // Sync to backend without triggering full refinement
        // Just update the data model
        await fetch('http://localhost:8000/api/refine/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            data_model: updatedModel
          })
        }).catch(err => console.log('Backend sync (optional):', err));
        
        console.log(`✓ Synced: ${attributeName} = ${JSON.stringify(newValue).substring(0, 50)}`);
      } catch (error) {
        // Silent fail - local state already updated
        console.log('Backend sync pending...');
      }
    }, 1500); // 1.5 second debounce

    setSyncTimer(newTimer);

    // Show quick feedback
    toast({
      title: 'Updated',
      description: `${attributeName.replace(/_/g, ' ')} changed`,
      duration: 1000,
    });

    // Update selected entity
    if (selectedEntity?.id === entityId) {
      const updated = updatedEntities.find(e => e.id === entityId);
      if (updated) setSelectedEntity(updated);
    }

    // If the change is significant (like location), trigger a refinement
    const entity = updatedEntities.find(e => e.id === entityId);
    const attribute = entity?.attributes.find(a => a.name === attributeName);
    
    if (attribute?.widget === 'location' && newValue !== attribute.value) {
      // Trigger automatic refinement for location changes
      console.log('Location changed, triggering refinement...');
      await handleFollowUp(`The ${attributeName} has been updated to ${newValue}. Please update relevant information accordingly.`);
    }
  };

  // Handle entity selection
  const handleSelectEntity = (entity: Entity) => {
    setSelectedEntity(entity);
  };

  // Show skeleton loading state first (highest priority)
  if (loading) {
    return (
      <div className="fixed inset-0 bg-background z-[100] overflow-hidden">
        {/* Always show tri-pane skeleton matching actual UI layout */}
        <div className="flex flex-col h-full w-full">
          {/* Header skeleton */}
          <div className="flex items-center justify-between gap-2 p-3 border-b border-border bg-sidebar">
            <div className="flex items-center gap-3">
              <div className="h-5 w-48 bg-muted/40 rounded animate-pulse" />
            </div>
            <div className="flex items-center gap-2">
              <div className="h-8 w-24 bg-muted/40 rounded-lg animate-pulse" />
              <div className="h-8 w-24 bg-muted/40 rounded-lg animate-pulse" />
            </div>
          </div>

          {/* Tri-pane skeleton body */}
          <div className="flex-1 overflow-hidden">
            <TriPaneSkeleton />
          </div>
        </div>

        {/* Subtle processing indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-[110]">
          <motion.div
            initial={{ y: 10, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-card/95 backdrop-blur-xl border border-border/50 rounded-full px-5 py-2.5 shadow-xl flex items-center gap-2.5"
          >
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            <span className="text-sm font-medium text-foreground">
              {dataModel ? 'Refining analysis...' : 'Generating interface...'}
            </span>
          </motion.div>
        </div>
      </div>
    );
  }

  // Show initial input screen if no data
  if (!dataModel || !uiSpec) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-8 bg-gradient-to-br from-background via-background to-primary/5">
        <div className="w-full max-w-2xl">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-10"
          >
            <h1 className="text-5xl font-bold mb-3 bg-gradient-to-r from-foreground via-foreground to-primary bg-clip-text text-transparent">
              Generative UI Browser
            </h1>
            <p className="text-lg text-muted-foreground/80">
              Describe your task, and we'll generate an intelligent interface
            </p>
          </motion.div>
          
          {/* Backend Health Check */}
          {backendHealthy === false && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-red-900">Backend Connection Error</p>
                <p className="text-sm text-red-700 mt-1">
                  Cannot connect to backend at http://localhost:8000. 
                  Please make sure the backend server is running.
                </p>
                <code className="text-xs bg-red-100 px-2 py-1 rounded mt-2 inline-block">
                  cd backend && uvicorn app.main:app --reload --port 8000
                </code>
              </div>
            </div>
          )}
          
          <div className="relative bg-card/80 backdrop-blur-xl rounded-2xl shadow-2xl p-8 border border-border/50">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/5 rounded-2xl" />
            <div className="relative">
              <label className="block text-sm font-semibold text-foreground/70 mb-4 uppercase tracking-wide">
                What would you like to do?
              </label>
              <form onSubmit={(e) => {
                e.preventDefault();
                const input = inputValue.trim();
                if (input) {
                  handleCreateTask(input);
                  setInputValue('');
                }
              }}>
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Describe your task... For example: Compare Paris, Rome, and Barcelona for a 7-day vacation"
                  className="w-full px-5 py-4 bg-background/50 text-foreground border-2 border-border/50 rounded-xl focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all mb-4 placeholder:text-muted-foreground/50 resize-none min-h-[120px] leading-relaxed backdrop-blur-sm"
                  disabled={loading || backendHealthy === false}
                  rows={4}
                />
                <Button
                  type="submit"
                  disabled={loading || !inputValue.trim() || backendHealthy === false}
                  className="w-full h-12 text-base font-semibold rounded-xl bg-primary hover:bg-primary/90 shadow-lg hover:shadow-xl transition-all"
                >
                  Generate Interface
                </Button>
              </form>

              {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                  {error}
                </div>
              )}
            </div>
          </div>

          {/* View info - simplified */}
          <p className="mt-4 text-xs text-muted-foreground text-center">
            Results will show in a tri-pane layout with list, map, and details
          </p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-8"
          >
            <p className="mb-4 text-sm font-semibold text-foreground/70 uppercase tracking-wider text-center">
              Try an example
            </p>
            <div className="grid grid-cols-1 gap-3">
              {examplesData.examples.slice(0, 3).map((example, idx) => (
                <motion.button
                  key={idx}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 + idx * 0.1 }}
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleCreateTask(example.text)}
                  disabled={loading || backendHealthy === false}
                  className="relative overflow-hidden group text-left px-6 py-4 bg-card/50 backdrop-blur-sm text-foreground rounded-2xl border border-border/50 hover:border-primary/40 hover:bg-card/80 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-lg"
                >
                  <div className="flex items-center gap-4">
                    <span className="text-3xl">{example.emoji}</span>
                    <span className="font-medium text-sm">{example.text}</span>
                  </div>
                  <div className="absolute inset-0 bg-gradient-to-r from-primary/0 via-primary/5 to-primary/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                </motion.button>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Theme Switcher - Hidden for cleaner UI (can be re-enabled via settings) */}
        {/* <ThemeSwitcher currentTheme={theme} onThemeChange={setTheme} /> */}
      </div>
    );
  }

  // Show full UI once data is loaded
  return (
    <div className="flex flex-col h-screen w-full overflow-hidden">
      {/* Header with task description */}
      <div className="flex items-center justify-between gap-2 p-3 border-b border-border bg-sidebar">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-medium text-foreground">
            {dataModel.entities.length >= 3
              ? `Comparing ${dataModel.entities.length} ${dataModel.entities[0]?.type?.split('_')[0] || 'Items'}s`
              : dataModel.entities.length === 1
              ? dataModel.entities[0]?.public_identifier || dataModel.task_description
              : dataModel.task_description.length > 60
              ? dataModel.task_description.substring(0, 60) + '...'
              : dataModel.task_description}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          {/* View Mode Toggle - Always show when data is loaded */}
          {dataModel.entities.length > 0 && (
            <div className="flex items-center gap-1 border border-border rounded-lg p-1 bg-background">
              <Button
                variant={viewMode === 'components' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('components')}
                className="h-7 px-2"
              >
                <LayoutGrid className="h-4 w-4 mr-1" />
                Cards
              </Button>
              <Button
                variant={viewMode === 'entities' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('entities')}
                className="h-7 px-2"
              >
                <List className="h-4 w-4 mr-1" />
                Details
              </Button>
            </div>
          )}
          
          {/* Theme Switcher - Hidden for cleaner OpenAI-style UI */}
          {/* <ThemeSwitcher currentTheme={theme} onThemeChange={setTheme} /> */}

          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setDataModel(null);
              setUiSpec(null);
              setSelectedEntity(null);
              setMessages([]);
              setComponents([]);
              setViewMode('components');
            }}
          >
            New Task
          </Button>
        </div>
      </div>

      {/* Cards View - Tri-Pane AppPanel Layout (OpenAI-style) */}
      {viewMode === 'components' && (
        <div className="flex-1 overflow-hidden bg-background">
          {components.length > 0 || entityStore.getVisibleEntities().length > 0 ? (
            <AppPanel
              title={dataModel.entities.length >= 2
                ? `Comparing ${dataModel.entities.filter(e => e.type?.toLowerCase().includes('destination')).length || dataModel.entities.length} destinations`
                : dataModel.task_description
              }
              subtitle={dataModel.task_description}
              components={components}
              primaryEntityType={initialPrimaryType || undefined}
              onAction={handleAction}
              onDeleteEntity={handleDeleteEntity}
              onAttributeChange={handleAttributeChange}
              suggestedActions={suggestedActions}
              loadingActionId={loadingActionId}
              allEntities={dataModel.entities}
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-muted-foreground p-8">
                <LayoutGrid className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p className="font-medium">No components generated yet</p>
                <p className="text-sm mt-1">Try using the chat to refine your query</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Details View - Entity-based UI with organized panels */}
      {viewMode === 'entities' && (
        <div className="flex flex-1 overflow-hidden">
          <EntitySidebar
            entities={entities}
            selectedId={selectedEntity?.id}
            onSelect={handleSelectEntity}
            onSwitchToCards={(entityType) => {
              // Switch to Cards view
              setViewMode('components');

              // If entity type provided, scroll to that section
              if (entityType) {
                const sectionId = `section-${entityType.toLowerCase().replace(/\s+/g, '-')}`;
                setTimeout(() => {
                  const section = document.getElementById(sectionId);
                  if (section) {
                    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    console.log('[Sidebar] Switched to Cards and scrolled to:', sectionId);
                  }
                }, 100); // Small delay for view switch
              }
            }}
          />
          <MainPanel
            allEntities={dataModel.entities}
            selectedEntityId={selectedEntity?.id || null}
            onEntitySelect={(entityId) => {
              if (entityId === null) {
                setSelectedEntity(null);
              } else {
                const entity = dataModel.entities.find(e => e.id === entityId);
                setSelectedEntity(entity || null);
              }
            }}
            onAttributeChange={handleAttributeChange}
            onDeleteEntity={handleDeleteEntity}
            loading={loading}
          />
          <ContextPanel 
            entity={selectedEntity}
            allEntities={dataModel.entities}
            dependencies={dataModel.dependencies}
          />
        </div>
      )}

      {/* Chat Interface - Fixed Bottom Centered */}
      <div className="fixed bottom-0 left-1/2 -translate-x-1/2 z-30 pointer-events-none pb-6" style={{ maxWidth: 'calc(100vw - 40rem)' }}>
        <div className="pointer-events-auto">
          <ChatInterface
            messages={messages}
            onSubmit={handleFollowUp}
            isLoading={loading}
            suggestions={suggestions}
            isVisible={chatVisible}
            onToggleVisibility={() => setChatVisible(!chatVisible)}
          />
        </div>
      </div>

      {/* NEW: Location Panel - Opens when map marker or card details is clicked */}
      <AnimatePresence mode="wait">
        {locationPanelCity && (() => {
          console.log('[Index] Rendering LocationPanel for:', locationPanelCity.id);
          return (
            <LocationPanel
              key={`location-panel-${locationPanelCity.id}`}
              entity={locationPanelCity}
              onClose={() => setLocationPanel(null)}
              onAction={handleAction}
            />
          );
        })()}
      </AnimatePresence>
    </div>
  );
};

/**
 * Index - Root component with EntityProvider + UIProvider wrappers
 */
const Index = () => {
  return (
    <EntityProvider>
      <UIProvider>
        <IndexContent />
      </UIProvider>
    </EntityProvider>
  );
};

export default Index;
