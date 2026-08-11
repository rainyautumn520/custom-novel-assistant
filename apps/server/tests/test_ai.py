def make_project(client):
    return client.post("/api/projects", json={"name": "AI讨论测试书"}).json()


def test_ai_session_and_prompt(client):
    project = make_project(client)
    base = f"/api/projects/{project['id']}/ai"

    session = client.post(f"{base}/sessions", json={"title": "境界体系讨论"}).json()
    assert session["title"] == "境界体系讨论"
    assert len(client.get(f"{base}/sessions").json()) == 1
    assert client.get(f"{base}/sessions/{session['id']}/messages").json() == []

    client.put(f"{base}/prompt", json={"prompt": "文风偏古龙"})
    assert client.get(f"{base}/prompt").json() == {"prompt": "文风偏古龙"}

    assert client.delete(f"{base}/sessions/{session['id']}").status_code == 204


def test_ai_chat_without_credentials(client):
    project = client.post("/api/projects", json={"name": "AI无凭证测试书"}).json()
    base = f"/api/projects/{project['id']}/ai"
    session = client.post(f"{base}/sessions", json={}).json()
    resp = client.post(
        f"{base}/sessions/{session['id']}/chat", json={"content": "帮我想一个境界体系"}
    )
    assert resp.status_code == 503
