import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database.database import SessionLocal
from decorator.decorator import token_required
from models.exception import InteropAEException
from models.request import LoginReq, RefreshTokenReq, UserReq
from models.response import ServerResponse
from service import service
from service.scheduler import scheduler

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(InteropAEException)
async def handle_exception(request: Request, ex: InteropAEException):
    return JSONResponse(
        content=ServerResponse(
            data=ex.message, statusCode=ex.status_code, success=False
        ).model_dump()
    )

@app.exception_handler(Exception)
async def handle_exception(request: Request, ex: Exception):
    logger.error(f"\t ===== Error =====\nReason: {ex}")
    return JSONResponse(
        content=ServerResponse(
            data="Server error", statusCode=500, success=False
        ).model_dump()
    )

@app.get("/credentials", include_in_schema=False)
async def get_credentials(db: Session = Depends(get_db)):
    response = await service.fetch_all_credentials(db)
    return JSONResponse(
        content=ServerResponse(
            data={"message": "Credentials fetched successfully!", "credentials": response},
            statusCode=200,
            success=True,
        ).model_dump(),
    )

@app.post("/register")
async def register_new_user(user: UserReq, db: Session = Depends(get_db)):
    print(user)
    response = await service.register_new_user(user, db)
    return JSONResponse(
        content=ServerResponse(
            data={"message": "user registered sucessfully!", "user": response.model_dump()},
            statusCode=200,
            success=True,
        ).model_dump(),
    )


@app.post("/login")
async def login_user_and_create_token(login: LoginReq, db: Session = Depends(get_db)):
    response = await service.login_user(login, db)
    return JSONResponse(
        content=ServerResponse(
            data={"message": "Login successful!", "token": response.model_dump()},
            statusCode=200,
            success=True,
        ).model_dump(),
    )


@app.post("/refresh")
async def create_token_from_refresh_token(
    refresh_token: RefreshTokenReq, db: Session = Depends(get_db)
):
    response = await service.create_access_token_from_refresh_token(refresh_token.refresh_token, db)
    return JSONResponse(
        content=ServerResponse(
            data={"message": "Access token generated from refresh token", "token": response.model_dump()},
            statusCode=200,
            success=True,
        ).model_dump(),
    )


@app.get("/user/{user_cred}")
@token_required
async def get_user_details(request: Request, user_cred: str, db: Session = Depends(get_db)):
    user = request.state.user
    if str(user["id"]) != user_cred and user["sub"] != user_cred:
        raise InteropAEException(
            message={
                "message": f"Forbidden Access: User does not have permission to access this resource",
                "user": None,
            },
            status_code=403,
        )
    response = await service.fetch_user_details(user_cred, db)
    return JSONResponse(
        content=ServerResponse(
            data={"message": "User fetched successfully!", "user": response.model_dump()},
            statusCode=200,
            success=True,
        ).model_dump(),
    )


@app.post("/logout")
@token_required
async def logout_user(request: Request, db: Session = Depends(get_db)):
    user = request.state.user
    response = await service.logout_user(user["id"], db)
    return JSONResponse(
        content=ServerResponse(
            data={"message": response},
            statusCode=200,
            success=True,
        ).model_dump(),
    )