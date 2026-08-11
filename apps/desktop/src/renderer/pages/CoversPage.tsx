import { useCallback, useEffect, useState } from 'react';
import type { CoverTask } from '@ai-novel-ide/shared-types';

import { API_BASE, api } from '../api';

const SIZES = ['1920x1920', '2048x2048', '2880x1620'];

export default function CoversPage({ projectId }: { projectId: string }) {
  const [tasks, setTasks] = useState<CoverTask[]>([]);
  const [prompt, setPrompt] = useState('');
  const [size, setSize] = useState(SIZES[0]);
  const [style, setStyle] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setTasks(await api.listCovers(projectId));
  }, [projectId]);

  useEffect(() => {
    void load().catch((e) => setError(String(e)));
  }, [load]);

  const submit = async () => {
    if (!prompt.trim() || busy) return;
    setBusy(true);
    setError('');
    try {
      await api.createCover(projectId, prompt.trim(), { size, style });
      setPrompt('');
      await load();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page-fill">
      <div className="page-head">
        <h1>封面工坊</h1>
        <div className="spacer" />
      </div>
      {error && <div className="page-error">{error}</div>}

      <div className="export-wrap">
        <div className="field">
          <label>画面需求（场景、氛围、元素）</label>
          <textarea
            className="textarea-field"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="例如：云海之上的仙山，青金色灵气环绕，史诗感，无文字"
          />
        </div>
        <div className="field-row">
          <div className="field">
            <label>尺寸</label>
            <select value={size} onChange={(e) => setSize(e.target.value)}>
              {SIZES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>风格（可选）</label>
            <input value={style} onChange={(e) => setStyle(e.target.value)} placeholder="国风水墨 / 厚涂…" />
          </div>
        </div>
        <div className="export-actions">
          <button className="btn primary" disabled={busy} onClick={() => void submit()}>
            {busy ? '提交中…' : '生成封面'}
          </button>
        </div>

        <h2 className="section-title">生成历史</h2>
        <div className="cover-list">
          {tasks.length === 0 && <div className="list-empty">还没有生成任务</div>}
          {tasks.map((t) => (
            <div key={t.id} className="cover-item">
              <div className="cover-prompt">{t.prompt}</div>
              {t.status === 'success' && t.resultPath && (
                <CoverResult projectId={projectId} task={t} onChanged={load} />
              )}
              <div className="cover-meta">
                <span className={`badge ${t.status === 'failed' ? 'active' : t.status === 'success' ? 'done' : ''}`}>
                  {t.status === 'failed' ? '失败' : t.status === 'success' ? '成功' : t.status}
                </span>
                <span className="mono">{String(t.params.size ?? '')}</span>
              </div>
              {t.error && <div className="hint">{t.error}</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function CoverResult({
  projectId,
  task,
  onChanged,
}: {
  projectId: string;
  task: CoverTask;
  onChanged: () => Promise<void>;
}) {
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [busy, setBusy] = useState(false);
  const src = task.composedPath
    ? api.coverComposedUrl(projectId, task.id)
    : `${API_BASE}/api/projects/${projectId}/covers/${task.id}/file`;

  const compose = async () => {
    if (!title.trim() && !author.trim()) return;
    setBusy(true);
    try {
      await api.composeCover(projectId, task.id, title.trim(), author.trim());
      await onChanged();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <img className="cover-preview" src={src} alt={task.prompt} />
      <div className="compose-row">
        <input placeholder="书名" value={title} onChange={(e) => setTitle(e.target.value)} />
        <input placeholder="作者名" value={author} onChange={(e) => setAuthor(e.target.value)} />
        <button className="btn primary" disabled={busy} onClick={() => void compose()}>
          {busy ? '合成中…' : '叠加文字'}
        </button>
      </div>
    </div>
  );
}
