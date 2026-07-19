"""
Enhanced Prompt Templates for Jelly-inspired UI Generation.

Generates:
- Render hints for dynamic UI
- Task-driven data models
- Incremental updates
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# Widget type mapping for LLM reference
WIDGET_TYPES_REFERENCE = """
AVAILABLE WIDGET TYPES:

Text Inputs:
- short_text: Single-line text input
- long_text: Multi-line textarea
- rich_text: Rich text editor

Numeric:
- number: Number input
- currency: Currency input with formatting
- percentage: Percentage input
- rating: Star/numeric rating (1-10)
- slider: Slider with min/max

Date/Time:
- date: Date picker
- time: Time picker
- datetime: Date and time picker
- date_range: Start and end date picker

Selection:
- dropdown: Dropdown select
- radio: Radio buttons
- checkbox: Single checkbox
- multi_select: Multiple selection
- tags: Tag input with autocomplete

Location:
- location: Location input with autocomplete
- map: Map display
- address: Structured address input

Media:
- image: Image upload/display
- file: File upload
- link: URL input

Special:
- color: Color picker
- phone: Phone number input
- email: Email input

Display:
- heading: Large heading text
- label: Small label text
- badge: Badge/tag display
- progress: Progress bar

Complex:
- array: Array of items
- object: Nested object
- reference: Reference to another entity
"""


FUNCTION_ROLES_REFERENCE = """
FUNCTION ROLES:

- identifier: Unique ID (hidden from user)
- publicIdentifier: Main name/title (shown prominently)
- display: Regular display field
- computed: Calculated/derived field (read-only)
- thumbnail: Show in card previews and summaries
- sortable: Can be used for sorting
- filterable: Can be used for filtering
"""


# ============================================================================
# NEW: Component Library Documentation (for dynamic UI generation)
# ============================================================================

COMPONENT_LIBRARY_REFERENCE = """
DYNAMIC COMPONENT LIBRARY:

You can now generate dynamic UI components directly! These components are more
interactive and visually appealing than basic entity attributes.

**Available Components:**

1. **metric_card** - Display key metrics with trends
   Props:
   - label: string (e.g., "Revenue")
   - value: string | number (e.g., "$130.5B" or 130500000000)
   - sublabel?: string (e.g., "FY2025 Revenue")
   - trend?: {direction: "up" | "down", value: number} (e.g., {direction: "up", value: 23.4})
   - icon?: string (lucide icon name like "DollarSign", "TrendingUp")
   - onClick?: {type: string, params: object} (action to trigger)

2. **action_button** - Interactive buttons that trigger actions
   Props:
   - label: string (e.g., "Open latest NVDA filing")
   - onClick: {type: string, params: object} (REQUIRED - see Action Types below)
   - variant?: "primary" | "secondary" | "ghost" (default: "primary")
   - icon?: string (lucide icon name)
   - iconPosition?: "left" | "right"
   - loading?: boolean
   - disabled?: boolean

3. **line_chart** - Time-series line chart
   Props:
   - data: Array<{[key: string]: any}> (e.g., [{quarter: "Q1", revenue: 26.0}, ...])
   - lines: Array<{dataKey: string, name: string, color?: string}>
   - xAxisLabel?: string
   - yAxisLabel?: string
   - height?: number (default: 300)
   - formatValue?: string (e.g., "${{value}}B")

4. **bar_chart** - Bar chart for comparisons
   Props:
   - data: Array<{label: string, [key: string]: any}>
   - bars: Array<{dataKey: string, name: string, color?: string}>
   - xAxisLabel?: string
   - yAxisLabel?: string
   - height?: number (default: 300)
   - horizontal?: boolean
   - showValues?: boolean
   - formatValue?: string

5. **comparison_table** - Side-by-side comparison table
   Props:
   - data: Array<{id: string, [key: string]: any}>
   - columns: string[] (column keys to display)
   - highlightBest?: boolean (highlight best values in each row)
   - onRowClick?: {type: string, params: object}

6. **expandable_section** - Collapsible content section
   Props:
   - title: string | ReactNode
   - children: ComponentSpec[] (nested components)
   - defaultExpanded?: boolean
   - badge?: string | number

7. **news_highlight** - Display news items
   Props:
   - items: Array<{
       id: string,
       headline: string,
       source: string,
       date: string (ISO format),
       url?: string,
       icon?: string
     }>
   - maxItems?: number (default: 5)
   - showMoreLink?: boolean

8. **area_chart** - Area chart for trends with filled regions
   Props:
   - data: Array<{x: string, [key: string]: any}> (e.g., [{x: "Jan", value: 100}, ...])
   - lines: Array<{dataKey: string, name: string, color?: string}>
   - xAxisLabel?: string
   - yAxisLabel?: string
   - height?: number (default: 300)
   - showGrid?: boolean (default: true)

9. **pie_chart** - Pie chart for proportions and distributions
   Props:
   - data: Array<{name: string, value: number}> (e.g., [{name: "Product A", value: 45}, ...])
   - nameKey?: string (default: "name")
   - valueKey?: string (default: "value")
   - height?: number (default: 300)
   - showLegend?: boolean (default: true)

10. **scatter_chart** - Scatter plot for correlations
    Props:
    - data: Array<{x: number, y: number, [key: string]: any}>
    - lines: Array<{dataKey: string, name: string, color?: string}>
    - xAxisLabel?: string
    - yAxisLabel?: string
    - height?: number (default: 300)

11. **map** - Interactive map with location markers
    Props:
    - locations: Array<{
        id: string,
        lat: number,
        lng: number,
        label: string,
        description?: string,
        color?: string
      }>
    - zoom?: number (default: 10)
    - center?: {lat: number, lng: number} (defaults to first location)
    - height?: number (default: 400)
    
12. **data_grid** - Advanced data table with sorting, filtering, pagination
    Props:
    - data: Array<object> (rows of data)
    - columns: Array<{header: string, accessorKey: string}> (column definitions)
    - sortable?: boolean (default: true)
    - filterable?: boolean (default: true)
    - pagination?: boolean (default: true)
    - pageSize?: number (default: 10)
    - editable?: boolean (default: false)
    - exportable?: boolean (default: true)
    - onChange?: {type: string, params: object} (for cell edits)

**Action Types (for onClick props):**

Actions are serializable objects that trigger backend operations:

