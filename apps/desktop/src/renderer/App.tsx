import { useCallback, useEffect, useState } from 'react';
import type { Project } from '@ai-novel-ide/shared-types';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

type View = 'home' | 'workspace';

const NAV_ITEMS = ['概览', '设定', '人物', '大纲', '正文', '素材', '导出'];

export default function App() {
  const [view, setView] = useState<View>('home');
  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState<Project | null>(null);
  const [name, setName] = useState('');
  const [backend, setBackend] = useState<'checking' | 'ok' | 'fail'>('checking');
  const [activeNav, setActiveNav] = useState('概览');

  const loadProjects = useCallback(async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/projects`);
      setProjects(await resp.json());
    } catch {
      setProjects([]);
    }
  }, []);

  useEffect(() => {
    fetch(`${API_BASE}/api/health`)
      .then((r) => (r.ok ? setBackend('ok') : setBackend('fail')))
      .catch(() => setBackend('fail'));
    void loadProjects();
  }, [loadProjects]);

  const createProject = async () => {
    if (!name.trim()) return;
    const resp = await fetch(`${API_BASE}/api/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name.trim() }),
    });
    if (resp.ok) {
      const project: Project = await resp.json();
      setSelected(project);
      setName('');
      setView('workspace');
      await loadProjects();
    }
  };

  return (
    <div className="app">
      <header className="topbar">
        <button className="logo" onClick={() => setView('home')}>
          <span className="logo-mark">书</span>
          <span>AI Novel IDE</span>
        </button>
        {selected && (
          <button className="project-switch" onClick={() => setView('workspace')}>
            {selected.name} ▾
          </button>
        )}
        <div className="search">⌕ 搜索设定、人物、章节…</div>
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
          {view === 'home' ? (
            <Home
              name={name}
              setName={setName}
              projects={projects}
              onCreate={createProject}
              onOpen={(p) => {
                setSelected(p);
                setView('workspace');
              }}
            />
          ) : (
            <Workspace project={selected} nav={activeNav} />
          )}
        </main>
      </div>

      <footer className="statusbar">
        <span>{selected ? `字数 0 · ${selected.name}` : 'AI Novel IDE 骨架'}</span>
        <div className="spacer" />
        <span>Ctrl S 保存</span>
        <span>Ctrl K 命令</span>
        <span>v0.4</span>
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
  return (
    <div className="page-pad">
      <h1>继续创作</h1>
      <p className="muted">你的作品都保存在本机。</p>

      <div className="create-box">
        <input
          placeholder="书名（必填）"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && onCreate()}
        />
        <button className="btn primary" onClick={onCreate}>
          ＋ 新建作品
        </button>
      </div>

      <h2>最近作品</h2>
      {projects.length === 0 ? (
        <div className="empty">
          <p>还没有作品，输入书名创建第一个。</p>
        </div>
      ) : (
        <div className="cards">
          {projects.map((p) => (
            <button key={p.id} className="card" onClick={() => onOpen(p)}>
              <div className="cover" />
              <div className="name">{p.name}</div>
              <div className="sub">
                {p.genre || '未设置题材'} · {p.targetWords.toLocaleString()} 字
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function Workspace({ project, nav }: { project: Project | null; nav: string }) {
  return (
    <div className="page-pad">
      <h1>{project?.name ?? '作品'}</h1>
      <p className="muted">
        当前模块：{nav}（骨架阶段，功能开发中。后端 API：/api/projects · /settings · /characters）
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
