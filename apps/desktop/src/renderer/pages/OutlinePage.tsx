import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import type { OutlineNode } from '@ai-novel-ide/shared-types';

import { api } from '../api';

const LEVEL_LABEL: Record<string, string> = {
  volume: '卷',
  chapter: '章',
  beat: '细纲',
};

export default function OutlinePage({
  projectId,
  onOpenChapter,
}: {
  projectId: string;
  onOpenChapter: (chapterId: string) => void;
}) {
  const [nodes, setNodes] = useState<OutlineNode[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    const items = await api.listOutline(projectId);
    setNodes(items);
    setExpanded((prev) => {
      const next = new Set(prev);
      items.filter((n) => n.parentId).forEach((n) => next.add(n.parentId!));
      return next;
    });
  }, [projectId]);

  useEffect(() => {
    void load().catch((e) => setError(String(e)));
  }, [load]);

  const selected = useMemo(
    () => nodes.find((n) => n.id === selectedId) ?? null,
    [nodes, selectedId],
  );

  const childrenOf = useCallback(
    (parentId: string | null) =>
      nodes
        .filter((n) => n.parentId === parentId)
        .sort((a, b) => a.sortOrder - b.sortOrder),
    [nodes],
  );

  const createNode = async (level: OutlineNode['level'], parentId: string | null) => {
    const titles: Record<string, string> = { volume: '新卷', chapter: '新章纲', beat: '新细纲' };
    try {
      const created = await api.createOutlineNode(projectId, {
        level,
        parentId,
        title: titles[level],
      });
      await load();
      setSelectedId(created.id);
      if (parentId) setExpanded((prev) => new Set(prev).add(parentId));
    } catch (e) {
      window.alert(String(e));
    }
  };

  const move = async (node: OutlineNode, delta: number) => {
    const siblings = childrenOf(node.parentId);
    const index = siblings.findIndex((s) => s.id === node.id);
    const target = siblings[index + delta];
    if (!target) return;
    await api.updateOutlineNode(projectId, node.id, { sortOrder: target.sortOrder });
    await api.updateOutlineNode(projectId, target.id, { sortOrder: node.sortOrder });
    await load();
  };

  const removeNode = async (node: OutlineNode) => {
    if (!window.confirm(`删除「${node.title}」？`)) return;
    try {
      await api.deleteOutlineNode(projectId, node.id);
      if (selectedId === node.id) setSelectedId(null);
      await load();
    } catch (e) {
      window.alert(String(e));
    }
  };

  const createChapter = async (node: OutlineNode) => {
    try {
      const chapter = await api.createChapterFromNode(projectId, node.id);
      onOpenChapter(chapter.id);
    } catch (e) {
      window.alert(String(e));
    }
  };

  const renderTree = (parentId: string | null, depth: number): ReactNode[] => {
    return childrenOf(parentId).map((node) => {
      const hasChildren = childrenOf(node.id).length > 0;
      const isExpanded = expanded.has(node.id);
      return (
        <div key={node.id}>
          <div
            className={`tree-item ${node.id === selectedId ? 'active' : ''}`}
            style={{ paddingLeft: 10 + depth * 18 }}
            onClick={() => setSelectedId(node.id)}
          >
            <span
              className="caret"
              onClick={(e) => {
                e.stopPropagation();
                if (!hasChildren) return;
                setExpanded((prev) => {
                  const next = new Set(prev);
                  if (next.has(node.id)) next.delete(node.id);
                  else next.add(node.id);
                  return next;
                });
              }}
            >
              {hasChildren ? (isExpanded ? '▾' : '▸') : ''}
            </span>
            <span className={`tag ${node.level}`}>{LEVEL_LABEL[node.level]}</span>
            <span className="tree-title">{node.title}</span>
            {node.chapterId && <span className="badge done">有正文</span>}
          </div>
          {isExpanded && renderTree(node.id, depth + 1)}
        </div>
      );
    });
  };

  return (
    <div className="page-fill">
      <div className="page-head">
        <h1>大纲</h1>
        <div className="spacer" />
        <button className="btn secondary" onClick={() => void createNode('volume', null)}>
          ＋ 新建卷
        </button>
      </div>

      {error && <div className="page-error">{error}</div>}

      <div className="outline-layout">
        <div className="outline-tree">
          {nodes.length === 0 && <div className="list-empty">还没有大纲，点「新建卷」开始。</div>}
          {renderTree(null, 0)}
          <div className="tree-add">
            <button className="btn ghost" onClick={() => void createNode('volume', null)}>
              ＋ 新建卷
            </button>
          </div>
        </div>

        <div className="outline-editor">
          {selected ? (
            <OutlineEditor
              key={selected.id}
              node={selected}
              canCreateChapter={selected.level === 'chapter'}
              onSave={async (data) => {
                await api.updateOutlineNode(projectId, selected.id, data);
                await load();
              }}
              onMoveUp={() => void move(selected, -1)}
              onMoveDown={() => void move(selected, 1)}
              onDelete={() => void removeNode(selected)}
              onCreateChild={() => {
                const childLevel = selected.level === 'volume' ? 'chapter' : 'beat';
                void createNode(childLevel, selected.id);
              }}
              onCreateChapter={() => void createChapter(selected)}
            />
          ) : (
            <div className="editor-empty">选择左侧节点编辑，或新建卷</div>
          )}
        </div>
      </div>
    </div>
  );
}