- {type: "fetch_data", params: {source: "sec_filing", ticker: "NVDA"}}
- {type: "refine_query", params: {query: "Show detailed breakdown"}}
- {type: "expand_card", params: {entityId: "company_nvda"}}
- {type: "add_entity", params: {template: "competitor_analysis"}}
- {type: "open_url", params: {url: "https://..."}}

**Component Examples:**

Example 1: Stock Metrics Dashboard
{
  "components": [
    {
      "type": "metric_card",
      "props": {
        "label": "Revenue",
        "value": "$130.5B",
        "sublabel": "FY2025 Revenue",
        "trend": {"direction": "up", "value": 23.4},
        "icon": "DollarSign"
      }
    },
    {
      "type": "action_button",
      "props": {
        "label": "Open latest NVDA filing",
        "onClick": {"type": "fetch_data", "params": {"source": "sec_filing", "ticker": "NVDA"}},
        "variant": "primary",
        "icon": "FileText"
      }
    },
    {
      "type": "line_chart",
      "props": {
        "data": [
          {"quarter": "Q1 2024", "revenue": 26.0, "profit": 8.2},
          {"quarter": "Q2 2024", "revenue": 30.0, "profit": 9.5},
          {"quarter": "Q3 2024", "revenue": 35.1, "profit": 11.3},
          {"quarter": "Q4 2024", "revenue": 39.4, "profit": 13.1}
        ],
        "lines": [
          {"dataKey": "revenue", "name": "Revenue", "color": "#3b82f6"},
          {"dataKey": "profit", "name": "Profit", "color": "#10b981"}
        ],
        "xAxisLabel": "Quarter",
        "yAxisLabel": "$ Billions",
        "height": 350
      }
    }
  ],
  "layout": {
    "type": "grid",
    "columns": 3,
    "gap": 16
  }
}

Example 2: Comparison with Nested Components
{
  "components": [
    {
      "type": "expandable_section",
      "props": {
        "title": "Financial Comparison",
        "defaultExpanded": true,
        "badge": "New"
      },
      "children": [
        {
          "type": "comparison_table",
          "props": {
            "data": [
              {"id": "nvda", "company": "NVIDIA", "revenue": 46.7, "margin": 72.5},
              {"id": "amd", "company": "AMD", "revenue": 6.5, "margin": 50.0}
            ],
            "columns": ["company", "revenue", "margin"],
            "highlightBest": true
          }
        }
      ]
    }
  ]
}

**CRITICAL: When to Use Components vs Entities**

Use COMPONENTS when:
- User wants visual comparison (charts, tables)
- Interactive actions needed (buttons, expandable sections)
- Financial/metric dashboards
- Data visualization required

Use ENTITIES when:
- User wants to edit data
- Form-like input needed
- Simple list/card display sufficient
- Backward compatibility required

You can generate BOTH components[] and entities[] in the same response!
"""


ACTION_SYSTEM_REFERENCE = """
ACTION SYSTEM:

Actions enable interactive buttons and dynamic data fetching.

**Action Structure:**
{
  "type": string,      // Action type identifier
  "params": object     // Action-specific parameters
}

**Available Action Types:**

1. fetch_data - Fetch new data from external sources
   Params: {source: string, ticker?: string, url?: string, query?: string}
   Example: {type: "fetch_data", params: {source: "sec_filing", ticker: "NVDA"}}

2. refine_query - Trigger follow-up query
   Params: {query: string}
   Example: {type: "refine_query", params: {query: "Show detailed breakdown"}}

3. expand_card - Expand entity details
   Params: {entityId: string}
   Example: {type: "expand_card", params: {entityId: "company_nvda"}}

4. add_entity - Add new entity to data model
   Params: {template: string, data?: object}
   Example: {type: "add_entity", params: {template: "competitor", data: {name: "Intel"}}}

5. open_url - Open external URL
   Params: {url: string}
   Example: {type: "open_url", params: {url: "https://investor.nvidia.com"}}

**IMPORTANT:**
- Actions must be JSON-serializable (no functions!)
- Always include type and params
- Params should contain all necessary data
- Use descriptive action types

**SUGGESTED ACTIONS FOR ACTION DOCK:**

You should ALWAYS include a "suggested_actions" array in your response to populate
the ActionDock - a persistent action bar at the top of the UI.

Format:
{
  "suggested_actions": [
    {
      "label": "User-facing action label",
      "query": "Optional: refine query to execute",
      "icon": "Optional: lucide icon name (sparkles, trending, zap, etc.)"
    }
  ]
}

Guidelines for suggested_actions:
1. **Context-aware**: Base actions on current entities and user task
   - For destinations: "Find flights", "Check weather", "Book hotels"
   - For stocks: "Show earnings", "Compare sectors", "Add watchlist"
   - For projects: "Add task", "Set deadline", "Assign team"

2. **Progressive disclosure**: Start simple, add complexity through actions
   - Initial: High-level actions ("Find hotels")
   - After refine: More specific actions ("Compare 5-star hotels in downtown")

3. **Domain-agnostic**: Never hardcode travel/finance-specific actions
   - Use entity types to infer relevant actions
   - If entities have "location" → suggest map/directions
   - If entities have "price" → suggest budget analysis

4. **Icon selection**:
   - sparkles: AI/smart suggestions
   - trending: Analytics/trends
   - zap: Quick actions
   - search: Find/explore more
   - file: Documents/details
   - plus: Add new items

5. **Quantity**: Provide 3-5 suggested actions per response

Examples:

For "Compare Tokyo, Paris, Barcelona":
{
  "suggested_actions": [
    {"label": "Find flights", "query": "Show flight options with prices and dates", "icon": "sparkles"},
    {"label": "Check weather", "query": "Show weather patterns and best time to visit", "icon": "trending"},
    {"label": "Explore attractions", "query": "Show top attractions and activities", "icon": "search"}
  ]
}

For "Analyze NVIDIA stock":
{
  "suggested_actions": [
    {"label": "Show earnings", "query": "Display quarterly earnings breakdown", "icon": "trending"},
    {"label": "Compare competitors", "query": "Compare with AMD and Intel", "icon": "sparkles"},
    {"label": "Recent news", "query": "Show latest NVIDIA news and analyst ratings", "icon": "file"}
  ]
}

