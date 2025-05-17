from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class UserCredential(BaseModel):
    """Schema for individual user credentials."""
    username: str
    password: str


class AuthenticationConfig(BaseModel):
    """Schema for authentication configuration grouping multiple credentials."""
    allowed_users: List[UserCredential]


class HoneypotCreate(BaseModel):
    """Payload schema for creating a new honeypot via API."""
    honeypot_type: str = Field(..., alias="type")
    honeypot_port: int = Field(..., alias="port")
    honeypot_cpu_limit: int = Field(100_000, alias="cpu_period")
    honeypot_cpu_quota: int = Field(50_000, alias="cpu_quota")
    honeypot_memory_limit: str = Field("512m", alias="memory_limit")
    honeypot_memory_swap_limit: str = Field("512m", alias="memory_swap_limit")
    authentication: Optional[AuthenticationConfig] = None
    banner: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
        populate_by_name = True

    @validator("honeypot_memory_limit", "honeypot_memory_swap_limit", pre=True)
    def _format_memory(cls, v):
        # ensure any integer values become strings with 'm' suffix
        if isinstance(v, int):
            return f"{v}m"
        return v


class HoneypotResponse(BaseModel):
    """Schema for responses returning honeypot container details."""
    id: str = Field(default="")
    name: str = Field(default="")
    type: str = Field(default="")
    port: int = Field(default=0)
    status: str = Field(default="unknown")
    image: str = Field(default="")


class PortCheckResponse(BaseModel):
    """Schema for port availability check responses."""
    available: bool
    message: str