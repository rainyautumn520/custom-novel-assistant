def build(client, name):
    project = client.post("/api/projects", json={"name": name}).json()
    outline = f"/api/projects/{project['id']}/outline"
    settings = f"/api/projects/{project['id']}/settings"
    characters = f"/api/projects/{project['id']}/characters"
    client.post(
        settings, json={"title": "灵气复苏", "contentMd": "天元历1024年开始。", "status": "confirmed"}
    )
    character = client.post(characters, json={"name": "林晚", "identity": "学宫弟子"}).json()
    volume = client.post(outline, json={"level": "volume", "title": "第一卷"}).json()
    node = client.post(
        outline, json={"level": "chapter", "title": "第1章", "parent_id": volume["id"]}
    ).json()
    chapter = client.post(f"{outline}/{node['id']}/create-chapter").json()
    chapters = f"/api/projects/{project['id']}/chapters"
    client.put(
        f"{chapters}/{chapter['id']}",
        json={"contentMd": "晨雾中林晚站在学宫门前，灵气复苏已三年。"},
    )
    return project, chapter, character


def test_commit_flow(client):
    project, chapter, character = build(client, "提交链测试书")
    commits_url = f"/api/projects/{project['id']}/chapters/{chapter['id']}/commits"

    resp = client.post(f"/api/projects/{project['id']}/chapters/{chapter['id']}/commit")
    assert resp.status_code == 201
    commit = resp.json()
    assert commit["status"] == "accepted"
    assert commit["summaryText"]
    assert commit["projectionStatus"]["index"] == "done"
    entity_titles = [e["title"] for e in commit["entityDeltas"]]
    assert "林晚" in entity_titles
    assert "灵气复苏" in entity_titles

    listed = client.get(f"/api/projects/{project['id']}/commits").json()
    assert len(listed) == 1
    assert listed[0]["chapterTitle"] == "第1章"
    assert len(client.get(commits_url).json()) == 1

    rejected = client.post(f"/api/projects/{project['id']}/commits/{commit['id']}/reject").json()
    assert rejected["status"] == "rejected"
    chapter_detail = client.get(
        f"/api/projects/{project['id']}/chapters/{chapter['id']}"
    ).json()
    assert chapter_detail["status"] == "draft"


def test_commit_rejects_empty_chapter(client):
    project = client.post("/api/projects", json={"name": "空章节测试书"}).json()
    chapter = client.post(
        f"/api/projects/{project['id']}/chapters", json={"title": "空章"}
    ).json()
    resp = client.post(f"/api/projects/{project['id']}/chapters/{chapter['id']}/commit")
    assert resp.status_code == 422
