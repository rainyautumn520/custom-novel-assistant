import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { Chapter, OutlineNode } from '@ai-novel-ide/shared-types';

import { api } from '../api';

type SaveState = 'saved' | 'saving' | 'failed';

function draftKey(projectId: string, chapterId: string) {
  return `ai-novel-draft:${projectId}:${chapterId}`;
}

function countWords(text: string): number {
  return text.replace(/\s/g, '').length;
}

export default function EditorPage({
  projectId,
  focusChapterId,
}: {
  projectId: string;
  focusChapterId: string | null;
}) {
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [outline, setOutline] = useState<OutlineNode[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');
  const [saveState, setSaveState] = useState<SaveState>('saved');
  const [fileIntegrity, setFileIntegrity] = useState('ok');
  const [error, setError] = useState('');
  const timerRef = useRef<number | null>(null);
  const contentRef = useRef(content);
  const titleRef = useRef(title);
  const selectedIdRef = useRef(selectedId);

  contentRef.current = content;
  titleRef.current = title;
  selectedIdRef.current = selectedId;

  const load = useCallback(async () => {
    const [chs, ol] = await Promise.all([
      api.listChapters(projectId),
      api.listOutline(projectId),
    ]);
    setChapters(chs);
    setOutline(ol);
    return chs;
  }, [projectId]);

  const doSave = useCallback(async () => {
    const id = selectedIdRef.current;
    if (!id) return;
    setSaveState('saving');
    try {
      const saved = await api.saveChapter(projectId, id, {
        title: titleRef.current,
        contentMd: contentRef.current,
      });
      setTitle(saved.title);
      setChapters((prev) =>
        prev.map((c) => (c.id === saved.id ? { ...c, title: saved.title, wordCount: saved.wordCount } : c)),
      );
      localStorage.removeItem(draftKey(projectId, id));
      setSaveState('saved');
    } catch (e) {
      setError(String(e));
      setSaveState('failed');
    }
  }, [projectId]);

  const selectChapter = useCallback(
    async (chapterId: string) => {
      const detail = await api.getChapter(projectId, chapterId);
      setSelectedId(chapterId);
      setTitle(detail.title);
      setContent(detail.contentMd);
      setFileIntegrity(detail.fileIntegrity);
      setSaveState('saved');

      const raw = localStorage.getItem(draftKey(projectId, chapterId));
      if (raw) {
        try {
          const draft = JSON.parse(raw) as { title: string; contentMd: string };
          const hasNewerDraft =
            draft.contentMd !== detail.contentMd || draft.title !== detail.title;
          if (hasNewerDraft && window.confirm('检测到未保存的本地草稿，恢复它？')) {
            setTitle(draft.title);
            setContent(draft.contentMd);
            setSaveState('saving');
            setTimeout(() => void doSave(), 300);
          } else {
            localStorage.removeItem(draftKey(projectId, chapterId));
          }
        } catch {
          localStorage.removeItem(draftKey(projectId, chapterId));
        }
      }
    },
    [projectId, doSave],
  );

  const scheduleSave = useCallback(() => {
    setSaveState('saving');
    if (timerRef.current) window.clearTimeout(timerRef.current);
    timerRef.current = window.setTimeout(() => void doSave(), 1000);
  }, [doSave]);

  useEffect(() => {
    void load()
      .then((chs) => {
        const target = focusChapterId ?? chs[0]?.id ?? null;
        if (target) return selectChapter(target);
      })
      .catch((e) => setError(String(e)));
  }, [load, selectChapter, focusChapterId]);

  useEffect(() => {
    return () => {
      if (timerRef.current) window.clearTimeout(timerRef.current);
    };
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        if (timerRef.current) window.clearTimeout(timerRef.current);
        void doSave();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [doSave]);

  useEffect(() => {
    if (!selectedId) return;
    const timer = window.setTimeout(() => {
      localStorage.setItem(
        draftKey(projectId, selectedId),
        JSON.stringify({ title: titleRef.current, contentMd: contentRef.current }),
      );
    }, 300);
    return () => window.clearTimeout(timer);
  }, [content, title, selectedId, projectId]);

  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (saveState === 'saving' || saveState === 'failed') {
        e.preventDefault();
      }
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [saveState]);

  const linkedNode = useMemo(
    () =>
      outline.find(
        (n) => n.id === chapters.find((c) => c.id === selectedId)?.outlineNodeId,
      ) ?? null,
    [outline, chapters, selectedId],
  );

  const createChapter = async () => {
    const created = await api.createChapter(projectId, `第 ${chapters.length + 1} 章`);
    setChapters((prev) => [...prev, created]);
    await selectChapter(created.id);
  };

  const removeChapter = async () => {
    if (!selectedId || !window.confirm('删除当前章节？文件会移入回收目录。')) return;
    await api.deleteChapter(projectId, selectedId);
    const remaining = chapters.filter((c) => c.id !== selectedId);
    setChapters(remaining);
    setSelectedId(null);
    setContent('');
    setTitle('');
    if (remaining[0]) await selectChapter(remaining[0].id);
  };

  return (
    <div className="page-fill">
      <div className="editor-layout">
        <div className="chapter-tree">
          <button className="tree-add-btn" onClick={() => void createChapter()}>
            ＋ 新建章节
          </button>
          {chapters.map((c) => (
            <div
              key={c.id}
              className={`tree-item ${c.id === selectedId ? 'active' : ''}`}
              onClick={() => void selectChapter(c.id)}
            >
              <span className="tree-title">{c.title}</span>
              <span className="count mono">{c.wordCount}</span>
            </div>
          ))}
        </div>

        <div className="write-area">
          <div className="write-toolbar">
            <input
              className="chapter-title-input"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                scheduleSave();
              }}
              placeholder="章节标题"
            />
            <div className="spacer" />
            <SaveIndicator state={saveState} onRetry={() => void doSave()} />
          </div>

          {error && <div className="page-error">{error}</div>}
          {fileIntegrity === 'modified' && (
            <div className="page-error">正文文件被外部修改过，继续编辑保存会覆盖外部内容。可先导出备份。</div>
          )}

          <textarea
            className="write-textarea"
            value={content}
            onChange={(e) => {
              setContent(e.target.value);
              scheduleSave();
            }}
            placeholder="开始写作…（自动保存，Ctrl+S 立即保存）"
            spellCheck={false}
          />

          <div className="write-statusbar">
            <span>字数 {countWords(content).toLocaleString()}</span>
            {linkedNode?.targetWords ? (
              <span>
                · 目标 {linkedNode.targetWords.toLocaleString()}
                {countWords(content) >= linkedNode.targetWords ? ' ✓' : ''}
              </span>
            ) : null}
            <div className="spacer" />
            {selectedId && (
              <button className="btn ghost" onClick={() => void removeChapter()}>
                删除章节
              </button>
            )}
          </div>
        </div>

        <aside className="context-panel">
          <div className="ctx-section">
            <h4>章纲合同</h4>
            {linkedNode ? (
              <>
                <div className="contract-box"><b>目标</b>：{linkedNode.goal || '（未填写）'}</div>
                <div className="contract-box">
                  <b>必须覆盖</b>：{linkedNode.mustCover.join(' / ') || '（未填写）'}
                </div>
                <div className="contract-box">
                  <b>禁区</b>：{linkedNode.forbidden.join(' / ') || '（未填写）'}
                </div>
              </>
            ) : (
              <div className="contract-box">本章未关联章纲，可在大纲页创建章纲后关联。</div>
            )}
          </div>
          <div className="ctx-section">
            <h4>自动保存</h4>
            <div className="contract-box">
              停止输入 1 秒后自动保存；保存失败会保留在编辑器内并允许重试，不会静默丢失。
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

function SaveIndicator({ state, onRetry }: { state: SaveState; onRetry: () => void }) {
  return (
    <div className="save-state">
      {state === 'saving' && (
        <>
          <span className="dot saving" />
          <span>保存中…</span>
        </>
      )}
      {state === 'saved' && (
        <>
          <span className="dot saved" />
          <span>已保存</span>
        </>
      )}
      {state === 'failed' && (
        <>
          <span className="dot failed" />
          <button className="btn ghost" onClick={onRetry}>保存失败 · 重试</button>
        </>
      )}
    </div>
  );
}
