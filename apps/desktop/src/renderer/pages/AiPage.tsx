import { useCallback, useEffect, useState } from 'react';
import type { AiMessage, AiSession, SettingCategory } from '@ai-novel-ide/shared-types';

import { api } from '../api';

export default function AiPage({ projectId }: { projectId: string }) {
  const [sessions, setSessions] = useState<AiSession[]>([]);
  const [messages, setMessages] = useState<AiMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [error, setError] = useState('');
  const [adopt, setAdopt] = useState<string | null>(null);
  const [categories, setCategories] = useState<SettingCategory[]>([]);
  const [rag, setRag] = useState<{ backend: string; count: number } | null>(null);

  const loadSessions = useCallback(async () => {
    const list = await api.listAiSessions(projectId);
    setSessions(list);
    if (!sessionId && list[0]) {
      setSessionId(list[0].id);
    }
  }, [projectId, sessionId]);

  useEffect(() => {
    void api.getAiPrompt(projectId).then((r) => setPrompt(r.prompt)).catch(() => undefined);
    void api.listCategories(projectId).then(setCategories).catch(() => undefined);
    void api.ragStatus(projectId).then(setRag).catch(() => undefined);
    void loadSessions().catch((e) => setError(String(e)));
  }, [projectId, loadSessions]);

  const rebuildRag = async () => {
    setBusy(true);
    try {
      const result = await api.rebuildIndex(projectId);
      const status = await api.ragStatus(projectId);
      setRag(status);
      setError(`知识索引已重建：${result.indexed} 个片段（${result.seconds}s）`);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    if (!sessionId) return;
    void api.listAiMessages(projectId, sessionId).then(setMessages).catch(() => undefined);
  }, [projectId, sessionId, busy]);

  const newSession = async () => {
    const created = await api.createAiSession(projectId);
    setSessions((prev) => [created, ...prev]);
    setSessionId(created.id);
    setMessages([]);
  };

  const send = async () => {
    const text = input.trim();
    if (!text || !sessionId || busy) return;
    setBusy(true);
    setError('');
    setMessages((prev) => [
      ...prev,
      { id: `tmp-${Date.now()}`, sessionId, role: 'user', content: text, sources: [], createdAt: '' },
    ]);
    setInput('');
    try {
      const { reply } = await api.aiChat(projectId, sessionId, text);
      setMessages((prev) => [
        ...prev.filter((m) => !m.id.startsWith('tmp-')),
        { id: `tmp-u-${Date.now()}`, sessionId, role: 'user', content: text, sources: [], createdAt: '' },
        { id: `tmp-a-${Date.now()}`, sessionId, role: 'assistant', content: reply, sources: [], createdAt: '' },
      ]);
      await loadSessions();
    } catch (e) {
      setError(String(e));
      setMessages((prev) => prev.filter((m) => !m.id.startsWith('tmp-')));
    } finally {
      setBusy(false);
    }
  };

  const adoptSetting = async (content: string, title: string, categoryId: string | null) => {
    await api.createSetting(projectId, {
      title,
      contentMd: content,
      categoryId,
      status: 'draft',
      tags: ['来自AI讨论'],
    });
    setAdopt(null);
    setError('');
  };

  return (
    <div className="page-fill">
      <div className="page-head">
        <h1>AI 设定讨论</h1>
        <div className="spacer" />
        {rag && (
          <span className="rag-status">
            {rag.count > 0 ? `向量库 ${rag.count} 片段` : '向量库未建立'}
          </span>
        )}
        <button className="btn secondary" onClick={() => void rebuildRag()} disabled={busy}>
          重建知识索引
        </button>
        <button className="btn primary" onClick={() => void newSession()}>＋ 新讨论</button>
      </div>

      {error && <div className="page-error">{error}</div>}

      <div className="ai-layout">
        <div className="ai-sessions">
          {sessions.length === 0 && <div className="list-empty">还没有会话</div>}
          {sessions.map((s) => (
            <div
              key={s.id}
              className={`tree-item ${s.id === sessionId ? 'active' : ''}`}
              onClick={() => setSessionId(s.id)}
            >
              <span className="tree-title">{s.title}</span>
              <button
                className="icon-btn"
                title="删除会话"
                onClick={(e) => {
                  e.stopPropagation();
                  if (!window.confirm('删除该讨论会话？')) return;
                  void api.deleteAiSession(projectId, s.id).then(() => {
                    if (sessionId === s.id) setSessionId(null);
                    void loadSessions();
                  });
                }}
              >
                ×
              </button>
            </div>
          ))}
          <div className="tree-add">
            <textarea
              className="prompt-box"
              placeholder="作品级提示词/文风要求（可选）…"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
            <button
              className="btn ghost"
              onClick={() => void api.setAiPrompt(projectId, prompt).then(() => setError(''))}
            >
              保存提示词
            </button>
          </div>
        </div>

        <div className="ai-chat">
          {sessionId ? (
            <>
              <div className="ai-messages">
                {messages.length === 0 && (
                  <div className="list-empty">和 AI 讨论设定：例如「帮我设计一个境界体系」</div>
                )}
                {messages.map((m) => (
                  <div key={m.id} className={`ai-msg ${m.role}`}>
                    <div className="ai-role">{m.role === 'user' ? '你' : 'AI'}</div>
                    <div className="ai-content">{m.content}</div>
                    {m.role === 'assistant' && !adopt && (
                      <button className="btn ghost adopt-btn" onClick={() => setAdopt(m.content)}>
                        纳入设定
                      </button>
                    )}
                  </div>
                ))}
                {busy && <div className="list-empty">AI 思考中…</div>}
              </div>
              {adopt && (
                <AdoptPanel
                  content={adopt}
                  categories={categories}
                  onCancel={() => setAdopt(null)}
                  onConfirm={(title, categoryId) => void adoptSetting(adopt, title, categoryId)}
                />
              )}
              <div className="ai-input-row">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && void send()}
                  placeholder="输入讨论内容，Enter 发送"
                  disabled={busy}
                />
                <button className="btn primary" onClick={() => void send()} disabled={busy}>
                  发送
                </button>
              </div>
            </>
          ) : (
            <div className="editor-empty">选择或新建一个讨论会话</div>
          )}
        </div>
      </div>
    </div>
  );
}

function AdoptPanel({
  content,
  categories,
  onCancel,
  onConfirm,
}: {
  content: string;
  categories: SettingCategory[];
  onCancel: () => void;
  onConfirm: (title: string, categoryId: string | null) => void;
}) {
  const [title, setTitle] = useState(content.slice(0, 24) || 'AI 建议设定');
  const [text, setText] = useState(content);
  const [categoryId, setCategoryId] = useState('');
  return (
    <div className="adopt-panel">
      <h4>纳入设定（保存为草稿，需人工确认后再标记「已确认」）</h4>
      <div className="field-row">
        <div className="field">
          <label>标题</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>
        <div className="field">
          <label>分类</label>
          <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
            <option value="">未分类</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
      </div>
      <textarea className="textarea-field" value={text} onChange={(e) => setText(e.target.value)} />
      <div className="editor-actions">
        <button className="btn ghost" onClick={onCancel}>取消</button>
        <button className="btn primary" onClick={() => onConfirm(title, categoryId || null)}>
          确认纳入
        </button>
      </div>
    </div>
  );
}
