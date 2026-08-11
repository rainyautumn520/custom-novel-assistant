import { useCallback, useEffect, useState } from 'react';

import { api, type Chekhov, type RhythmData } from '../api';

const STRAND_COLOR: Record<string, string> = {
  quest: 'var(--accent)',
  fire: 'var(--danger)',
  constellation: 'var(--info)',
};

export default function StrandPage({ projectId }: { projectId: string }) {
  const [rhythm, setRhythm] = useState<RhythmData | null>(null);
  const [chekhovs, setChekhovs] = useState<Chekhov[]>([]);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    const [r, c] = await Promise.all([
      api.getRhythm(projectId),
      api.listChekhovs(projectId),
    ]);
    setRhythm(r);
    setChekhovs(c);
  }, [projectId]);

  useEffect(() => {
    void load().catch((e) => setError(String(e)));
  }, [load]);

  const addChekhov = async () => {
    if (!title.trim()) return;
    await api.createChekhov(projectId, { title: title.trim(), description });
    setTitle('');
    setDescription('');
    await load();
  };

  const setStatus = async (c: Chekhov, status: string) => {
    await api.updateChekhov(projectId, c.id, { status });
    await load();
  };

  const removeChekhov = async (c: Chekhov) => {
    if (!window.confirm(`删除伏笔「${c.title}」？`)) return;
    await api.deleteChekhov(projectId, c.id);
    await load();
  };

  return (
    <div className="page-fill">
      <div className="page-head">
        <h1>节奏与伏笔</h1>
        <div className="spacer" />
        {rhythm && (
          <span className="rag-status">未回收伏笔 {rhythm.openChekhovs}</span>
        )}
      </div>

      {error && <div className="page-error">{error}</div>}

      <div className="strand-cards">
        {rhythm &&
          Object.entries(rhythm.strands).map(([key, s]) => (
            <div key={key} className="strand-card">
              <div className="strand-head">
                <span className="strand-dot" style={{ background: STRAND_COLOR[key] }} />
                <span className="strand-name">{s.label}</span>
                <span className={`badge ${s.ok ? 'done' : 'active'}`}>
                  {s.ok ? '正常' : `断档 ${s.maxGap}/${s.limit}`}
                </span>
              </div>
              <div className="strand-nums">
                覆盖 <span className="num mono">{s.chapters}</span> 章 · 占比{' '}
                <span className="num mono">{Math.round(s.ratio * 100)}%</span>
              </div>
              <div className="strand-bar">
                <div
                  className="strand-fill"
                  style={{ width: `${Math.min(100, s.ratio * 100)}%`, background: STRAND_COLOR[key] }}
                />
              </div>
              <div className="strand-gap">
                最大断档 <span className="num mono">{s.maxGap}</span> / 红线{' '}
                <span className="num mono">{s.limit}</span> 章
              </div>
            </div>
          ))}
      </div>

      <div className="strand-layout">
        <div className="strand-main">
          <h2 className="section-title">章节时间线（按大纲顺序）</h2>
          <div className="timeline">
            {rhythm?.timeline.length === 0 && <div className="list-empty">还没有章纲</div>}
            {rhythm?.timeline.map((item) => (
              <div key={item.chapterId} className="timeline-item">
                <span className="pv-vol">{item.volumeTitle}</span>
                <span className="pv-ch">{item.chapterTitle}</span>
                <span className="pv-words mono">{item.words.toLocaleString()} 字</span>
                {item.strands.map((s) => (
                  <span key={s} className="strand-chip" style={{ color: STRAND_COLOR[s] }}>
                    {s === 'quest' ? '主线' : s === 'fire' ? '感情' : '世界观'}
                  </span>
                ))}
                <span className={`badge ${item.status === 'committed' ? 'done' : item.status === 'no_draft' ? '' : 'active'}`}>
                  {item.status === 'committed' ? '已提交' : item.status === 'no_draft' ? '无正文' : '草稿'}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="strand-side">
          <h2 className="section-title">伏笔管理</h2>
          <div className="chekhov-form">
            <input
              placeholder="伏笔名称（例如：山海令的来历）"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <textarea
              className="textarea-field"
              placeholder="伏笔描述（埋在哪、预期怎么回收）…"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            <button className="btn primary" onClick={() => void addChekhov()}>
              ＋ 记录伏笔
            </button>
          </div>
          <div className="chekhov-list">
            {chekhovs.length === 0 && <div className="list-empty">还没有伏笔</div>}
            {chekhovs.map((c) => (
              <div key={c.id} className={`chekhov-item chekhov-${c.status}`}>
                <div className="commit-head">
                  <span className="chekhov-title">{c.title}</span>
                  <button className="icon-btn" onClick={() => void removeChekhov(c)}>×</button>
                </div>
                {c.description && <div className="commit-summary">{c.description}</div>}
                <select value={c.status} onChange={(e) => void setStatus(c, e.target.value)}>
                  <option value="open">未回收</option>
                  <option value="resolved">已回收</option>
                  <option value="abandoned">已弃用</option>
                </select>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
