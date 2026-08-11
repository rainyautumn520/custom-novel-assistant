"""AI 能力真实联调冒烟：任务书 / 续写 / 五维审查 / 设定讨论。

要求：后端已在 localhost:8000 运行，且 .env 已配置 AI_NOVEL_DEEPSEEK_API_KEY。
用法：
    .venv\\Scripts\\python scripts\\ai_smoke.py
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("AI_SMOKE_BASE", "http://localhost:8000")


def req(method: str, path: str, body: dict | None = None, timeout: int = 240):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"} if data else {},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def show(label: str, value, limit: int = 400) -> None:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    print(f"\n=== {label} ===")
    print(text[:limit] + ("..." if len(text) > limit else ""))


def main() -> int:
    stamp = time.strftime("%H%M%S")
    st, project = req("POST", "/api/projects", {"name": f"AI联调测试书{stamp}"})
    if st != 201:
        print("创建项目失败:", project)
        return 1
    pid = project["id"]
    print(f"project: {pid}")

    req("POST", f"/api/projects/{pid}/settings", {
        "title": "灵气复苏",
        "contentMd": "天元历1024年开始，灵气浓度每十年翻倍。",
        "status": "confirmed",
    })
    req("POST", f"/api/projects/{pid}/characters", {"name": "林晚", "identity": "天元学宫内门弟子"})
    req("POST", f"/api/projects/{pid}/characters", {"name": "张小凡", "identity": "灵脉村少年"})
    _, volume = req("POST", f"/api/projects/{pid}/outline", {"level": "volume", "title": "第一卷 灵起"})
    _, node = req("POST", f"/api/projects/{pid}/outline", {
        "level": "chapter",
        "parentId": volume["id"],
        "title": "第1章 初入天元",
        "goal": "主角完成学宫报到，与林晚重逢",
        "mustCover": ["报到", "林晚"],
        "forbidden": ["不揭示灵脉枯竭真相"],
        "targetWords": 800,
    })
    _, chapter = req("POST", f"/api/projects/{pid}/outline/{node['id']}/create-chapter")
    content = (
        "晨雾还未散尽，天元学宫的牌楼已经遥遥在望。\n\n"
        "张小凡攥紧手里的报到文书，指节微微发白。文书背面压着灵脉村的印章，"
        "边缘被汗水洇开了一小片。他抬起头，看见牌楼下立着一个人——墨色长发，"
        "左腕一道浅色灵纹，正是林晚。\n\n"
        "“你迟到了。”林晚说。\n\n"
        "牌楼两侧的石柱上，灵纹缓慢流转。灵气复苏之后的第三年，连学宫的门柱都刻满了阵法。"
    )
    req("PUT", f"/api/projects/{pid}/chapters/{chapter['id']}", {"contentMd": content})

    _, node_check = req("GET", f"/api/projects/{pid}/outline/{node['id']}")
    print("forbidden stored:", node_check.get("forbidden"))

    failures = []

    t0 = time.perf_counter()
    st, brief = req("POST", f"/api/projects/{pid}/brief/{node['id']}")
    ok = st == 200 and brief.get("mode") == "ai" and bool(brief.get("polished"))
    print(f"brief: {st} mode={brief.get('mode')} ok={ok} ({time.perf_counter() - t0:.1f}s)")
    show("AI 任务书", brief.get("polished") or brief)
    if not ok:
        failures.append("brief")

    t0 = time.perf_counter()
    st, assist = req("POST", f"/api/projects/{pid}/chapters/{chapter['id']}/assist", {
        "mode": "continue", "selection": "", "instructions": "自然衔接，画面感强",
    })
    ok = st == 200 and len(assist.get("suggestion", "")) > 80
    print(f"assist: {st} ok={ok} ({time.perf_counter() - t0:.1f}s)")
    show("AI 续写", assist.get("suggestion", assist))
    if not ok:
        failures.append("assist")

    t0 = time.perf_counter()
    st, review = req("POST", f"/api/projects/{pid}/chapters/{chapter['id']}/review")
    ok = st == 200 and review.get("mode") == "ai" and len(review.get("dims", [])) == 5
    print(f"review: {st} mode={review.get('mode')} ok={ok} ({time.perf_counter() - t0:.1f}s)")
    show("AI 五维审查", review, limit=700)
    if not ok:
        failures.append("review")

    _, ai_session = req("POST", f"/api/projects/{pid}/ai/sessions", {"title": "联调"})
    t0 = time.perf_counter()
    st, chat = req("POST", f"/api/projects/{pid}/ai/sessions/{ai_session['id']}/chat", {
        "content": "帮我设计一个贴合'灵气复苏'设定的境界体系",
    })
    ok = st == 200 and len(chat.get("reply", "")) > 40
    print(f"chat: {st} ok={ok} ({time.perf_counter() - t0:.1f}s)")
    show("AI 设定讨论", chat.get("reply", chat))
    if not ok:
        failures.append("chat")

    if failures:
        print("\nAI SMOKE FAILED:", ", ".join(failures))
        return 1
    print("\nAI SMOKE PASSED: brief / assist / review / chat all real LLM responses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
