import { useCallback, useEffect, useMemo, useState } from 'react';
import type { Asset } from '@ai-novel-ide/shared-types';

import { api } from '../api';

export default function AssetsPage({ projectId }: { projectId: string }) {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setAssets(await api.listAssets(projectId));
  }, [projectId]);

  useEffect(() => {
    void load().catch((e) => setError(String(e)));
  }, [load]);

  const selected = useMemo(
    () => assets.find((a) => a.id === selectedId) ?? null,
    [assets, selectedId],
  );
  const visible = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return assets;
    return assets.filter(
      (a) =>
        a.title.toLowerCase().includes(q) ||
        a.contentMd.toLowerCase().includes(q) ||
        a.tags.some((t) => t.toLowerCase().includes(q)),
    );
  }, [assets, search]);

  const createAsset = async () => {
    const created = await api.createAsset(projectId, {});
    await load();
    setSelectedId(created.id);
  };

  return (
    <div className="page-fill">
      <div className="page-head">
        <h1>素材</h1>
        <div className="spacer" />
        <div className="search-box">
          <input placeholder="搜索素材…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <button className="btn primary" onClick={() => void createAsset()}>
          ＋ 新建素材
        </button>
      </div>

      {error && <div className="page-error">{error}</div>}

      <div className="lib-layout">
        <div className="lib-list">
          {visible.length === 0 && <div className="list-empty">没有素材，点「新建素材」。</div>}
          {visible.map((a) => (
            <div
              key={a.id}
              className={`list-row ${a.id === selectedId ? 'active' : ''}`}
              onClick={() => setSelectedId(a.id)}
            >
              <span className="title">{a.title}</span>
              <span className="tag">{a.kind === 'text' ? '文本' : '文件'}</span>
            </div>
          ))}
        </div>

        <div className="lib-editor">
          {selected ? (
            <AssetEditor
              key={selected.id}
              asset={selected}
              projectId={projectId}
              onSaved={(updated) =>
                setAssets((prev) => prev.map((a) => (a.id === updated.id ? updated : a)))
              }
              onDelete={async () => {
                if (!window.confirm(`删除素材「${selected.title}」？`)) return;
                await api.deleteAsset(projectId, selected.id);
                setSelectedId(null);
                await load();
              }}
            />
          ) : (
            <div className="editor-empty">选择左侧素材开始编辑</div>
          )}
        </div>
      </div>
    </div>
  );
}

function AssetEditor({
  asset,
  projectId,
  onSaved,
  onDelete,
}: {
  asset: Asset;
  projectId: string;
  onSaved: (a: Asset) => void;
  onDelete: () => void;
}) {
  const [title, setTitle] = useState(asset.title);
  const [kind, setKind] = useState(asset.kind);
  const [contentMd, setContentMd] = useState(asset.contentMd);
  const [source, setSource] = useState(asset.source);
  const [tags, setTags] = useState(asset.tags.join(', '));
  const [notes, setNotes] = useState(asset.notes);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    setTitle(asset.title);
    setKind(asset.kind);
    setContentMd(asset.contentMd);
    setSource(asset.source);
    setTags(asset.tags.join(', '));
    setNotes(asset.notes);
    setDirty(false);
  }, [asset]);

  return (
    <div>
      <div className="editor-head">
        <input className="title" value={title} onChange={(e) => { setTitle(e.target.value); setDirty(true); }} />
        <span className="tag">{kind === 'text' ? '文本' : '文件'}</span>
      </div>
      <div className="field-row">
        <div className="field">
          <label>类型</label>
          <select
            value={kind}
            onChange={(e) => {
              setKind(e.target.value as Asset['kind']);
              setDirty(true);
            }}
          >
            <option value="text">文本</option>
            <option value="file">文件</option>
          </select>
        </div>
        <div className="field">
          <label>来源</label>
          <input value={source} onChange={(e) => { setSource(e.target.value); setDirty(true); }} />
        </div>
        <div className="field">
          <label>标签（逗号分隔）</label>
          <input value={tags} onChange={(e) => { setTags(e.target.value); setDirty(true); }} />
        </div>
      </div>
      <div className="field">
        <label>内容</label>
        <textarea className="md-editor-textarea" value={contentMd} onChange={(e) => { setContentMd(e.target.value); setDirty(true); }} />
      </div>
      <div className="field">
        <label>备注</label>
        <textarea className="textarea-field" value={notes} onChange={(e) => { setNotes(e.target.value); setDirty(true); }} />
      </div>
      <div className="editor-actions">
        {dirty && <span className="hint">有未保存修改</span>}
        <div className="spacer" />
        <button className="btn secondary" onClick={onDelete}>删除</button>
        <button
          className="btn primary"
          onClick={() => {
            void api
              .updateAsset(projectId, asset.id, {
                title,
                kind,
                contentMd,
                source,
                tags: tags.split(/[,，]/).map((t) => t.trim()).filter(Boolean),
                notes,
              })
              .then(onSaved);
            setDirty(false);
          }}
        >
          保存素材
        </button>
      </div>
    </div>
  );
}
