from __future__ import annotations

from datetime import date, timedelta

from .database import db
from .models import Payment, Reservation, Room, RoomType, User


def seed_initial_data() -> None:
    """Populate the database with initial data if empty."""
    if RoomType.query.count() > 0:
        return

    room_types = [
        RoomType(
            name="Simple",
            description="Habitación individual cómoda para viajes rápidos.",
            capacity=1,
            base_price=80.0,
        ),
        RoomType(
            name="Doble",
            description="Habitación doble con cama queen y vista a la ciudad.",
            capacity=2,
            base_price=120.0,
        ),
        RoomType(
            name="Suite",
            description="Suite ejecutiva con sala de estar y desayuno incluido.",
            capacity=4,
            base_price=220.0,
        ),
    ]
    db.session.add_all(room_types)
    db.session.flush()

    rooms = []
    room_number = 100
    for room_type in room_types:
        for _ in range(6):
            rooms.append(
                Room(
                    room_number=str(room_number),
                    floor=int(room_number / 100),
                    status="available",
                    room_type=room_type,
                )
            )
            room_number += 1
    db.session.add_all(rooms)

    admin = User(username="admin", email="admin@hotel.test")
    admin.set_password("admin123")
    admin.refresh_token()
    db.session.add(admin)

    demo_user = User(username="cliente", email="cliente@hotel.test")
    demo_user.set_password("cliente123")
    demo_user.refresh_token()
    db.session.add(demo_user)

    db.session.commit()

    # Create sample reservation history
    create_demo_reservations(demo_user, room_types)


def create_demo_reservations(user: User, room_types: list[RoomType]) -> None:
    """Generate sample reservations and payments for demos and tests."""
    check_in = date.today() + timedelta(days=3)
    for index, room_type in enumerate(room_types):
        room = Room.query.filter_by(room_type=room_type).first()
        reservation = Reservation(
            user=user,
            room=room,
            check_in=check_in + timedelta(days=index * 3),
            check_out=check_in + timedelta(days=index * 3 + 2),
            status="confirmed",
            total_price=room_type.base_price * 2,
        )
        db.session.add(reservation)
        db.session.flush()

        payment = Payment(
            reservation=reservation,
            amount=reservation.total_price,
            status="success",
            method="credit_card",
            transaction_reference=f"TXN-DEMO-{reservation.id}",
        )
        db.session.add(payment)

    db.session.commit()