For "Plan dinner party":
{
  "suggested_actions": [
    {"label": "Guest list", "query": "Create guest list with dietary restrictions", "icon": "plus"},
    {"label": "Menu ideas", "query": "Suggest menu based on preferences", "icon": "sparkles"},
    {"label": "Shopping list", "query": "Generate shopping list with quantities", "icon": "file"}
  ]
}

**WHEN TO EMIT suggested_actions:**
- Initial task creation: Always include 3-5 high-level next steps
- After refine: Update with new context-aware actions
- Never leave empty - always suggest logical next actions based on current state
"""


# REMOVED: Manual scenario detection - LLM is smart enough to understand context
# The LLM will naturally create appropriate entity structures based on user input


def get_data_grounded_prompt(rows: list, question: str, source: str = "") -> str:
    """
    Prompt for rendering a dashboard GROUNDED on real, externally-provided data.

    Unlike get_task_creation_prompt (which synthesizes data from an intent), this
    instructs the model to visualize ONLY the rows provided and never invent
    values. It reuses the same component/widget catalog so output matches the
    renderer, and bakes in the renderer's strict prop rules.
    """
    import json as _json
    data_json = _json.dumps(rows, ensure_ascii=False, indent=2)
    source_line = f"\nDATA SOURCE: {source}" if source else ""

    return f"""You are an expert at turning REAL structured data into a dynamic dashboard UI.

USER QUESTION: "{question}"{source_line}

You are given REAL data rows (scraped from the web). Build the best dashboard to
answer the user's question USING ONLY THIS DATA.

DATA ROWS (JSON):
{data_json}

🚨 GROUNDING RULES — MUST FOLLOW:
1. USE ONLY the values present in the data rows above. NEVER invent, guess, estimate, or add data not present.
2. If a value is missing for a row, omit it — do not fabricate.
3. Choose components that best answer the question (comparisons -> comparison_table + bar_chart; key numbers -> metric_card; geographic -> map).
4. Map each data column to an appropriate entity attribute (with the right widget) and/or component field.
5. Preserve exact names, prices, ratings, and URLs from the data.

COMPONENT PROP RULES (the renderer is strict — follow EXACTLY or components render blank):
- bar_chart: every object in "data" MUST include a "label" field (the category shown on the axis) plus the numeric key(s). "bars" is a list of {{"dataKey": "<numeric_key>", "name": "<legend label>"}}.
- comparison_table: every row in "data" MUST include a unique "id"; cells must be REAL non-empty values (never null, "N/A", or empty). "columns" is either ["col1","col2"] or a list of {{"key": "...", "label": "..."}}.
- metric_card: props are {{"label": "...", "value": "..."}}; the value must come from the data.
- For any location/address, include a "coordinates" object attribute {{"lat": <num>, "lng": <num>}} when the coordinates are known.

{WIDGET_TYPES_REFERENCE}

{FUNCTION_ROLES_REFERENCE}

{COMPONENT_LIBRARY_REFERENCE}

{ACTION_SYSTEM_REFERENCE}

OUTPUT FORMAT — return ONLY a single valid JSON object (no prose, no code fences):
{{
  "task_description": "<one line describing the dashboard>",
  "entities": [ /* optional: one per data row when the row is an inspectable item; each has id, type, public_identifier, and attributes:[{{"name","value","widget","function"}}] */ ],
  "components": [ /* charts / tables / metric cards per the COMPONENT LIBRARY and the prop rules above */ ],
  "layout": {{"type": "grid", "columns": 2, "gap": 16}}
}}

Return BOTH entities (for detail/metric/map rendering) AND components (for charts/tables) when useful. The output MUST be a single valid JSON object."""


def get_task_creation_prompt(user_input: str, web_context: str = "") -> str:
    """
    Enhanced prompt for creating a NEW task-driven data model from scratch.
    
    The LLM intelligently determines entity structure based on user input.
    Example: "I'm moving to San Francisco"
    Example: "Compare Tokyo, Barcelona, and Bali for a 2-week trip"
    """
    
    # Add web context section if provided (FULL CONTEXT, NO TRUNCATION)
    web_context_section = ""
    if web_context:
        web_context_section = f"""

🌐 REAL-WORLD WEB DATA (USE THIS!):
{web_context}

IMPORTANT: Use the real-world data above to create accurate, specific entities with actual names, prices, and details from the web. DO NOT create placeholder or generic data when real data is available.
"""
    
    return f"""You are an expert at creating task-driven data models for dynamic UI generation.

USER INTENT: "{user_input}"
{web_context_section}

Your task is to create a comprehensive data model that helps the user accomplish their goal.

🎯 INTELLIGENT ENTITY GENERATION:
Analyze the user's intent and create appropriate entities automatically:

**For Comparisons** (e.g., "Compare Tokyo, Barcelona, Bali"):
- Create entities with comparable attributes
- Include quantitative metrics (costs, ratings, times)
- Add location data with COORDINATES: {{"lat": 35.6762, "lng": 139.6503}}
- Calculate totals/aggregates in computed fields
- Use entity types like "Destination_[Name]" or "Offer_[Company]"

**For Locations** (any entity with city/address):
- Create TWO separate attributes:
  1. "location" attribute (string) - Human-readable address
  2. "coordinates" attribute (object) - Lat/lng for mapping
- Example structure:
  {{"name": "location", "value": "Tokyo, Japan", "widget": "location"}},
  {{"name": "coordinates", "value": {{"lat": 35.6762, "lng": 139.6503}}, "widget": "object"}}
- Include specific coordinates for venues, not just city centers
- If you don't know exact coordinates, use approximate city/region center
- The system will refine coordinates automatically if needed

**For Travel Destinations** (Tokyo, Barcelona, Bali, etc.):
- ALWAYS include a "top_attractions" array attribute
- Each attraction MUST be an OBJECT with name, description, AND coordinates
- Example structure:
  {{
    "name": "top_attractions",
    "data_type": "array",
    "value": [
      {{
        "name": "Senso-ji Temple",
        "description": "Ancient Buddhist temple in Asakusa district, Tokyo's oldest temple",
        "coordinates": {{"lat": 35.7148, "lng": 139.7967}}
      }},
      {{
        "name": "Shibuya Crossing",
        "description": "World's busiest pedestrian crossing, iconic Tokyo landmark",
        "coordinates": {{"lat": 35.6595, "lng": 139.7004}}
      }}
    ],
    "widget": "array",
    "function": "display"
  }}
