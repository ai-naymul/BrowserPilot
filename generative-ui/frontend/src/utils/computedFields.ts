/**
 * Compute derived fields for entities based on their attributes
 */

import { Entity, EntityAttribute } from '@/types/entity';

/**
 * Dynamically compute a field based on attribute name patterns
 * This is GENERIC and works for ANY entity type
 */
function computeFieldValue(
  fieldName: string,
  attributes: EntityAttribute[]
): number | null {
  console.log(`[ComputedFields] Computing: ${fieldName}`);
  
  // Pattern 1: total_X = sum of all X_* fields
  // Examples: total_cost, total_budget, estimated_total_cost, allocated_total
  if (fieldName.startsWith('total_') || fieldName.endsWith('_total') || fieldName.includes('total')) {
    // Extract the meaningful part (e.g., "cost" from "estimated_total_cost")
    let prefix = fieldName.replace('total_', '').replace('_total', '');

    // For fields like "estimated_total_cost", extract "cost"
    const parts = prefix.split('_');
    const suffix = parts[parts.length - 1]; // Get last word (e.g., "cost", "budget")

    // Helper function to check if field is numeric/currency
    const isNumericField = (attr: any) => {
      const value = attr.value;
      return (typeof value === 'number' && !isNaN(value)) ||
             (typeof value === 'string' && !isNaN(Number(value)) && value.trim() !== '');
    };

    // Helper function to check if field is a cost/price/budget field
    const isCostField = (attr: any) => {
      return attr.name.includes('cost') ||
             attr.name.includes('price') ||
             attr.name.includes('budget') ||
             attr.name.includes('fee') ||
             attr.name.includes('expense');
    };

    // Strategy 1: Find fields containing the prefix
    let relatedFields = attributes.filter(attr =>
      attr.name.includes(prefix) &&
      attr.name !== fieldName &&
      attr.function !== 'computed' &&
      isNumericField(attr)
    );

    console.log(`  → Trying prefix match for "${prefix}": found ${relatedFields.length} fields`);

    // Strategy 2: Sum ALL cost/budget/price fields (for fields like "estimated_total_cost")
    if (relatedFields.length === 0 && isCostField({ name: fieldName })) {
      relatedFields = attributes.filter(attr =>
        isCostField(attr) &&
        attr.name !== fieldName &&
        attr.function !== 'computed' &&
        isNumericField(attr)
      );
      console.log(`  → Strategy: Summing all cost/budget fields for ${fieldName}: found ${relatedFields.length} fields`);
    }

    // Strategy 3: Match fields with similar suffix pattern (e.g., "*_cost" for "total_cost")
    if (relatedFields.length === 0 && suffix) {
      relatedFields = attributes.filter(attr =>
        attr.name.endsWith(`_${suffix}`) &&
        attr.name !== fieldName &&
        attr.function !== 'computed' &&
        isNumericField(attr)
      );
      if (relatedFields.length > 0) {
        console.log(`  → Strategy: Matching fields ending with _${suffix}: found ${relatedFields.length} fields`);
      }
    }
    
    if (relatedFields.length > 0) {
      const sum = relatedFields.reduce((acc, attr) => acc + Number(attr.value || 0), 0);
      console.log(`  → Sum of ${relatedFields.length} related fields:`, relatedFields.map(f => f.name));
      console.log(`  → Total = ${sum}`);
      return sum;
    }
    
    // Special case: total_estimated_cost = avg_daily_budget * duration_days
    // Look for multiplication pattern: X * Y
    const budgetAttr = attributes.find(a => 
      a.name.includes('budget') && a.name.includes('daily')
    );
    const durationAttr = attributes.find(a => 
      (a.name.includes('duration') || a.name.includes('days')) && 
      typeof a.value === 'number'
    );
    
    if (budgetAttr && durationAttr) {
      const product = Number(budgetAttr.value || 0) * Number(durationAttr.value || 0);
      console.log(`  → ${budgetAttr.name} (${budgetAttr.value}) × ${durationAttr.name} (${durationAttr.value}) = ${product}`);
      return product;
    }
  }
  
  // Pattern 2: X_percentage = (completed / total) * 100
  // Examples: completion_percentage, progress_percentage
  if (fieldName.includes('percentage') || fieldName.includes('progress')) {
    // Find array attributes with boolean completion fields
    const arrayAttrs = attributes.filter(attr => Array.isArray(attr.value) && attr.value.length > 0);
    
    for (const arrayAttr of arrayAttrs) {
      const items = arrayAttr.value as any[];
      const firstItem = items[0];
      
      if (typeof firstItem === 'object' && firstItem !== null) {
        // Check for boolean completion keys
        const completionKeys = Object.keys(firstItem).filter(key =>
          typeof firstItem[key] === 'boolean' &&
          (key.includes('done') || key.includes('complete') || key.includes('checked') || key.includes('purchased'))
        );
        
        if (completionKeys.length > 0) {
          const completed = items.filter(item => 
            completionKeys.some(key => item[key] === true)
          ).length;
          const percentage = Math.round((completed / items.length) * 100);
          console.log(`  → ${completed}/${items.length} items completed = ${percentage}%`);
          return percentage;
        }
      }
    }
  }
  
  // Pattern 3: remaining_X = total_X - spent_X
  // Examples: remaining_budget
  if (fieldName.includes('remaining')) {
    const suffix = fieldName.replace('remaining_', '');
    const totalAttr = attributes.find(a => a.name === `total_${suffix}`);
    const spentAttr = attributes.find(a => a.name === `spent_${suffix}` || a.name === `used_${suffix}`);
    
    if (totalAttr && spentAttr) {
      const remaining = Number(totalAttr.value || 0) - Number(spentAttr.value || 0);
      console.log(`  → total (${totalAttr.value}) - spent (${spentAttr.value}) = ${remaining}`);
      return remaining;
    }
  }
  
  // Pattern 4: X_per_Y = X / Y
  // Examples: cost_per_guest, price_per_unit, cost_per_day
  if (fieldName.includes('_per_')) {
    const [numeratorPart, denominatorPart] = fieldName.split('_per_');
    
    // Find the numerator (could be total_cost, cost, price, etc.)
    const numeratorAttr = attributes.find(a => 
      (a.name.includes(numeratorPart) || a.name === numeratorPart || a.name === `total_${numeratorPart}` || a.name === `${numeratorPart}_total`) &&
      (a.widget === 'currency' || typeof a.value === 'number') &&
      a.name !== fieldName
    );
    
    // Find the denominator (could be guest_count, guests, quantity, days, etc.)
    const denominatorAttr = attributes.find(a =>
      (a.name.includes(denominatorPart) || a.name === denominatorPart || a.name === `${denominatorPart}_count`) &&
      typeof a.value === 'number' &&
      a.name !== fieldName
    );
    
    if (numeratorAttr && denominatorAttr) {
      const divisor = Number(denominatorAttr.value || 1);
      if (divisor === 0) {
        console.log(`  → Cannot divide by zero (${denominatorAttr.name} = 0)`);
        return 0;
      }
      const result = Math.round(Number(numeratorAttr.value || 0) / divisor);
      console.log(`  → ${numeratorAttr.name} (${numeratorAttr.value}) ÷ ${denominatorAttr.name} (${denominatorAttr.value}) = ${result}`);
      return result;
    }
  }
  
  return null;
}

