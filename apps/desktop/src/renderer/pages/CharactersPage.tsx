import { useCallback, useEffect, useMemo, useState } from 'react';
import type { Character, Setting } from '@ai-novel-ide/shared-types';

import { api } from '../api';

export default function CharactersPage({
  projectId,
  focusCharacterId = null,
}: {
  projectId: string;
  focusCharacterId?: string | null;
}) {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [settings, setSettings] = useState<Setting[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    const [chars, sets] = await Promise.all([
      api.listCharacters(projectId),
      api.listSettings(projectId),
    ]);
    setCharacters(chars);
    setSettings(sets);
  }, [projectId]);

  useEffect(() => {
    void load().catch((e) => setError(String(e)));
  }, [load]);

  useEffect(() => {
    if (focusCharacterId) setSelectedId(focusCharacterId);
  }, [focusCharacterId]);

  const selected = useMemo(
    () => characters.find((c) => c.id === selectedId) ?? null,
    [characters, selectedId],
  );

  const visible = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return characters;
    return characters.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.identity.toLowerCase().includes(q) ||
        c.tags.some((t) => t.toLowerCase().includes(q)),
    );
  }, [characters, search]);

  const createCharacter = async () => {
    const created = await api.createCharacter(projectId, '新人物');
    await load();
    setSelectedId(created.id);
  };

  const removeCharacter = async () => {
    if (!selected || !window.confirm(`删除人物「${selected.name}」？`)) return;
    await api.deleteCharacter(projectId, selected.id);
    setSelectedId(null);
    await load();
  };

  return (
    <div className="page-fill">
      <div className="page-head">
        <h1>人物</h1>
        <div className="spacer" />
        <div className="search-box">
          <input placeholder="搜索人物…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <button className="btn primary" onClick={() => void createCharacter()}>
          ＋ 新建人物
        </button>
      </div>

      {error && <div className="page-error">{error}</div>}

      <div className="char-layout">
        <div className="char-list">
          {visible.length === 0 && <div className="list-empty">没有人物，点「新建人物」。</div>}
          {visible.map((c) => (
            <div
              key={c.id}
              className={`char-card ${c.id === selectedId ? 'active' : ''}`}
              onClick={() => setSelectedId(c.id)}
            >
              <div className="avatar">{c.name.slice(0, 1)}</div>
              <div>
                <div className="name">{c.name}</div>
                <div className="role">{c.identity || '未填写身份'}</div>
              </div>
              <span className={`tag ${c.status === 'confirmed' ? 'confirmed' : 'draft'}`}>
                {c.status === 'confirmed' ? '已确认' : '草稿'}
              </span>
            </div>
          ))}
        </div>

        <div className="char-detail">
          {selected ? (
            <CharacterEditor
              key={selected.id}
              character={selected}
              settings={settings}
              projectId={projectId}
              onSaved={(updated) =>
                setCharacters((prev) => prev.map((c) => (c.id === updated.id ? updated : c)))
              }
              onDelete={() => void removeCharacter()}
            />
          ) : (
            <div className="editor-empty">选择左侧人物开始编辑</div>
          )}
        </div>
      </div>
    </div>
  );
}

