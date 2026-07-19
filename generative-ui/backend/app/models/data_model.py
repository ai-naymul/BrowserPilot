
"""
Enhanced domain models for Jelly-inspired Generative UI Browser.

Key additions:
- Widget types for render hints
- Editable flags for data mutation
- Function roles for UI behavior
- Categories and validation rules
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import uuid4
from enum import Enum

from pydantic import BaseModel, Field


class WidgetType(str, Enum):
    """UI widget types that can render attributes"""
    # Text inputs
    SHORT_TEXT = "short_text"
    LONG_TEXT = "long_text"
    RICH_TEXT = "rich_text"
    
    # Numeric inputs
    NUMBER = "number"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    RATING = "rating"
    SLIDER = "slider"
    
    # Date/Time
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    DATE_RANGE = "date_range"
    
    # Selection
    DROPDOWN = "dropdown"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    MULTI_SELECT = "multi_select"
    TAGS = "tags"
    
    # Location
    LOCATION = "location"
    MAP = "map"
    ADDRESS = "address"
    
    # Media
    IMAGE = "image"
    FILE = "file"
    LINK = "link"
    
    # Special
    COLOR = "color"
    PHONE = "phone"
    EMAIL = "email"
    
    # Display only
    HEADING = "heading"
    LABEL = "label"
    BADGE = "badge"
    PROGRESS = "progress"
    
    # Complex
    ARRAY = "array"
    OBJECT = "object"
    REFERENCE = "reference"


class FunctionRole(str, Enum):
    """Functional role of an attribute"""
    IDENTIFIER = "identifier"          # Unique ID
    PUBLIC_IDENTIFIER = "publicIdentifier"  # Display name/title
    DISPLAY = "display"                # Regular display field
    COMPUTED = "computed"              # Calculated field
    THUMBNAIL = "thumbnail"            # Show in card previews
    SORTABLE = "sortable"             # Can sort by this
    FILTERABLE = "filterable"         # Can filter by this


class Attribute(BaseModel):
    """
    Enhanced attribute with render hints for dynamic UI generation.
    """
    name: str = Field(..., description="The name of the attribute")
    
    data_type: Literal["primitive", "reference", "array", "dict"] = Field(
        ..., 
        description="The type of data this attribute contains"
    )
    
    value: Any = Field(..., description="The actual value of the attribute")
    
    # Render hints
    widget: WidgetType = Field(
        default=WidgetType.SHORT_TEXT,
        description="Widget type for rendering this attribute"
    )
    
    editable: bool = Field(
        default=True,
        description="Whether this field can be edited by user"
    )
    
    function: FunctionRole = Field(
        default=FunctionRole.DISPLAY,
        description="Functional role of this attribute"
    )
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for UI rendering"
    )
    
    # Validation and constraints
    validation: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Validation rules (min, max, pattern, etc.)"
    )
    
    # For dropdowns, radio, etc.
    options: Optional[List[Any]] = Field(
        default=None,
        description="Available options for selection widgets"
    )
    
    # For references to other entities
    ref_entity_type: Optional[str] = Field(
        default=None,
        description="Referenced entity type for reference data_type"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_render_spec(self) -> Dict[str, Any]:
        """Convert to render specification for frontend"""
        spec = {
            "name": self.name,
            "widget": self.widget.value,
            "editable": self.editable,
            "function": self.function.value,
            "value": self.value,
            "data_type": self.data_type
        }
        
        if self.options:
            spec["options"] = self.options
        
        if self.validation:
            spec["validation"] = self.validation
        
        if self.ref_entity_type:
            spec["ref_entity_type"] = self.ref_entity_type
        
        spec.update(self.metadata)
        
        return spec


class Entity(BaseModel):
    """
    Enhanced entity with better attribute management.
    """
    id: str = Field(
        default_factory=lambda: str(uuid4()), 
        description="Unique identifier for the entity"
    )
    
    type: str = Field(
        ..., 
        description="The type/category of the entity"
    )
    
    attributes: List[Attribute] = Field(
        default_factory=list,
        description="List of attributes belonging to this entity"
    )
    
    # Visual presentation
    icon: Optional[str] = Field(
        default=None,
        description="Icon name or emoji for this entity type"
    )
    
    color: Optional[str] = Field(
        default=None,
        description="Color theme for this entity"
    )

    def get_attribute(self, name: str) -> Optional[Attribute]:
        """Get an attribute by name."""
        for attr in self.attributes:
            if attr.name == name:
                return attr
        return None

    def set_attribute(
        self, 
        name: str, 
        value: Any, 
        data_type: str = "primitive",
        widget: WidgetType = WidgetType.SHORT_TEXT,
        editable: bool = True,
        function: FunctionRole = FunctionRole.DISPLAY,
        metadata: Dict[str, Any] = None,
        **kwargs
    ) -> None:
        """Set or update an attribute with full render hints."""
        if metadata is None:
            metadata = {}
        
        # Check if attribute already exists
        existing_attr = self.get_attribute(name)
        if existing_attr:
            existing_attr.value = value
            existing_attr.data_type = data_type
            existing_attr.widget = widget
            existing_attr.editable = editable
            existing_attr.function = function
            existing_attr.metadata.update(metadata)
            
            # Update additional fields if provided
            if kwargs.get('options'):
                existing_attr.options = kwargs['options']
            if kwargs.get('validation'):
                existing_attr.validation = kwargs['validation']
        else:
            new_attr = Attribute(
                name=name,
                data_type=data_type,
                value=value,
                widget=widget,
                editable=editable,
                function=function,
                metadata=metadata,
                options=kwargs.get('options'),
                validation=kwargs.get('validation'),
                ref_entity_type=kwargs.get('ref_entity_type')
            )
            self.attributes.append(new_attr)
    
    def get_public_identifier(self) -> Optional[str]:
        """Get the public identifier (title/name) of this entity"""
        for attr in self.attributes:
            if attr.function == FunctionRole.PUBLIC_IDENTIFIER:
                return str(attr.value)
        
        # Fallback to first attribute
        if self.attributes:
            return str(self.attributes[0].value)
        
        return self.type
    
    def get_thumbnail_attributes(self) -> List[Attribute]:
        """Get attributes suitable for thumbnail/preview display"""
        thumbnails = [attr for attr in self.attributes 
                     if attr.function == FunctionRole.THUMBNAIL]
        
        if not thumbnails:
            # Return first 3 attributes as fallback
            return self.attributes[:3]
        
        return thumbnails

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary representation."""
        return {
            "id": self.id,
            "type": self.type,
            "icon": self.icon,
            "color": self.color,
            "attributes": {attr.name: attr.value for attr in self.attributes}
        }
    
    def to_render_spec(self) -> Dict[str, Any]:
        """Convert to render specification for frontend"""
        return {
            "id": self.id,
            "type": self.type,
            "icon": self.icon,
            "color": self.color,
            "public_identifier": self.get_public_identifier(),
            "attributes": [attr.to_render_spec() for attr in self.attributes]
        }


