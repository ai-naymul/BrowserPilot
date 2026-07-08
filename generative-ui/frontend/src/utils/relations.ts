/**
 * Relationship Graph - Related Module Updates
 *
 * Defines relationships between modules so that actions on one module
 * can trigger visual feedback in related modules.
 *
 * Example: Clicking Tokyo marker highlights Tokyo metric card and updates cost chart.
 *
 * This implements "feedforward" - showing the user what will happen
 * before they complete an action.
 */

import { bus } from './eventBus';

/**
 * Relationship map: module ID → array of related module IDs
 *
 * This is dynamically built from entity relationships and UI structure.
 * No hardcoded relationships - all inferred from data.
 */
const relationshipMap: Record<string, string[]> = {};

/**
 * Register a relationship between modules
 */
export function registerRelationship(moduleId: string, relatedModuleIds: string[]): void {
  relationshipMap[moduleId] = relatedModuleIds;
}

/**
 * Get related module IDs for a given module
 */
export function getRelatedModules(moduleId: string): string[] {
  return relationshipMap[moduleId] || [];
}

/**
 * Update related modules when one module changes
 *
 * This emits events to trigger visual feedback (brief flash, highlight, etc.)
 * in related modules.
 *
 * @param changedModuleId The module that changed
 * @param metadata Optional metadata about the change
 */
export function updateRelated(
  changedModuleId: string,
  metadata?: { reason?: string; [key: string]: any }
): void {
  const related = getRelatedModules(changedModuleId);

  if (related.length === 0) {
    return;
  }

  console.log(
    `[Relations] Module "${changedModuleId}" changed, updating ${related.length} related modules:`,
    related
  );

  // Emit event for each related module
  related.forEach((moduleId) => {
    bus.emit('MODULE_UPDATED', {
      moduleId,
      source: changedModuleId,
      reason: metadata?.reason || 'related-change',
      metadata,
    });
  });
}

/**
 * Auto-detect relationships from entity data
 *
 * This can be used to build the relationship map dynamically
 * based on entity dependencies or shared attributes.
 *
 * @param entities Array of entities with their attributes
 * @param dependencies Array of entity dependencies
 */
export function buildRelationshipMap(entities: any[], dependencies: any[]): void {
  // Clear existing relationships
  Object.keys(relationshipMap).forEach((key) => {
    delete relationshipMap[key];
  });

  // Build relationships from dependencies
  dependencies.forEach((dep) => {
    const sourceModule = `metric_card_${dep.source_entity_id}`;
    const targetModule = `metric_card_${dep.target_entity_id}`;

    if (!relationshipMap[sourceModule]) {
      relationshipMap[sourceModule] = [];
    }
    if (!relationshipMap[sourceModule].includes(targetModule)) {
      relationshipMap[sourceModule].push(targetModule);
    }
  });

  // Add common modules that relate to all entities
  const allCardModules = entities.map((e) => `metric_card_${e.id}`);

  // Map and charts relate to all cards
  relationshipMap.map = allCardModules;
  relationshipMap.cost_chart = allCardModules;
  relationshipMap.comparison_table = allCardModules;

  console.log('[Relations] Built relationship map:', relationshipMap);
}

/**
 * Get the complete relationship map (for debugging)
 */
export function getRelationshipMap(): Record<string, string[]> {
  return { ...relationshipMap };
}

/**
 * Clear all relationships
 */
export function clearRelationships(): void {
  Object.keys(relationshipMap).forEach((key) => {
    delete relationshipMap[key];
  });
}

// Event type for module updates
export interface ModuleUpdatedEvent {
  moduleId: string;
  source: string;
  reason: string;
  metadata?: any;
}
