import { useCallback, useEffect, useMemo, useState } from 'react';
import type { Setting, SettingCategory } from '@ai-novel-ide/shared-types';

import { api } from '../api';

const CATEGORY_LABELS: Record<string, string> = {
  rule: '规则',
  geography: '地理',
  history: '历史',
  faction: '势力',
};

export default function SettingsPage({
  projectId,
  focusSettingId = null,
}: {
  projectId: string;
  focusSettingId?: string | null;
}) {
  const [categories, setCategories] = useState<SettingCategory[]>([]);
  const [settings, setSettings] = useState<Setting[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [filterCategory, setFilterCategory] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [newCategory, setNewCategory] = useState('');
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    const [cats, items] = await Promise.all([
      api.listCategories(projectId),
      api.listSettings(projectId),
    ]);
    setCategories(cats);
    setSettings(items);
  }, [projectId]);

  useEffect(() => {
    void load().catch((e) => setError(String(e)));
  }, [load]);

  useEffect(() => {
    if (focusSettingId) setSelectedId(focusSettingId);
  }, [focusSettingId]);

  const selected = useMemo(
    () => settings.find((s) => s.id === selectedId) ?? null,
    [settings, selectedId],
  );

  const visibleSettings = useMemo(
    () =>
      settings.filter((s) => {
        if (filterCategory && s.categoryId !== filterCategory) return false;
        const q = search.trim().toLowerCase();
        if (!q) return true;
        return (
          s.title.toLowerCase().includes(q) ||
          s.contentMd.toLowerCase().includes(q) ||
          s.tags.some((t) => t.toLowerCase().includes(q))
        );
      }),
    [settings, filterCategory, search],
  );

  const roots = useMemo(
    () =>
      categories
        .filter((c) => !c.parentId)
        .sort((a, b) => a.sortOrder - b.sortOrder),
    [categories],
  );
  const childrenOf = useCallback(
    (parentId: string) =>
      categories
        .filter((c) => c.parentId === parentId)
        .sort((a, b) => a.sortOrder - b.sortOrder),
    [categories],
  );

  const createSetting = async () => {
    const created = await api.createSetting(projectId, {
      categoryId: filterCategory,
    });
    await load();
    setSelectedId(created.id);
  };

  const saveSetting = async (data: Partial<Setting>) => {
    if (!selected) return;
    const updated = await api.updateSetting(projectId, selected.id, data);
    setSettings((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
  };

  const removeSetting = async () => {
    if (!selected || !window.confirm(`删除设定「${selected.title}」？`)) return;
    await api.deleteSetting(projectId, selected.id);
    setSelectedId(null);
    await load();
  };

  const addCategory = async () => {
    const name = newCategory.trim();
    if (!name) return;
    await api.createCategory(projectId, name);
    setNewCategory('');
    await load();
  };

  const removeCategory = async (id: string, name: string) => {
    if (!window.confirm(`删除分类「${name}」？分类下的设定会保留但脱离分类。`)) return;
    try {
      await api.deleteCategory(projectId, id);
      if (filterCategory === id) setFilterCategory(null);
      await load();
    } catch (e) {
      window.alert(String(e));
    }
  };

  return (
    <div className="page-fill">
      <div className="page-head">
        <h1>设定</h1>
        <div className="spacer" />
        <div className="search-box">
          <input placeholder="搜索设定…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <button className="btn primary" onClick={() => void createSetting()}>
          ＋ 新建设定
        </button>
      </div>

      {error && <div className="page-error">{error}</div>}

      <div className="lib-layout">
        <div className="lib-tree">
          <div
            className={`tree-item ${filterCategory === null ? 'active' : ''}`}
            onClick={() => setFilterCategory(null)}
          >
            <span>全部</span>
            <span className="count">{settings.length}</span>
          </div>
          {roots.map((c) => (
            <div key={c.id}>
              <div
                className={`tree-item ${filterCategory === c.id ? 'active' : ''}`}
                onClick={() => setFilterCategory(c.id)}
              >
                <span>{CATEGORY_LABELS[c.name] ?? c.name}</span>
                <span className="count">
                  {settings.filter((s) => s.categoryId === c.id).length}
                </span>
                <button
                  className="icon-btn"
                  title="删除分类"
                  onClick={(e) => {
                    e.stopPropagation();
                    void removeCategory(c.id, c.name);
                  }}
                >
                  ×
                </button>
              </div>
              {childrenOf(c.id).map((child) => (
                <div
                  key={child.id}
                  className={`tree-item indent-1 ${filterCategory === child.id ? 'active' : ''}`}
                  onClick={() => setFilterCategory(child.id)}
                >
                  <span>{child.name}</span>
                </div>
              ))}
            </div>
          ))}
          <div className="tree-add">
            <input
              placeholder="新分类名…"
              value={newCategory}
              onChange={(e) => setNewCategory(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && void addCategory()}
            />
            <button className="btn ghost" onClick={() => void addCategory()}>
              ＋
            </button>
          </div>
        </div>

        <div className="lib-list">
          {visibleSettings.length === 0 && (
            <div className="list-empty">没有设定条目，点右上角「新建设定」。</div>
          )}
          {visibleSettings.map((s) => (
            <div
              key={s.id}
              className={`list-row ${s.id === selectedId ? 'active' : ''}`}
              onClick={() => setSelectedId(s.id)}
            >
              <div className="list-main">
                <span className="title">{s.title}</span>
                <span className="sub">{s.contentMd.slice(0, 36) || '（还没有内容）'}</span>
              </div>
              <span className={`tag ${s.status === 'confirmed' ? 'confirmed' : 'draft'}`}>
                {s.status === 'confirmed' ? '已确认' : '草稿'}
              </span>
            </div>
          ))}
        </div>

        <div className="lib-editor">
          {selected ? (
            <SettingEditor
              key={selected.id}
              setting={selected}
              categories={categories}
              onSave={(data) => void saveSetting(data)}
              onDelete={() => void removeSetting()}
            />
          ) : (
            <div className="editor-empty">选择左侧条目开始编辑</div>
          )}
        </div>
      </div>
    </div>
  );
}

function SettingEditor({
  setting,
  categories,
  onSave,
  onDelete,
}: {
  setting: Setting;
  categories: SettingCategory[];
  onSave: (data: Partial<Setting>) => void;
  onDelete: () => void;
}) {
  const [title, setTitle] = useState(setting.title);
  const [categoryId, setCategoryId] = useState(setting.categoryId ?? '');
  const [tags, setTags] = useState(setting.tags.join(', '));
  const [contentMd, setContentMd] = useState(setting.contentMd);
  const [status, setStatus] = useState(setting.status);
  const [saved, setSaved] = useState(true);

  useEffect(() => {
    setTitle(setting.title);
    setCategoryId(setting.categoryId ?? '');
    setTags(setting.tags.join(', '));
    setContentMd(setting.contentMd);
    setStatus(setting.status);
    setSaved(true);
  }, [setting]);

  const markDirty = () => setSaved(false);

  const handleSave = () => {
    onSave({
      title,
      categoryId: categoryId || null,
      tags: tags
        .split(/[,，]/)
        .map((t) => t.trim())
        .filter(Boolean),
      contentMd,
      status,
    });
    setSaved(true);
  };

  return (
    <div>
      <div className="editor-head">
        <input className="title" value={title} onChange={(e) => { setTitle(e.target.value); markDirty(); }} />
        <span className={`tag ${status === 'confirmed' ? 'confirmed' : 'draft'}`}>
          {status === 'confirmed' ? '已确认设定' : '草稿'}
        </span>
      </div>

      <div className="field-grid">
        <div className="field">
          <label>分类</label>
          <select value={categoryId} onChange={(e) => { setCategoryId(e.target.value); markDirty(); }}>
            <option value="">未分类</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>状态</label>
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value as Setting['status']);
              markDirty();
            }}
          >
            <option value="draft">草稿</option>
            <option value="confirmed">已确认</option>
          </select>
        </div>
        <div className="field">
          <label>标签（逗号分隔）</label>
          <input value={tags} onChange={(e) => { setTags(e.target.value); markDirty(); }} />
        </div>
      </div>

      <div className="field">
        <label>正文（Markdown）</label>
        <textarea
          className="md-editor-textarea"
          value={contentMd}
          onChange={(e) => { setContentMd(e.target.value); markDirty(); }}
          placeholder="写设定正文…"
        />
      </div>

      <div className="editor-actions">
        {!saved && <span className="hint">有未保存修改</span>}
        <div className="spacer" />
        <button className="btn secondary" onClick={onDelete}>
          删除
        </button>
        <button className="btn primary" onClick={handleSave}>
          保存设定
        </button>
      </div>
    </div>
  );
}
