def make_project(client):
    return client.post("/api/projects", json={"name": "章节测试书"}).json()


def test_chapter_atomic_save_and_snapshot(client):
    project = make_project(client)
    base = f"/api/projects/{project['id']}/chapters"

    created = client.post(base, json={"title": "第1章"}).json()
    chapter_id = created["id"]

    saved = client.put(f"{base}/{chapter_id}", json={"content_md": "晨雾未散，山门在望。"})
    assert saved.status_code == 200
    assert saved.json()["wordCount"] == 10
    assert saved.json()["contentMd"] == "晨雾未散，山门在望。"

    # 第二次保存应产生自动快照
    client.put(f"{base}/{chapter_id}", json={"content_md": "新的正文内容。"})
    detail = client.get(f"{base}/{chapter_id}").json()
    assert detail["contentMd"] == "新的正文内容。"

    # 章节文件存在
    import sqlite3
    from pathlib import Path

    db = Path(project["dataDir"], "novel.db")
    conn = sqlite3.connect(db)
    row = conn.execute("select count(*) from chapter_snapshots").fetchone()
    conn.close()
    assert row[0] == 1


def test_chapter_delete_unlinks_outline(client):
    project = client.post("/api/projects", json={"name": "章节删除测试书"}).json()
    outline = f"/api/projects/{project['id']}/outline"
    volume = client.post(outline, json={"level": "volume", "title": "第一卷"}).json()
    node = client.post(
        outline, json={"level": "chapter", "title": "第1章", "parent_id": volume["id"]}
    ).json()
    chapter = client.post(f"{outline}/{node['id']}/create-chapter").json()

    assert client.delete(f"/api/projects/{project['id']}/chapters/{chapter['id']}").status_code == 204
    updated = client.get(f"{outline}/{node['id']}").json()
    assert updated["chapterId"] is None