/**
 * Update computed fields for an entity after an attribute changes
 * This runs on EVERY attribute change to keep all computed fields in sync
 * NOW FULLY DYNAMIC - works for ANY entity type!
 */
export function updateComputedFields(entity: Entity): Entity {
  console.log(`[ComputedFields] Updating computed fields for: ${entity.public_identifier}`);
  
  const updatedEntity = { ...entity };
  const attributes = [...entity.attributes];
  
  // Track if we made any changes
  let hasChanges = false;
  
  // DYNAMIC APPROACH: Find all computed fields and calculate them
  const computedFields = attributes.filter(attr => attr.function === 'computed');
  
  console.log(`[ComputedFields] Found ${computedFields.length} computed fields`);
  
  computedFields.forEach(computedField => {
    const newValue = computeFieldValue(computedField.name, attributes);
    
    // ALWAYS update the value to trigger React re-render
    if (newValue !== null) {
      const oldValue = computedField.value;
      computedField.value = newValue;
      hasChanges = true;  // Always mark as changed to force update
      
      if (oldValue !== newValue) {
        console.log(`[ComputedFields] ✓ Updated ${computedField.name}: ${oldValue} → ${newValue}`);
      } else {
        console.log(`[ComputedFields] ✓ Reapplied ${computedField.name}: ${newValue} (unchanged but refreshed)`);
      }
    }
  });
  
  // ADDITIONAL DYNAMIC PATTERNS (for complex scenarios)
  
  // Pattern: Arrays with cost/budget fields
  const arrayAttrs = attributes.filter(attr => Array.isArray(attr.value) && attr.value.length > 0);
  
  arrayAttrs.forEach(arrayAttr => {
    const items = arrayAttr.value as any[];
    const firstItem = items[0];
    
    if (typeof firstItem === 'object' && firstItem !== null) {
      // Sum all numeric fields in array
      Object.keys(firstItem).forEach(key => {
        if (typeof firstItem[key] === 'number' && 
            (key.includes('cost') || key.includes('budget') || key.includes('price'))) {
          
          const total = items.reduce((sum, item) => sum + Number(item[key] || 0), 0);
          const totalFieldName = `total_${arrayAttr.name}_${key}`;
          const totalField = attributes.find(a => a.name === totalFieldName);
          
          if (totalField && totalField.value !== total) {
            console.log(`[ComputedFields] ✓ Updated ${totalFieldName}: ${totalField.value} → ${total}`);
            totalField.value = total;
            hasChanges = true;
          }
        }
      });
    }
  });

  updatedEntity.attributes = attributes;
  
  if (hasChanges) {
    console.log(`[ComputedFields] ✅ Successfully updated computed fields for ${entity.public_identifier}`);
  } else {
    console.log(`[ComputedFields] No changes needed for ${entity.public_identifier}`);
  }
  
  return updatedEntity;
}

/**
 * Recalculate all computed fields in a data model
 */
export function recalculateDataModel(entities: Entity[]): Entity[] {
  return entities.map(entity => updateComputedFields(entity));
}
