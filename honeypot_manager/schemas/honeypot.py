from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class UserCredential(BaseModel):
    """Schema for user credentials."""
    username: str
    password: str

class AuthenticationConfig(BaseModel):
    """Schema for authentication configuration."""
    allowed_users: List[UserCredential]

class HoneypotCreate(BaseModel):
    """Schema for creating a new honeypot.
    
    Allows setting honeypot type and port, plus optional resource limits,
    authentication details and banner.
    """
    honeypot_type: str
    honeypot_port: int
    honeypot_cpu_limit: int = 100_000
    honeypot_cpu_quota: int = 50_000
    honeypot_memory_limit: str = "512m"
    honeypot_memory_swap_limit: str = "512m"
    authentication: Optional[AuthenticationConfig] = None
    banner: Optional[str] = None


class HoneypotResponse(BaseModel):
    """Schema for honeypot response data.
    
    This ensures consistent API responses and handles optional fields properly.
    """
    id: str = Field(default="")
    name: str = Field(default="")
    type: str = Field(default="")
    port: int = Field(default=0)
    status: str = Field(default="unknown")
    image: str = Field(default="")