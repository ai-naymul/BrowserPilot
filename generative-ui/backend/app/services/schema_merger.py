"""
Schema Merger Service for Jelly-inspired UI Browser.

Handles incremental updates to data models:
- Merging new entities with existing ones
- Updating entity attributes
- Managing dependencies
- Maintaining referential integrity
"""

import logging
from typing import Dict, List, Optional, Set
from datetime import datetime

from app.models.data_model import (
    TaskDrivenDataModel, 
    Entity, 
    Dependency,
    Attribute
)

logger = logging.getLogger(__name__)


class SchemaMerger:
    """
    Merges data models incrementally without losing existing data.
    """
    
    def merge_models(
        self,
        existing_model: TaskDrivenDataModel,
        new_model: TaskDrivenDataModel,
        merge_strategy: str = "add"
    ) -> TaskDrivenDataModel:
        """
        Merge two data models.
        
        Args:
            existing_model: Current data model
            new_model: New data model to merge in
            merge_strategy: "add" (add new), "update" (update existing), "replace" (replace all)
            
        Returns:
            Merged TaskDrivenDataModel
        """
        logger.info(f"Merging models with strategy: {merge_strategy}")
        
        if merge_strategy == "replace":
            # Complete replacement
            return new_model
        
        # Create merged model based on existing
        merged = TaskDrivenDataModel(
            version=existing_model.version + 1,
            task_description=existing_model.task_description,
            entities=existing_model.entities.copy(),
            dependencies=existing_model.dependencies.copy(),
            created_at=existing_model.created_at,
            updated_at=datetime.utcnow(),
            metadata=existing_model.metadata.copy(),
            conversation_history=existing_model.conversation_history.copy()
        )
        
        if merge_strategy == "add":
            # Add new entities and dependencies
            merged = self._add_new_entities(merged, new_model)
            merged = self._add_new_dependencies(merged, new_model)
        
        elif merge_strategy == "update":
            # Update existing and add new
            merged = self._update_existing_entities(merged, new_model)
            merged = self._add_new_entities(merged, new_model)
            merged = self._update_dependencies(merged, new_model)
        
        logger.info(f"Merge complete: {len(merged.entities)} entities, {len(merged.dependencies)} dependencies")
        
        return merged
    
    def _add_new_entities(
        self,
        existing_model: TaskDrivenDataModel,
        new_model: TaskDrivenDataModel
    ) -> TaskDrivenDataModel:
        """Add new entities from new_model that don't exist in existing_model."""
        
        # Get existing entity IDs
        existing_ids = {entity.id for entity in existing_model.entities}
        
        # Add new entities
        for new_entity in new_model.entities:
            if new_entity.id not in existing_ids:
                existing_model.entities.append(new_entity)
                logger.debug(f"Added new entity: {new_entity.type} (id: {new_entity.id})")
        
        return existing_model
    
    def _update_existing_entities(
        self,
        existing_model: TaskDrivenDataModel,
        new_model: TaskDrivenDataModel
    ) -> TaskDrivenDataModel:
        """Update existing entities with new data."""
        
        # Create lookup for new entities
        new_entities_by_id = {entity.id: entity for entity in new_model.entities}
        
        # Update matching entities
        for existing_entity in existing_model.entities:
            if existing_entity.id in new_entities_by_id:
                new_entity = new_entities_by_id[existing_entity.id]
                
                # Update attributes
                for new_attr in new_entity.attributes:
                    existing_attr = existing_entity.get_attribute(new_attr.name)
                    
                    if existing_attr:
                        # Update existing attribute
                        existing_attr.value = new_attr.value
                        existing_attr.widget = new_attr.widget
                        existing_attr.editable = new_attr.editable
                        existing_attr.metadata.update(new_attr.metadata)
                    else:
                        # Add new attribute
                        existing_entity.attributes.append(new_attr)
                
                logger.debug(f"Updated entity: {existing_entity.type} (id: {existing_entity.id})")
        
        return existing_model
    
    def _add_new_dependencies(
        self,
        existing_model: TaskDrivenDataModel,
        new_model: TaskDrivenDataModel
    ) -> TaskDrivenDataModel:
        """Add new dependencies from new_model."""
        
        # Create set of existing dependency pairs
        existing_pairs = {
            (dep.source_entity_id, dep.target_entity_id, dep.relationship)
            for dep in existing_model.dependencies
        }
        
        # Add new dependencies
        for new_dep in new_model.dependencies:
            dep_tuple = (new_dep.source_entity_id, new_dep.target_entity_id, new_dep.relationship)
            
            if dep_tuple not in existing_pairs:
                existing_model.dependencies.append(new_dep)
                logger.debug(f"Added dependency: {new_dep.relationship}")
        
        return existing_model
    
    def _update_dependencies(
        self,
        existing_model: TaskDrivenDataModel,
        new_model: TaskDrivenDataModel
    ) -> TaskDrivenDataModel:
        """Update dependencies, removing invalid ones and adding new ones."""
        
        # Get valid entity IDs
        valid_entity_ids = {entity.id for entity in existing_model.entities}
        
        # Remove dependencies with invalid entity references
        existing_model.dependencies = [
            dep for dep in existing_model.dependencies
            if dep.source_entity_id in valid_entity_ids 
            and dep.target_entity_id in valid_entity_ids
        ]
        
        # Add new dependencies
        return self._add_new_dependencies(existing_model, new_model)
    
    def remove_entity_by_criteria(
        self,
        model: TaskDrivenDataModel,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        match_attributes: Optional[Dict[str, any]] = None
    ) -> TaskDrivenDataModel:
        """
        Remove entities matching criteria.
        
        Args:
            model: Data model to modify
            entity_type: Entity type to remove
            entity_id: Specific entity ID to remove
            match_attributes: Dict of attribute name/value pairs to match
            
        Returns:
            Modified TaskDrivenDataModel
        """
        entities_to_remove = []
        
        for entity in model.entities:
            # Check entity ID
            if entity_id and entity.id == entity_id:
                entities_to_remove.append(entity.id)
                continue
            
            # Check entity type
            if entity_type and entity.type != entity_type:
                continue
            
            # Check attributes
            if match_attributes:
                matches = True
                for attr_name, attr_value in match_attributes.items():
                    entity_attr = entity.get_attribute(attr_name)
                    if not entity_attr or entity_attr.value != attr_value:
                        matches = False
                        break
                
                if matches:
                    entities_to_remove.append(entity.id)
        
        # Remove entities
        for entity_id_to_remove in entities_to_remove:
            model.remove_entity(entity_id_to_remove)
            logger.info(f"Removed entity: {entity_id_to_remove}")
        
        return model
    
    def update_entity_attribute(
        self,
        model: TaskDrivenDataModel,
        entity_id: str,
        attribute_name: str,
        new_value: any
    ) -> TaskDrivenDataModel:
        """Update a specific attribute of an entity."""
        
        entity = model.get_entity(entity_id)
        if not entity:
            logger.warning(f"Entity not found: {entity_id}")
            return model
        
        attr = entity.get_attribute(attribute_name)
        if attr:
            attr.value = new_value
            model.updated_at = datetime.utcnow()
            model.version += 1
            logger.info(f"Updated {entity.type}.{attribute_name} = {new_value}")
        else:
            logger.warning(f"Attribute not found: {attribute_name}")
        
        return model
    
    def find_entity_by_name(
        self,
        model: TaskDrivenDataModel,
        name: str,
        entity_type: Optional[str] = None
    ) -> Optional[Entity]:
        """
        Find an entity by its public identifier (name/title).
        
        Args:
            model: Data model to search
            name: Name to search for (case-insensitive)
            entity_type: Optional entity type to filter by
            
        Returns:
            Entity if found, None otherwise
        """
        name_lower = name.lower()
        
        for entity in model.entities:
            if entity_type and entity.type != entity_type:
                continue
            
            # Check public identifier
            public_id = entity.get_public_identifier()
            if public_id and public_id.lower() == name_lower:
                return entity
            
            # Check all attributes for partial match
            for attr in entity.attributes:
                if isinstance(attr.value, str) and name_lower in attr.value.lower():
                    return entity
        
        return None
    
    def get_merge_summary(
        self,
        existing_model: TaskDrivenDataModel,
        new_model: TaskDrivenDataModel
    ) -> Dict[str, any]:
        """
        Get a summary of what would be merged.
        
        Returns:
            Dictionary with merge statistics
        """
        existing_ids = {e.id for e in existing_model.entities}
        new_ids = {e.id for e in new_model.entities}
        
        entities_to_add = new_ids - existing_ids
        entities_to_update = new_ids & existing_ids
        
        return {
            "existing_entities": len(existing_model.entities),
            "new_entities_to_add": len(entities_to_add),
            "entities_to_update": len(entities_to_update),
            "total_after_merge": len(existing_ids | new_ids),
            "existing_dependencies": len(existing_model.dependencies),
            "new_dependencies": len(new_model.dependencies)
        }