class DependencyType(str, Enum):
    """Types of dependencies between entities"""
    VALIDATE = "validate"      # Constraint checking
    UPDATE = "update"          # Auto-propagation
    REFERENCE = "reference"    # Simple reference
    COMPUTE = "compute"        # Derived calculation


class Dependency(BaseModel):
    """
    Enhanced relationship between two entities with mechanism.
    """
    source_entity_id: str = Field(..., description="ID of the source entity")
    target_entity_id: str = Field(..., description="ID of the target entity")
    relationship: str = Field(..., description="Type of relationship")
    
    mechanism: DependencyType = Field(
        default=DependencyType.REFERENCE,
        description="How this dependency works"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the relationship"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskDrivenDataModel(BaseModel):
    """
    Enhanced data model with versioning and conversation tracking.
    """
    version: int = Field(
        default=1,
        description="Version number for tracking changes"
    )
    
    task_description: str = Field(
        ..., 
        description="Description of the task this data model serves"
    )
    
    entities: List[Entity] = Field(
        default_factory=list,
        description="List of entities in this data model"
    )
    
    dependencies: List[Dependency] = Field(
        default_factory=list,
        description="List of dependencies between entities"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this data model was created"
    )
    
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this data model was last updated"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the data model"
    )
    
    # Conversation tracking
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="History of user interactions"
    )

    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the data model."""
        self.entities.append(entity)
        self.updated_at = datetime.utcnow()
        self.version += 1

    def remove_entity(self, entity_id: str) -> bool:
        """Remove an entity by ID."""
        initial_count = len(self.entities)
        self.entities = [e for e in self.entities if e.id != entity_id]
        
        if len(self.entities) < initial_count:
            # Also remove dependencies involving this entity
            self.dependencies = [
                d for d in self.dependencies 
                if d.source_entity_id != entity_id and d.target_entity_id != entity_id
            ]
            self.updated_at = datetime.utcnow()
            self.version += 1
            return True
        return False

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID."""
        for entity in self.entities:
            if entity.id == entity_id:
                return entity
        return None

    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Get all entities of a specific type."""
        return [entity for entity in self.entities if entity.type == entity_type]

    def add_dependency(self, dependency: Dependency) -> None:
        """Add a dependency to the data model."""
        self.dependencies.append(dependency)
        self.updated_at = datetime.utcnow()

    def get_dependencies_for_entity(self, entity_id: str) -> List[Dependency]:
        """Get all dependencies involving a specific entity."""
        return [
            dep for dep in self.dependencies
            if dep.source_entity_id == entity_id or dep.target_entity_id == entity_id
        ]

    def get_entity_graph(self) -> Dict[str, List[str]]:
        """Get a graph representation of entity relationships."""
        graph = {}
        for entity in self.entities:
            graph[entity.id] = []
        
        for dep in self.dependencies:
            if dep.source_entity_id in graph:
                graph[dep.source_entity_id].append(dep.target_entity_id)
        
        return graph
    
    def add_conversation_turn(self, user_message: str, assistant_response: str = "") -> None:
        """Add a conversation turn to history"""
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        if assistant_response:
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_response,
                "timestamp": datetime.utcnow().isoformat()
            })

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entire data model to dictionary representation."""
        return {
            "version": self.version,
            "task_description": self.task_description,
            "entities": [entity.to_dict() for entity in self.entities],
            "dependencies": [
                {
                    "source_entity_id": dep.source_entity_id,
                    "target_entity_id": dep.target_entity_id,
                    "relationship": dep.relationship,
                    "mechanism": dep.mechanism.value,
                    "metadata": dep.metadata
                }
                for dep in self.dependencies
            ],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "conversation_history": self.conversation_history
        }
    
    def to_render_spec(self) -> Dict[str, Any]:
        """Convert to render specification for frontend"""
        return {
            "version": self.version,
            "task_description": self.task_description,
            "entities": [entity.to_render_spec() for entity in self.entities],
            "dependencies": [
                {
                    "source_entity_id": dep.source_entity_id,
                    "target_entity_id": dep.target_entity_id,
                    "relationship": dep.relationship,
                    "mechanism": dep.mechanism.value,
                    "metadata": dep.metadata
                }
                for dep in self.dependencies
            ],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# NEW: Component-Based UI Models (for dynamic component generation)
# ============================================================================

class ComponentSpec(BaseModel):
    """
    Specification for a dynamic UI component.
    
    This enables the LLM to generate component-based UIs directly
    instead of relying solely on entity/attribute rendering.
    
    Examples:
        - metric_card: Display key metrics with trends
        - action_button: Interactive buttons that trigger actions
        - line_chart: Time-series data visualization
        - comparison_table: Side-by-side comparisons
    """
    type: str = Field(
        ...,
        description="Component type (e.g., 'metric_card', 'action_button', 'line_chart')"
    )
    
    props: Dict[str, Any] = Field(
        default_factory=dict,
        description="Component properties (flexible dict for any component props)"
    )
    
    children: Optional[List['ComponentSpec']] = Field(
        default=None,
        description="Nested child components (recursive structure)"
    )
    
    key: Optional[str] = Field(
        default=None,
        description="Unique key for React rendering"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LayoutSpec(BaseModel):
    """
    Layout specification for arranging components.
    
    Defines how components should be arranged on the page.
    """
    type: str = Field(
        default="grid",
        description="Layout type (grid, stack, flex)"
    )
    
    columns: Optional[int] = Field(
        default=None,
        description="Number of columns for grid layout"
    )
    
    gap: Optional[int] = Field(
        default=16,
        description="Gap between items in pixels"
    )
    
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional layout configuration"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UIResponse(BaseModel):
    """
    Enhanced UI response that includes both component specs and entities.
    
    This maintains backward compatibility with existing entity-based rendering
    while enabling new component-based dynamic UIs.
    """
    success: bool = Field(
        default=True,
        description="Whether the generation was successful"
    )
    
    components: List[ComponentSpec] = Field(
        default_factory=list,
        description="Component specifications for dynamic rendering"
    )
    
    layout: Optional[LayoutSpec] = Field(
        default=None,
        description="Layout specification for component arrangement"
    )
    
    entities: List[Entity] = Field(
        default_factory=list,
        description="Entity data (for backward compatibility)"
    )
    
    dependencies: List[Dependency] = Field(
        default_factory=list,
        description="Entity dependencies"
    )
    
    task_description: Optional[str] = Field(
        default=None,
        description="Description of the task"
    )
    
    suggested_questions: Optional[List[str]] = Field(
        default=None,
        description="Context-aware follow-up questions"
    )
    
    error: Optional[str] = Field(
        default=None,
        description="Error message if generation failed"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Enable recursive type reference for ComponentSpec.children
ComponentSpec.model_rebuild()
