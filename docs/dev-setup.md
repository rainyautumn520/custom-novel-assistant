# 开发环境搭建与部署指南

> AI Novel IDE — 面向网文作者的 AI 创作操作系统
>
> 版本：v0.6 | 更新：2026-08-11

本文覆盖：环境要求、依赖安装、启动方式、数据库迁移、AI 能力配置（DeepSeek /
Seedream / Ollama）、测试与 E2E、常见问题。

---

## 1. 环境要求

| 工具 | 最低版本 | 用途 |
|---|---|---|
| Node.js | >= 20 LTS | 前端构建、Electron |
| Python | >= 3.12 | 后端、RAG、AI |
| Git | >= 2.40 | 版本控制 |
| npm | >= 10 | 前端依赖 |
| Ollama（可选） | >= 0.30 | 本地 bge-m3 嵌入后端 |

磁盘建议预留 >= 3 GB（Python 依赖约 1.5 GB，嵌入模型约 0.1–1.2 GB）。

---

## 2. 安装

```bash
# 克隆
git clone https://github.com/rainyautumn520/custom-novel-assistant
cd custom-novel-assistant

# 前端（npm workspaces，含 Electron；国内网络慢时可先跳过二进制）
npm install
# 若 Electron 下载卡住：
#   $env:ELECTRON_SKIP_BINARY_DOWNLOAD='1'; npm install
#   cd apps/desktop; node node_modules\electron\install.js   # 之后再补

# 后端
cd apps/server
python -m venv .venv
# Windows:
.\.venv\Scripts\pip install -r requirements.txt
# macOS/Linux:
source .venv/bin/pip install -r requirements.txt
```

后端依赖说明（requirements.txt）：

| 依赖 | 用途 |
|---|---|
| fastapi / uvicorn / pydantic | API 服务 |
| sqlalchemy / alembic | ORM 与迁移 |
| chromadb | 向量库 |
| sentence-transformers + torch(CUDA 可选) | 默认中文嵌入（BGE-small-zh-v1.5） |
| python-multipart | 素材文件上传 |
| pytest / httpx | 测试 |

> 如果不想装 torch，可改用 Ollama 嵌入后端（见 5.3），并把
> `sentence-transformers` 从 requirements 中移除。

---

## 3. 启动

### 一键启动（Windows）

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1
```

脚本会自动创建后端虚拟环境、安装依赖，然后同时启动：

- 后端 API：http://localhost:8000（文档 /docs）
- 前端 Dev Server：http://localhost:5173

### 手动启动（两个终端）

```bash
# 终端 1：后端
cd apps/server
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000

# 终端 2：浏览器模式
npm run dev:desktop

# 终端 2 备选：Electron 桌面窗口
npm run electron:dev -w @ai-novel-ide/desktop
```

> Electron 生产模式由主进程动态分配端口并启动后端，不依赖固定 8000（ADR-01）。

---

## 4. 数据库迁移

项目使用双迁移链（ADR-07）：

```bash
cd apps/server

# 1) 应用级库（最近作品、全局设置、凭证密文）
.\.venv\Scripts\python -m alembic upgrade head

# 2) 作品库（每个作品独立 novel.db）
# Windows PowerShell：
$env:NOVEL_DB_URL='sqlite:///C:/Users/<你>/ai-novel-ide-data/workspaces/<作品ID>/novel.db'
.\.venv\Scripts\python -m alembic -c alembic_novel.ini upgrade head