function OutlineEditor({
  node,
  canCreateChapter,
  onSave,
  onMoveUp,
  onMoveDown,
  onDelete,
  onCreateChild,
  onCreateChapter,
}: {
  node: OutlineNode;
  canCreateChapter: boolean;
  onSave: (data: Partial<OutlineNode>) => Promise<void>;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onDelete: () => void;
  onCreateChild: () => void;
  onCreateChapter: () => void;
}) {
  const [title, setTitle] = useState(node.title);
  const [goal, setGoal] = useState(node.goal);
  const [mustCover, setMustCover] = useState(node.mustCover.join('\n'));
  const [forbidden, setForbidden] = useState(node.forbidden.join('\n'));
  const [targetWords, setTargetWords] = useState(String(node.targetWords));
  const [status, setStatus] = useState(node.status);

  useEffect(() => {
    setTitle(node.title);
    setGoal(node.goal);
    setMustCover(node.mustCover.join('\n'));
    setForbidden(node.forbidden.join('\n'));
    setTargetWords(String(node.targetWords));
    setStatus(node.status);
  }, [node]);

  const handleSave = async () => {
    await onSave({
      title,
      goal,
      mustCover: mustCover.split('\n').map((x) => x.trim()).filter(Boolean),
      forbidden: forbidden.split('\n').map((x) => x.trim()).filter(Boolean),
      targetWords: Number(targetWords) || 0,
      status,
    });
  };

  return (
    <div>
      <div className="editor-head">
        <span className={`tag ${node.level}`}>{LEVEL_LABEL[node.level]}</span>
        <input
          className="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <span className={`badge ${node.status === 'done' ? 'done' : 'active'}`}>
          {node.status === 'done' ? '已完成' : node.status === 'active' ? '写作中' : '草稿'}
        </span>
      </div>

      <div className="field">
        <label>目标</label>
        <textarea className="textarea-field" value={goal} onChange={(e) => setGoal(e.target.value)} />
      </div>
      <div className="field">
        <label>必须覆盖（每行一条）</label>
        <textarea
          className="textarea-field"
          value={mustCover}
          onChange={(e) => setMustCover(e.target.value)}
        />
      </div>
      <div className="field">
        <label>禁区（每行一条）</label>
        <textarea
          className="textarea-field"
          value={forbidden}
          onChange={(e) => setForbidden(e.target.value)}
        />
      </div>

      <div className="field-row">
        <div className="field">
          <label>目标字数</label>
          <input
            type="number"
            value={targetWords}
            onChange={(e) => setTargetWords(e.target.value)}
          />
        </div>
        <div className="field">
          <label>状态</label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as OutlineNode['status'])}
          >
            <option value="draft">草稿</option>
            <option value="active">写作中</option>
            <option value="done">已完成</option>
          </select>
        </div>
      </div>

      <div className="editor-actions">
        <button className="btn ghost" onClick={onMoveUp}>↑ 上移</button>
        <button className="btn ghost" onClick={onMoveDown}>↓ 下移</button>
        {node.level !== 'beat' && (
          <button className="btn ghost" onClick={onCreateChild}>
            ＋ {node.level === 'volume' ? '章纲' : '细纲'}
          </button>
        )}
        {canCreateChapter && (
          <button className="btn primary" onClick={onCreateChapter}>
            从章纲创建正文 →
          </button>
        )}
        <div className="spacer" />
        <button className="btn secondary" onClick={onDelete}>删除</button>
        <button className="btn primary" onClick={() => void handleSave()}>保存</button>
      </div>
    </div>
  );
}
