from __future__ import annotations

from datetime import date, timedelta

import pytest

from helynota import create_app
from helynota.database import db
from helynota.seed import seed_initial_data


@pytest.fixture()
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with app.app_context():
        db.create_all()
        seed_initial_data()

    yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client) -> str:
    response = client.post(
        "/api/auth/login", json={"username": "cliente", "password": "cliente123"}
    )
    payload = response.get_json()
    assert response.status_code == 200
    return payload["session_token"]


def test_user_registration_and_login_flow(client):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "nueva_persona",
            "email": "nueva@hotel.test",
            "password": "segura123",
        },
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert "token" in payload

    login_response = client.post(
        "/api/auth/login", json={"username": "nueva_persona", "password": "segura123"}
    )
    assert login_response.status_code == 200
    login_payload = login_response.get_json()
    assert "session_token" in login_payload


def test_room_search_returns_available_rooms(client):
    check_in = (date.today() + timedelta(days=14)).isoformat()
    check_out = (date.today() + timedelta(days=17)).isoformat()
    response = client.get(
        "/api/rooms/search",
        query_string={"check_in": check_in, "check_out": check_out, "room_type": "Suite"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["count"] > 0
    assert all("room_id" in room for room in payload["available_rooms"])


def test_reservation_creation_and_payment_flow(client):
    token = login(client)
    headers = {"Authorization": f"Bearer {token}"}

    room_types_response = client.get("/api/room-types")
    assert room_types_response.status_code == 200
    room_types = room_types_response.get_json()
    suite = next(rt for rt in room_types if rt["name"] == "Suite")

    check_in = (date.today() + timedelta(days=30)).isoformat()
    check_out = (date.today() + timedelta(days=33)).isoformat()
    reservation_response = client.post(
        "/api/reservations",
        headers=headers,
        json={
            "room_type_id": suite["id"],
            "check_in": check_in,
            "check_out": check_out,
        },
    )
    assert reservation_response.status_code == 201
    reservation_payload = reservation_response.get_json()
    assert reservation_payload["status"] == "pending"

    reservation_id = reservation_payload["reservation_id"]
    payment_response = client.post(
        "/api/payments/simulate",
        headers=headers,
        json={"reservation_id": reservation_id, "method": "credit_card"},
    )
    assert payment_response.status_code == 200
    payment_payload = payment_response.get_json()
    assert payment_payload["reservation_status"] == "confirmed"
    assert payment_payload["payment_status"] == "success"

    reservations_response = client.get("/api/reservations", headers=headers)
    assert reservations_response.status_code == 200
    reservations = reservations_response.get_json()
    assert any(r["id"] == reservation_id for r in reservations)