- Include 5-8 attractions per destination
- Use real coordinates for actual landmarks
- NEVER use simple string arrays - always use objects with coordinates

**For Financial Comparisons** (jobs, purchases, investments):
- Include all cost breakdown components
- Create computed total fields
- Use realistic 2025 market rates
- Calculate ROI, hourly rates, or comparisons

**For Ratings** (safety, culture, food quality, etc.):
- Include rating value (0-10 scale)
- ALWAYS add a separate reasoning attribute: append "_reasoning" to the rating name
- Reasoning should explain WHY that rating was given
- Include specific factors, not generic statements
- Example:
  {{"name": "safety_rating", "value": 9.5, "widget": "rating"}},
  {{"name": "safety_rating_reasoning", "value": "Tokyo ranks as one of the world's safest cities with extremely low crime rates, 24/7 police presence, and excellent emergency services. Solo travelers report feeling very safe at all hours.", "widget": "short_text"}}

🚨 CRITICAL RULES - MUST FOLLOW:
1. **NO PLACEHOLDER DATA**: Never use generic values like "Enter location", "TBD", "Not set", empty strings, or 0 for important fields
2. **USE REAL CONTEXT**: If the user mentions a specific location (e.g., "San Francisco"), use actual neighborhood names, real price ranges, and authentic details
3. **MEANINGFUL DEFAULTS**: Every field should have a sensible default value based on the context
4. **RICH COMPARISONS**: For comparison scenarios, create 3-5 entities minimum to enable meaningful evaluation
5. **ACTIONABLE ENTITIES**: Create entities that represent things the user can interact with
6. **CALCULATE TOTALS**: For financial/numeric comparisons, always include computed total fields

IMPORTANT PRINCIPLES:
1. Focus on TASK COMPLETION, not just information display
2. Create entities that represent ACTIONABLE items (plans, decisions, tasks, etc.)
3. Include entities for TOOLS the user needs (calculators, planners, trackers)
4. Think about what the user needs to DO, not just what they want to KNOW
5. Start SIMPLE - Add complexity through follow-ups, not all at once

{WIDGET_TYPES_REFERENCE}

{FUNCTION_ROLES_REFERENCE}

{COMPONENT_LIBRARY_REFERENCE}

{ACTION_SYSTEM_REFERENCE}

OUTPUT FORMAT - Return valid JSON with BOTH components and entities:

**ENHANCED OUTPUT STRUCTURE:**
You can now generate BOTH component-based UIs AND entity data in a single response!

- Use "components" for rich visualizations (charts, metrics, comparisons)
- Use "entities" for editable data and form inputs
- Include "layout" to specify how components are arranged
- ALWAYS include "suggested_actions" for ActionDock (3-5 context-aware next steps)
{{
    "task_description": "Clear description of what the user is trying to accomplish",
    "entities": [
        {{
            "id": "unique_id_1",
            "type": "EntityType",  // e.g., "Moving_Plan", "Budget", "Checklist"
            "icon": "📦",  // Emoji or icon name
            "color": "#3b82f6",  // Hex color
            "attributes": [
                {{
                    "name": "attribute_name",
                    "data_type": "primitive" | "reference" | "array" | "dict",
                    "value": <initial_value>,
                    "widget": "<widget_type_from_list>",
                    "editable": true | false,
                    "function": "<function_role_from_list>",
                    "metadata": {{
                        "placeholder": "Optional placeholder text",
                        "help_text": "Optional help text"
                    }},
                    "options": ["option1", "option2"],  // For dropdowns, etc.
                    "validation": {{
                        "min": 0,
                        "max": 100,
                        "required": true
                    }}
                }}
            ]
        }}
    ],
    "dependencies": [
        {{
            "source_entity_id": "entity_1_id",
            "target_entity_id": "entity_2_id",
            "relationship": "relationship_type",
            "mechanism": "validate" | "update" | "reference" | "compute",
            "metadata": {{}}
        }}
    ],
    "suggested_views": {{
        "entity_type_name": ["table", "map", "cards", "list"]
    }},
    "components": [
        {{
            "type": "component_type",  // e.g., "metric_card", "action_button", "line_chart"
            "props": {{
                // Component-specific props
            }},
            "children": [],  // Optional nested components
            "key": "unique_key"  // Optional React key
        }}
    ],
    "layout": {{
        "type": "grid",  // or "stack", "flex"
        "columns": 3,    // For grid layouts
        "gap": 16        // Gap in pixels
    }},
    "suggested_actions": [
        {{
            "label": "Action label",
            "query": "Refine query to execute",
            "icon": "sparkles"  // lucide icon name
        }}
    ]
}}

EXAMPLE - For "I'm moving to San Francisco":
{{
    "task_description": "Plan and manage relocation to San Francisco",
    "entities": [
        {{
            "id": "moving_plan_1",
            "type": "Moving_Plan",
            "icon": "🚚",
            "color": "#3b82f6",
            "attributes": [
                {{
                    "name": "destination",
                    "data_type": "primitive",
                    "value": "San Francisco, CA",
                    "widget": "location",
                    "editable": true,
                    "function": "publicIdentifier",
                    "metadata": {{"help_text": "Your destination city"}}
                }},
                {{
                    "name": "move_date",
                    "data_type": "primitive",
                    "value": null,
                    "widget": "date",
                    "editable": true,
                    "function": "display",
                    "validation": {{"required": true}}
                }},
                {{
                    "name": "budget",
                    "data_type": "primitive",
                    "value": 0,
                    "widget": "currency",
                    "editable": true,
                    "function": "display"
                }},
                {{
                    "name": "status",
                    "data_type": "primitive",
                    "value": "planning",
                    "widget": "dropdown",
                    "editable": true,
                    "function": "display",
                    "options": ["planning", "in_progress", "completed"]
                }}
            ]
        }},
        {{
            "id": "checklist_1",
            "type": "Checklist",
            "icon": "✅",
            "color": "#10b981",
            "attributes": [
                {{
                    "name": "tasks",
                    "data_type": "array",
                    "value": [
                        {{"task": "Find apartment", "done": false}},
                        {{"task": "Book movers", "done": false}},
                        {{"task": "Update address", "done": false}}
                    ],
                    "widget": "array",
                    "editable": true,
                    "function": "display"
                }}
            ]
        }}
    ],
    "dependencies": [
        {{
            "source_entity_id": "moving_plan_1",
            "target_entity_id": "checklist_1",
            "relationship": "manages",
            "mechanism": "reference"
        }}
    ],
    "suggested_views": {{
        "Moving_Plan": ["form"],
        "Checklist": ["list", "table"]
    }},
    "suggested_actions": [
        {{"label": "Find apartments", "query": "Show available apartments in San Francisco with prices", "icon": "search"}},
        {{"label": "Calculate costs", "query": "Break down moving costs and budget", "icon": "trending"}},
        {{"label": "Plan timeline", "query": "Create moving timeline with key dates", "icon": "sparkles"}}
    ]
}}

