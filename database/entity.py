from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DATETIME, Text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    user_id = Column(name="user_id", type_=Integer, primary_key=True, autoincrement=True, nullable=False)
    user_name = Column(name="user_name", type_=String, nullable=False)
    email = Column(name="email", type_=String, unique=True, nullable=False)
    password = Column(name="password", type_=String, nullable=False)
    created_by = Column(name="created_by", type_=String, nullable=False, default="admin")
    created_at = Column(name="created_at", type_=DATETIME, nullable=False, server_default="GETDATE()")
    updated_by = Column(name="updated_by", type_=String, nullable=True, default="admin")
    updated_at = Column(name="updated_at", type_=DATETIME, nullable=True, server_default="GETDATE()")

    roles = relationship("UserRoles", back_populates="user")
    token = relationship("Token", back_populates="user", uselist=False)

    actual_roles = relationship(
        "Role",
        secondary="user_roles",
        primaryjoin="User.user_id==UserRoles.user_id",
        secondaryjoin="UserRoles.role_id==Role.role_id",
        viewonly=True,
    )

class Role(Base):
    __tablename__ = 'role'

    role_id = Column(name="role_id", type_=Integer, primary_key=True, autoincrement=True, nullable=False)
    role_name = Column(name="role_name", type_=String, nullable=False, unique=True)
    created_by = Column(name="created_by", type_=String, nullable=False, default="admin")
    created_at = Column(name="created_at", type_=DATETIME, nullable=False, server_default="GETDATE()")
    updated_by = Column(name="updated_by", type_=String, nullable=True, default="admin")
    updated_at = Column(name="updated_at", type_=DATETIME, nullable=True, server_default="GETDATE()")

    users = relationship("UserRoles", back_populates="role")

class UserRoles(Base):
    __tablename__ = 'user_roles'

    user_id = Column(ForeignKey('user.user_id'), name="user_id", type_=Integer, primary_key=True)
    role_id = Column(ForeignKey('role.role_id'), name="role_id", type_=Integer, primary_key=True)
    is_active = Column(name="is_active", type_=Boolean, default=True)
    created_by = Column(name="created_by", type_=String, nullable=False, default="admin")
    created_at = Column(name="created_at", type_=DATETIME, nullable=False, server_default="GETDATE()")
    updated_by = Column(name="updated_by", type_=String, nullable=True, default="admin")
    updated_at = Column(name="updated_at", type_=DATETIME, nullable=True, server_default="GETDATE()")

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")


class Token(Base):
    __tablename__ = 'token'

    token_id = Column(name="token_id", type_=Integer, primary_key=True, autoincrement=True, nullable=False)
    refresh_token = Column(name="refresh_token", type_=String, nullable=False)
    expiration_time = Column(name="expiration_time", type_=DATETIME, nullable=False)
    user_id = Column(ForeignKey('user.user_id'), name="user_id", type_=Integer, nullable=False)
    is_revoked = Column(name="is_revoked", type_=Boolean, default=True)
    created_by = Column(name="created_by", type_=String, nullable=False, default="admin")
    created_at = Column(name="created_at", type_=DATETIME, nullable=False, server_default="GETDATE()")
    updated_by = Column(name="updated_by", type_=String, nullable=True, default="admin")
    updated_at = Column(name="updated_at", type_=DATETIME, nullable=True, server_default="GETDATE()")

    user = relationship("User", back_populates="token") 


class Credentials(Base):
    __tablename__ = "credentials"

    credential_id = Column(name="credential_id",type_=UNIQUEIDENTIFIER,primary_key=True,server_default="NEWID()",)
    credential_name = Column(name="credential_name", type_=String, nullable=False)
    credential_value = Column(name="credential_value", type_=Text, nullable=False)
    created_by = Column(name="created_by", type_=String, nullable=False)
    created_at = Column(name="created_at", type_=DATETIME, nullable=False, server_default="GETDATE()")
    updated_by = Column(name="updated_by", type_=String, nullable=True)
    updated_at = Column(name="updated_at", type_=DATETIME, nullable=True)
