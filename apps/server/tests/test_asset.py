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


def test_asset_file_upload_download_delete(client):
    project = client.post("/api/projects", json={"name": "素材上传测试书"}).json()
    base = f"/api/projects/{project['id']}/assets"

    uploaded = client.post(
        f"{base}/upload",
        files={"file": ("北境地图.png", b"\x89PNG fake-image-bytes", "image/png")},
        data={"title": "北境地图", "source": "本地", "tags": "地图,北境"},
    ).json()
    assert uploaded["kind"] == "file"
    assert uploaded["tags"] == ["地图", "北境"]
    assert uploaded["filePath"].endswith("北境地图.png")

    download = client.get(f"{base}/{uploaded['id']}/file")
    assert download.status_code == 200
    assert download.content == b"\x89PNG fake-image-bytes"
    from urllib.parse import unquote

    assert "北境地图.png" in unquote(download.headers["content-disposition"])

    assert client.delete(f"{base}/{uploaded['id']}").status_code == 204
