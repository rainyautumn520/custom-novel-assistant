from pathlib import Path


def test_project_crud_flow(client):
    # 创建作品：应生成作品库文件
    resp = client.post(
        "/api/projects",
        json={"name": "测试之书", "genre": "玄幻", "synopsis": "测试", "target_words": 100000},
    )
    assert resp.status_code == 201
    project = resp.json()
    assert project["name"] == "测试之书"
    assert Path(project["dataDir"], "novel.db").exists()

    # 列表包含新作品
    listed = client.get("/api/projects").json()
    assert any(item["id"] == project["id"] for item in listed)

    # 按 ID 查询
    got = client.get(f"/api/projects/{project['id']}")
    assert got.status_code == 200
    assert got.json()["status"] == "active"

    # 不存在作品返回 404
    assert client.get("/api/projects/no-such-id").status_code == 404


def test_project_name_required(client):
    resp = client.post("/api/projects", json={"name": "   "})
    assert resp.status_code == 422