EXAMPLE - For "Compare NVIDIA, AMD, and Broadcom stocks":
{{
    "task_description": "Compare tech semiconductor stocks with financial analysis",
    "components": [
        {{
            "type": "metric_card",
            "props": {{
                "label": "NVIDIA Revenue",
                "value": "$130.5B",
                "sublabel": "FY2025",
                "trend": {{"direction": "up", "value": 265.3}},
                "icon": "DollarSign"
            }},
            "key": "metric-nvda-revenue"
        }},
        {{
            "type": "action_button",
            "props": {{
                "label": "Open latest NVDA filing",
                "onClick": {{"type": "fetch_data", "params": {{"source": "sec_filing", "ticker": "NVDA"}}}},
                "variant": "primary",
                "icon": "FileText"
            }},
            "key": "action-nvda-filing"
        }},
        {{
            "type": "comparison_table",
            "props": {{
                "data": [
                    {{"id": "nvda", "company": "NVIDIA", "revenue": "46.7B", "margin": "72.5%", "valuation": "40x"}},
                    {{"id": "amd", "company": "AMD", "revenue": "6.5B", "margin": "50%", "valuation": "35x"}},
                    {{"id": "avgo", "company": "Broadcom", "revenue": "13B", "margin": "70%", "valuation": "28x"}}
                ],
                "columns": ["company", "revenue", "margin", "valuation"],
                "highlightBest": true
            }},
            "key": "comparison-table"
        }}
    ],
    "layout": {{
        "type": "grid",
        "columns": 3,
        "gap": 16
    }},
    "entities": [
        {{
            "id": "stock_nvda",
            "type": "Stock",
            "icon": "💹",
            "color": "#10b981",
            "attributes": [
                {{"name": "ticker", "value": "NVDA", "widget": "short_text", "function": "publicIdentifier"}},
                {{"name": "company_name", "value": "NVIDIA Corporation", "widget": "short_text"}},
                {{"name": "revenue", "value": 130500000000, "widget": "currency", "editable": true}}
            ]
        }}
    ],
    "dependencies": [],
    "suggested_views": {{"Stock": ["table", "cards"]}},
    "suggested_actions": [
        {{"label": "Show earnings", "query": "Display quarterly earnings breakdown with charts", "icon": "trending"}},
        {{"label": "Compare competitors", "query": "Add AMD and Intel for comparison", "icon": "sparkles"}},
        {{"label": "Recent news", "query": "Show latest NVIDIA news and analyst ratings", "icon": "file"}},
        {{"label": "Price targets", "query": "Show analyst price targets and recommendations", "icon": "zap"}}
    ]
}}

Now create a data model for: "{user_input}"

Remember:
- For comparison/analysis tasks, use COMPONENTS (charts, metrics, tables)
- For data entry/editing tasks, use ENTITIES (forms, inputs)
- You can mix both in the same response!
- Create ACTIONABLE entities (plans, budgets, checklists, calculators)
- Use appropriate widgets for each field type
- Set initial values where appropriate
- Make fields editable where users should be able to change them
- Use publicIdentifier for main names/titles
- Include helpful metadata

**CRITICAL UI RULES:**
1. ALWAYS include "suggested_actions" array (3-5 actions) for the ActionDock
   - Make actions context-aware based on current entities (see examples above)
   - Use appropriate icons: sparkles, trending, search, zap, file, plus
   - Each action needs: label (user-facing), query (what to execute), icon (optional)
2. ALWAYS generate 3-5 action_button components at the END of the components array
   - Actions should be contextual follow-ups (e.g., "Add another item", "Show more details", "Compare X and Y")
   - Use appropriate onClick types: "refine_query", "fetch_data", "expand_card", "add_entity"
3. ALWAYS wrap comparison_table components inside expandable_section for better UX
   - Set defaultExpanded: true for the first table
   - Use descriptive titles like "Destination Comparison" or "Cost Breakdown"
4. When users request weather/time info, create separate entities (type: "BestTimeToVisit" or "WeatherInfo")
   - Do NOT modify existing destination entities
   - Link new entities to destinations via dependencies

Return ONLY the JSON, no additional text."""


def get_information_addition_prompt(
    user_input: str,
    existing_model: Dict,
    conversation_history: List[Dict[str, str]]
) -> str:
    """
    Prompt for ADDING new entities to existing model.
    
    Used when user wants to expand the current model.
    Example: "Tell me about different neighborhoods"
    """
    
    # Format conversation history - show recent turns (last 10 to balance context vs tokens)
    history_text = ""
    if conversation_history:
        recent_turns = conversation_history[-10:]  # Last 10 turns for context
        history_text = "\n".join([
            f"{turn['role'].upper()}: {turn['content']}"
            for turn in recent_turns
        ])
        if len(conversation_history) > 10:
            history_text = f"Recent conversation (last 10 of {len(conversation_history)} turns):\n{history_text}"
        else:
            history_text = f"Conversation history ({len(conversation_history)} turns):\n{history_text}"
    
    return f"""You are adding new information to an existing task-driven data model.

CURRENT DATA MODEL:
Task: {existing_model.get('task_description', 'N/A')}

Existing Entities:
{_format_entities_summary(existing_model.get('entities', []))}

CONVERSATION HISTORY:
{history_text if history_text else "No prior conversation"}

USER REQUEST: "{user_input}"

{WIDGET_TYPES_REFERENCE}

{FUNCTION_ROLES_REFERENCE}

CRITICAL: MATCH THE EXISTING ENTITY STRUCTURE EXACTLY!
- Use the SAME attribute names as the reference entity
- Use the SAME widget types (e.g., if reference uses "currency", you use "currency")  
- Use the SAME data format (e.g., if coordinates are strings "lat, lng", use strings)
- Use the SAME level of detail (if reference has 20+ attributes, you should too)
- Maintain CONSISTENCY in naming (e.g., "accommodation cost" not "accommodation_cost")

