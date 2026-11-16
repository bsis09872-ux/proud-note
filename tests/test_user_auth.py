from fastapi.testclient import TestClient

from tests.conftest import PASSWORD


def test_signup_validation_and_duplicate(client: TestClient, signup):
    r = client.post(
        "/v1/users",
        json={"email": "a@x.com", "name": "앨리스", "password": "abcdefgh1"},
    )
    assert r.status_code == 422
    assert r.json()["code"] == "INVALID_USER"  # 특수문자 없음 -> 도메인 검증

    signup("a@x.com")
    r = client.post(
        "/v1/users", json={"email": "A@X.com", "name": "다른이", "password": PASSWORD}
    )
    assert r.status_code == 409
    assert r.json()["code"] == "EMAIL_ALREADY_EXISTS"


def test_login_and_me(client: TestClient, signup):
    headers = signup("a@x.com", "앨리스")
    r = client.get("/v1/users/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["data"]["name"] == "앨리스"

    assert client.get("/v1/users/me").status_code == 401
    r = client.get("/v1/users/me", headers={"Authorization": "Bearer nope"})
    assert r.json()["code"] == "INVALID_TOKEN"

    r = client.post(
        "/v1/auth/login", json={"email": "a@x.com", "password": "Wrong1234!"}
    )
    assert r.status_code == 401
    assert r.json()["code"] == "INVALID_CREDENTIALS"


def test_logout_revokes_token(client: TestClient, signup):
    headers = signup("a@x.com")
    assert client.post("/v1/auth/logout", headers=headers).status_code == 200
    r = client.get("/v1/users/me", headers=headers)
    assert r.status_code == 401
    assert r.json()["code"] == "TOKEN_REVOKED"


def test_change_password(client: TestClient, signup):
    headers = signup("a@x.com")
    r = client.patch(
        "/v1/users/me/password",
        json={"old_password": "Wrong1234!", "new_password": "New1234!!"},
        headers=headers,
    )
    assert r.json()["code"] == "INVALID_OLD_PASSWORD"
    r = client.patch(
        "/v1/users/me/password",
        json={"old_password": PASSWORD, "new_password": "New1234!!"},
        headers=headers,
    )
    assert r.status_code == 200
    r = client.post(
        "/v1/auth/login", json={"email": "a@x.com", "password": "New1234!!"}
    )
    assert r.status_code == 200


def test_withdraw_blocks_login(client: TestClient, signup):
    headers = signup("a@x.com")
    assert client.delete("/v1/users/me", headers=headers).status_code == 200
    assert (
        client.get("/v1/users/me", headers=headers).json()["code"] == "USER_WITHDRAWN"
    )
    r = client.post("/v1/auth/login", json={"email": "a@x.com", "password": PASSWORD})
    assert r.status_code == 401
