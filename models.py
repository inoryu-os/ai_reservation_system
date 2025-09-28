import os
from datetime import datetime
from typing import List

from sqlalchemy import (
    create_engine, Integer, String, DateTime, ForeignKey, select
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session

from config.rooms import ROOMS_CONFIG

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///meeting_rooms.db')

class Base(DeclarativeBase):
    pass

class Room(Base):
    __tablename__ = 'rooms'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    reservations: Mapped[List["Reservation"]] = relationship(
        "Reservation", back_populates="room", cascade="all, delete-orphan"
    )

class Reservation(Base):
    __tablename__ = 'reservations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey('rooms.id'), nullable=False)
    user_name: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    room: Mapped["Room"] = relationship("Room", back_populates="reservations")

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

def get_session() -> Session:
    return SessionLocal()

def _seed_rooms(session: Session) -> None:
    """存在しない会議室だけを追加（何度呼んでも安全）"""
    existing_names = set(session.execute(select(Room.name)).scalars())
    to_add = [Room(**d) for d in ROOMS_CONFIG if d["name"] not in existing_names]
    if to_add:
        session.add_all(to_add)
        session.commit()

def init_db() -> List[Room]:
    """定義済みテーブルの作成 + 初期データ投入（idempotent）"""
    Base.metadata.create_all(bind=engine)
    # トランザクション境界：成功ならコミット、例外なら自動ロールバック
    with get_session() as session:
        _seed_rooms(session)
        return session.query(Room).all()

def get_rooms() -> List[Room]:
    """全ての会議室を取得"""
    with get_session() as session:
        return session.query(Room).all()


if __name__ == "__main__":
    init_db()
    print("Database initialized.")