function CharacterEditor({
  character,
  settings,
  projectId,
  onSaved,
  onDelete,
}: {
  character: Character;
  settings: Setting[];
  projectId: string;
  onSaved: (c: Character) => void;
  onDelete: () => void;
}) {
  const [name, setName] = useState(character.name);
  const [aliases, setAliases] = useState(character.aliases.join(', '));
  const [identity, setIdentity] = useState(character.identity);
  const [personality, setPersonality] = useState(character.personality);
  const [appearance, setAppearance] = useState(character.appearance);
  const [background, setBackground] = useState(character.background);
  const [goals, setGoals] = useState(character.goals);
  const [tags, setTags] = useState(character.tags.join(', '));
  const [notes, setNotes] = useState(character.notes);
  const [status, setStatus] = useState(character.status);
  const [linkedSettingIds, setLinkedSettingIds] = useState<string[]>([]);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    setName(character.name);
    setAliases(character.aliases.join(', '));
    setIdentity(character.identity);
    setPersonality(character.personality);
    setAppearance(character.appearance);
    setBackground(character.background);
    setGoals(character.goals);
    setTags(character.tags.join(', '));
    setNotes(character.notes);
    setStatus(character.status);
    setDirty(false);
    void api
      .listCharacterLinks(projectId, character.id)
      .then((links) => setLinkedSettingIds(links.map((l) => l.targetId)))
      .catch(() => undefined);
  }, [character, projectId]);

  const markDirty = () => setDirty(true);

  const handleSave = async () => {
    const updated = await api.updateCharacter(projectId, character.id, {
      name,
      aliases: aliases.split(/[,，]/).map((x) => x.trim()).filter(Boolean),
      identity,
      personality,
      appearance,
      background,
      goals,
      tags: tags.split(/[,，]/).map((x) => x.trim()).filter(Boolean),
      notes,
      status: status as Character['status'],
    });
    await api.replaceCharacterLinks(projectId, character.id, linkedSettingIds);
    onSaved(updated);
    setDirty(false);
  };

  const toggleLink = (settingId: string) => {
    setLinkedSettingIds((prev) =>
      prev.includes(settingId)
        ? prev.filter((id) => id !== settingId)
        : [...prev, settingId],
    );
    markDirty();
  };

  return (
    <div>
      <div className="editor-head">
        <input
          className="title"
          value={name}
          onChange={(e) => { setName(e.target.value); markDirty(); }}
        />
        <span className={`tag ${status === 'confirmed' ? 'confirmed' : 'draft'}`}>
          {status === 'confirmed' ? '已确认' : '草稿'}
        </span>
      </div>

      <div className="field-row">
        <div className="field">
          <label>别名（逗号分隔）</label>
          <input value={aliases} onChange={(e) => { setAliases(e.target.value); markDirty(); }} />
        </div>
        <div className="field">
          <label>身份</label>
          <input value={identity} onChange={(e) => { setIdentity(e.target.value); markDirty(); }} />
        </div>
        <div className="field">
          <label>状态</label>
          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value as Character['status']); markDirty(); }}
          >
            <option value="draft">草稿</option>
            <option value="confirmed">已确认</option>
          </select>
        </div>
      </div>

      <div className="field">
        <label>性格</label>
        <textarea className="textarea-field" value={personality} onChange={(e) => { setPersonality(e.target.value); markDirty(); }} />
      </div>
      <div className="field">
        <label>外貌</label>
        <textarea className="textarea-field" value={appearance} onChange={(e) => { setAppearance(e.target.value); markDirty(); }} />
      </div>
      <div className="field">
        <label>背景故事</label>
        <textarea className="textarea-field" value={background} onChange={(e) => { setBackground(e.target.value); markDirty(); }} />
      </div>
      <div className="field">
        <label>目标</label>
        <textarea className="textarea-field" value={goals} onChange={(e) => { setGoals(e.target.value); markDirty(); }} />
      </div>
      <div className="field">
        <label>标签（逗号分隔）</label>
        <input value={tags} onChange={(e) => { setTags(e.target.value); markDirty(); }} />
      </div>
      <div className="field">
        <label>备注</label>
        <textarea className="textarea-field" value={notes} onChange={(e) => { setNotes(e.target.value); markDirty(); }} />
      </div>

      <div className="field">
        <label>关联设定（可多选）</label>
        <div className="link-picker">
          {settings.length === 0 && <span className="hint">还没有设定，先去「设定」页创建。</span>}
          {settings.map((s) => (
            <label key={s.id} className="link-option">
              <input
                type="checkbox"
                checked={linkedSettingIds.includes(s.id)}
                onChange={() => toggleLink(s.id)}
              />
              <span>{s.title}</span>
              <span className={`tag ${s.status === 'confirmed' ? 'confirmed' : 'draft'}`}>
                {s.status === 'confirmed' ? '已确认' : '草稿'}
              </span>
            </label>
          ))}
        </div>
      </div>

      <div className="editor-actions">
        {dirty && <span className="hint">有未保存修改</span>}
        <div className="spacer" />
        <button className="btn secondary" onClick={onDelete}>删除</button>
        <button className="btn primary" onClick={() => void handleSave()}>保存人物</button>
      </div>
    </div>
  );
}
