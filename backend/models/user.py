import enum
from datetime import datetime
from typing import TYPE_CHECKING

from models.base import BaseModel
from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from starlette.authentication import SimpleUser

if TYPE_CHECKING:
    from models.assets import Save, Screenshot, State
    from models.rom import RomNote


class Role(enum.Enum):
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"


class User(BaseModel, SimpleUser):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    username: Mapped[str | None] = mapped_column(
        String(length=255), unique=True, index=True
    )
    hashed_password: Mapped[str | None] = mapped_column(String(length=255))
    enabled: Mapped[bool | None] = mapped_column(default=True)
    role: Mapped[Role | None] = mapped_column(Enum(Role), default=Role.VIEWER)
    avatar_path: Mapped[str | None] = mapped_column(String(length=255), default="")
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_active: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    saves: Mapped[list["Save"]] = relationship(back_populates="user")
    states: Mapped[list["State"]] = relationship(back_populates="user")
    screenshots: Mapped[list["Screenshot"]] = relationship(back_populates="user")
    notes: Mapped[list["RomNote"]] = relationship(back_populates="user")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @property
    def oauth_scopes(self):
        from handler.auth.base_handler import DEFAULT_SCOPES, FULL_SCOPES, WRITE_SCOPES

        if self.role == Role.ADMIN:
            return FULL_SCOPES

        if self.role == Role.EDITOR:
            return WRITE_SCOPES

        return DEFAULT_SCOPES

    @property
    def fs_safe_folder_name(self):
        # Uses the ID to avoid issues with username changes
        return f"User:{self.id}".encode().hex()

    def set_last_active(self):
        from handler.database import db_user_handler

        db_user_handler.update_user(self.id, {"last_active": datetime.now()})
