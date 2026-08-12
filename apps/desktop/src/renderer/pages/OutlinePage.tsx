import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import type { OutlineNode } from '@ai-novel-ide/shared-types';

import { api } from '../api';

const LEVEL_LABEL: Record<string, string> = {
  volume: '卷',
  chapter: '章',
  beat: '细纲',
};

const CN_DIGITS: Record<string, number> = {
  零: 0, 一: 1, 二: 2, 两: 2, 三: 3, 四: 4, 五: 5, 六: 6, 七: 7, 八: 8, 九: 9,
};
const CN_UNITS: Record<string, number> = {
  十: 10, 百: 100, 千: 1000, 万: 10000, 亿: 100000000,
};

export function parseWordCount(text: string): number | null {
  const s = text.trim();
  if (!s) return 0;
  const pure = s.replace(/[字个约]/g, '').trim();
  if (/^[\d,]+$/.test(pure)) return parseInt(pure.replace(/,/g, ''), 10);
  const kMatch = /^([\d.]+)\s*k$/i.exec(pure);
  if (kMatch) return Math.round(parseFloat(kMatch[1]) * 1000);
  const wanMatch = /^([\d.]+)\s*万$/.exec(pure);
  if (wanMatch) return Math.round(parseFloat(wanMatch[1]) * 10000);
  if (/[零一二两三四五六七八九十百千万亿]/.test(pure)) {
    let total = 0;
    let section = 0;
    let num = 0;
    let lastUnit = 0;
    for (const ch of pure) {
      if (ch in CN_DIGITS) {
        num = CN_DIGITS[ch];
      } else if (ch in CN_UNITS) {
        const unit = CN_UNITS[ch];
        if (unit === 10000 || unit === 100000000) {
          section = (section + (num || 1)) * unit;
          total += section;
          section = 0;
          num = 0;
        } else {
          section += (num || 1) * unit;
          num = 0;
        }
        lastUnit = unit;
      } else {
        return null;
      }
    }
    let result = total + section;
    if (num > 0) {
      // 口语省略：两千五 = 2500，二百五 = 250
      result += lastUnit > 10 ? num * (lastUnit / 10) : num;
    }
    return result > 0 ? result : null;
  }
  return null;
}

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
  const [dropTarget, setDropTarget] = useState<{ id: string | null; zone: string } | null>(null);
  const dragIdRef = useRef<string | null>(null);
  const dropZoneRef = useRef<{ id: string | null; zone: string } | null>(null);

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

  const dropZoneClass = (nodeId: string) => {
    if (!dropTarget || dropTarget.id !== nodeId) return '';
    return `drop-${dropTarget.zone}`;
  };

  const handleDrop = async (node: OutlineNode | null, zone: string) => {
    const draggedId = dragIdRef.current;
    if (!draggedId || draggedId === node?.id) {
      dragIdRef.current = null;
      setDropTarget(null);
      return;
    }
    const dragged = nodes.find((n) => n.id === draggedId);
    if (!dragged) return;
    try {
      if (node === null) {
        await api.moveOutlineNode(projectId, dragged.id, null, 'inside');
      } else if (zone === 'inside') {
        await api.moveOutlineNode(projectId, dragged.id, node.id, 'inside');
      } else {
        await api.moveOutlineNode(
          projectId,
          dragged.id,
          node.parentId,
          zone as 'before' | 'after',
          node.id,
        );
      }
      await load();
      setSelectedId(dragged.id);
    } catch (e) {
      window.alert(String(e));
      await load(); // 回滚到服务端状态
    } finally {
      dragIdRef.current = null;
      setDropTarget(null);
    }
  };

  const renderTree = (parentId: string | null, depth: number): ReactNode[] => {
    return childrenOf(parentId).map((node) => {
      const hasChildren = childrenOf(node.id).length > 0;
      const isExpanded = expanded.has(node.id);
      return (
        <div key={node.id}>
          <div
            style={{ paddingLeft: 10 + depth * 18 }}
            draggable
            onDragStart={(e) => {
              dragIdRef.current = node.id;
              e.dataTransfer.effectAllowed = 'move';
              e.dataTransfer.setData('text/plain', node.id);
            }}
            onDragOver={(e) => {
              e.preventDefault();
              e.stopPropagation();
              const rect = e.currentTarget.getBoundingClientRect();
              const y = (e.clientY - rect.top) / rect.height;
              const zone = y < 0.3 ? 'before' : y > 0.7 ? 'after' : 'inside';
              dropZoneRef.current = { id: node.id, zone };
              setDropTarget({ id: node.id, zone });
            }}
            onDragLeave={() => {
              if (dropZoneRef.current?.id === node.id) dropZoneRef.current = null;
              setDropTarget((prev) => (prev?.id === node.id ? null : prev));
            }}
            onDrop={(e) => {
              e.preventDefault();
              e.stopPropagation();
              const zone =
                dropZoneRef.current?.id === node.id ? dropZoneRef.current.zone : 'inside';
              void handleDrop(node, zone);
            }}
            className={`tree-item ${node.id === selectedId ? 'active' : ''} ${dropZoneClass(node.id)}`}
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
        <div
          className="outline-tree"
          onDragOver={(e) => {
            if (dragIdRef.current) {
              e.preventDefault();
              dropZoneRef.current = { id: null, zone: 'inside' };
              setDropTarget({ id: null, zone: 'inside' });
            }
          }}
          onDrop={(e) => {
            e.preventDefault();
            void handleDrop(null, 'inside');
          }}
        >
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
  const [strands, setStrands] = useState<string[]>(node.strands);

  useEffect(() => {
    setTitle(node.title);
    setGoal(node.goal);
    setMustCover(node.mustCover.join('\n'));
    setForbidden(node.forbidden.join('\n'));
    setTargetWords(String(node.targetWords));
    setStatus(node.status);
    setStrands(node.strands);
  }, [node]);

  const toggleStrand = (key: string) => {
    setStrands((prev) =>
      prev.includes(key) ? prev.filter((s) => s !== key) : [...prev, key],
    );
  };

  const handleSave = async () => {
    const parsed = parseWordCount(targetWords);
    if (parsed === null) {
      window.alert(
        `无法识别目标字数「${targetWords}」，支持 2500、2,500、1万、两千五 等写法`,
      );
      return;
    }
    await onSave({
      title,
      goal,
      mustCover: mustCover.split('\n').map((x) => x.trim()).filter(Boolean),
      forbidden: forbidden.split('\n').map((x) => x.trim()).filter(Boolean),
      targetWords: parsed,
      status,
      strands,
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
            type="text"
            inputMode="numeric"
            value={targetWords}
            onChange={(e) => setTargetWords(e.target.value)}
            placeholder="如 2500 或 两千五"
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

      <div className="field">
        <label>节奏标签（Strand Weave）</label>
        <div className="strand-picker">
          {[
            ['quest', '主线 Quest'],
            ['fire', '感情线 Fire'],
            ['constellation', '世界观 Constellation'],
          ].map(([key, label]) => (
            <label key={key} className="link-option">
              <input
                type="checkbox"
                checked={strands.includes(key)}
                onChange={() => toggleStrand(key)}
              />
              <span>{label}</span>
            </label>
          ))}
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
