# 项目目录结构

> AI Novel IDE — 面向网文作者的 AI 创作操作系统
>
> 版本：v0.1-draft | 日期：2025-07-13

---

## 1. Monorepo 布局

```
ai-novel-ide/
├── apps/
│   ├── desktop/                 # Electron 桌面应用
│   │   ├── src/
│   │   │   ├── main/            # Electron 主进程
│   │   │   │   ├── index.ts     # 主进程入口
│   │   │   │   ├── window.ts    # 窗口管理
│   │   │   │   └── ipc.ts       # IPC 通信桥接
│   │   │   ├── preload/         # 预加载脚本
│   │   │   │   └── index.ts
│   │   │   └── renderer/        # React 渲染进程
│   │   │       ├── App.tsx
│   │   │       ├── main.tsx
│   │   │       ├── pages/       # 页面组件
│   │   │       ├── components/  # 通用 UI 组件
│   │   │       ├── hooks/       # 自定义 Hooks
│   │   │       ├── stores/      # Zustand 状态
│   │   │       ├── lib/         # 工具函数
│   │   │       └── styles/      # 全局样式
│   │   ├── electron-builder.yml # 打包配置
│   │   ├── vite.config.ts
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   └── server/                  # FastAPI 后端服务
│       ├── app/
│       │   ├── main.py          # FastAPI 入口
│       │   ├── config.py        # 配置管理
│       │   ├── api/             # API 路由
│       │   │   ├── __init__.py
│       │   │   ├── worlds.py    # 世界观 API
│       │   │   ├── characters.py# 人物 API
│       │   │   ├── outlines.py  # 大纲 API
│       │   │   ├── chapters.py  # 章节 API
│       │   │   ├── assets.py    # 素材 API
│       │   │   └── agent.py     # Agent API (v0.2)
│       │   ├── services/        # 业务逻辑层
│       │   │   ├── __init__.py
│       │   │   ├── world_service.py
│       │   │   ├── character_service.py
│       │   │   ├── outline_service.py
│       │   │   ├── chapter_service.py
│       │   │   ├── asset_service.py
│       │   │   └── rag_service.py  # RAG (v0.2)
│       │   ├── models/          # SQLAlchemy 数据模型
│       │   │   ├── __init__.py
│       │   │   ├── world.py
│       │   │   ├── character.py
│       │   │   ├── outline.py
│       │   │   ├── chapter.py
│       │   │   └── asset.py
│       │   ├── schemas/         # Pydantic Schema
│       │   │   ├── __init__.py
│       │   │   └── ...
│       │   ├── agents/          # AI Agent (v0.2)
│       │   │   ├── __init__.py
│       │   │   ├── editor_agent.py
│       │   │   ├── writer_agent.py
│       │   │   └── base.py
│       │   └── core/            # 核心基础设施
│       │       ├── database.py  # DB 连接
│       │       ├── vector_store.py # ChromaDB
│       │       └── llm.py       # LLM 客户端
│       ├── alembic/             # 数据库迁移
│       ├── tests/
│       ├── requirements.txt
│       └── pyproject.toml
│
├── packages/                    # 共享包
│   └── shared-types/            # 前后端共享 TypeScript 类型
│       ├── index.ts
│       ├── novel.ts             # 小说/世界观/人物等类型
│       └── package.json
│
├── docs/                        # 项目文档
│   ├── mvp-scope.md
│   ├── tech-stack.md
│   ├── architecture.md
│   ├── project-structure.md     # 本文件
│   └── dev-setup.md
│
├── scripts/                     # 构建/开发脚本
│   ├── dev.sh / dev.ps1         # 一键启动开发环境
│   └── build.sh / build.ps1     # 构建打包脚本
│
├── .gitignore
├── .eslintrc.cjs
├── .prettierrc
├── README.md
└── LICENSE
```

---

## 2. 目录设计原则

| 原则 | 说明 |
|------|------|
| **Monorepo 统一管理** | 前端、后端、共享类型在一个仓库，简化协作和 CI |
| **约定优于配置** | 目录结构即架构约定，新人看目录就懂分层 |
| **按功能模块拆分** | 每个子系统在 API/Service/Model 层各有独立文件 |
| **MVP 先简化** | agent/rag 等 v0.2 模块的文件仅在父目录留 __init__.py 占位 |
| **共享类型独立包** | 前端 TS 类型和后端 Pydantic Schema 通过 shared-types 保持一致 |

---

## 3. 命名规范

| 类别 | 规范 | 示例 |
|------|------|------|
| Python 文件 | snake_case | world_service.py |
| Python 类 | PascalCase | WorldService |
| Python 函数 | snake_case | get_world_by_id() |
| TypeScript 文件 | kebab-case | world-panel.tsx |
| TypeScript 组件 | PascalCase | WorldPanel |
| TypeScript 函数 | camelCase | useWorldQuery() |
| 数据库表 | snake_case 复数 | characters |
| API 路由 | kebab-case | /api/worlds/{id} |
| Git 分支 | kebab-case | eat/character-system |

---

## 4. 文件不在仓库的内容

| 内容 | 位置 | 原因 |
|------|------|------|
| 用户创作数据 | ~/ai-novel-ide-data/ | 与代码分离，方便备份 |
| SQLite 数据库 | ~/ai-novel-ide-data/novel.db | 用户本地数据 |
| ChromaDB 向量库 | ~/ai-novel-ide-data/vectors/ | 嵌入向量持久化 |
| 素材文件 | ~/ai-novel-ide-data/assets/ | 用户上传的图片等 |
| 环境变量 | .env (gitignore) | API Key 等敏感信息 |
| Electron 打包产物 | pps/desktop/dist/ | 构建产物不入库 |

---

> 相关文档：[README.md](../README.md) · [mvp-scope.md](mvp-scope.md) · [tech-stack.md](tech-stack.md) · [architecture.md](architecture.md) · [dev-setup.md](dev-setup.md)
