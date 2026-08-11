def build(client, name):
    project = client.post("/api/projects", json={"name": name}).json()
    outline = f"/api/projects/{project['id']}/outline"
    volume = client.post(outline, json={"level": "volume", "title": "第一卷"}).json()
    node1 = client.post(
        outline,
        json={
            "level": "chapter",
            "title": "第1章",
            "parent_id": volume["id"],
            "strands": ["quest", "fire"],
        },
    ).json()
    node2 = client.post(
        outline,
        json={"level": "chapter", "title": "第2章", "parent_id": volume["id"]},
    ).json()
    return project, volume, node1, node2


def test_rhythm_stats(client):
    project, _volume, node1, node2 = build(client, "节奏测试书")
    base = f"/api/projects/{project['id']}/outline"
    for node in (node1, node2):
        client.post(f"{base}/{node['id']}/create-chapter")

    data = client.get(f"/api/projects/{project['id']}/rhythm").json()
    quest = data["strands"]["quest"]
    assert quest["chapters"] == 1
    assert quest["ratio"] == 0.5
    assert quest["maxGap"] == 1
    assert quest["ok"] is True
    assert data["strands"]["constellation"]["maxGap"] == 2
    assert len(data["timeline"]) == 2
    assert data["timeline"][0]["strands"] == ["quest", "fire"]


def test_rhythm_gap_exceeds_limit(client):
    project = client.post("/api/projects", json={"name": "断档测试书"}).json()
    outline = f"/api/projects/{project['id']}/outline"
    volume = client.post(outline, json={"level": "volume", "title": "第一卷"}).json()
    client.post(
        outline,
        json={"level": "chapter", "title": "第1章", "parent_id": volume["id"], "strands": ["fire"]},
    )
    for i in range(11):
        client.post(
            outline, json={"level": "chapter", "title": f"第{i + 2}章", "parent_id": volume["id"]}
        )
    data = client.get(f"/api/projects/{project['id']}/rhythm").json()
    assert data["strands"]["fire"]["maxGap"] == 11
    assert data["strands"]["fire"]["ok"] is False
