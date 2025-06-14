from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.entity import Credentials, Role, Token, User

DATABASE_URL = URL.create(
    drivername="mssql+pyodbc",
    username="interopae_dev",
    password="User@PwCAdmin",
    host="tcp:interopae-dev.database.windows.net",
    database="InteropAE",
    query={"driver": "ODBC Driver 17 for SQL Server"},
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.user_id == user_id).first()


def create_new_user(db: Session, user: User) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_role_by_role_name(db: Session, role_name: str):
    return db.query(Role).filter(Role.role_name == role_name).first()


def create_new_refresh_token(db: Session, tokens: Token) -> Token:
    db.add(tokens)
    db.commit()
    db.refresh(tokens)
    return tokens


def get_valid_refresh_token(db: Session, refresh_token: str):
    return (
        db.query(Token)
        .filter(
            Token.refresh_token == refresh_token,
            Token.is_revoked == False,
        )
        .first()
    )


def get_non_revoked_token_details_by_user_id(db: Session, user_id: int):
    return db.query(Token).filter(Token.user_id == user_id, Token.is_revoked == False).all()


def update_token(db: Session, token: Token):
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def delete_refresh_tokens(db: Session, user_id: int):
    if not user_id:
        db.query(Token).filter(Token.is_revoked == True).delete()
    else:
        db.query(Token).filter(Token.user_id == user_id).delete()
    db.commit()


def get_credentials(db: Session):
    return db.query(Credentials).all()
    
