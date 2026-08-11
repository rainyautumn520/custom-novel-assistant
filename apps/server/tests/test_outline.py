def make_project(client):
    return client.post("/api/projects", json={"name": "大纲测试书"}).json()


def test_outline_hierarchy_rules(client):
    project = make_project(client)
    base = f"/api/projects/{project['id']}/outline"

    volume = client.post(base, json={"level": "volume", "title": "第一卷 灵起"}).json()
    assert volume["level"] == "volume"

    # 卷纲不能有父节点
    assert (
        client.post(base, json={"level": "volume", "title": "x", "parent_id": volume["id"]}).status_code
        == 422
    )
    # 章纲必须有卷父节点
    assert client.post(base, json={"level": "chapter", "title": "x"}).status_code == 422
    # 章纲挂在细纲下非法
    beat = client.post(
        base,
        json={"level": "beat", "title": "细纲1", "parent_id": volume["id"]},
    )
    assert beat.status_code == 422

    chapter = client.post(
        base, json={"level": "chapter", "title": "第1章", "parent_id": volume["id"]}
    ).json()
    beat = client.post(
        base, json={"level": "beat", "title": "细纲1", "parent_id": chapter["id"]}
    ).json()
    assert beat["level"] == "beat"

    # 删除有子节点的卷 → 409
    assert client.delete(f"{base}/{volume['id']}").status_code == 409
    # 删除叶子节点 → 204
    assert client.delete(f"{base}/{beat['id']}").status_code == 204


def test_create_chapter_from_chapter_node(client):
    project = client.post("/api/projects", json={"name": "大纲建章测试书"}).json()
    base = f"/api/projects/{project['id']}/outline"
    volume = client.post(base, json={"level": "volume", "title": "第一卷"}).json()
    chapter_node = client.post(
        base, json={"level": "chapter", "title": "第1章", "parent_id": volume["id"]}
    ).json()

    chapter = client.post(f"{base}/{chapter_node['id']}/create-chapter").json()
    assert chapter["title"] == "第1章"
    # 再次调用返回同一章节
    again = client.post(f"{base}/{chapter_node['id']}/create-chapter").json()
    assert again["id"] == chapter["id"]
