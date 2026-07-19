from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[str] = None


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: str
    version: Optional[str] = None


class ComponentConfig(BaseModel):
    id: str
    name: str
    type: str
    props: Dict[str, Any]
    children: Optional[List['ComponentConfig']] = None


class GenerationRequest(BaseModel):
    prompt: str
    component_type: Optional[str] = None
    framework: Optional[str] = "react"
    styling: Optional[str] = "tailwind"


class GenerationResponse(BaseModel):
    success: bool
    component: Optional[ComponentConfig] = None
    code: Optional[str] = None
    error: Optional[str] = None
