from pydantic import BaseModel, Field, field_validator
from typing import Optional

class HoneypotCreate(BaseModel):
    """Schema for creating a new honeypot"""
    honeypot_type: str = Field(..., description="Type of honeypot")
    honeypot_port: int = Field(..., description="Port for the honeypot")
    honeypot_cpu_limit: int = Field(100000, description="CPU limit for the honeypot")
    honeypot_cpu_quota: int = Field(50000, description="CPU quota for the honeypot")
    honeypot_memory_limit: str = Field("512m", description="Memory limit for the honeypot")
    honeypot_memory_swap_limit: str = Field("512m", description="Memory swap limit for the honeypot")

    @field_validator("honeypot_port")
    def port_must_be_valid(cls, v):
        # Only validate port range, not privileges
        if v <= 0:
            raise ValueError("Port number must be greater than 0")
        if v > 65535:
            raise ValueError("Port number must be less than or equal to 65535")
        return v

class HoneypotResponse(BaseModel):
    """Schema for honeypot responses"""
    honeypot_id: Optional[str] = None
    honeypot_type: Optional[str] = None
    honeypot_port: Optional[int] = None
    image: Optional[str] = None
    honeypot_name: Optional[str] = None
    honeypot_status: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "honeypot_id": "a1b2c3d4e5f6",
                "honeypot_type": "ssh",
                "honeypot_port": 2222,
                "image": "hive-ssh-image",
                "honeypot_name": "hive-ssh-2222",
                "honeypot_status": "running"
            }
        }