"""
Enhanced UI Generator for Jelly-inspired system.

Generates:
- Task-driven UIs from data models
- Incremental panel updates
- View change specifications
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import uuid4

from app.models.data_model import TaskDrivenDataModel, Entity, Dependency
from app.models.ui_spec import (
    UISpecification,
    UIPanel,
    PanelType,
    create_summary_panel,
    create_card_grid_panel,
    create_table_panel,
    create_graph_panel,
    create_chart_panel
)

logger = logging.getLogger(__name__)


class UIGenerator:
    """
    Enhanced UI generator with support for incremental updates.
    """
    
    def generate_task_ui(
        self,
        data_model: TaskDrivenDataModel,
        suggested_views: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate complete UI for a task-driven data model.
        
        Args:
            data_model: Task-driven data model
            suggested_views: Optional suggested views per entity type
            
        Returns:
            UI specification dict
        """
        logger.info(f"Generating task UI for: {data_model.task_description}")
        
        ui_spec = UISpecification()
        
        # Group entities by type
        entities_by_type = {}
        for entity in data_model.entities:
            if entity.type not in entities_by_type:
                entities_by_type[entity.type] = []
            entities_by_type[entity.type].append(entity)
        
        row = 0
        
        # Create summary panel at top
        summary_panel = self._create_summary_panel(
            data_model=data_model,
            row=row,
            col=0,
            col_span=12
        )
        ui_spec.add_panel(summary_panel)
        row += 1
        
        # Create panels for each entity type
        for entity_type, entities in entities_by_type.items():
            # Determine best view type
            view_types = suggested_views.get(entity_type, ["cards"]) if suggested_views else ["cards"]
            primary_view = view_types[0] if view_types else "cards"
            
            # Generate panel based on view type
            panel = self._create_entity_panel(
                entities=entities,
                entity_type=entity_type,
                view_type=primary_view,
                row=row,
                col=0,
                available_views=view_types
            )
            
            if panel:
                ui_spec.add_panel(panel)
                row += 1
        
        # Add relationships panel if dependencies exist
        if data_model.dependencies:
            graph_panel = create_graph_panel(
                title="Relationships",
                entity_ids=[e.id for e in data_model.entities],
                position={"row": row, "col": 0},
                size={"col_span": 12, "row_span": 2}
            )
            ui_spec.add_panel(graph_panel)
        
        result = ui_spec.to_dict()
        result["available_views"] = suggested_views or {}
        
        return result
    
    def generate_incremental_ui(
        self,
        new_entities: List[Entity],
        new_dependencies: List[Dependency],
        suggested_views: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate UI specification for only new entities.
        
        Args:
            new_entities: Newly added entities
            new_dependencies: Newly added dependencies
            suggested_views: Suggested views for new entity types
            
        Returns:
            Incremental UI specification with only new panels
        """
        logger.info(f"Generating incremental UI for {len(new_entities)} new entities")
        
        # Group new entities by type
        entities_by_type = {}
        for entity in new_entities:
            if entity.type not in entities_by_type:
                entities_by_type[entity.type] = []
            entities_by_type[entity.type].append(entity)
        
        new_panels = []
        
        # Create panels for each new entity type
        for entity_type, entities in entities_by_type.items():
            view_types = suggested_views.get(entity_type, ["cards"]) if suggested_views else ["cards"]
            primary_view = view_types[0]
            
            panel = self._create_entity_panel(
                entities=entities,
                entity_type=entity_type,
                view_type=primary_view,
                row=0,  # Frontend will position it
                col=0,
                available_views=view_types
            )
            
            if panel:
                new_panels.append(panel.to_dict())
        
        return {
            "panels": new_panels,
            "available_views": suggested_views or {}
        }
    
    def generate_view_change_spec(
        self,
        entities: List[Entity],
        view_type: str
    ) -> Dict[str, Any]:
        """
        Generate UI spec for changing view type of existing entities.
        
        Args:
            entities: Entities to display
            view_type: New view type (table, map, cards, list)
            
        Returns:
            UI specification for new view
        """
        logger.info(f"Generating view change to: {view_type}")
        
        if not entities:
            return {"panels": []}
        
        entity_type = entities[0].type
        
        panel = self._create_entity_panel(
            entities=entities,
            entity_type=entity_type,
            view_type=view_type,
            row=0,
            col=0,
            available_views=[view_type]
        )
        
        return {
            "panels": [panel.to_dict()] if panel else [],
            "replace_panel_type": entity_type  # Signal to replace existing panel
        }
    
    def _create_summary_panel(
        self,
        data_model: TaskDrivenDataModel,
        row: int,
        col: int,
        col_span: int
    ) -> UIPanel:
        """Create summary panel for task overview."""
        
        panel = UIPanel(
            id=str(uuid4()),
            title=data_model.task_description,
            panel_type=PanelType.SUMMARY,
            entity_ids=[e.id for e in data_model.entities[:5]],  # First 5
            layout={
                "grid_area": f"{row} / {col} / {row + 1} / {col + col_span}",
                "col_span": col_span,
                "row_span": 1,
                "row": row,
                "col": col
            },
            config={
                "show_key_points": True,
                "highlight_important": True,
                "include_metadata": True
            }
        )
        
        return panel
    
    def _create_entity_panel(
        self,
        entities: List[Entity],
        entity_type: str,
        view_type: str,
        row: int,
        col: int,
        available_views: List[str]
    ) -> Optional[UIPanel]:
        """
        Create panel for entity display based on view type.
        
        Args:
            entities: Entities to display
            entity_type: Type of entities
            view_type: How to display (table, cards, map, list, form)
            row: Grid row position
            col: Grid column position
            available_views: Available view options
            
        Returns:
            UIPanel or None
        """
        if not entities:
            return None
        
        entity_ids = [e.id for e in entities]
        title = f"{entity_type}s" if len(entities) > 1 else entity_type
        
        # Determine grid span based on view type
        col_span = 12
        row_span = 2
        
        if view_type == "form":
            col_span = 6
            row_span = 3
        elif view_type in ["table", "map"]:
            col_span = 12
            row_span = 2
        elif view_type == "cards":
            col_span = 12
            row_span = 2
        
        panel_id = str(uuid4())
        
        # Map view type to panel type
        panel_type_map = {
            "table": PanelType.TABLE,
            "cards": PanelType.CARD_GRID,
            "list": PanelType.CARD_GRID,
            "map": PanelType.CHART,  # Placeholder
            "form": PanelType.CARD_GRID,
            "graph": PanelType.GRAPH,
            "chart": PanelType.CHART
        }
        
        panel_type = panel_type_map.get(view_type, PanelType.CARD_GRID)
        
        # Create config based on view type
        config = {
            "view_type": view_type,
            "available_views": available_views
        }
        
        if view_type == "table":
            config.update({
                "sortable": True,
                "filterable": True,
                "pagination": True,
                "page_size": 10
            })
        elif view_type in ["cards", "list"]:
            config.update({
                "columns": 3 if view_type == "cards" else 1,
                "card_size": "medium",
                "show_images": True,
                "show_metadata": True
            })
        elif view_type == "form":
            config.update({
                "layout": "vertical",
                "show_labels": True,
                "editable": True
            })
        
        panel = UIPanel(
            id=panel_id,
            title=title,
            panel_type=panel_type,
            entity_ids=entity_ids,
            layout={
                "grid_area": f"{row} / {col} / {row + row_span} / {col + col_span}",
                "col_span": col_span,
                "row_span": row_span,
                "row": row,
                "col": col
            },
            config=config,
            metadata={
                "entity_type": entity_type,
                "count": len(entities)
            }
        )
        
        return panel
    
    def generate_ui_spec(self, data_model: TaskDrivenDataModel) -> UISpecification:
        """
        Legacy method for backward compatibility.
        Generates complete UI specification from data model.
        """
        logger.info(f"Generating UI spec (legacy method)")
        
        ui_spec = UISpecification()
        
        # Group entities
        entities_by_type = {}
        for entity in data_model.entities:
            if entity.type not in entities_by_type:
                entities_by_type[entity.type] = []
            entities_by_type[entity.type].append(entity)
        
        row = 0
        
        # Summary
        if data_model.entities:
            summary = create_summary_panel(
                title="Overview",
                entity_ids=[e.id for e in data_model.entities[:10]],
                position={"row": row, "col": 0},
                size={"col_span": 12, "row_span": 1}
            )
            ui_spec.add_panel(summary)
            row += 1
        
        # Entity panels
        for entity_type, entities in entities_by_type.items():
            # Card grid
            card_panel = create_card_grid_panel(
                title=entity_type,
                entity_ids=[e.id for e in entities],
                columns=3,
                position={"row": row, "col": 0},
                size={"col_span": 8, "row_span": 2}
            )
            ui_spec.add_panel(card_panel)
            
            # Table
            table_panel = create_table_panel(
                title=f"{entity_type} Table",
                entity_ids=[e.id for e in entities],
                position={"row": row, "col": 8},
                size={"col_span": 4, "row_span": 2}
            )
            ui_spec.add_panel(table_panel)
            
            row += 2
        
        # Graph
        if data_model.dependencies:
            graph = create_graph_panel(
                title="Relationships",
                entity_ids=[e.id for e in data_model.entities],
                position={"row": row, "col": 0},
                size={"col_span": 12, "row_span": 2}
            )
            ui_spec.add_panel(graph)
        
        return ui_spec
