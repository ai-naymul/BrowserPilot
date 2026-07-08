"""
UI Specification models for the Generative UI Browser.

This module defines the structure and configuration for generated user interfaces,
enabling flexible and dynamic UI generation based on data models and task requirements.

The models support:
- Multiple panel types for different data visualizations
- Flexible layout configurations
- Entity-based content organization
- Theme and styling specifications
"""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class PanelType(str, Enum):
    """
    Enumeration of available panel types for UI generation.
    
    Each panel type is optimized for displaying specific types of data
    and relationships in the most effective way.
    """
    SUMMARY = "summary"           # Text summary with key insights
    LIST = "list"                 # Simple list of items
    CARD_GRID = "card_grid"       # Grid of cards for entities
    TABLE = "table"               # Tabular data display
    CHART = "chart"               # Data visualization charts
    GRAPH = "graph"               # Network/relationship graphs
    MAP = "map"                   # Geographic or conceptual maps


class UIPanel(BaseModel):
    """
    Represents a single UI panel with its configuration and content.
    
    Panels are the building blocks of the generated interface, each
    responsible for displaying specific entities and their relationships.
    """
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for the panel")
    title: str = Field(..., description="Display title for the panel")
    panel_type: PanelType = Field(..., description="Type of panel to render")
    entity_ids: List[str] = Field(
        default_factory=list,
        description="List of entity IDs to display in this panel"
    )
    layout: Dict[str, Any] = Field(
        default_factory=dict,
        description="Layout configuration (position, size, etc.)"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Panel-specific configuration (sorting, filtering, etc.)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the panel"
    )

    def add_entity(self, entity_id: str) -> None:
        """Add an entity ID to this panel."""
        if entity_id not in self.entity_ids:
            self.entity_ids.append(entity_id)

    def remove_entity(self, entity_id: str) -> None:
        """Remove an entity ID from this panel."""
        if entity_id in self.entity_ids:
            self.entity_ids.remove(entity_id)

    def set_layout(self, position: Dict[str, int] = None, size: Dict[str, int] = None, **kwargs) -> None:
        """Set layout configuration for the panel."""
        if position:
            self.layout["position"] = position
        if size:
            self.layout["size"] = size
        
        # Add any additional layout properties
        for key, value in kwargs.items():
            self.layout[key] = value

    def set_config(self, **kwargs) -> None:
        """Set configuration options for the panel."""
        self.config.update(kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert panel to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "panel_type": self.panel_type.value,
            "entity_ids": self.entity_ids,
            "layout": self.layout,
            "config": self.config,
            "metadata": self.metadata
        }


