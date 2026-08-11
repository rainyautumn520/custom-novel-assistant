def test_chekhov_crud(client):
    project = client.post("/api/projects", json={"name": "伏笔测试书"}).json()
    base = f"/api/projects/{project['id']}/chekhovs"

    created = client.post(
        base,
        json={"title": "山海令的来历", "description": "第1章提到令牌纹路", "status": "open"},
    ).json()
    assert created["status"] == "open"

    updated = client.put(
        f"{base}/{created['id']}", json={"status": "resolved"}
    ).json()
    assert updated["status"] == "resolved"
    assert len(client.get(base).json()) == 1
    assert client.delete(f"{base}/{created['id']}").status_code == 204


def test_doctor_detects_dangling_link(client):
    project = client.post("/api/projects", json={"name": "体检测试书"}).json()
    settings = f"/api/projects/{project['id']}/settings"
    characters = f"/api/projects/{project['id']}/characters"
    s = client.post(settings, json={"title": "灵气复苏"}).json()
    c = client.post(characters, json={"name": "林晚"}).json()
    client.put(
        f"{characters}/{c['id']}/links", json={"settingIds": [s["id"]]}
    )
    client.delete(f"{settings}/{s['id']}")

    data = client.get(f"/api/projects/{project['id']}/doctor").json()
    dangling = next(check for check in data["checks"] if check["id"] == "dangling_links")
    assert dangling["status"] == "fail"
    assert data["healthy"] is False
