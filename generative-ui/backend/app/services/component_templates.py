"""
Component Template System

Provides default templates and validation for all UI components.
Used as fallbacks when LLM output is invalid or missing.
"""

from typing import Dict, Any, List, Optional
from pydantic import ValidationError
import logging

from app.models.data_model import ComponentSpec

logger = logging.getLogger(__name__)

# Component Template Registry
# Templates must match TypeScript interfaces exactly
COMPONENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "metric_card": {
        "label": "Metric",
        "value": "0",
        "sublabel": None,
        "trend": None,
        "icon": None,
        "onClick": None,
    },
    "action_button": {
        "label": "Action",
        "onClick": {"type": "refine_query", "params": {"query": ""}},
        "variant": "primary",
        "icon": None,
        "iconPosition": "left",
        "loading": False,
        "disabled": False,
    },
    "line_chart": {
        "data": [],
        "lines": [],
        "xAxisLabel": None,
        "yAxisLabel": None,
        "height": 300,
        "showGrid": True,
        "showLegend": True,
    },
    "area_chart": {
        "data": [],
        "lines": [],
        "chartType": "area",
        "xAxisLabel": None,
        "yAxisLabel": None,
        "height": 300,
        "showGrid": True,
        "showLegend": True,
    },
    "pie_chart": {
        "data": [],
        "chartType": "pie",
        "nameKey": "name",
        "valueKey": "value",
        "height": 300,
        "showLegend": True,
    },
    "scatter_chart": {
        "data": [],
        "lines": [],
        "chartType": "scatter",
        "xAxisLabel": None,
        "yAxisLabel": None,
        "height": 300,
        "showGrid": True,
    },
    "bar_chart": {
        "data": [],
        "bars": [],
        "xAxisLabel": None,
        "yAxisLabel": None,
        "height": 300,
        "horizontal": False,
        "showValues": False,
    },
    "comparison_table": {
        "data": [],
        "columns": [],
        "highlightBest": False,
        "onRowClick": None,
    },
    "data_grid": {
        "data": [],
        "columns": [],
        "sortable": True,
        "filterable": True,
        "pagination": True,
        "pageSize": 10,
        "editable": False,
        "exportable": True,
    },
    "map": {
        "locations": [],
        "zoom": 10,
        "center": None,
        "height": 400,
    },
    "expandable_section": {
        "title": "Section",
        "children": [],
        "defaultExpanded": False,
        "badge": None,
    },
    "news_highlight": {
        "items": [],
        "maxItems": 5,
        "showMoreLink": False,
    },
}

# Required props for each component
REQUIRED_PROPS: Dict[str, List[str]] = {
    "metric_card": ["label", "value"],
    "action_button": ["label", "onClick"],
    "line_chart": ["data", "lines"],
    "area_chart": ["data", "lines"],
    "pie_chart": ["data"],
    "scatter_chart": ["data", "lines"],
    "bar_chart": ["data", "bars"],
    "comparison_table": ["data", "columns"],
    "data_grid": ["data", "columns"],
    "map": ["locations"],
    "expandable_section": ["title"],
    "news_highlight": ["items"],
}


def generate_component_from_data(
    data: Dict[str, Any],
    template_type: str,
    component_key: Optional[str] = None
) -> ComponentSpec:
    """
    Generate a ComponentSpec from data using templates.
    
    Args:
        data: Dictionary with component data
        template_type: Component type (e.g., "metric_card")
        component_key: Optional unique key for the component
        
    Returns:
        ComponentSpec with props populated from data
        
    Raises:
        ValueError: If template_type is not registered
    """
    if template_type not in COMPONENT_TEMPLATES:
        raise ValueError(
            f"Unknown component type: {template_type}. "
            f"Available types: {list(COMPONENT_TEMPLATES.keys())}"
        )
    
    # Start with template defaults
    template = COMPONENT_TEMPLATES[template_type].copy()
    
    # Merge data into template
    props = {**template, **data}
    
    # Handle type conversions
    props = _convert_types(props, template_type)
    
    # Validate required props
    _validate_required_props(props, template_type)
    
    # Create component spec
    return ComponentSpec(
        type=template_type,
        props=props,
        key=component_key or f"{template_type}_{id(data)}",
    )


