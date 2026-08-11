import pytest

from app.services import rag_service


def build(client, name):
    project = client.post("/api/projects", json={"name": name}).json()
    settings = f"/api/projects/{project['id']}/settings"
    client.post(
        settings,
        json={"title": "灵气复苏", "contentMd": "天元历1024年开始，灵气浓度每十年翻倍。", "status": "confirmed"},
    )
    client.post(
        settings,
        json={"title": "境界体系", "contentMd": "炼气、筑基、金丹、元婴四境。", "status": "confirmed"},
    )
    characters = f"/api/projects/{project['id']}/characters"
    client.post(characters, json={"name": "林晚", "identity": "天元学宫弟子"})
    return project


def test_rag_rebuild_and_vector_search(client):
    try:
        project = build(client, "RAG向量测试书")
    except Exception:
        pytest.skip("无法创建测试项目")
    result = rag_service.rebuild_index(project["id"])
    assert result["indexed"] >= 3
    status = rag_service.status(project["id"])
    assert status["count"] >= 3

    hits = rag_service.search_vector(project["id"], "境界怎么分", top_k=3)
    assert hits, "向量检索应返回结果"
    assert hits[0]["type"] == "setting"
    assert hits[0]["title"] == "境界体系"

    hits2 = rag_service.search_vector(project["id"], "林晚是谁", top_k=3)
    assert hits2[0]["type"] == "character"
    assert hits2[0]["title"] == "林晚"


def test_rag_status_endpoint(client):
    project = build(client, "RAG状态测试书")
    resp = client.get(f"/api/projects/{project['id']}/rag/status")
    assert resp.status_code == 200
    assert "backend" in resp.json()
    assert "count" in resp.json()
