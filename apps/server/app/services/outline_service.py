from sqlalchemy import select

from app.core.database import new_id, project_session
from app.models.chapter import Chapter
from app.models.outline import OutlineNode

PARENT_RULES = {
    "volume": None,
    "chapter": "volume",
    "beat": "chapter",
}


def _validate_parent(session, level: str, parent_id: str | None, exclude_id: str | None = None):
    from fastapi import HTTPException

    required_parent_level = PARENT_RULES[level]
    if required_parent_level is None:
        if parent_id is not None:
            raise HTTPException(status_code=422, detail="卷纲不能有父节点")
        return
    if parent_id is None:
        raise HTTPException(status_code=422, detail=f"{level} 必须有父节点")
    if exclude_id and parent_id == exclude_id:
        raise HTTPException(status_code=422, detail="不能移动到自身")
    parent = session.get(OutlineNode, parent_id)
    if parent is None:
        raise HTTPException(status_code=404, detail="父节点不存在")
    if parent.level != required_parent_level:
        raise HTTPException(
            status_code=422, detail=f"{level} 的父节点必须是 {required_parent_level}"
        )


def list_outline(project_id: str) -> list[OutlineNode]:
    with project_session(project_id) as session:
        return list(
            session.scalars(
                select(OutlineNode).order_by(
                    OutlineNode.parent_id, OutlineNode.sort_order, OutlineNode.created_at
                )
            )
        )


def create_node(project_id: str, data: dict) -> OutlineNode:
    with project_session(project_id) as session:
        _validate_parent(session, data["level"], data.get("parent_id"))
        node = OutlineNode(**data)
        session.add(node)
        session.commit()
        session.refresh(node)
        return node


def get_node_or_404(project_id: str, node_id: str) -> OutlineNode:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        node = session.get(OutlineNode, node_id)
        if node is None:
            raise HTTPException(status_code=404, detail="大纲节点不存在")
        return node


def update_node(project_id: str, node_id: str, data: dict) -> OutlineNode:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        node = session.get(OutlineNode, node_id)
        if node is None:
            raise HTTPException(status_code=404, detail="大纲节点不存在")
        if "parent_id" in data:
            _validate_parent(session, node.level, data["parent_id"], exclude_id=node.id)
            node.parent_id = data["parent_id"]
        for key in (
            "title",
            "goal",
            "must_cover",
            "forbidden",
            "status",
            "target_words",
            "strands",
            "sort_order",
        ):
            if key in data and data[key] is not None:
                setattr(node, key, data[key])
        session.commit()
        session.refresh(node)
        return node


def delete_node(project_id: str, node_id: str) -> None:
    from fastapi import HTTPException
    from sqlalchemy import func

    with project_session(project_id) as session:
        node = session.get(OutlineNode, node_id)
        if node is None:
            raise HTTPException(status_code=404, detail="大纲节点不存在")
        child_count = session.scalar(
            select(func.count()).select_from(OutlineNode).where(
                OutlineNode.parent_id == node_id
            )
        )
        if child_count:
            raise HTTPException(status_code=409, detail=f"节点下还有 {child_count} 个子节点")
        session.delete(node)
        session.commit()


def move_node(
    project_id: str,
    node_id: str,
    new_parent_id: str | None,
    position: str = "inside",
    sibling_id: str | None = None,
) -> OutlineNode:
    """原子移动：校验层级与循环后，重排目标兄弟列表。"""
    from fastapi import HTTPException

    with project_session(project_id) as session:
        node = session.get(OutlineNode, node_id)
        if node is None:
            raise HTTPException(status_code=404, detail="大纲节点不存在")

        if new_parent_id is not None:
            parent = session.get(OutlineNode, new_parent_id)
            if parent is None:
                raise HTTPException(status_code=404, detail="目标节点不存在")
            cursor: OutlineNode | None = parent
            while cursor is not None:
                if cursor.id == node.id:
                    raise HTTPException(status_code=422, detail="不能移动到自己的子节点")
                cursor = session.get(OutlineNode, cursor.parent_id) if cursor.parent_id else None
            _validate_parent(session, node.level, new_parent_id, exclude_id=node.id)
        elif node.level != "volume":
            raise HTTPException(status_code=422, detail="只有卷纲可以移动到根")

        old_parent_id = node.parent_id
        node.parent_id = new_parent_id
        session.flush()

        siblings = list(
            session.scalars(
                select(OutlineNode)
                .where(OutlineNode.parent_id == new_parent_id)
                .order_by(OutlineNode.sort_order, OutlineNode.created_at)
            )
        )
        siblings = [s for s in siblings if s.id != node.id]
        if sibling_id is not None:
            if position == "before":
                index = next((i for i, s in enumerate(siblings) if s.id == sibling_id), len(siblings))
            elif position == "after":
                index = next(
                    (i for i, s in enumerate(siblings) if s.id == sibling_id), len(siblings) - 1
                ) + 1
            else:
                index = len(siblings)
        else:
            index = len(siblings)
        siblings.insert(index, node)

        for order, sibling in enumerate(siblings):
            sibling.sort_order = order
        session.commit()
        session.refresh(node)
        return node


def create_chapter_from_node(project_id: str, node_id: str) -> Chapter:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        node = session.get(OutlineNode, node_id)
        if node is None:
            raise HTTPException(status_code=404, detail="大纲节点不存在")
        if node.level != "chapter":
            raise HTTPException(status_code=422, detail="只有章纲可以创建正文")
        if node.chapter_id:
            chapter = session.get(Chapter, node.chapter_id)
            if chapter:
                return chapter
        chapter = Chapter(
            id=new_id(),
            title=node.title,
            outline_node_id=node.id,
            file_path=f"chapters/{new_id()}.md",
        )
        session.add(chapter)
        session.flush()
        node.chapter_id = chapter.id
        session.commit()
        session.refresh(chapter)
        return chapter
