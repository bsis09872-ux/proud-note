from fastapi.testclient import TestClient

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def upload(client, name, headers, data=PNG):
    return client.post(
        "/v1/emojis",
        data={"name": name},
        files={"image": ("e.png", data, "image/png")},
        headers=headers,
    )


def make_note(client, headers):
    r = client.post("/v1/spaces/friends/notes", json={"learned": "x"}, headers=headers)
    return r.json()["data"]["id"]


def test_custom_emoji_upload(client: TestClient, signup):
    alice, bob = signup("a@x.com"), signup("b@x.com")
    assert upload(client, "party", {}).status_code == 401
    r = upload(client, "party", alice)
    assert r.status_code == 201
    image_url = r.json()["data"]["image_url"]
    assert client.get(image_url).status_code == 200  # /media 서빙

    assert upload(client, "party", bob).json()["code"] == "EMOJI_NAME_TAKEN"
    assert (
        upload(client, "fake", bob, data=b"not an image").json()["code"]
        == "INVALID_EMOJI_IMAGE"
    )
    assert upload(client, "Bad Name!", bob).json()["code"] == "INVALID_EMOJI"
    assert (
        client.delete("/v1/emojis/party", headers=bob).json()["code"]
        == "NOT_EMOJI_OWNER"
    )


def test_reactions(client: TestClient, signup):
    alice, bob = signup("a@x.com"), signup("b@x.com")
    upload(client, "party", alice)
    note_id = make_note(client, alice)
    url = f"/v1/notes/{note_id}/reactions"

    assert client.post(url, json={"emoji": "🎉"}, headers=bob).status_code == 201
    assert client.post(url, json={"emoji": "🎉"}, headers=bob).status_code == 409
    assert client.post(url, json={"emoji": "🎉"}, headers=alice).status_code == 201
    assert client.post(url, json={"emoji": ":party:"}, headers=bob).status_code == 201
    assert client.post(url, json={"emoji": ":nope:"}, headers=bob).status_code == 404
    assert client.post(url, json={"emoji": "abc"}, headers=bob).status_code == 422

    summary = client.get(url, headers=bob).json()["data"]
    assert [(s["emoji"], s["count"], s["reacted_by_me"]) for s in summary] == [
        ("🎉", 2, True),
        (":party:", 1, True),
    ]
    assert summary[1]["image_url"].startswith("/media/emojis/")

    # 취소하면 캐시도 바로 갱신
    assert client.delete(url, params={"emoji": "🎉"}, headers=bob).status_code == 200
    summary = client.get(url, headers=alice).json()["data"]
    assert summary[0] == {
        "emoji": "🎉",
        "count": 1,
        "reacted_by_me": True,
        "image_url": None,
    }


def test_deleting_emoji_removes_its_reactions(client: TestClient, signup):
    alice = signup("a@x.com")
    upload(client, "party", alice)
    note_id = make_note(client, alice)
    client.post(
        f"/v1/notes/{note_id}/reactions", json={"emoji": ":party:"}, headers=alice
    )
    assert client.delete("/v1/emojis/party", headers=alice).status_code == 200
    assert (
        client.get(f"/v1/notes/{note_id}/reactions", headers=alice).json()["data"] == []
    )


def test_guest_cannot_react(client: TestClient, signup):
    alice = signup("a@x.com")
    note_id = client.post(
        "/v1/spaces/plaza/notes", json={"learned": "x"}, headers=alice
    ).json()["data"]["id"]
    r = client.post(f"/v1/notes/{note_id}/reactions", json={"emoji": "🎉"})
    assert r.status_code == 401
