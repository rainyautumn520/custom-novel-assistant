def test_character_crud_flow(client):
    project = client.post("/api/projects", json={"name": "人物测试书"}).json()
    base = f"/api/projects/{project['id']}/characters"

    created = client.post(
        base, json={"name": "林晚", "identity": "天元学宫弟子", "tags": ["女主"]}
    )
    assert created.status_code == 201
    character = created.json()
    assert character["name"] == "林晚"

    updated = client.put(f"{base}/{character['id']}", json={"goals": "查明真相"})
    assert updated.json()["goals"] == "查明真相"

    assert len(client.get(base).json()) == 1
    assert client.delete(f"{base}/{character['id']}").status_code == 204
