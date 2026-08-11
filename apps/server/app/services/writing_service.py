"""v0.3 写章流水线：任务书 / 续写改写 / 五维审查。"""

import json
from typing import Any

import httpx
from sqlalchemy import select

from app.config import settings
from app.core.database import project_db_path, project_session
from app.models.character import Character
from app.models.chapter import Chapter
from app.models.outline import OutlineNode
from app.models.world import Setting


def _call_llm(system: str, user: str, temperature: float = 0.7) -> str:
    if not settings.deepseek_api_key:
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="AI 凭证未配置（AI_NOVEL_DEEPSEEK_API_KEY）")
    resp = httpx.post(
        f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
        json={
            "model": settings.deepseek_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
        },
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _related_settings(project_id: str, query: str) -> list[dict]:
    try:
        from app.services import rag_service

        return rag_service.search_vector(project_id, query, top_k=6)
    except Exception:
        return []


def _chapter_context(project_id: str, chapter: Chapter) -> tuple[str, OutlineNode | None]:
    root = project_db_path(project_id).parent
    content = (root / chapter.file_path).read_text(encoding="utf-8") if (
        root / chapter.file_path
    ).exists() else ""
    node = None
    with project_session(project_id) as session:
        if chapter.outline_node_id:
            node = session.get(OutlineNode, chapter.outline_node_id)
    return content, node


def build_brief(project_id: str, node_id: str) -> dict[str, Any]:
    """五段写作任务书：本地数据组装；配置 Key 后由 AI 润色为写作建议。"""
    from fastapi import HTTPException

    with project_session(project_id) as session:
        node = session.get(OutlineNode, node_id)
        if node is None or node.level != "chapter":
            raise HTTPException(status_code=404, detail="章纲不存在")
        chapters = list(session.scalars(select(Chapter).order_by(Chapter.created_at)))
        characters = list(session.scalars(select(Character).order_by(Character.name)))
        settings_rows = list(
            session.scalars(select(Setting).where(Setting.status == "confirmed").limit(15))
        )

    prev_summary = ""
    for ch in reversed(chapters):
        if ch.id != (chapters[-1].id if chapters else None) and ch.created_at < node.created_at:
            path = project_db_path(project_id).parent / ch.file_path
            if path.exists():
                prev_summary = path.read_text(encoding="utf-8")[-500:]
                break

    related = _related_settings(project_id, f"{node.title} {node.goal}")
    related_lines = "\n".join(f"- {r['title']}：{r['snippet'][:80]}" for r in related) or "（无）"
    character_lines = "\n".join(f"- {c.name}：{c.identity}" for c in characters[:10]) or "（无）"
    setting_lines = "\n".join(f"- {s.title}：{s.content_md[:100]}" for s in settings_rows) or "（无）"

    sections = {
        "开篇委托": prev_summary[-300:] or "本章为新卷/新线开局，直接进入本章场景。",
        "本章故事": (
            f"目标：{node.goal or '（未填写）'}\n"
            f"必须覆盖：{('、'.join(node.must_cover)) or '（无）'}\n"
            f"禁区：{('、'.join(node.forbidden)) or '（无）'}\n"
            f"目标字数：{node.target_words or 2500}"
        ),
        "本章人物": character_lines,
        "相关设定": setting_lines + "\nRAG 相关：" + related_lines,
        "收在哪": "建议：停在冲突升级或新信息出现的节点，留钩子。",
    }

    if settings.deepseek_api_key:
        try:
            polished = _call_llm(
                "你是网文写作助手的任务书生成器。基于素材生成简洁可执行的五段任务书，每段 60-120 字。",
                "素材：\n" + json.dumps(sections, ensure_ascii=False),
            )
            return {"mode": "ai", "sections": sections, "polished": polished}
        except Exception:
            pass
    return {"mode": "local", "sections": sections, "polished": ""}


def assist(
    project_id: str,
    chapter_id: str,
    mode: str,
    selection: str = "",
    instructions: str = "",
) -> dict[str, Any]:
    """续写/改写建议（AI，需凭证）。"""
    with project_session(project_id) as session:
        chapter = session.get(Chapter, chapter_id)
        if chapter is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="章节不存在")
    content, node = _chapter_context(project_id, chapter)
    related = _related_settings(project_id, content[-500:] + (node.goal if node else ""))
    related_lines = "\n".join(f"- {r['title']}：{r['snippet'][:80]}" for r in related) or "（无）"
    contract = (
        f"目标：{node.goal}\n必须覆盖：{'、'.join(node.must_cover)}\n禁区：{'、'.join(node.forbidden)}"
        if node
        else "（无章纲合同）"
    )

    if mode == "rewrite":
        system = "你是网文改写助手。只输出改写后的段落本身，不要解释，保持原意与文风，避免 AI 味。"
        user = (
            f"章纲合同：{contract}\n相关设定：{related_lines}\n\n"
            f"作者要求：{instructions or '更自然、更有画面感'}\n\n改写以下段落：\n{selection}"
        )
    else:
        system = "你是网文续写助手。只输出续写正文（300-500字），不解释；严格遵循章纲与设定，不得违背禁区。"
        user = (
            f"章纲合同：{contract}\n相关设定：{related_lines}\n\n"
            f"当前正文（末尾）：\n{content[-2500:]}\n\n"
            f"作者要求：{instructions or '自然衔接，推进情节'}"
        )
    suggestion = _call_llm(system, user)
    return {"mode": mode, "suggestion": suggestion}


