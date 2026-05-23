from fastapi.testclient import TestClient

from aippt_api.main import create_app


def register(client: TestClient, email: str) -> TestClient:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password-123", "display_name": email.split("@")[0]},
    )
    assert response.status_code == 201
    return client


def test_users_only_see_their_own_decks() -> None:
    app = create_app()
    alice = register(TestClient(app), "alice@example.com")
    bob = register(TestClient(app), "bob@example.com")

    alice_deck = alice.post("/api/decks", json={"title": "Alice Deck", "outline_md": "# A"})
    assert alice_deck.status_code == 201
    deck_id = alice_deck.json()["id"]

    bob_list = bob.get("/api/decks")
    assert bob_list.status_code == 200
    assert bob_list.json() == []

    bob_get = bob.get(f"/api/decks/{deck_id}")
    assert bob_get.status_code == 404