class UISpecification(BaseModel):
    """
    Complete UI specification that defines the entire generated interface.
    
    This is the top-level model that brings together all panels, layout
    configuration, and theming to create a cohesive user interface.
    """
    panels: List[UIPanel] = Field(
        default_factory=list,
        description="List of panels in the UI"
    )
    layout_mode: Literal["grid", "flex", "masonry"] = Field(
        default="grid",
        description="Layout mode for arranging panels"
    )
    theme: Dict[str, Any] = Field(
        default_factory=dict,
        description="Theme configuration for styling"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the UI specification"
    )

    def add_panel(self, panel: UIPanel) -> None:
        """Add a panel to the UI specification."""
        self.panels.append(panel)

    def get_panel(self, panel_id: str) -> Optional[UIPanel]:
        """Get a panel by ID."""
        for panel in self.panels:
            if panel.id == panel_id:
                return panel
        return None

    def get_panels_by_type(self, panel_type: PanelType) -> List[UIPanel]:
        """Get all panels of a specific type."""
        return [panel for panel in self.panels if panel.panel_type == panel_type]

    def remove_panel(self, panel_id: str) -> bool:
        """Remove a panel by ID. Returns True if removed, False if not found."""
        for i, panel in enumerate(self.panels):
            if panel.id == panel_id:
                del self.panels[i]
                return True
        return False

    def set_theme(self, **kwargs) -> None:
        """Set theme configuration."""
        self.theme.update(kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert UI specification to dictionary representation."""
        return {
            "panels": [panel.to_dict() for panel in self.panels],
            "layout_mode": self.layout_mode,
            "theme": self.theme,
            "metadata": self.metadata
        }


# Factory functions for common panel types
def create_summary_panel(
    title: str,
    entity_ids: List[str],
    position: Dict[str, int] = None,
    size: Dict[str, int] = None
) -> UIPanel:
    """Create a summary panel for displaying key insights."""
    panel = UIPanel(
        title=title,
        panel_type=PanelType.SUMMARY,
        entity_ids=entity_ids
    )
    
    if position:
        panel.set_layout(position=position)
    if size:
        panel.set_layout(size=size)
    
    panel.set_config(
        max_length=500,
        show_key_points=True,
        highlight_important=True
    )
    
    return panel


def create_list_panel(
    title: str,
    entity_ids: List[str],
    sort_by: str = None,
    filter_by: str = None,
    position: Dict[str, int] = None,
    size: Dict[str, int] = None
) -> UIPanel:
    """Create a list panel for displaying entities in a list format."""
    panel = UIPanel(
        title=title,
        panel_type=PanelType.LIST,
        entity_ids=entity_ids
    )
    
    if position:
        panel.set_layout(position=position)
    if size:
        panel.set_layout(size=size)
    
    config = {}
    if sort_by:
        config["sort_by"] = sort_by
    if filter_by:
        config["filter_by"] = filter_by
    
    panel.set_config(**config)
    
    return panel


def create_card_grid_panel(
    title: str,
    entity_ids: List[str],
    columns: int = 3,
    card_size: str = "medium",
    position: Dict[str, int] = None,
    size: Dict[str, int] = None
) -> UIPanel:
    """Create a card grid panel for displaying entities as cards."""
    panel = UIPanel(
        title=title,
        panel_type=PanelType.CARD_GRID,
        entity_ids=entity_ids
    )
    
    if position:
        panel.set_layout(position=position)
    if size:
        panel.set_layout(size=size)
    
    panel.set_config(
        columns=columns,
        card_size=card_size,
        show_images=True,
        show_metadata=True
    )
    
    return panel


def create_table_panel(
    title: str,
    entity_ids: List[str],
    columns: List[str] = None,
    sortable: bool = True,
    filterable: bool = True,
    position: Dict[str, int] = None,
    size: Dict[str, int] = None
) -> UIPanel:
    """Create a table panel for displaying entities in tabular format."""
    panel = UIPanel(
        title=title,
        panel_type=PanelType.TABLE,
        entity_ids=entity_ids
    )
    
    if position:
        panel.set_layout(position=position)
    if size:
        panel.set_layout(size=size)
    
    config = {
        "sortable": sortable,
        "filterable": filterable,
        "pagination": True,
        "page_size": 10
    }
    
    if columns:
        config["columns"] = columns
    
    panel.set_config(**config)
    
    return panel


def create_chart_panel(
    title: str,
    entity_ids: List[str],
    chart_type: str = "bar",
    x_axis: str = None,
    y_axis: str = None,
    position: Dict[str, int] = None,
    size: Dict[str, int] = None
) -> UIPanel:
    """Create a chart panel for data visualization."""
    panel = UIPanel(
        title=title,
        panel_type=PanelType.CHART,
        entity_ids=entity_ids
    )
    
    if position:
        panel.set_layout(position=position)
    if size:
        panel.set_layout(size=size)
    
    config = {
        "chart_type": chart_type,
        "interactive": True,
        "show_legend": True,
        "show_tooltips": True
    }
    
    if x_axis:
        config["x_axis"] = x_axis
    if y_axis:
        config["y_axis"] = y_axis
    
    panel.set_config(**config)
    
    return panel


def create_graph_panel(
    title: str,
    entity_ids: List[str],
    layout_algorithm: str = "force",
    show_labels: bool = True,
    interactive: bool = True,
    position: Dict[str, int] = None,
    size: Dict[str, int] = None
) -> UIPanel:
    """Create a graph panel for displaying entity relationships."""
    panel = UIPanel(
        title=title,
        panel_type=PanelType.GRAPH,
        entity_ids=entity_ids
    )
    
    if position:
        panel.set_layout(position=position)
    if size:
        panel.set_layout(size=size)
    
    panel.set_config(
        layout_algorithm=layout_algorithm,
        show_labels=show_labels,
        interactive=interactive,
        show_edge_weights=True,
        node_size="auto"
    )
    
    return panel


def create_map_panel(
    title: str,
    entity_ids: List[str],
    map_type: str = "geographic",
    show_markers: bool = True,
    interactive: bool = True,
    position: Dict[str, int] = None,
    size: Dict[str, int] = None
) -> UIPanel:
    """Create a map panel for geographic or conceptual mapping."""
    panel = UIPanel(
        title=title,
        panel_type=PanelType.MAP,
        entity_ids=entity_ids
    )
    
    if position:
        panel.set_layout(position=position)
    if size:
        panel.set_layout(size=size)
    
    panel.set_config(
        map_type=map_type,
        show_markers=show_markers,
        interactive=interactive,
        zoom_controls=True,
        show_scale=True
    )
    
    return panel


# Theme presets
def get_dark_theme() -> Dict[str, Any]:
    """Get a dark theme configuration."""
    return {
        "colors": {
            "primary": "#3b82f6",
            "secondary": "#a855f7",
            "accent": "#10b981",
            "background": "#0a0a0a",
            "foreground": "#ededed",
            "muted": "#6b7280"
        },
        "typography": {
            "font_family": "system-ui, sans-serif",
            "heading_size": "lg",
            "body_size": "base"
        },
        "spacing": {
            "panel_padding": "1rem",
            "panel_margin": "0.5rem",
            "grid_gap": "1rem"
        }
    }


def get_light_theme() -> Dict[str, Any]:
    """Get a light theme configuration."""
    return {
        "colors": {
            "primary": "#2563eb",
            "secondary": "#7c3aed",
            "accent": "#059669",
            "background": "#ffffff",
            "foreground": "#1f2937",
            "muted": "#6b7280"
        },
        "typography": {
            "font_family": "system-ui, sans-serif",
            "heading_size": "lg",
            "body_size": "base"
        },
        "spacing": {
            "panel_padding": "1rem",
            "panel_margin": "0.5rem",
            "grid_gap": "1rem"
        }
    }


def get_scientific_theme() -> Dict[str, Any]:
    """Get a scientific/academic theme configuration."""
    return {
        "colors": {
            "primary": "#1e40af",
            "secondary": "#7c2d12",
            "accent": "#059669",
            "background": "#f8fafc",
            "foreground": "#1e293b",
            "muted": "#64748b"
        },
        "typography": {
            "font_family": "Georgia, serif",
            "heading_size": "xl",
            "body_size": "sm"
        },
        "spacing": {
            "panel_padding": "1.5rem",
            "panel_margin": "1rem",
            "grid_gap": "1.5rem"
        }
    }