def review(project_id: str, chapter_id: str) -> dict[str, Any]:
    """五维审查：无凭证时运行本地规则，有凭证时 AI 增强。"""
    with project_session(project_id) as session:
        chapter = session.get(Chapter, chapter_id)
        if chapter is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="章节不存在")
    content, node = _chapter_context(project_id, chapter)

    dims = [
        {"name": "设定一致性", "status": "pass", "issues": []},
        {"name": "时间线", "status": "pass", "issues": []},
        {"name": "叙事连贯", "status": "pass", "issues": []},
        {"name": "角色一致性", "status": "pass", "issues": []},
        {"name": "逻辑", "status": "pass", "issues": []},
    ]

    # 本地规则
    if node:
        if node.forbidden:
            hits = [w for w in node.forbidden if w and w in content]
            if hits:
                dims[0]["status"] = "fail"
                dims[0]["issues"] = [f"命中禁区词：{ '、'.join(hits) }"]
        if node.target_words and len(content.replace(" ", "")) < node.target_words:
            dims[2]["status"] = "warn"
            dims[2]["issues"] = [
                f"字数 {len(content.replace(' ', ''))}，低于目标 {node.target_words}"
            ]
        if node.must_cover:
            missing = [m for m in node.must_cover if m and m not in content]
            if missing:
                dims[1]["status"] = "warn"
                dims[1]["issues"] = [f"必须覆盖节点未在正文出现：{'、'.join(missing)}"]

    if not settings.deepseek_api_key:
        return {
            "mode": "local",
            "summary": "本地规则检查完成；配置 AI Key 后可获得完整五维审查。",
            "dims": dims,
        }

    related = _related_settings(project_id, content[-800:])
    related_lines = "\n".join(f"- {r['title']}：{r['snippet'][:80]}" for r in related) or "（无）"
    contract = (
        f"目标：{node.goal}\n必须覆盖：{'、'.join(node.must_cover)}\n禁区：{'、'.join(node.forbidden)}"
        if node
        else "（无章纲合同）"
    )
    system = (
        "你是网文五维审查员。对给定章节输出 JSON：{\"dims\":[{\"name\":\"设定一致性|时间线|叙事连贯|角色一致性|逻辑\","
        "\"status\":\"pass|warn|fail\",\"issues\":[\"具体问题\"]}],\"summary\":\"总评\"}。"
        "只输出 JSON，不要其他文字。"
    )
    user = f"章纲合同：{contract}\n相关设定：{related_lines}\n\n正文：\n{content[:6000]}"
    try:
        raw = _call_llm(system, user, temperature=0.2)
        data = json.loads(raw[raw.find("{") : raw.rfind("}") + 1])
        return {"mode": "ai", "summary": data.get("summary", ""), "dims": data.get("dims", dims)}
    except Exception:
        return {
            "mode": "local",
            "summary": "AI 审查失败，已回退本地规则。",
            "dims": dims,
        }
