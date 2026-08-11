def build(client, name):
    project = client.post("/api/projects", json={"name": name}).json()
    outline = f"/api/projects/{project['id']}/outline"
    volume = client.post(outline, json={"level": "volume", "title": "第一卷"}).json()
    node = client.post(
        outline,
        json={
            "level": "chapter",
            "title": "第1章 初入天元",
            "parent_id": volume["id"],
            "goal": "主角完成学宫报到",
            "mustCover": ["报到", "林晚"],
            "forbidden": ["真相"],
            "targetWords": 500,
        },
    ).json()
    chapter = client.post(f"{outline}/{node['id']}/create-chapter").json()
    chapters = f"/api/projects/{project['id']}/chapters"
    client.put(
        f"{chapters}/{chapter['id']}",
        json={"contentMd": "晨雾未散，主角来到学宫报到，与林晚重逢。"},
    )
    return project, node, chapter


def test_brief_local(client):
    project, node, _chapter = build(client, "任务书测试书")
    resp = client.post(f"/api/projects/{project['id']}/brief/{node['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "local"
    assert "开篇委托" in data["sections"]
    assert "本章故事" in data["sections"]
    assert "主角完成学宫报到" in data["sections"]["本章故事"]


def test_review_local_rules(client):
    project, _node, chapter = build(client, "审查测试书")
    resp = client.post(f"/api/projects/{project['id']}/chapters/{chapter['id']}/review")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "local"
    names = {d["name"] for d in data["dims"]}
    assert names == {"设定一致性", "时间线", "叙事连贯", "角色一致性", "逻辑"}


def test_review_catches_forbidden_word(client):
    project, _node, chapter = build(client, "禁区测试书")
    chapters = f"/api/projects/{project['id']}/chapters"
    client.put(f"{chapters}/{chapter['id']}", json={"contentMd": "真相被揭开了。"})
    data = client.post(
        f"/api/projects/{project['id']}/chapters/{chapter['id']}/review"
    ).json()
    assert data["dims"][0]["status"] == "fail"


def test_assist_requires_credentials(client):
    project, _node, chapter = build(client, "续写凭证测试书")
    resp = client.post(
        f"/api/projects/{project['id']}/chapters/{chapter['id']}/assist",
        json={"mode": "continue"},
    )
    assert resp.status_code == 503
