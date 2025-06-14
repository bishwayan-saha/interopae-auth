import configparser
import logging
import re
import secrets
import string
from datetime import datetime, timedelta
from uuid import uuid4

import bcrypt
import httpx
import jwt
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session

from database import database
from database.entity import Role, Token, User, UserRoles
from models.exception import InteropAEException
from models.request import LoginReq, UserReq
from models.response import TokenDetails, UserRes

config = configparser.ConfigParser()
config.read("config.ini")
SECRET_KEY = config["JWT"]["SECRET_KEY"]
ALGORITHM = config["JWT"]["ALGORITHM"]
ACCESS_TOKEN_EXPIRE_MINUTES = int(config["JWT"]["ACCESS_TOKEN_EXPIRE_MINUTES"])
REFRESH_TOKEN_EXPIRE_MINUTES = int(config["JWT"]["REFRESH_TOKEN_EXPIRE_MINUTES"])

logger = logging.getLogger(__name__)


async def register_new_user(user: UserReq, db: Session) -> UserRes:

    existing_user = database.get_user_by_email(db, user.email)
    if existing_user:
        raise InteropAEException(
            message={
                "message": f"User with email {user.email} already exists",
                "user": None,
            },
            status_code=400,
        )
    else:
        password = _generate_random_password()
        print(f"Password: {password}")
        hashed_pwd = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        new_user: User = User(**user.model_dump(exclude={"role_name"}), password=hashed_pwd)
        role: Role = database.get_role_by_role_name(db, user.role_name)
        new_user.roles = [
            UserRoles(
                role_id=role.role_id, user_id=new_user.user_id, is_active=True
            )
        ]
        # await _send_email(user, password)
        database.create_new_user(db, new_user)
        return UserRes(
            userId=str(new_user.user_id),
            userName=new_user.user_name,
            email=new_user.email,
            roleId=str(new_user.roles[0].role_id),
        )


async def login_user(login: LoginReq, db: Session) -> TokenDetails:

    user = database.get_user_by_email(db, login.email)

    if not user:
        raise InteropAEException(
            message={
                "message": f"Invalid credentials: User with email {login.email} does not exist in our records",
                "token": None,
            },
            status_code=401,
        )
    if not bcrypt.checkpw(
        login.password.encode("utf-8"), user.password.encode("utf-8")
    ):
        raise InteropAEException(
            message={
                "message": f"Invalid credentials: Password does not match",
                "token": None,
            },
            status_code=401,
        )
    print(user.actual_roles[0].role_name)
    access_token = _create_access_token(data={"sub": user.email, "id": user.user_id, "role": user.actual_roles[0].role_name})
    # Revoke existing refresh tokens
    existing_refresh_tokens = database.get_non_revoked_token_details_by_user_id(db, user.user_id)
    for token in existing_refresh_tokens:
        token.is_revoked = True
        database.update_token(db, token)

    # Generate new refresh token and store it in the database
    refresh_token = uuid4().hex
    new_token = Token(
        refresh_token=refresh_token,
        expiration_time=datetime.now()
        + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES),
        user_id=user.user_id,
        is_revoked=False,
    )
    database.create_new_refresh_token(db, new_token)
    return TokenDetails(accessToken=access_token, refreshToken=refresh_token)


async def create_access_token_from_refresh_token(refresh_token: str, db: Session) -> TokenDetails:
    token = database.get_valid_refresh_token(db, refresh_token)
    # If token is not found or expired, raise an exception

    if not token:
        raise InteropAEException(
            message={
                "message": f"Invalid token: Refresh token is invoked. Please login with your credentials again",
                "token": None,
            },
            status_code=401,
        )   
    token.is_revoked = True
    database.update_token(db, token)
    if datetime.now() > token.expiration_time:
        raise InteropAEException(
            message={
                "message": f"Invalid token: Refresh token is expired. Please login with your credentials again",
                "token": None,
            },
            status_code=401,
        )

    # If token is valid, generate a new access token and refresh token
    user = database.get_user_by_id(db, token.user_id)
    access_token = _create_access_token(
        data={"sub": user.email, "id": user.user_id, "role": user.actual_roles[0].role_name}
    )
    refresh_token = uuid4().hex
    new_token = Token(
        refresh_token=refresh_token,
        expiration_time=datetime.now()
        + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES),
        user_id=user.user_id,
        is_revoked=False,
    )
    database.create_new_refresh_token(db, new_token)
    return TokenDetails(accessToken=access_token, refreshToken=refresh_token)


async def fetch_user_details(user_cred: str, db: Session):
    existing_user = None
    if _is_valid_email(user_cred):
        existing_user = database.get_user_by_email(db, user_cred)
    else:
        existing_user = database.get_user_by_id(db, user_cred)
    if not existing_user:
        raise InteropAEException(
            message={
                "message": f"User with credentials {user_cred} does not exist in our records",
                "user": None,
            },
            status_code=404,
        )
    return UserRes(
        userId=str(existing_user.user_id),
        userName=existing_user.user_name,
        email=existing_user.email,
        roleId=str(existing_user.roles[0].role_id),
    )

async def logout_user(user_id: str, db: Session):
    database.delete_refresh_tokens(db, user_id)
    return "User logged out successfully!"


async def fetch_all_credentials(db: Session):
    credentials = database.get_credentials(db)
    return {creds.credential_name: creds.credential_value for creds in credentials}
    

def _generate_random_password(length=16):
    allowed_punctuation = "@#$=%+-;"
    characters = string.ascii_letters + string.digits + allowed_punctuation
    # Ensure password includes at least one lowercase, uppercase, digit, and symbol
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice(string.punctuation),
    ]
    password += [secrets.choice(characters) for _ in range(length - 4)]
    secrets.SystemRandom().shuffle(password)
    return "".join(password)


def _create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def _is_valid_email(email: str) -> bool:
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


async def _send_email(user: UserReq, password: str):
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("send_password.html")
    html_body = template.render(
        name=user.user_name,
        email=user.email,
        password=password,
        title="Team PwC, India"
    )

    logic_app_url = "https://prod-16.centralindia.logic.azure.com:443/workflows/804301f846874454be13d04afedbae72/triggers/manual/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=jBoAsrpe_vNzfqmLs6lzNMA_GqvOokOVCtaubjwCCKg"
    payload = {
        "to": user.email,
        "subject": "InteropAE Registration",
        "email_body": html_body
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(logic_app_url, json=payload)
            response.raise_for_status()
            logger.info("Email sent successfully")
        except Exception as e:
            logger.error(f"\t===== Error while sending mail =====\nReason: {e}")
            raise InteropAEException(
                message={
                    "message": "Failed to send email",
                    "user": None,
                },
                status_code=500,
            )
