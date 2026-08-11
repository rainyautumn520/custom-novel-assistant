def build_project(client, name):
    project = client.post("/api/projects", json={"name": name}).json()
    outline = f"/api/projects/{project['id']}/outline"
    volume = client.post(outline, json={"level": "volume", "title": "第一卷"}).json()
    node1 = client.post(
        outline, json={"level": "chapter", "title": "第1章", "parent_id": volume["id"]}
    ).json()
    node2 = client.post(
        outline, json={"level": "chapter", "title": "第2章", "parent_id": volume["id"]}
    ).json()
    chapter = client.post(f"{outline}/{node1['id']}/create-chapter").json()
    chapters = f"/api/projects/{project['id']}/chapters"
    client.put(
        f"{chapters}/{chapter['id']}",
        json={"contentMd": "第一章正文内容。"},
    )
    return project, volume, chapter, node2


def test_export_single_and_book(client):
    project, volume, chapter, node2 = build_project(client, "导出测试书")
    base = f"/api/projects/{project['id']}/exports"

    preview = client.get(f"{base}/preview").json()
    assert preview["exportedCount"] == 1
    assert preview["skippedCount"] == 1
    assert preview["items"][0]["chapterTitle"] == "第1章"

    single = client.post(f"{base}/single", json={"chapterId": chapter["id"]}).json()
    assert single["chaptersExported"] == 1
    with open(single["path"], "rb") as fh:
        data = fh.read()
    assert data.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM
    text = data.decode("utf-8-sig")
    assert "第1章" in text and "第一章正文内容。" in text

    book = client.post(f"{base}/book", json={"includeVolume": True, "includeChapter": True}).json()
    assert book["chaptersExported"] == 1
    assert book["chaptersSkipped"] == 1
    assert book["skippedTitles"] == ["第2章"]
    with open(book["path"], encoding="utf-8-sig") as fh:
        book_text = fh.read()
    assert "第一卷" in book_text
    assert "第1章" in book_text
    assert "第一章正文内容。" in book_text


def test_export_to_custom_path(client):
    import tempfile
    from pathlib import Path

    project, _volume, chapter, _node2 = build_project(client, "导出路径测试书")
    target = f"{tempfile.gettempdir()}/ai_novel_export_test.txt"
    resp = client.post(
        f"/api/projects/{project['id']}/exports/single",
        json={"chapterId": chapter["id"], "outputPath": target},
    )
    assert resp.status_code == 200
    assert resp.json()["path"] == str(Path(target))
