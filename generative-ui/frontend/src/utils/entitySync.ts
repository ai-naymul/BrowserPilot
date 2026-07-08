/**
 * Dynamic Entity Synchronization System
 * Syncs related entities when attributes change
 */

import { Entity, EntityAttribute } from '@/types/entity';

/**
 * Sync related entities when a value changes
 * This propagates changes across entity relationships dynamically
 */
export function syncRelatedEntities(
  entities: Entity[],
  changedEntityId: string,
  changedAttributeName: string,
  newValue: any
): Entity[] {
  const changedEntity = entities.find(e => e.id === changedEntityId);
  if (!changedEntity) return entities;

  let updatedEntities = [...entities];

  // Find all entities that might be related
  entities.forEach((entity, index) => {
    if (entity.id === changedEntityId) return; // Skip the changed entity itself

    // Check if this entity has a dependency/relationship to the changed entity
    const hasRelationship = checkRelationship(entity, changedEntity, entities);
    
    if (hasRelationship) {
      // Sync matching attributes across related entities
      const syncedEntity = syncMatchingAttributes(
        entity,
        changedEntity,
        changedAttributeName,
        newValue
      );
      
      if (syncedEntity !== entity) {
        updatedEntities[entities.indexOf(entity)] = syncedEntity;
      }
    }
  });

  return updatedEntities;
}

/**
 * Check if two entities have a relationship
 */
function checkRelationship(entity1: Entity, entity2: Entity, allEntities: Entity[]): boolean {
  // 1. Direct parent-child relationship
  if (entity1.children?.some(child => child.id === entity2.id)) return true;
  if (entity2.children?.some(child => child.id === entity1.id)) return true;

  // 2. Shared attributes with similar names (e.g., "total_budget", "budget")
  const entity1AttrNames = entity1.attributes.map(a => normalizeAttributeName(a.name));
  const entity2AttrNames = entity2.attributes.map(a => normalizeAttributeName(a.name));
  const sharedAttrs = entity1AttrNames.filter(name => entity2AttrNames.includes(name));
  if (sharedAttrs.length > 0) return true;

  // 3. Entity type similarity (e.g., "Budget", "Budget_Tracker", "Moving_Budget")
  const type1Normalized = normalizeEntityType(entity1.type);
  const type2Normalized = normalizeEntityType(entity2.type);
  if (type1Normalized.some(word => type2Normalized.includes(word))) return true;

  // 4. Dependencies in data model (if they exist)
  const deps1 = (entity1 as any).dependencies;
  const deps2 = (entity2 as any).dependencies;
  if (deps1 && Array.isArray(deps1) && deps1.some((dep: any) => dep.target === entity2.id)) return true;
  if (deps2 && Array.isArray(deps2) && deps2.some((dep: any) => dep.target === entity1.id)) return true;

  return false;
}

/**
 * Normalize attribute name for comparison
 */
function normalizeAttributeName(name: string): string {
  return name.toLowerCase()
    .replace(/_/g, '')
    .replace(/\s/g, '')
    .replace(/total/g, '')
    .replace(/estimated/g, '')
    .replace(/current/g, '');
}

/**
 * Normalize entity type for comparison
 */
function normalizeEntityType(type: string): string[] {
  return type.toLowerCase()
    .split(/[_\s-]/)
    .filter(word => word.length > 0);
}

/**
 * Sync matching attributes between entities
 */
function syncMatchingAttributes(
  targetEntity: Entity,
  sourceEntity: Entity,
  changedAttributeName: string,
  newValue: any
): Entity {
  let updated = false;
  const normalizedChangedAttr = normalizeAttributeName(changedAttributeName);

  const updatedAttributes = targetEntity.attributes.map(attr => {
    const normalizedAttr = normalizeAttributeName(attr.name);
    
    // Check if this attribute should sync with the changed one
    if (shouldSyncAttribute(attr.name, changedAttributeName, normalizedAttr, normalizedChangedAttr)) {
      updated = true;
      return { ...attr, value: newValue };
    }
    
    return attr;
  });

  if (updated) {
    return {
      ...targetEntity,
      attributes: updatedAttributes
    };
  }

  return targetEntity;
}

/**
 * Determine if an attribute should sync
 */
function shouldSyncAttribute(
  attrName: string,
  changedAttrName: string,
  normalizedAttr: string,
  normalizedChangedAttr: string
): boolean {
  // Exact match
  if (attrName === changedAttrName) return true;
  
  // Normalized match
  if (normalizedAttr === normalizedChangedAttr) return true;
  
  // Common attribute mappings
  const mappings: Record<string, string[]> = {
    'budget': ['totalbudget', 'budgettotal', 'estimatedbudget', 'budgetestimated'],
    'cost': ['totalcost', 'costtotal', 'estimatedcost', 'costestimated'],
    'expenses': ['totalexpenses', 'expensestotal', 'monthlyexpenses'],
    'income': ['totalincome', 'incometotal', 'monthlyincome'],
    'salary': ['totalsalary', 'salarytotal', 'annualsalary', 'monthlysalary'],
  };

  for (const [key, variants] of Object.entries(mappings)) {
    if ((normalizedAttr === key || variants.includes(normalizedAttr)) &&
        (normalizedChangedAttr === key || variants.includes(normalizedChangedAttr))) {
      return true;
    }
  }

  return false;
}

/**
 * Fix object display issues (like [object Object])
 */
export function fixObjectDisplay(entity: Entity): Entity {
  const fixedAttributes = entity.attributes.map(attr => {
    // If value is an object and shouldn't be, convert it
    if (typeof attr.value === 'object' && attr.value !== null && !Array.isArray(attr.value)) {
      // Check if this attribute should be a simple value
      if (attr.widget && !['array', 'contact_card', 'location'].includes(attr.widget)) {
        // Try to extract a meaningful value
        if (attr.value.total) return { ...attr, value: attr.value.total };
        if (attr.value.value) return { ...attr, value: attr.value.value };
        if (attr.value.amount) return { ...attr, value: attr.value.amount };
        
        // Convert to string representation
        const keys = Object.keys(attr.value);
        if (keys.length === 1) {
          return { ...attr, value: attr.value[keys[0]] };
        }
      }
    }
    
    return attr;
  });

  return {
    ...entity,
    attributes: fixedAttributes
  };
}
