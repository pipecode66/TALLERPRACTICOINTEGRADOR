from __future__ import annotations

import time
from datetime import date, datetime
from functools import wraps
from http import HTTPStatus
from typing import Any, Callable, Dict, Optional

from flask import Blueprint, jsonify, request

from .database import db, utcnow
from .models import (
    Payment,
    Reservation,
    Room,
    RoomType,
    SessionToken,
    User,
    active_token,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")


def parse_date(value: str, field_name: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError(f"{field_name} must follow YYYY-MM-DD format")


def get_current_user() -> Optional[User]:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token_value = auth_header.split(" ", 1)[1].strip()
    session = active_token(token_value)
    return session.user if session else None


def login_required(fn: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), HTTPStatus.UNAUTHORIZED
        request.current_user = user  # type: ignore[attr-defined]
        return fn(*args, **kwargs)

    return wrapper


@api_bp.get("/health")
def healthcheck() -> Any:
    return jsonify({"status": "ok"}), HTTPStatus.OK


@api_bp.post("/auth/register")
def register() -> Any:
    payload = request.get_json(force=True, silent=True) or {}
    username = (payload.get("username") or "").strip()
    email = (payload.get("email") or "").strip()
    password = (payload.get("password") or "").strip()

    if not username or not email or not password:
        return jsonify({"error": "username, email and password are required"}), HTTPStatus.BAD_REQUEST

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "User already exists"}), HTTPStatus.CONFLICT

    user = User(username=username, email=email)
    user.set_password(password)
    token = user.refresh_token()
    db.session.add(user)
    db.session.commit()

    return (
        jsonify({"message": "User registered successfully", "token": token}),
        HTTPStatus.CREATED,
    )


@api_bp.post("/auth/login")
def login() -> Any:
    payload = request.get_json(force=True, silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), HTTPStatus.UNAUTHORIZED

    session_token = SessionToken.generate(user)
    db.session.add(session_token)
    token = user.refresh_token()
    db.session.commit()
    return jsonify({"message": "Login successful", "token": token, "session_token": session_token.token})


@api_bp.get("/room-types")
def list_room_types() -> Any:
    room_types = RoomType.query.order_by(RoomType.name).all()
    return jsonify(
        [
            {
                "id": rt.id,
                "name": rt.name,
                "capacity": rt.capacity,
                "base_price": rt.base_price,
                "description": rt.description,
            }
            for rt in room_types
        ]
    )


@api_bp.get("/rooms/search")
def search_rooms() -> Any:
    check_in_raw = request.args.get("check_in")
    check_out_raw = request.args.get("check_out")
    room_type_name = request.args.get("room_type")

    if not check_in_raw or not check_out_raw:
        return jsonify({"error": "check_in and check_out are required"}), HTTPStatus.BAD_REQUEST

    try:
        check_in = parse_date(check_in_raw, "check_in")
        check_out = parse_date(check_out_raw, "check_out")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST

    if check_in >= check_out:
        return jsonify({"error": "check_out must be after check_in"}), HTTPStatus.BAD_REQUEST

    query = Room.query.join(RoomType)
    if room_type_name:
        query = query.filter(RoomType.name.ilike(f"%{room_type_name}%"))

    rooms = query.all()
    available = []
    for room in rooms:
        if is_room_available(room, check_in, check_out):
            available.append(
                {
                    "room_id": room.id,
                    "room_number": room.room_number,
                    "room_type": room.room_type.name,
                    "capacity": room.room_type.capacity,
                    "nightly_rate": room.room_type.base_price,
                }
            )

    return jsonify({"available_rooms": available, "count": len(available)})


def is_room_available(room: Room, check_in: date, check_out: date) -> bool:
    overlapping = (
        Reservation.query.filter_by(room_id=room.id)
        .filter(Reservation.status.in_(["pending", "confirmed"]))
        .filter(Reservation.check_in < check_out, Reservation.check_out > check_in)
        .count()
    )
    return overlapping == 0


