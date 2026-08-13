import { useEffect, useRef, useState } from 'react';
import type { Project } from '@ai-novel-ide/shared-types';

import { api } from './api';
import AiPage from './pages/AiPage';
import CharactersPage from './pages/CharactersPage';
import CoversPage from './pages/CoversPage';
import EditorPage from './pages/EditorPage';
import ExportPage from './pages/ExportPage';
import GraphPage from './pages/GraphPage';
import OutlinePage from './pages/OutlinePage';
import AssetsPage from './pages/AssetsPage';
import SettingsPage from './pages/SettingsPage';
import StrandPage from './pages/StrandPage';
import type { DoctorData, RhythmData, SearchResult } from './api';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

type View = 'home' | 'workspace';

const NAV_ITEMS = [
  '概览', '设定', '人物', '大纲', '正文', '素材', '导出',
  'AI 讨论', '封面工坊', '图谱', '节奏',
];

const SEARCH_TYPE_LABEL: Record<string, string> = {
  setting: '设定',
  character: '人物',
  chapter: '章节',
  asset: '素材',
};

export default function App() {
  const [view, setView] = useState<View>('home');
  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState<Project | null>(null);
  const [name, setName] = useState('');
  const [backend, setBackend] = useState<'checking' | 'ok' | 'fail'>('checking');
  const [activeNav, setActiveNav] = useState('概览');
  const [focusChapterId, setFocusChapterId] = useState<string | null>(null);
  const [focusSettingId, setFocusSettingId] = useState<string | null>(null);
  const [focusCharacterId, setFocusCharacterId] = useState<string | null>(null);
  const [focusAssetId, setFocusAssetId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[] | null>(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const searchTimer = useRef<number | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/health`)
      .then((r) => (r.ok ? setBackend('ok') : setBackend('fail')))
      .catch(() => setBackend('fail'));
    void api.listProjects().then(setProjects).catch(() => setProjects([]));
  }, []);

  const createProject = async () => {
    if (!name.trim()) return;
      const project = await api.createProject(name.trim());
      if (project) {
        setSelected(project);
        setName('');
        setActiveNav('概览');
        setFocusChapterId(null);
        setFocusSettingId(null);
        setFocusCharacterId(null);
        setFocusAssetId(null);
        setView('workspace');
        await api.listProjects().then(setProjects).catch(() => undefined);
      }
  };

  const goHome = () => {
    setView('home');
    setSelected(null);
    setActiveNav('概览');
    setFocusChapterId(null);
    setFocusSettingId(null);
    setFocusCharacterId(null);
    setFocusAssetId(null);
  };

  const graphNavigate = (type: string, id: string) => {
    if (type === 'setting') {
      setFocusSettingId(id);
      setActiveNav('设定');
    } else if (type === 'character') {
      setFocusCharacterId(id);
      setActiveNav('人物');
    } else if (type === 'chapter') {
      setFocusChapterId(id);
      setActiveNav('正文');
    } else if (type === 'asset') {
      setFocusAssetId(id);
      setActiveNav('素材');
    }
  };

  const runSearch = (q: string) => {
    setSearchQuery(q);
    if (!selected || !q.trim()) {
      setSearchResults(null);
      setSearchOpen(false);
      return;
    }
    if (searchTimer.current) window.clearTimeout(searchTimer.current);
    searchTimer.current = window.setTimeout(() => {
      void api
        .searchProject(selected.id, q.trim())
        .then((items) => {
          setSearchResults(items);
          setSearchOpen(true);
        })
        .catch(() => setSearchResults([]));
    }, 300);
  };

  const openSearchResult = (type: string, id: string) => {
    setSearchOpen(false);
    setSearchQuery('');
    setSearchResults(null);
    graphNavigate(type, id);
  };

  return (
    <div className="app">
      <header className="topbar">
        <button className="logo" onClick={goHome} title="返回主页">
          <span className="logo-mark">书</span>
          <span>AI Novel IDE</span>
        </button>
        {view === 'workspace' && selected && (
          <button className="back-home" onClick={goHome}>
            ← 返回主页
          </button>
        )}
        {selected && (
          <button className="project-switch" onClick={() => setView('workspace')}>
            {selected.name} ▾
          </button>
        )}
        <div className="search">
          <span>⌕</span>
          <input
            placeholder={selected ? '搜索设定、人物、章节、正文…' : '进入作品后可搜索'}
            value={searchQuery}
            onChange={(e) => runSearch(e.target.value)}
            onFocus={() => searchResults && searchResults.length > 0 && setSearchOpen(true)}
            onBlur={() => window.setTimeout(() => setSearchOpen(false), 150)}
            onKeyDown={(e) => {
              if (e.key === 'Escape') setSearchOpen(false);
              if (e.key === 'Enter') setSearchOpen(true);
            }}
          />
          {searchOpen && searchResults && (
            <div className="search-dropdown">
              {searchResults.length === 0 ? (
                <div className="search-empty">没有匹配结果</div>
              ) : (
                searchResults.map((r, i) => (
                  <button
                    key={`${r.type}-${r.id}-${i}`}
                    className="search-item"
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => openSearchResult(r.type, r.id)}
                  >
                    <span className={`tag search-tag`}>{SEARCH_TYPE_LABEL[r.type] ?? r.type}</span>
                    <span className="search-main">
                      <span className="search-title">{r.title}</span>
                      {r.snippet && <span className="search-snippet">{r.snippet}</span>}
                    </span>
                  </button>
                ))
              )}
            </div>
          )}
        </div>
        <div className="spacer" />
        <span className={`backend backend-${backend}`}>
          {backend === 'checking' && '连接后端…'}
          {backend === 'ok' && '● 后端已连接'}
          {backend === 'fail' && '● 后端未连接'}
        </span>
      </header>

      <div className="shell">
        {view === 'workspace' && (
          <nav className="sidebar">
            {NAV_ITEMS.map((item) => (
              <button
                key={item}
                className={`nav-item ${activeNav === item ? 'active' : ''}`}
                onClick={() => setActiveNav(item)}
              >
                {item}
              </button>
            ))}
          </nav>
        )}

        <main className="main">
          <div key={view} className="view-enter">
            {view === 'home' ? (
              <Home
                name={name}
                setName={setName}
                projects={projects}
                onCreate={createProject}
                onOpen={(p) => {
                  setSelected(p);
                  setActiveNav('概览');
                  setFocusChapterId(null);
                  setFocusSettingId(null);
                  setFocusCharacterId(null);
                  setFocusAssetId(null);
                  setView('workspace');
                }}
              />
            ) : (
              <Workspace
                project={selected}
                nav={activeNav}
                focusChapterId={focusChapterId}
                focusSettingId={focusSettingId}
                focusCharacterId={focusCharacterId}
                focusAssetId={focusAssetId}
                onOpenChapter={(id) => {
                  setFocusChapterId(id);
                  setActiveNav('正文');
                }}
                onGraphNavigate={graphNavigate}
              />
            )}
          </div>
        </main>
      </div>

      <footer className="statusbar">
        <span>{selected ? `字数 0 · ${selected.name}` : 'AI Novel IDE 骨架'}</span>
        <div className="spacer" />
        <span>Ctrl S 保存</span>
        <span>Ctrl K 命令</span>
        <span>v0.5</span>
      </footer>
    </div>
  );
}

function Home({
  name,
  setName,
  projects,
  onCreate,
  onOpen,
}: {
  name: string;
  setName: (v: string) => void;
  projects: Project[];
  onCreate: () => void;
  onOpen: (p: Project) => void;
}) {
  const latest = projects[0] ?? null;
  return (
    <div className="home">
      <div className="home-hero">
        <div className="home-glow" />
        <div className="home-grid-bg" />
        <div className="home-hero-inner">
          <p className="home-eyebrow">AI NOVEL IDE</p>
          <h1 className="home-title">
            把脑中的世界，
            <br />
            写成<span className="home-title-accent">百章长卷</span>
          </h1>
          <p className="home-sub">设定 · 人物 · 大纲 · 正文，一处管理，AI 陪你写到结局。</p>
        </div>
      </div>

      {latest && (
        <button className="continue-card" onClick={() => onOpen(latest)}>
          <div className="continue-cover">
            <span className="continue-glyph">书</span>
          </div>
          <div className="continue-meta">
            <span className="continue-label">继续写作</span>
            <span className="continue-title">{latest.name}</span>
            <span className="continue-sub">
              {latest.genre || '未设置题材'} · {latest.targetWords.toLocaleString()} 字目标
            </span>
            <div className="progress">
              <div className="progress-fill" style={{ width: '0%' }} />
            </div>
          </div>
          <span className="continue-action">继续 →</span>
        </button>
      )}

      <div className="home-section">
        <div className="home-section-head">
          <h2>最近作品</h2>
          {projects.length > 0 && <span className="muted">{projects.length} 部作品</span>}
        </div>
        {projects.length === 0 ? (
          <div className="empty empty-fancy">
            <span className="empty-glyph">✦</span>
            <p>还没有作品，写下第一本书的名字，故事从这里开始。</p>
          </div>
        ) : (
          <div className="cards">
            {projects.map((p, i) => (
              <button key={p.id} className="card" onClick={() => onOpen(p)}>
                <div className={`cover cover-${i % 5}`}>
                  <span className="cover-glyph">书</span>
                </div>
                <div className="name">{p.name}</div>
                <div className="sub">
                  {p.genre || '未设置题材'} · {p.targetWords.toLocaleString()} 字
                </div>
              </button>
            ))}
            <button className="card new-card" onClick={() => document.querySelector<HTMLInputElement>('.create-box input')?.focus()}>
              <div className="new-plus">＋</div>
              <div className="name">新建作品</div>
            </button>
          </div>
        )}
      </div>

      <div className="home-section">
        <div className="create-box">
          <input
            placeholder="输入书名，开始一段新故事…"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onCreate()}
          />
          <button className="btn primary" onClick={onCreate}>
            开始创作
          </button>
        </div>
      </div>
    </div>
  );
}

function Workspace({
  project,
  nav,
  focusChapterId,
  focusSettingId,
  focusCharacterId,
  focusAssetId,
  onOpenChapter,
  onGraphNavigate,
}: {
  project: Project | null;
  nav: string;
  focusChapterId: string | null;
  focusSettingId: string | null;
  focusCharacterId: string | null;
  focusAssetId: string | null;
  onOpenChapter: (chapterId: string) => void;
  onGraphNavigate: (type: string, id: string) => void;
}) {
  if (!project) return <div className="page-pad muted">未选择作品</div>;

  if (nav === '设定')
    return <SettingsPage projectId={project.id} focusSettingId={focusSettingId} />;
  if (nav === '大纲')
    return <OutlinePage projectId={project.id} onOpenChapter={onOpenChapter} />;
  if (nav === '正文')
    return <EditorPage projectId={project.id} focusChapterId={focusChapterId} />;
  if (nav === '人物')
    return <CharactersPage projectId={project.id} focusCharacterId={focusCharacterId} />;
  if (nav === '导出') return <ExportPage projectId={project.id} />;
  if (nav === '素材') return <AssetsPage projectId={project.id} focusAssetId={focusAssetId} />;
  if (nav === 'AI 讨论') return <AiPage projectId={project.id} />;
  if (nav === '封面工坊') return <CoversPage projectId={project.id} />;
  if (nav === '图谱') return <GraphPage projectId={project.id} onNavigate={onGraphNavigate} />;
  if (nav === '节奏') return <StrandPage projectId={project.id} />;
  if (nav === '概览') return <Overview projectId={project.id} />;

  return (
    <div className="page-pad">
      <h1>{project.name}</h1>
      <p className="muted">
        当前模块：{nav}（该模块开发中）
      </p>
      <div className="stats">
        <div className="stat"><div className="num">0</div><div className="lbl">总字数</div></div>
        <div className="stat"><div className="num">0</div><div className="lbl">章节</div></div>
        <div className="stat"><div className="num">0</div><div className="lbl">设定</div></div>
        <div className="stat"><div className="num">0</div><div className="lbl">人物</div></div>
      </div>
    </div>
  );
}

function Overview({ projectId }: { projectId: string }) {
  const [doctor, setDoctor] = useState<DoctorData | null>(null);
  const [rhythm, setRhythm] = useState<RhythmData | null>(null);
  useEffect(() => {
    void api.getDoctor(projectId).then(setDoctor).catch(() => undefined);
    void api.getRhythm(projectId).then(setRhythm).catch(() => undefined);
  }, [projectId]);

  return (
    <div className="page-pad">
      <h1>作品概览</h1>
      <p className="muted">
        项目体检：{doctor ? (doctor.healthy ? '✓ 健康' : '发现需要处理的问题') : '检查中…'}
      </p>

      {doctor && (
        <div className="doctor-list">
          {doctor.checks.map((check) => (
            <div key={check.id} className={`doctor-item doctor-${check.status}`}>
              <span className="doctor-label">{check.label}</span>
              <span className="doctor-status">
                {check.status === 'ok' ? '通过' : check.status === 'warn' ? '提醒' : check.status === 'fail' ? '问题' : '信息'}
              </span>
              <span className="doctor-detail">{check.detail}</span>
            </div>
          ))}
        </div>
      )}

      {rhythm && (
        <div className="strand-cards">
          {Object.entries(rhythm.strands).map(([key, s]) => (
            <div key={key} className="strand-card">
              <div className="strand-head">
                <span className="strand-name">{s.label}</span>
                <span className={`badge ${s.ok ? 'done' : 'active'}`}>
                  {s.ok ? '正常' : `断档 ${s.maxGap}/${s.limit}`}
                </span>
              </div>
              <div className="strand-nums">
                覆盖 {s.chapters} 章 · 占比 {Math.round(s.ratio * 100)}% · 未回收伏笔 {rhythm.openChekhovs}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
