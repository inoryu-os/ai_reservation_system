import os
from datetime import datetime
from typing import List

from sqlalchemy import (
    create_engine, Integer, String, DateTime, ForeignKey, select
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session

from config import ROOMS_CONFIG

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

from typing import List
from sqlalchemy import select

def init_db() -> List[Room]:
    """ROOMS_CONFIG と DB を同期（追加・削除）。挿入順は ROOMS_CONFIG の順を保証する。"""
    Base.metadata.create_all(bind=engine)

    with get_session() as session:
        # 既存の部屋名セット
        names_db = set(session.execute(select(Room.name)).scalars())

        # 追加：config の並び順で追加（セットの反復順非決定性を回避）
        to_add_rooms: List[Room] = [
            Room(name=room["name"], capacity=room["capacity"]) 
            for room in ROOMS_CONFIG 
            if room["name"] not in names_db
        ]
        if to_add_rooms:
            session.add_all(to_add_rooms)

        # 削除：DBにあるがconfigにない部屋（Reservationはcascadeで一緒に削除）
        names_cfg = {room["name"] for room in ROOMS_CONFIG}
        to_delete_name_set = names_db - names_cfg
        if to_delete_name_set:
            to_delete_rooms = session.scalars(select(Room).where(Room.name.in_(to_delete_name_set))).all()
            for to_delete in to_delete_rooms:
                session.delete(to_delete)

        session.commit()
        # 一貫した順序で返却（id 昇順）
        return session.scalars(select(Room).order_by(Room.id)).all()


def get_rooms() -> List[Room]:
    """全ての会議室を取得（id 昇順）"""
    with get_session() as session:
        return session.scalars(select(Room).order_by(Room.id)).all()


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
