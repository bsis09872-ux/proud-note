from fastapi.testclient import TestClient


def write(client, space, body, headers=None):
    return client.post(f"/v1/spaces/{space}/notes", json=body, headers=headers or {})


def test_friends_is_members_only(client: TestClient, signup):
    assert client.get("/v1/spaces/friends/notes").status_code == 401
    assert write(client, "friends", {"learned": "x"}).status_code == 401

    alice = signup("a@x.com", "앨리스")
    r = write(client, "friends", {"learned": "JWT", "tags": ["#Auth", "auth"]}, alice)
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["author_name"] == "앨리스"
    assert data["tags"] == ["auth"]  # 소문자·중복 제거
    assert data["is_mine"] is True


def test_note_needs_at_least_one_field(client: TestClient, signup):
    alice = signup("a@x.com")
    r = write(client, "friends", {"learned": "  "}, alice)
    assert r.status_code == 422
    assert r.json()["code"] == "INVALID_NOTE"


def test_only_owner_can_edit(client: TestClient, signup):
    alice, bob = signup("a@x.com"), signup("b@x.com")
    admin = signup("admin@x.com", admin=True)
    note_id = write(client, "friends", {"achieved": "버그 잡음"}, alice).json()["data"][
        "id"
    ]

    r = client.patch(f"/v1/notes/{note_id}", json={"achieved": "x"}, headers=bob)
    assert r.json()["code"] == "NOT_OWNER"
    r = client.patch(
        f"/v1/notes/{note_id}", json={"proud_of_me": "잘 웃었다"}, headers=alice
    )
    assert r.json()["data"]["proud_of_me"] == "잘 웃었다"
    assert client.delete(f"/v1/notes/{note_id}", headers=admin).status_code == 200
    assert client.get(f"/v1/notes/{note_id}", headers=alice).status_code == 404


def test_list_paging_and_search(client: TestClient, signup):
    alice = signup("a@x.com")
    for i in range(3):
        write(client, "friends", {"learned": f"파이썬 {i}", "tags": ["python"]}, alice)
    write(client, "friends", {"learned": "도커 공부", "tags": ["docker"]}, alice)

    page = client.get("/v1/spaces/friends/notes?size=2", headers=alice).json()["data"]
    assert (page["total"], page["total_pages"], len(page["items"])) == (4, 2, 2)
    assert page["items"][0]["learned"] == "도커 공부"  # 최신순

    by_tag = client.get("/v1/spaces/friends/notes?tag=python", headers=alice).json()[
        "data"
    ]
    assert by_tag["total"] == 3
    by_kw = client.get("/v1/spaces/friends/notes?keyword=도커", headers=alice).json()[
        "data"
    ]
    assert by_kw["total"] == 1


def test_comments(client: TestClient, signup):
    alice, bob = signup("a@x.com"), signup("b@x.com", "밥이")
    note_id = write(client, "friends", {"learned": "x"}, alice).json()["data"]["id"]

    assert (
        client.post(
            f"/v1/notes/{note_id}/comments", json={"content": "멋져"}
        ).status_code
        == 401
    )
    r = client.post(
        f"/v1/notes/{note_id}/comments", json={"content": "멋져요!"}, headers=bob
    )
    comment_id = r.json()["data"]["id"]
    r = client.patch(f"/v1/comments/{comment_id}", json={"content": "x"}, headers=alice)
    assert r.json()["code"] == "NOT_OWNER"
    comments = client.get(f"/v1/notes/{note_id}/comments", headers=alice).json()["data"]
    assert [c["author_name"] for c in comments] == ["밥이"]


def test_writing_guide(client: TestClient):
    data = client.get("/v1/notes/writing-guide?space_id=plaza").json()["data"]
    assert [f["key"] for f in data["fields"]] == ["learned", "achieved", "proud_of_me"]
    assert any("하루에 한 번" in tip for tip in data["tips"])
