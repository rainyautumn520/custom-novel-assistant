def test_asset_crud(client):
    project = client.post("/api/projects", json={"name": "素材测试书"}).json()
    base = f"/api/projects/{project['id']}/assets"

    created = client.post(
        base,
        json={"title": "北境地图灵感", "contentMd": "群山与灵脉分布", "tags": ["地图", "北境"]},
    ).json()
    assert created["title"] == "北境地图灵感"
    assert created["tags"] == ["地图", "北境"]

    updated = client.put(
        f"{base}/{created['id']}", json={"source": "资料书 P.42", "notes": "待考证"}
    ).json()
    assert updated["source"] == "资料书 P.42"

    assert len(client.get(base).json()) == 1
    assert client.delete(f"{base}/{created['id']}").status_code == 204
    assert client.get(f"{base}/{created['id']}").status_code == 404