@api_bp.post("/reservations")
@login_required
def create_reservation() -> Any:
    payload = request.get_json(force=True, silent=True) or {}

    check_in_raw = payload.get("check_in")
    check_out_raw = payload.get("check_out")
    room_type_id = payload.get("room_type_id")

    if not all([check_in_raw, check_out_raw, room_type_id]):
        return (
            jsonify({"error": "room_type_id, check_in and check_out are required"}),
            HTTPStatus.BAD_REQUEST,
        )

    try:
        check_in = parse_date(check_in_raw, "check_in")
        check_out = parse_date(check_out_raw, "check_out")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST

    if check_in >= check_out:
        return jsonify({"error": "check_out must be after check_in"}), HTTPStatus.BAD_REQUEST

    try:
        room_type_id = int(room_type_id)
    except (TypeError, ValueError):
        return jsonify({"error": "room_type_id must be an integer"}), HTTPStatus.BAD_REQUEST

    room_type = db.session.get(RoomType, room_type_id)
    if not room_type:
        return jsonify({"error": "Room type not found"}), HTTPStatus.NOT_FOUND

    room = Room.query.filter_by(room_type_id=room_type.id, status="available").all()
    available_room = next(
        (r for r in room if is_room_available(r, check_in, check_out)),
        None,
    )
    if not available_room:
        return jsonify({"error": "No rooms available for the selected criteria"}), HTTPStatus.CONFLICT

    nights = (check_out - check_in).days
    total_price = nights * room_type.base_price

    reservation = Reservation(
        user=request.current_user,  # type: ignore[attr-defined]
        room=available_room,
        check_in=check_in,
        check_out=check_out,
        status="pending",
        total_price=total_price,
    )
    db.session.add(reservation)
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Reservation created",
                "reservation_id": reservation.id,
                "status": reservation.status,
                "total_price": reservation.total_price,
            }
        ),
        HTTPStatus.CREATED,
    )


@api_bp.get("/reservations")
@login_required
def list_reservations() -> Any:
    user: User = request.current_user  # type: ignore[attr-defined]
    reservations = (
        Reservation.query.filter_by(user=user)
        .order_by(Reservation.created_at.desc())
        .all()
    )
    return jsonify(
        [
            {
                "id": r.id,
                "room_number": r.room.room_number,
                "room_type": r.room.room_type.name,
                "status": r.status,
                "check_in": r.check_in.isoformat(),
                "check_out": r.check_out.isoformat(),
                "total_price": r.total_price,
                "payment_status": r.payment.status if r.payment else "unpaid",
            }
            for r in reservations
        ]
    )


@api_bp.post("/payments/simulate")
@login_required
def simulate_payment() -> Any:
    payload = request.get_json(force=True, silent=True) or {}
    reservation_id = payload.get("reservation_id")
    method = (payload.get("method") or "credit_card").strip()
    simulate_failure = payload.get("force_failure", False)

    if not reservation_id:
        return jsonify({"error": "reservation_id is required"}), HTTPStatus.BAD_REQUEST

    reservation = db.session.get(Reservation, reservation_id)
    if not reservation or reservation.user != request.current_user:  # type: ignore[attr-defined]
        return jsonify({"error": "Reservation not found"}), HTTPStatus.NOT_FOUND

    if reservation.payment:
        return jsonify({"error": "Reservation already paid"}), HTTPStatus.CONFLICT

    now_utc = utcnow()
    reference_suffix = int(time.time())
    payment = Payment(
        reservation=reservation,
        amount=reservation.total_price,
        method=method,
        status="failed" if simulate_failure else "success",
        transaction_reference=f"SIM-{reservation.id}-{reference_suffix}",
        processed_at=now_utc,
    )
    reservation.status = "cancelled" if simulate_failure else "confirmed"
    db.session.add(payment)
    db.session.commit()

    return jsonify(
        {
            "message": "Payment processed",
            "reservation_status": reservation.status,
            "payment_status": payment.status,
            "transaction_reference": payment.transaction_reference,
        }
    )


@api_bp.get("/users/me")
@login_required
def current_user() -> Any:
    user: User = request.current_user  # type: ignore[attr-defined]
    return jsonify(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "token": user.api_token,
        }
    )
