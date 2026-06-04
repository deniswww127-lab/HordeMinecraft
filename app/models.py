"""
Модели базы данных (SQLAlchemy 2.0, async).
Хранит пользователей VK, подключённые ими сообщества с токенами и посты.
"""
from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    """Пользователь, авторизовавшийся через VK."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    vk_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(120), default="")
    last_name: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    communities: Mapped[list["Community"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Community(Base):
    """
    Сообщество ВК, которое пользователь подключил к сервису.
    group_token — токен сообщества со scope wall/manage/photos,
    выдаётся при выборе группы в окне VK OAuth.
    """
    __tablename__ = "communities"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    vk_group_id: Mapped[int] = mapped_column(BigInteger, index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    screen_name: Mapped[str] = mapped_column(String(255), default="")
    photo_url: Mapped[str] = mapped_column(String(512), default="")
    members_count: Mapped[int] = mapped_column(Integer, default=0)
    group_token: Mapped[str] = mapped_column(Text)  # токен сообщества (в проде — шифровать!)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="communities")
    posts: Mapped[list["Post"]] = relationship(back_populates="community", cascade="all, delete-orphan")


class Post(Base):
    """Сгенерированный пост: черновик, в очереди или опубликован."""
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    community_id: Mapped[int] = mapped_column(ForeignKey("communities.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(Text, default="")
    tone: Mapped[str] = mapped_column(String(40), default="дружеский")
    format: Mapped[str] = mapped_column(String(40), default="анонс")
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|queued|published|failed
    vk_post_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    community: Mapped["Community"] = relationship(back_populates="posts")
