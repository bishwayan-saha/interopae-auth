from pydantic import BaseModel, Field

class UserReq(BaseModel):
    user_name: str = Field(..., description="User name")
    email: str = Field(..., description="User email")
    role_name: str = Field(..., description="Role name, either Admin or User")



class LoginReq(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")


class RefreshTokenReq(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")