def _convert_types(props: Dict[str, Any], template_type: str) -> Dict[str, Any]:
    """
    Convert prop types to match expected types.
    
    Handles common conversions:
    - String numbers to actual numbers
    - String booleans to actual booleans
    - Nested object conversions
    """
    converted = props.copy()
    
    # Number conversions
    number_props = {
        "line_chart": ["height"],
        "area_chart": ["height"],
        "pie_chart": ["height"],
        "scatter_chart": ["height"],
        "bar_chart": ["height"],
        "map": ["zoom", "height"],
        "data_grid": ["pageSize"],
        "news_highlight": ["maxItems"],
    }
    
    if template_type in number_props:
        for prop in number_props[template_type]:
            if prop in converted and isinstance(converted[prop], str):
                try:
                    converted[prop] = int(converted[prop])
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert {prop} to number: {converted[prop]}")
    
    # Boolean conversions
    boolean_props = {
        "line_chart": ["showGrid", "showLegend"],
        "area_chart": ["showGrid", "showLegend"],
        "scatter_chart": ["showGrid"],
        "bar_chart": ["horizontal", "showValues"],
        "comparison_table": ["highlightBest"],
        "data_grid": ["sortable", "filterable", "pagination", "editable", "exportable"],
        "expandable_section": ["defaultExpanded"],
        "news_highlight": ["showMoreLink"],
        "action_button": ["loading", "disabled"],
    }
    
    if template_type in boolean_props:
        for prop in boolean_props[template_type]:
            if prop in converted and isinstance(converted[prop], str):
                converted[prop] = converted[prop].lower() in ('true', '1', 'yes')
    
    # Ensure arrays are arrays
    array_props = {
        "line_chart": ["data", "lines"],
        "area_chart": ["data", "lines"],
        "pie_chart": ["data"],
        "scatter_chart": ["data", "lines"],
        "bar_chart": ["data", "bars"],
        "comparison_table": ["data", "columns"],
        "data_grid": ["data", "columns"],
        "map": ["locations"],
        "news_highlight": ["items"],
        "expandable_section": ["children"],
    }
    
    if template_type in array_props:
        for prop in array_props[template_type]:
            if prop in converted and not isinstance(converted[prop], list):
                if converted[prop] is None:
                    converted[prop] = []
                else:
                    converted[prop] = [converted[prop]]
    
    return converted


def _validate_required_props(props: Dict[str, Any], template_type: str) -> None:
    """
    Validate that all required props are present and non-empty.
    
    Raises:
        ValueError: If required props are missing
    """
    required = REQUIRED_PROPS.get(template_type, [])
    missing = []
    
    for prop in required:
        if prop not in props:
            missing.append(prop)
        elif props[prop] is None:
            missing.append(f"{prop} (is None)")
        elif isinstance(props[prop], (list, dict, str)) and not props[prop]:
            missing.append(f"{prop} (is empty)")
    
    if missing:
        raise ValueError(
            f"Component '{template_type}' missing required props: {', '.join(missing)}"
        )


def validate_component_spec(spec: Dict[str, Any]) -> Optional[str]:
    """
    Validate a component spec dictionary.
    
    Args:
        spec: Component specification dictionary
        
    Returns:
        Error message if invalid, None if valid
    """
    # Check type exists
    if "type" not in spec:
        return "Component spec missing 'type' field"
    
    component_type = spec["type"]
    
    # Check type is registered
    if component_type not in COMPONENT_TEMPLATES:
        return f"Unknown component type: {component_type}"
    
    # Check props exist
    if "props" not in spec:
        return f"Component spec missing 'props' field"
    
    # Validate required props
    props = spec["props"]
    required = REQUIRED_PROPS.get(component_type, [])
    
    for prop in required:
        if prop not in props:
            return f"Component '{component_type}' missing required prop: {prop}"
        
        # Check non-empty for collections
        if isinstance(props[prop], (list, dict, str)) and not props[prop]:
            return f"Component '{component_type}' has empty required prop: {prop}"
    
    return None


def create_fallback_component(
    component_type: str,
    error_message: str,
    data: Optional[Dict[str, Any]] = None
) -> ComponentSpec:
    """
    Create a fallback component when generation fails.
    
    Shows an error state with helpful information.
    """
    logger.warning(f"Creating fallback for {component_type}: {error_message}")
    
    # Create error display component
    return ComponentSpec(
        type="text",
        props={
            "children": f"⚠️ Error generating {component_type}: {error_message}",
            "className": "text-destructive bg-destructive/10 p-4 rounded-lg border border-destructive/20"
        },
        key=f"error_{component_type}_{id(data)}"
    )


def generate_components_from_list(
    components_data: List[Dict[str, Any]]
) -> List[ComponentSpec]:
    """
    Generate multiple components from a list of data dictionaries.
    
    Validates each component and creates fallbacks for invalid ones.
    """
    results = []
    
    for idx, comp_data in enumerate(components_data):
        try:
            # Check if it's already a valid component spec
            if "type" in comp_data and "props" in comp_data:
                error = validate_component_spec(comp_data)
                if error:
                    logger.warning(f"Component {idx} validation failed: {error}")
                    results.append(create_fallback_component(
                        comp_data.get("type", "unknown"),
                        error,
                        comp_data
                    ))
                else:
                    results.append(ComponentSpec(**comp_data))
            else:
                # Assume it needs template generation
                component_type = comp_data.pop("type", "metric_card")
                comp = generate_component_from_data(
                    comp_data,
                    component_type,
                    comp_data.get("key", f"comp_{idx}")
                )
                results.append(comp)
                
        except Exception as e:
            logger.error(f"Error generating component {idx}: {str(e)}")
            results.append(create_fallback_component(
                comp_data.get("type", "unknown"),
                str(e),
                comp_data
            ))
    
    return results