Your task:
1. Understand what NEW information the user wants
2. Create NEW entities matching the REFERENCE ENTITY structure shown above
3. DO NOT modify or remove existing entities
4. Create dependencies between new and existing entities where appropriate
5. Ensure new entities are COMPATIBLE with existing ones for comparison

CRITICAL: Each new entity MUST have a COMPLETE attributes array!
- DO NOT return entities with empty attributes: []
- REPLICATE the full attribute list from the reference entity
- Change only the VALUES, keep structure identical

🚨 EXAMPLE OF CORRECT OUTPUT (for Destination entity):
If reference entity has 20+ attributes (city_name, country, location, coordinates, 
trip_duration, accommodation_cost, food_cost, etc.), your new entity MUST also have 
ALL 20+ attributes with the SAME names, widgets, and data types!

OUTPUT FORMAT - Return valid JSON:
{{
    "new_entities": [
        {{
            "id": "unique_id",
            "type": "EntityType",
            "icon": "📍",
            "color": "#f59e0b",
            "attributes": [
                {{
                    "name": "city_name",
                    "data_type": "primitive",
                    "value": "Tokyo",
                    "widget": "short_text",
                    "editable": false,
                    "function": "publicIdentifier"
                }},
                {{
                    "name": "country",
                    "data_type": "primitive",
                    "value": "Japan",
                    "widget": "short_text",
                    "editable": false,
                    "function": "display"
                }},
                {{
                    "name": "location",
                    "data_type": "primitive",
                    "value": "Tokyo, Japan",
                    "widget": "location",
                    "editable": false,
                    "function": "display"
                }}
                ...CONTINUE WITH ALL OTHER ATTRIBUTES FROM REFERENCE...
            ]
        }}
    ],
    "new_dependencies": [
        {{
            "source_entity_id": "existing_or_new_entity_id",
            "target_entity_id": "new_entity_id",
            "relationship": "relationship_type",
            "mechanism": "reference"
        }}
    ],
    "suggested_views": {{
        "new_entity_type": ["table", "map", "cards"]
    }}
}}

EXAMPLE - For "tell me about different neighborhoods" when moving to SF:
{{
    "new_entities": [
        {{
            "id": "neighborhood_1",
            "type": "Neighborhood",
            "icon": "🏘️",
            "color": "#a855f7",
            "attributes": [
                {{
                    "name": "name",
                    "data_type": "primitive",
                    "value": "Mission District",
                    "widget": "heading",
                    "editable": false,
                    "function": "publicIdentifier"
                }},
                {{
                    "name": "avg_rent",
                    "data_type": "primitive",
                    "value": 3200,
                    "widget": "currency",
                    "editable": false,
                    "function": "display"
                }},
                {{
                    "name": "safety_score",
                    "data_type": "primitive",
                    "value": 7,
                    "widget": "rating",
                    "editable": false,
                    "function": "display",
                    "validation": {{"min": 1, "max": 10}}
                }},
                {{
                    "name": "commute_time",
                    "data_type": "primitive",
                    "value": 25,
                    "widget": "number",
                    "editable": false,
                    "function": "display",
                    "metadata": {{"unit": "minutes"}}
                }},
                {{
                    "name": "location",
                    "data_type": "primitive",
                    "value": {{"lat": 37.7599, "lng": -122.4148}},
                    "widget": "location",
                    "editable": false,
                    "function": "display"
                }}
            ]
        }}
        // ... more neighborhoods
    ],
    "new_dependencies": [
        {{
            "source_entity_id": "moving_plan_1",
            "target_entity_id": "neighborhood_1",
            "relationship": "evaluating",
            "mechanism": "reference"
        }}
    ],
    "suggested_views": {{
        "Neighborhood": ["map", "table", "cards"]
    }}
}}

Now create NEW entities for: "{user_input}"

🚨 FINAL CHECKLIST BEFORE RETURNING JSON:
✓ Did I copy ALL attributes from the reference entity? (Not just 3-4, but ALL of them!)
✓ Are my attribute names EXACTLY the same as reference?
✓ Are my widget types EXACTLY the same as reference?
✓ Is my "attributes" array populated with data (not empty [])?
✓ Did I include coordinates for location-based entities?
✓ Did I include all cost breakdowns for financial entities?
✓ Did I include all ratings with reasoning for comparison entities?

Important:
- Return ONLY new entities, not existing ones
- Create multiple instances of the same entity type if appropriate
- Use realistic data values
- Set appropriate widgets for each attribute
- Include location data if relevant to the request
- NEVER return entities with empty attributes arrays

Return ONLY the JSON, no additional text."""


def get_url_analysis_prompt(
    scraped_content: Dict[str, any],
    additional_context: Optional[str] = None
) -> str:
    """
    Prompt for analyzing a URL and creating a data model.
    
    Enhanced with render hints.
    """
    
    content = scraped_content.get('content', '')[:4000]  # Limit content
    title = scraped_content.get('title', 'Untitled')
    url = scraped_content.get('url', '')
    
    context_section = ""
    if additional_context:
        context_section = f"\nADDITIONAL CONTEXT: {additional_context}\n"
    
    return f"""You are analyzing web content and creating a task-driven data model.

URL: {url}
TITLE: {title}
{context_section}
CONTENT:
{content}

{WIDGET_TYPES_REFERENCE}

{FUNCTION_ROLES_REFERENCE}

Analyze this content and create a data model that:
1. Extracts key entities (people, organizations, concepts, products, etc.)
2. Captures relationships between entities
3. Provides appropriate widgets for each attribute
4. Organizes information in a useful way

OUTPUT FORMAT - Return valid JSON:
{{
    "task_description": "Brief description of what this content is about",
    "entities": [
        {{
            "id": "entity_id",
            "type": "EntityType",
            "icon": "📄",
            "color": "#3b82f6",
            "attributes": [
                {{
                    "name": "attribute_name",
                    "data_type": "primitive",
                    "value": <value>,
                    "widget": "<widget_type>",
                    "editable": false,
                    "function": "display"
                }}
            ]
        }}
    ],
    "dependencies": [
        {{
            "source_entity_id": "entity_1",
            "target_entity_id": "entity_2",
            "relationship": "relationship",
            "mechanism": "reference"
        }}
    ],
    "suggested_views": {{
        "EntityType": ["table", "cards"]
    }}
}}

