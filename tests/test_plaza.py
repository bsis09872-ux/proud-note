from fastapi.testclient import TestClient

from tests.conftest import run_sql


def write(client, body, headers=None):
    return client.post("/v1/spaces/plaza/notes", json=body, headers=headers or {})


def test_guest_can_post_anonymously_once_a_day(client: TestClient):
    assert write(client, {"learned": "x"}).json()["code"] == "GUEST_PASSWORD_REQUIRED"

    r = write(client, {"proud_of_me": "잘 웃었다", "guest_password": "1234"})
    assert r.status_code == 201
    assert r.json()["data"]["author_name"] == "익명의 프라우더 🫧"

    r = write(client, {"learned": "또", "guest_password": "1234"})
    assert r.status_code == 409
    assert r.json()["code"] == "DAILY_LIMIT_EXCEEDED"

    assert client.get("/v1/spaces/plaza/notes").status_code == 200  # 비회원 열람 가능


def test_delete_and_repost_is_blocked(client: TestClient):
    note_id = write(client, {"learned": "x", "guest_password": "1234"}).json()["data"][
        "id"
    ]
    r = client.delete(f"/v1/notes/{note_id}", headers={"X-Guest-Password": "0000"})
    assert r.json()["code"] == "GUEST_PASSWORD_MISMATCH"
    r = client.delete(f"/v1/notes/{note_id}", headers={"X-Guest-Password": "1234"})
    assert r.status_code == 200
    assert write(client, {"learned": "y", "guest_password": "1234"}).status_code == 409


def test_member_is_anonymous_too(client: TestClient, signup):
    alice = signup("a@x.com", "앨리스")
    r = write(client, {"achieved": "x"}, alice)
    assert r.json()["data"]["author_name"] == "익명의 프라우더 🫧"
    assert r.json()["data"]["is_mine"] is True


def test_keeps_only_latest_n(client: TestClient, signup):
    run_sql(client, "UPDATE spaces SET max_notes=3, daily_limit=NULL WHERE id='plaza'")
    alice = signup("a@x.com")
    for i in range(5):
        write(client, {"learned": f"n{i}"}, alice)
    page = client.get("/v1/spaces/plaza/notes").json()["data"]
    assert page["total"] == 3
    assert [n["learned"] for n in page["items"]] == ["n4", "n3", "n2"]


def test_no_comments_in_plaza(client: TestClient, signup):
    alice = signup("a@x.com")
    note_id = write(client, {"learned": "x"}, alice).json()["data"]["id"]
    r = client.post(
        f"/v1/notes/{note_id}/comments", json={"content": "hi"}, headers=alice
    )
    assert r.json()["code"] == "COMMENTS_DISABLED"


def test_space_policy_admin_only(client: TestClient, signup):
    user, admin = signup("a@x.com"), signup("admin@x.com", admin=True)
    body = {"page_size": 10}
    assert client.patch("/v1/spaces/plaza", json=body, headers=user).status_code == 403
    r = client.patch("/v1/spaces/plaza", json=body, headers=admin)
    assert r.json()["data"]["page_size"] == 10
