def make_project(client, name):
    return client.post("/api/projects", json={"name": name}).json()


def test_cover_task_registered(client):
    project = make_project(client, "封面测试书")
    base = f"/api/projects/{project['id']}/covers"
    created = client.post(
        base, json={"prompt": "玄幻大陆俯瞰图", "params": {"size": "1024x1024"}}
    ).json()
    assert created["status"] in ("queued", "failed")
    assert created["prompt"] == "玄幻大陆俯瞰图"
    assert len(client.get(base).json()) == 1


def test_cover_task_real_call_success(client, monkeypatch):
    import base64
    import io

    import httpx
    from PIL import Image

    from app.services.cover_service import settings

    monkeypatch.setattr(settings, "seedream_api_key", "test-ark-key")

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            buf = io.BytesIO()
            Image.new("RGB", (64, 64), (80, 120, 200)).save(buf, format="PNG")
            return {"data": [{"b64_json": base64.b64encode(buf.getvalue()).decode()}]}

    monkeypatch.setattr(httpx, "post", lambda *a, **k: FakeResponse())

    project = client.post("/api/projects", json={"name": "封面真实调用测试书"}).json()
    base = f"/api/projects/{project['id']}/covers"
    created = client.post(
        base, json={"prompt": "云海仙山", "params": {"size": "1024x1024"}}
    ).json()
    assert created["status"] == "success"
    assert created["resultPath"].endswith(".png")

    download = client.get(f"{base}/{created['id']}/file")
    assert download.status_code == 200
    assert download.content[:8] == b"\x89PNG\r\n\x1a\n"

    composed = client.post(
        f"{base}/{created['id']}/compose",
        json={"title": "大梦山海", "author": "灵风"},
    )
    assert composed.status_code == 200
    assert composed.json()["composedPath"].endswith("_composed.png")
    comp_img = client.get(f"{base}/{created['id']}/composed")
    assert comp_img.status_code == 200
    assert comp_img.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_search_and_links(client):
    project = make_project(client, "检索测试书")
    pid = project["id"]
    settings = f"/api/projects/{pid}/settings"
    characters = f"/api/projects/{pid}/characters"
    assets = f"/api/projects/{pid}/assets"

    s = client.post(settings, json={"title": "灵气复苏", "contentMd": "天元历1024年开始"}).json()
    c = client.post(characters, json={"name": "林晚", "identity": "天元学宫弟子"}).json()
    client.post(assets, json={"title": "北境笔记", "contentMd": "灵脉分布图"}).json()

    result = client.post(f"/api/projects/{pid}/search", json={"query": "灵"}).json()
    titles = {item["title"] for item in result}
    assert "灵气复苏" in titles
    assert "北境笔记" in titles

    client.put(f"/api/projects/{pid}/characters/{c['id']}/links", json={"settingIds": [s["id"]]})
    links = client.get(f"/api/projects/{pid}/links").json()
    assert len(links) == 1
    assert links[0]["sourceType"] == "character"
    assert links[0]["targetId"] == s["id"]