Return ONLY the JSON, no additional text."""


def _format_entities_summary(entities: List[Dict]) -> str:
    """Format entities - FULL first entity, summarized others to avoid token limits."""
    if not entities:
        return "No entities yet"
    
    lines = []
    lines.append("=" * 80)
    lines.append("REFERENCE ENTITY STRUCTURE (REPLICATE THIS EXACTLY FOR NEW ENTITIES)")
    lines.append("=" * 80)
    lines.append("")
    
    # Show FULL FIRST entity as the reference template
    if entities and len(entities) > 0:
        first_entity = entities[0]
        lines.append(f"Type: {first_entity.get('type', 'Unknown')}")
        lines.append(f"ID: {first_entity.get('id', 'unknown')}")
        lines.append(f"Public Identifier: {first_entity.get('public_identifier', 'N/A')}")
        lines.append(f"Icon: {first_entity.get('icon', 'N/A')}")
        lines.append(f"Color: {first_entity.get('color', 'N/A')}")
        lines.append("")
        lines.append("COMPLETE ATTRIBUTE LIST (replicate this structure):")
        
        attrs = first_entity.get('attributes', [])
        if isinstance(attrs, list):
            for attr_idx, attr in enumerate(attrs):
                if isinstance(attr, dict):
                    value = attr.get('value')
                    # Smart value truncation - be aggressive to avoid token overload
                    if isinstance(value, dict):
                        value_repr = f"dict(keys: {', '.join(list(value.keys())[:3])})"
                    elif isinstance(value, list):
                        if len(value) > 0 and isinstance(value[0], dict):
                            # Show structure of first array item only
                            first_keys = list(value[0].keys()) if value else []
                            value_repr = f"array[{len(value)}] of dicts with keys: {', '.join(first_keys[:4])}"
                        else:
                            value_repr = f"array[{len(value)}]"
                    elif isinstance(value, str) and len(value) > 50:
                        value_repr = value[:50] + "..."
                    else:
                        value_repr = str(value)[:100]  # Hard limit
                    
                    lines.append(f"  [{attr_idx + 1}] name: '{attr.get('name')}'")
                    lines.append(f"      widget: '{attr.get('widget')}'")
                    lines.append(f"      data_type: '{attr.get('data_type')}'")
                    lines.append(f"      function: '{attr.get('function')}'")
                    lines.append(f"      editable: {attr.get('editable', False)}")
                    lines.append(f"      value_example: {value_repr}")
                    if attr.get('help_text'):
                        lines.append(f"      help_text: {attr.get('help_text')}")
                    lines.append("")
        
        lines.append(f"Total attributes in reference: {len(attrs) if isinstance(attrs, list) else 0}")
        lines.append("")
    
    # Show other entities in SUMMARY form (just counts and key fields)
    if len(entities) > 1:
        lines.append("=" * 80)
        lines.append(f"OTHER EXISTING ENTITIES ({len(entities) - 1} more):")
        lines.append("=" * 80)
        for idx, entity in enumerate(entities[1:], start=2):
            attrs = entity.get('attributes', [])
            attr_count = len(attrs) if isinstance(attrs, list) else 0
            lines.append(f"  [{idx}] {entity.get('public_identifier')} - {entity.get('type')} - {attr_count} attributes")
        lines.append("")
    
    lines.append("=" * 80)
    lines.append("CRITICAL INSTRUCTIONS FOR NEW ENTITIES:")
    lines.append("=" * 80)
    lines.append("1. Use the EXACT SAME attribute structure as the reference entity above")
    lines.append("2. Match attribute names precisely (spaces, underscores, capitalization)")
    lines.append("3. Use the SAME widget types (currency, rating, short_text, etc.)")
    lines.append("4. Match data formats (e.g., if coordinates are {lat, lng} objects, use objects)")
    lines.append("5. Include ALL attributes from reference - don't skip any")
    lines.append("6. Use same data types (str, int, dict, list)")
    lines.append(f"7. Your new entity MUST have ~{len(attrs) if isinstance(attrs, list) else 0} attributes")
    lines.append("")
    lines.append("⚠️ CRITICAL: DO NOT return entities with empty 'attributes' arrays!")
    lines.append("⚠️ Each new entity MUST replicate the FULL attribute list shown above")
    lines.append("⚠️ Only change the VALUES, keep all attribute names/widgets/types identical")
    lines.append("")
    
    return "\n".join(lines)


def get_refinement_prompt(
    user_input: str,
    existing_model: Dict,
    conversation_history: List[Dict[str, str]]
) -> str:
    """
    Enhanced prompt for refinement that generates NEW comparative analysis components.

    Used when user wants deeper analysis, comparisons, or insights from existing data.
    Example: "Which city has the best public transportation?"
    Example: "Show me a comparison of food ratings"
    """

    # Format conversation history - show recent turns (last 10 to balance context vs tokens)
    history_text = ""
    if conversation_history:
        recent_turns = conversation_history[-10:]  # Last 10 turns for context
        history_text = "\n".join([
            f"{turn['role'].upper()}: {turn['content']}"
            for turn in recent_turns
        ])
        if len(conversation_history) > 10:
            history_text = f"Recent conversation (last 10 of {len(conversation_history)} turns):\n{history_text}"
        else:
            history_text = f"Conversation history ({len(conversation_history)} turns):\n{history_text}"

    return f"""You are a data analysis expert generating NEW comparative visualizations and insights based on user queries.

CURRENT DATA MODEL:
Task: {existing_model.get('task_description', 'N/A')}

Existing Entities (FULL DETAILS):
{_format_entities_summary(existing_model.get('entities', []))}

CONVERSATION:
{history_text if history_text else "No prior conversation"}

USER REQUEST: "{user_input}"

🎯 YOUR TASK:
The user is asking for a SPECIFIC ANALYSIS or COMPARISON using the existing data.
You must generate NEW UI COMPONENTS that directly answer their question.

DO NOT just reprioritize attributes - CREATE NEW VISUAL COMPONENTS!

{COMPONENT_LIBRARY_REFERENCE}

{ACTION_SYSTEM_REFERENCE}

🚨 CRITICAL RULES FOR REFINEMENT:

