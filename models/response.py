from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ServerResponse(BaseModel):
    data: Any = Field(
        ...,
        description="Server response, can be list, dictionary or primitive data types",
    )
    statusCode: int = Field(..., description="HTTP response status code")
    success: bool = Field(..., description="HTTP response status code") 
    timestamp: str = Field(
        default=datetime.now().__str__(), description="current timestamp for tracking"
    )

    class Config:
        use_enum_values = True
    
class UserRes(BaseModel):
    userId: str = Field(..., description="User id")
    userName: str = Field(..., description="User name")
    email: str = Field(..., description="User email")
    roleId: str = Field(..., description="User role id")

    model_config = ConfigDict(from_attributes=True)

class TokenDetails(BaseModel):
    accessToken: str = Field(..., description="Access token")
    refreshToken: str = Field(..., description="Refresh token")
    tokenType: str = Field(default="Bearer")