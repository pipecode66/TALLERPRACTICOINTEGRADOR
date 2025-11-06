from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from werkzeug.security import check_password_hash, generate_password_hash

from .database import BaseModel, db, utcnow


class User(BaseModel):
    __tablename__ = "users"

    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    api_token = db.Column(db.String(255), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    reservations = db.relationship(
        "Reservation", back_populates="user", cascade="all, delete-orphan"
    )
    tokens = db.relationship(
        "SessionToken", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def refresh_token(self) -> str:
        token = uuid4().hex
        self.api_token = token
        return token


class RoomType(BaseModel):
    __tablename__ = "room_types"

    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    base_price = db.Column(db.Float, nullable=False)

    rooms = db.relationship("Room", back_populates="room_type", cascade="all, delete-orphan")


class Room(BaseModel):
    __tablename__ = "rooms"

    room_number = db.Column(db.String(10), unique=True, nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="available", nullable=False)

    room_type_id = db.Column(db.Integer, db.ForeignKey("room_types.id"), nullable=False)
    room_type = db.relationship("RoomType", back_populates="rooms")

    reservations = db.relationship(
        "Reservation", back_populates="room", cascade="all, delete-orphan"
    )


class Reservation(BaseModel):
    __tablename__ = "reservations"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    user = db.relationship("User", back_populates="reservations")
    room = db.relationship("Room", back_populates="reservations")
    payment = db.relationship(
        "Payment", back_populates="reservation", uselist=False, cascade="all, delete-orphan"
    )

    def duration_nights(self) -> int:
        return (self.check_out - self.check_in).days


class Payment(BaseModel):
    __tablename__ = "payments"

    reservation_id = db.Column(
        db.Integer, db.ForeignKey("reservations.id"), unique=True, nullable=False
    )
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="initiated", nullable=False)
    method = db.Column(db.String(30), nullable=False)
    transaction_reference = db.Column(db.String(60), unique=True, nullable=True)
    processed_at = db.Column(db.DateTime, nullable=True)

    reservation = db.relationship("Reservation", back_populates="payment")


class SessionToken(BaseModel):
    __tablename__ = "session_tokens"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    user = db.relationship("User", back_populates="tokens")

    @staticmethod
    def generate(user: User, lifetime_minutes: int = 60) -> "SessionToken":
        token_value = uuid4().hex
        expires = utcnow() + timedelta(minutes=lifetime_minutes)
        return SessionToken(user=user, token=token_value, expires_at=expires)


def active_token(token_value: str) -> SessionToken | None:
    token = SessionToken.query.filter_by(token=token_value).first()
    if not token:
        return None
    if token.expires_at < utcnow():
        db.session.delete(token)
        db.session.commit()
        return None
    return token
