def make_project(client):
    return client.post("/api/projects", json={"name": "设定测试书"}).json()


def test_setting_crud_flow(client):
    project = make_project(client)
    base = f"/api/projects/{project['id']}/settings"

    created = client.post(base, json={"title": "灵气复苏", "content_md": "天元历1024年", "tags": ["规则"]})
    assert created.status_code == 201
    setting = created.json()
    assert setting["title"] == "灵气复苏"
    assert setting["tags"] == ["规则"]

    listed = client.get(base).json()
    assert len(listed) == 1

    updated = client.put(
        f"{base}/{setting['id']}",
        json={"status": "confirmed", "content_md": "已确认版本"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "confirmed"

    deleted = client.delete(f"{base}/{setting['id']}")
    assert deleted.status_code == 204
    assert client.get(f"{base}/{setting['id']}").status_code == 404


def test_setting_requires_existing_project(client):
    resp = client.post("/api/projects/nope/settings", json={"title": "x"})
    assert resp.status_code == 404
