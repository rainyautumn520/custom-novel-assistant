# 开发环境搭建指南

> AI Novel IDE — 面向网文作者的 AI 创作操作系统
>
> 版本：v0.1-draft | 日期：2025-07-13

---

## 1. 环境要求

| 工具 | 最低版本 | 用途 |
|------|----------|------|
| Node.js | >= 20 LTS | 前端构建、Electron 打包 |
| Python | >= 3.12 | 后端服务、AI 模块 |
| Git | >= 2.40 | 版本控制 |
| npm | >= 10 | 前端包管理 |
| pip | >= 24 | Python 包管理 |

### 可选工具

| 工具 | 用途 |
|------|------|
| Ollama | 本地 AI 模型运行（离线降级/开发测试） |
| VS Code / Cursor | 推荐 IDE |

---

## 2. 推荐 IDE 与插件

### VS Code / Cursor

推荐的扩展列表（放入 .vscode/extensions.json）：

- ms-python.python
- ms-python.vscode-pylance
- charliermarsh.ruff
- dbaeumer.vscode-eslint
- esbenp.prettier-vscode
- bradlc.vscode-tailwindcss
- ms-vscode.vscode-typescript-next

### 推荐设置

Python 文件使用 Ruff 格式化并开启保存时自动格式化；TypeScript/React 文件使用 Prettier 格式化并开启保存时自动格式化；.css 文件关联为 tailwindcss 语言模式。

---

## 3. 克隆与初始化

```bash
# 克隆仓库
git clone <repo-url>
cd ai-novel-ide

# 安装前端依赖
cd apps/desktop
npm install

# 安装后端依赖
cd ../server
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv/Scripts/activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

---

## 4. 环境变量配置

在项目根目录创建 .env 文件（已加入 .gitignore）：

```bash
# .env — API Keys

# DeepSeek API (后端逻辑生成、RAG、Agent)
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# OpenAI API (产品规划、代码 Review)
OPENAI_API_KEY=sk-your-key-here

# 本地 Ollama（可选，离线降级）
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:14b
```

---

## 5. 启动开发环境

### 终端 1 — 后端

```bash
cd apps/server
source .venv/bin/activate  # Windows: .venv/Scripts/activate
python -m uvicorn app.main:app --reload --port 8000
```

### 终端 2 — 前端

```bash
cd apps/desktop
npm run dev
```

启动后：

- 前端 Dev Server: http://localhost:5173
- 后端 API 文档: http://localhost:8000/docs
- 后端 OpenAPI Schema: http://localhost:8000/openapi.json

---

## 6. 数据库初始化

```bash
cd apps/server

# 初始化数据库（自动创建 SQLite 文件）
python -c 'from app.core.database import init_db; init_db()'

# 运行迁移
alembic upgrade head

# 填充测试数据（可选）
python scripts/seed_data.py
```

---

## 7. 常用命令

### 前端

```bash
npm run dev          # 启动开发服务器
npm run build        # 生产构建
npm run preview      # 预览生产构建
npm run lint         # ESLint 检查
npm run format       # Prettier 格式化
npm run test         # Vitest 单元测试
npm run test:e2e     # Playwright E2E 测试
npm run electron:dev # Electron 开发模式
npm run electron:build # Electron 打包
```

### 后端

```bash
pytest                          # 运行所有测试
pytest -v -k test_character     # 运行指定测试
ruff check .                    # 代码检查
ruff format .                   # 代码格式化
alembic revision --autogenerate # 生成迁移
alembic upgrade head            # 执行迁移
```

---

## 8. 本地 AI 模型（可选）

安装 Ollama 并拉取模型用于离线开发：

```bash
# 安装 Ollama
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.com/install.sh | sh
# Windows: 从 https://ollama.com 下载安装包

# 拉取模型
ollama pull qwen2.5:14b       # 前端代码生成替代
ollama pull deepseek-r1:8b    # 后端逻辑生成替代
ollama pull bge-m3            # 本地嵌入模型
```

---

## 9. 常见问题

| 问题 | 解决方案 |
|------|----------|
| npm install 失败 | 清除缓存: npm cache clean --force，删除 node_modules 重试 |
| Python 找不到模块 | 确认已激活虚拟环境 |
| SQLite 写入权限 | 确认数据目录存在且有写入权限 |
| Electron 启动白屏 | 检查 DevTools Console，通常为 Vite 端口冲突 |
| Ollama 连接失败 | 确认 ollama serve 在运行，检查 OLLAMA_BASE_URL |
| 端口 8000 被占用 | 使用 netstat 或 lsof 查找占用进程并结束 |

---

## 10. 项目约定

| 约定 | 说明 |
|------|------|
| 代码规范 | 前端 ESLint + Prettier，后端 Ruff |
| Commit 规范 | Conventional Commits (feat:, fix:, docs:, refactor:) |
| 分支策略 | main (稳定) -> develop (开发) -> feat/* (功能分支) |
| 代码审查 | 每个 PR 需经过 GPT Code Review |
| 测试要求 | MVP 阶段：核心业务逻辑单元测试覆盖 >= 60% |

---

> 相关文档：[README.md](../README.md) · [mvp-scope.md](mvp-scope.md) · [tech-stack.md](tech-stack.md) · [architecture.md](architecture.md) · [project-structure.md](project-structure.md)
