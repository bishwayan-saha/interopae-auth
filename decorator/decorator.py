import configparser
from functools import wraps

import jwt
from fastapi import Request, status

from models.exception import InteropAEException

config = configparser.ConfigParser()
config.read("config.ini")
SECRET_KEY = config["JWT"]["SECRET_KEY"]
ALGORITHM = config["JWT"]["ALGORITHM"]

def token_required(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        # Check for Authorization header
        if "Authorization" not in request.headers:
            raise InteropAEException(
                message= "Missing authorization token",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
            
        auth_header = request.headers["Authorization"]
        
        # Verify token format
        if not auth_header.startswith("Bearer "):
            raise InteropAEException(
                message="Invalid token format. Use 'Bearer <token>'",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
            
        token = auth_header.split(" ")[1]
        
        if not token:
            raise InteropAEException(
                message="Token is required",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            request.state.user = payload
        except jwt.ExpiredSignatureError:
            raise InteropAEException(
                message="Expired access token",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        except jwt.InvalidTokenError:
            raise InteropAEException(
                message="Invalid access token",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        return await func(request, *args, **kwargs)
    return wrapper
