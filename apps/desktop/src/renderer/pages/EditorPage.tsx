import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { Chapter, OutlineNode } from '@ai-novel-ide/shared-types';

import { api, type ChapterCommitItem } from '../api';

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
  const selRef = useRef<{ start: number; end: number }>({ start: 0, end: 0 });
  const [brief, setBrief] = useState<{
    mode: string;
    sections: Record<string, string>;
    polished: string;
  } | null>(null);
  const [review, setReview] = useState<{
    mode: string;
    summary: string;
    dims: { name: string; status: string; issues: string[] }[];
  } | null>(null);
  const [suggestion, setSuggestion] = useState<{
    mode: string;
    text: string;
    start: number;
    end: number;
  } | null>(null);
  const [aiBusy, setAiBusy] = useState(false);
  const [undoStack, setUndoStack] = useState<{ content: string }[]>([]);
  const [commits, setCommits] = useState<ChapterCommitItem[]>([]);
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
      void api.listChapterCommits(projectId, chapterId).then(setCommits).catch(() => undefined);

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

  const runBrief = async () => {
    if (!linkedNode || linkedNode.level !== 'chapter') {
      setError('请先通过大纲页「从章纲创建正文」关联章纲');
      return;
    }
    setAiBusy(true);
    setError('');
    try {
      setBrief(await api.writingBrief(projectId, linkedNode.id));
    } catch (e) {
      setError(String(e));
    } finally {
      setAiBusy(false);
    }
  };

  const runAssist = async (mode: 'continue' | 'rewrite') => {
    if (!selectedId) return;
    const { start, end } = selRef.current;
    const selection = content.slice(start, end);
    if (mode === 'rewrite' && !selection) {
      setError('请先选中要改写的文字');
      return;
    }
    setAiBusy(true);
    setError('');
    try {
      const r = await api.assistChapter(projectId, selectedId, mode, selection, '');
      setSuggestion({ mode, text: r.suggestion, start, end });
    } catch (e) {
      setError(String(e));
    } finally {
      setAiBusy(false);
    }
  };

  const applySuggestion = () => {
    if (!suggestion) return;
    setUndoStack((prev) => [...prev, { content }].slice(-10));
    const next =
      suggestion.mode === 'rewrite'
        ? content.slice(0, suggestion.start) + suggestion.text + content.slice(suggestion.end)
        : content.trimEnd() + '\n\n' + suggestion.text;
    setContent(next);
    setSuggestion(null);
    scheduleSave();
  };

  const undoLast = () => {
    setUndoStack((prev) => {
      if (!prev.length) return prev;
      const last = prev[prev.length - 1];
      setContent(last.content);
      scheduleSave();
      return prev.slice(0, -1);
    });
  };

  const runReview = async () => {
    if (!selectedId) return;
    setAiBusy(true);
    setError('');
    try {
      setReview(await api.reviewChapter(projectId, selectedId));
    } catch (e) {
      setError(String(e));
    } finally {
      setAiBusy(false);
    }
  };

  const submitChapter = async () => {
    if (!selectedId) return;
    if (!window.confirm('提交章节？将生成事实记录并标记为已提交，可随时驳回。')) return;
    setAiBusy(true);
    setError('');
    try {
      await doSave();
      await api.commitChapter(projectId, selectedId);
      await load();
      setCommits(await api.listChapterCommits(projectId, selectedId));
    } catch (e) {
      setError(String(e));
    } finally {
      setAiBusy(false);
    }
  };

  const rejectLatestCommit = async (commitId: string) => {
    if (!window.confirm('驳回该提交？章节将回到草稿状态。')) return;
    try {
      await api.rejectCommit(projectId, commitId);
      setCommits(await api.listChapterCommits(projectId, selectedId!));
      await load();
    } catch (e) {
      setError(String(e));
    }
  };

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
              {c.status === 'committed' && <span className="badge done">已提交</span>}
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
            onSelect={(e) => {
              const el = e.currentTarget;
              selRef.current = { start: el.selectionStart, end: el.selectionEnd };
            }}
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
              <>
                <button className="btn primary" disabled={aiBusy} onClick={() => void submitChapter()}>
                  提交章节
                </button>
                <button className="btn ghost" onClick={() => void removeChapter()}>
                  删除章节
                </button>
              </>
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
            <h4>写章流水线</h4>
            <div className="ai-actions">
              <button className="btn ghost" disabled={aiBusy} onClick={() => void runBrief()}>
                生成任务书
              </button>
              <button className="btn ghost" disabled={aiBusy} onClick={() => void runAssist('continue')}>
                续写
              </button>
              <button className="btn ghost" disabled={aiBusy} onClick={() => void runAssist('rewrite')}>
                改写选中
              </button>
              {undoStack.length > 0 && (
                <button className="btn ghost" onClick={undoLast}>
                  撤销
                </button>
              )}
              <button className="btn ghost" disabled={aiBusy} onClick={() => void runReview()}>
                五维审查
              </button>
            </div>
            {brief && (
              <div className="brief-box">
                {brief.mode === 'ai' && brief.polished && (
                  <div className="contract-box">{brief.polished}</div>
                )}
                {Object.entries(brief.sections).map(([title, text]) => (
                  <div key={title} className="brief-item">
                    <b>{title}</b>
                    <span>{text}</span>
                  </div>
                ))}
              </div>
            )}
            {suggestion && (
              <div className="ai-card">
                <b>AI 建议（{suggestion.mode === 'rewrite' ? '改写' : '续写'}）</b>
                <p>{suggestion.text}</p>
                <button className="btn primary" onClick={applySuggestion}>
                  应用建议
                </button>
                <button className="btn ghost" onClick={() => setSuggestion(null)}>
                  放弃
                </button>
              </div>
            )}
            {review && (
              <div className="review-box">
                {review.summary && <div className="contract-box">{review.summary}</div>}
                {review.dims.map((d) => (
                  <div key={d.name} className={`review-dim review-${d.status}`}>
                    <span className="review-name">{d.name}</span>
                    <span className="review-status">
                      {d.status === 'pass' ? '通过' : d.status === 'warn' ? '提醒' : '失败'}
                    </span>
                    {d.issues.map((issue, i) => (
                      <div key={i} className="review-issue">{issue}</div>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="ctx-section">
            <h4>提交记录</h4>
            {commits.length === 0 ? (
              <div className="contract-box">本章尚未提交；写完后点「提交章节」入账。</div>
            ) : (
              commits.map((c) => (
                <div key={c.id} className={`commit-item commit-${c.status}`}>
                  <div className="commit-head">
                    <span className="commit-status">
                      {c.status === 'accepted' ? '已提交' : '已驳回'}
                    </span>
                    <span className="mono">{new Date(c.createdAt).toLocaleString()}</span>
                  </div>
                  <div className="commit-summary">{c.summaryText}</div>
                  {c.entityDeltas.length > 0 && (
                    <div className="commit-links">自动关联 {c.entityDeltas.length} 个实体</div>
                  )}
                  {c.projectionStatus.index === 'failed' && (
                    <div className="hint">向量索引更新失败</div>
                  )}
                  {c.status === 'accepted' && (
                    <button className="btn ghost" onClick={() => void rejectLatestCommit(c.id)}>
                      驳回
                    </button>
                  )}
                </div>
              ))
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