1. **ANALYZE THE QUESTION**: What specifically is the user asking?
   - "Which city has best X?" → Generate comparison_table + bar_chart for X
   - "Show me X comparison" → Generate comparison_table with X columns
   - "How do X and Y compare?" → Generate bar_chart or comparison_table
   - "Tell me about X" → Generate metric_cards + expandable_section with details

2. **GENERATE NEW COMPONENTS**: Create 3-8 NEW components that answer the question:
   - comparison_table: For side-by-side attribute comparisons
   - bar_chart: For visual metric comparisons
   - metric_card: For highlighting specific winners/values
   - expandable_section: For detailed breakdowns
   - action_button: For follow-up actions

3. **USE REAL DATA**: Extract actual values from the existing entities
   - Use entity attributes to populate component data
   - Calculate aggregates/comparisons where needed
   - Format currency, ratings, and numbers properly

4. **PROVIDE CONTEXT**: Add descriptive sections explaining the analysis
   - Use expandable_section with titles like "Transportation Analysis"
   - Include badge or sublabel annotations
   - Set defaultExpanded: true for primary sections

5. **SUGGEST NEXT STEPS**: Add 3-5 action_button components for related queries
   - "Show more details about [winner]"
   - "Compare [other attributes]"
   - "Add another [entity type]"

📊 EXAMPLE OUTPUT STRUCTURE:

For query: "Which city has the best public transportation?"

{{
    "components": [
        {{
            "type": "metric_card",
            "props": {{
                "label": "Best Transportation",
                "value": "Paris",
                "sublabel": "Winner: Lowest transport cost €210",
                "icon": "Award"
            }},
            "key": "winner-transport"
        }},
        {{
            "type": "expandable_section",
            "props": {{
                "title": "Transportation Cost Comparison",
                "defaultExpanded": true,
                "badge": "Analysis"
            }},
            "children": [
                {{
                    "type": "comparison_table",
                    "props": {{
                        "data": [
                            {{
                                "id": "paris",
                                "destination": "Paris",
                                "transport_cost": "€210",
                                "walkability": "9.0/10",
                                "transport_reasoning": "Excellent metro system..."
                            }},
                            {{
                                "id": "rome",
                                "destination": "Rome",
                                "transport_cost": "€175",
                                "walkability": "8.5/10",
                                "transport_reasoning": "Limited metro but walkable..."
                            }},
                            {{
                                "id": "barcelona",
                                "destination": "Barcelona",
                                "transport_cost": "€190",
                                "walkability": "9.0/10",
                                "transport_reasoning": "Excellent grid layout..."
                            }}
                        ],
                        "columns": ["destination", "transport_cost", "walkability", "transport_reasoning"],
                        "highlightBest": true
                    }},
                    "key": "transport-comparison-table"
                }}
            ],
            "key": "transport-section"
        }},
        {{
            "type": "bar_chart",
            "props": {{
                "data": [
                    {{"label": "Transport Cost", "Paris": 210, "Rome": 175, "Barcelona": 190}},
                    {{"label": "Walkability", "Paris": 9.0, "Rome": 8.5, "Barcelona": 9.0}}
                ],
                "bars": [
                    {{"dataKey": "Paris", "name": "Paris", "color": "#3b82f6"}},
                    {{"dataKey": "Rome", "name": "Rome", "color": "#10b981"}},
                    {{"dataKey": "Barcelona", "name": "Barcelona", "color": "#f59e0b"}}
                ],
                "xAxisLabel": "Category",
                "yAxisLabel": "Value",
                "height": 300,
                "showValues": true
            }},
            "key": "transport-chart"
        }},
        {{
            "type": "action_button",
            "props": {{
                "label": "Show detailed metro coverage",
                "onClick": {{"type": "refine_query", "params": {{"query": "Can you add information about metro coverage and frequency for each city?"}}}},
                "variant": "primary",
                "icon": "Sparkles"
            }},
            "key": "action-metro-details"
        }},
        {{
            "type": "action_button",
            "props": {{
                "label": "Compare walking vs metro time",
                "onClick": {{"type": "refine_query", "params": {{"query": "Compare average commute times between walking and metro for major attractions"}}}},
                "variant": "secondary",
                "icon": "TrendingUp"
            }},
            "key": "action-commute-compare"
        }}
    ],
    "layout": {{
        "type": "stack",
        "gap": 24
    }},
    "suggested_questions": [
        "How do the daily transportation costs compare between Paris, Rome, and Barcelona?",
        "Can you add information about metro coverage and frequency for each city?",
        "Which city between Paris and Barcelona has better connections to major attractions via public transit?",
        "Help me decide which city to visit based on ease of getting around and overall transportation convenience"
    ],
    "message": "Analyzed transportation data across 3 cities. Paris and Barcelona have excellent walkability (9.0), while Rome has the lowest transport costs at €175. See detailed comparison above."
}}

OUTPUT FORMAT - Return valid JSON:
{{
    "components": [
        // 3-8 NEW components that directly answer the user's question
        // Must include: comparison visualizations, analysis sections, action buttons
    ],
    "layout": {{
        "type": "stack",  // Use "stack" for vertical layout, "grid" for grid layout
        "gap": 24         // Spacing between components
    }},
    "suggested_questions": [
        // 4 new follow-up questions based on this analysis
    ],
    "message": "Brief summary explaining what analysis was done and key findings (1-2 sentences)"
}}

🚨 CRITICAL REQUIREMENTS:
1. **ALWAYS generate 3-8 NEW components** - Never return empty components array!
2. **Use REAL data from existing entities** - Extract actual attribute values
3. **Answer the SPECIFIC question** - Generate components that directly address the user's query
4. **Include visual comparisons** - Use comparison_table AND bar_chart
5. **Add action buttons** - 2-3 buttons for follow-up queries
6. **Provide explanation** - Set message field with key findings

❌ NEVER DO THIS:
- Return empty components array
- Just reprioritize attributes without new components
- Use placeholder/generic data instead of actual entity values
- Skip comparison visualizations when user asks "which" or "compare"

✅ ALWAYS DO THIS:
- Generate comparison_table when comparing entities
- Generate bar_chart for visual metric comparison
- Extract real values from entity attributes
- Add expandable_section wrapper for better UX
- Include 2-3 action_button components for next steps

Now generate components that answer: "{user_input}"

Return ONLY the JSON, no additional text."""
