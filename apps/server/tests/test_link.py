def test_character_setting_links(client):
    project = client.post("/api/projects", json={"name": "关联测试书"}).json()
    settings = f"/api/projects/{project['id']}/settings"
    characters = f"/api/projects/{project['id']}/characters"
    s1 = client.post(settings, json={"title": "灵气复苏"}).json()
    s2 = client.post(settings, json={"title": "天元学宫"}).json()
    character = client.post(characters, json={"name": "林晚"}).json()

    links_url = f"{characters}/{character['id']}/links"
    created = client.put(links_url, json={"settingIds": [s1["id"], s2["id"]]})
    assert created.status_code == 200
    assert len(created.json()) == 2

    listed = client.get(links_url).json()
    assert {item["targetId"] for item in listed} == {s1["id"], s2["id"]}

    replaced = client.put(links_url, json={"settingIds": [s2["id"]]}).json()
    assert len(replaced) == 1
    assert replaced[0]["targetId"] == s2["id"]