# macOS/Linux：
# NOVEL_DB_URL="sqlite:///~/ai-novel-ide-data/workspaces/<作品ID>/novel.db" \
#   .venv/bin/python -m alembic -c alembic_novel.ini upgrade head
```

说明：

- 新建作品时服务端自动建表；老作品升级只需对每个作品库执行一次 `upgrade head`。
- 打开作品时版本不匹配会阻止写入（打开时校验逻辑在接入中）。
- 生成新迁移（改模型后）：
  ```bash
  .\.venv\Scripts\python -m alembic revision --autogenerate -m "描述"
  $env:NOVEL_DB_URL='sqlite:///临时.db'
  .\.venv\Scripts\python -m alembic -c alembic_novel.ini revision --autogenerate -m "描述"
  ```

---

## 5. 环境变量与 AI 配置

后端通过环境变量或 `apps/server/.env` 读取配置（模板见 [.env.example](../apps/server/.env.example)），
前缀统一为 `AI_NOVEL_`。

### 5.1 基础

| 变量 | 默认 | 说明 |
|---|---|---|
| `AI_NOVEL_DATA_DIR` | `~/ai-novel-ide-data` | 用户创作数据根目录（app.db + workspaces/） |
| `AI_NOVEL_CORS_ORIGINS` | `["http://localhost:5173","http://127.0.0.1:5173"]` | 开发用 CORS 白名单 |

### 5.2 DeepSeek（AI 讨论 / 续写 / 改写 / AI 审查 / AI 任务书）

```ini
AI_NOVEL_DEEPSEEK_API_KEY=sk-xxxx
AI_NOVEL_DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
AI_NOVEL_DEEPSEEK_MODEL=deepseek-chat
```

未配置时：任务书、五维审查自动使用**本地规则版**，续写/改写返回 503 提示，不影响其他功能。

### 5.3 向量嵌入（RAG）

默认后端：sentence-transformers + `BAAI/bge-small-zh-v1.5`（首次使用自动下载约 100 MB）。

```ini
AI_NOVEL_VECTOR_BACKEND=sentence-transformers
AI_NOVEL_VECTOR_MODEL=BAAI/bge-small-zh-v1.5
```

切换 Ollama bge-m3（需要先 `ollama pull bge-m3`）：

```ini
AI_NOVEL_VECTOR_BACKEND=ollama
AI_NOVEL_VECTOR_MODEL=bge-m3
AI_NOVEL_OLLAMA_BASE_URL=http://localhost:11434
```

切换后到「AI 设定讨论」页点「重建知识索引」即可。

### 5.4 封面生成（Seedream 5.0）

```ini
AI_NOVEL_SEEDREAM_API_KEY=xxxx
AI_NOVEL_SEEDREAM_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
AI_NOVEL_SEEDREAM_MODEL=doubao-seedream-5-0
```

> 注意：模型标识以火山方舟官方文档为准（ADR-05 待联调确认）。未配置时封面任务会
> 如实标记 failed 并提示凭证缺失，不会静默失败。

---

## 6. 测试与 E2E

```bash
# 后端单元/集成测试（31 个）
cd apps/server
.\.venv\Scripts\python -m pytest -q

# 前端类型检查 + 构建
cd ../..
npm run build

# 端到端（需先启动后端 8000 与前端 5173）
node scripts/e2e-smoke.mjs
```

E2E 会播种一个测试项目，驱动本机 Edge：首页 → 设定 → 大纲（含拖拽）→ 正文（自动保存/
任务书/审查/提交）→ 人物 → 导出 → 素材上传 → AI 讨论 → 封面工坊 → 图谱 → 节奏，
并在 `prototype/` 输出截图。

### RAG 性能验收数据

```bash
cd apps/server
.\.venv\Scripts\python scripts\seed_rag_data.py
```

生成 3 卷 30 章（每章约 1 万字）+ 设定/人物/素材，并输出索引与检索耗时。

---

## 7. 常见问题

| 问题 | 解决 |
|---|---|
| npm install 卡在 Electron | `ELECTRON_SKIP_BINARY_DOWNLOAD=1` 后补跑 `node node_modules/electron/install.js` |
| git push 连不上 GitHub | 系统代理生效但 git 未用：`git -c http.proxy=http://127.0.0.1:7897 -c https.proxy=http://127.0.0.1:7897 push`（按本机代理端口调整） |
| 首次 RAG 检索慢 | 是嵌入模型下载/加载；之后走本地缓存，无网络依赖 |
| 向量检索空结果 | 到「AI 设定讨论」点「重建知识索引」 |
| AI 讨论 503 | 未配置 `AI_NOVEL_DEEPSEEK_API_KEY` |
| 封面任务失败 | 未配置 Seedream 凭证或模型标识待确认 |
| 老作品缺新表 | 对该作品库执行 `alembic -c alembic_novel.ini upgrade head` |
| 端口 8000 被占用 | 改 `--port` 或结束占用进程 |

---

## 8. 目录速览

```text
apps/desktop        Electron + Vite + React（渲染进程、主进程、preload）
apps/server         FastAPI 后端（api/services/models/schemas/core + alembic）
packages/shared-types  前后端共享 TS 类型（与 data-model.md 一一对应）
scripts/dev.ps1     一键启动；scripts/e2e-smoke.mjs E2E
prototype/          可点击设计原型 + 真实应用截图
docs/               需求、架构、数据模型、UI、RAG、图谱、Agent 文档
```

---

> 相关文档：[README.md](../README.md) · [architecture-decisions.md](architecture-decisions.md) ·
> [data-model.md](data-model.md) · [rag-test-report.md](rag-test-report.md)
