"""封面生成真实联调：调用 Seedream 5.0 生成一张测试图并保存到本地。

要求：后端已在 localhost:8000 运行，.env 已配置 AI_NOVEL_SEEDREAM_API_KEY 与模型标识。
用法：
    .venv\\Scripts\\python scripts\\cover_smoke.py [输出路径]
"""

import json
import os
import sys
import time
import urllib.request

BASE = os.environ.get("AI_SMOKE_BASE", "http://localhost:8000")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    ROOT,
    "prototype",
    "cover-test.png",
)


def req(method: str, path: str, body: dict | None = None, timeout: int = 240):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"} if data else {},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        return resp.status, json.load(resp)


def main() -> int:
    stamp = time.strftime("%H%M%S")
    _, project = req("POST", "/api/projects", {"name": f"封面联调{stamp}"})
    pid = project["id"]
    print(f"project: {pid}")

    print("generating (may take 30-120s)...")
    t0 = time.perf_counter()
    st, task = req(
        "POST",
        f"/api/projects/{pid}/covers",
        {
            "prompt": "云海之上的仙山，青金色灵气环绕，史诗感，国风水墨，无文字",
            "params": {"size": "1920x1920"},
        },
        timeout=240,
    )
    print(f"task status={task.get('status')} ({time.perf_counter() - t0:.1f}s)")
    if task.get("error"):
        print("error:", task["error"])
    if task.get("status") != "success":
        print("COVER SMOKE FAILED")
        return 1

    with urllib.request.urlopen(
        f"{BASE}/api/projects/{pid}/covers/{task['id']}/file", timeout=60
    ) as resp:
        data = resp.read()
    with open(OUT, "wb") as fh:
        fh.write(data)
    print(f"COVER SMOKE PASSED: {len(data)} bytes -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
