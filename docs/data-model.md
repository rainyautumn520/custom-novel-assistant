# 数据模型设计

> AI Novel IDE — 面向网文作者的 AI 创作操作系统
>
> 阶段：3 | 状态：已裁决 | 日期：2026-08-11

本文定义 MVP（v0.1）与 v0.2 的数据结构，是 SQLAlchemy 模型、Alembic 迁移和
前端 TypeScript 类型（`packages/shared-types`）的唯一依据。

---

## 1. 存储拓扑

依据 ADR-02/03，数据分两层：

```text
~/ai-novel-ide-data/
├── app.db                  # 应用级元数据库
└── workspaces/<project_id>/
    ├── novel.db            # 作品结构化数据
    ├── chapters/<chapter_id>.md
    ├── snapshots/<chapter_id>/<ts>_<hash>.md
    └── assets/
```

- `app.db` 只存跨作品数据；作品内部数据一律进 `novel.db`。
- 所有正文、素材文件的**内容**不进数据库；数据库只存路径、哈希与元数据。
- JSON 数组/对象字段统一用 TEXT 存 JSON 字符串，读取时解析（SQLite JSON1 可用，但 Python 侧以 Pydantic 解析为准）。

---

## 2. app.db（应用级元库）

### 2.1 projects

作品登记表（不存创作内容）。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT (PK) | UUID，同时也是 workspaces 目录名 |
| name | TEXT NOT NULL | 书名，去除首尾空格后不得为空 |
| genre | TEXT | 题材 |
| synopsis | TEXT | 简介 |
| target_words | INTEGER DEFAULT 0 | 预计字数 |
| status | TEXT DEFAULT 'active' | active / archived |
| data_dir | TEXT NOT NULL | 作品数据目录绝对路径 |
| created_at / updated_at | TEXT (ISO8601) | 时间戳 |

约束：`name` 唯一；删除走回收站（status='archived'），不物理删除。

### 2.2 app_settings

| 字段 | 类型 | 说明 |
|---|---|---|
| key | TEXT (PK) | 设置键 |
| value | TEXT | JSON 值 |
| updated_at | TEXT | 时间戳 |

存放全局设置：外观、编辑器、数据目录、导出默认路径、AI 服务配置引用。

### 2.3 secrets

凭证密文表（ADR-04）。

| 字段 | 类型 | 说明 |
|---|---|---|
| key | TEXT (PK) | 如 `deepseek.api_key`、`seedream.api_key` |
| ciphertext | TEXT NOT NULL | safeStorage 加密后的密文 |
| created_at / updated_at | TEXT | 时间戳 |

渲染进程不读取明文；后端经主进程 IPC 临时注入。

---

## 3. novel.db（作品库）

### 3.1 setting_categories（设定分类）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT (PK) | UUID |
| parent_id | TEXT NULL | 父分类，支持树形（MVP 最多两层） |
| name | TEXT NOT NULL | 分类名 |
| sort_order | INTEGER DEFAULT 0 | 同级排序 |
| created_at / updated_at | TEXT | 时间戳 |

### 3.2 settings（设定条目）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT (PK) | UUID |
| category_id | TEXT NULL | 所属分类（FK → setting_categories.id, ON DELETE SET NULL） |
| title | TEXT NOT NULL | 标题 |
| content_md | TEXT DEFAULT '' | Markdown 正文 |
| tags | TEXT DEFAULT '[]' | JSON 字符串数组 |
| status | TEXT DEFAULT 'draft' | draft / confirmed（confirmed 为"已确认设定"，AI 硬约束） |
| created_at / updated_at | TEXT | 时间戳 |

索引：`(category_id)`、`(status)`；标题/正文/标签搜索用 LIKE（MVP 规模），v0.2 换 FTS5 或向量检索。

### 3.3 characters（人物）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT (PK) | UUID |
| name | TEXT NOT NULL | 姓名 |
| aliases | TEXT DEFAULT '[]' | JSON 别名数组 |
| identity | TEXT DEFAULT '' | 身份 |
| personality | TEXT DEFAULT '' | 性格 |
| appearance | TEXT DEFAULT '' | 外貌 |
| background | TEXT DEFAULT '' | 背景故事 |
| goals | TEXT DEFAULT '' | 目标 |
| tags | TEXT DEFAULT '[]' | JSON 标签数组 |
| notes | TEXT DEFAULT '' | 备注 |
| status | TEXT DEFAULT 'draft' | draft / confirmed |
| created_at / updated_at | TEXT | 时间戳 |

索引：`(name)`。长文本字段以 Markdown 格式存储，编辑器内支持简单格式。

### 3.4 outline_nodes（大纲节点）

固定三级：`volume`（卷纲）→ `chapter`（章纲）→ `beat`（细纲）。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT (PK) | UUID |
| parent_id | TEXT NULL | 父节点（FK → outline_nodes.id, ON DELETE RESTRICT） |
| level | TEXT NOT NULL | volume / chapter / beat |
| sort_order | INTEGER DEFAULT 0 | 同级顺序 |
| title | TEXT NOT NULL | 标题 |
| goal | TEXT DEFAULT '' | 本章/节点目标 |
| must_cover | TEXT DEFAULT '[]' | JSON 必须覆盖节点数组 |
| forbidden | TEXT DEFAULT '[]' | JSON 禁区数组 |
| status | TEXT DEFAULT 'draft' | draft / active / done |
| target_words | INTEGER DEFAULT 0 | 章纲目标字数 |
| chapter_id | TEXT NULL | 章纲关联正文（FK → chapters.id, ON DELETE SET NULL） |
| created_at / updated_at | TEXT | 时间戳 |

约束（应用层强制，数据库层用触发器兜底）：

- `volume` 的 parent_id 必须为 NULL。
- `chapter` 的 parent_id 必须指向 `volume`。
- `beat` 的 parent_id 必须指向 `chapter`，且不允许再有子节点。
- 删除父节点前必须提示子节点数量；有子节点时禁止删除。

索引：`(parent_id, sort_order)`、`(level)`、`(chapter_id)`。

### 3.5 chapters（章节）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT (PK) | UUID |
| title | TEXT NOT NULL | 章节名 |
| outline_node_id | TEXT NULL | 关联章纲（FK → outline_nodes.id, ON DELETE SET NULL） |
| word_count | INTEGER DEFAULT 0 | 中文字符数 |
| file_path | TEXT NOT NULL | 正文文件相对路径（如 `chapters/xxx.md`） |
| file_hash | TEXT DEFAULT '' | 正文 SHA-256，用于外部修改检测 |
| status | TEXT DEFAULT 'draft' | draft / committed / archived |
| created_at / updated_at | TEXT | 时间戳 |

索引：`(outline_node_id)`、`(status)`。

正文内容一律在 `file_path` 对应文件内，数据库不存正文文本。

### 3.6 chapter_snapshots（章节快照）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT (PK) | UUID |
| chapter_id | TEXT NOT NULL | FK → chapters.id, ON DELETE CASCADE |
| snapshot_path | TEXT NOT NULL | 快照文件相对路径 |
| file_hash | TEXT NOT NULL | 快照 SHA-256 |
| word_count | INTEGER | 快照字数 |
| note | TEXT DEFAULT '' | 备注（auto/manual） |
| created_at | TEXT | 快照时间 |

策略：覆盖保存前自动保留上一版本；每章默认保留最近 20 份，可配置；手动快照不参与自动清理。

### 3.7 assets（素材）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT (PK) | UUID |
| title | TEXT NOT NULL | 素材标题 |
| kind | TEXT NOT NULL | text / file |
| content_md | TEXT DEFAULT '' | 文本素材内容（kind=text） |
| file_path | TEXT NULL | 文件相对路径（kind=file） |
| source | TEXT DEFAULT '' | 来源 |
| tags | TEXT DEFAULT '[]' | JSON 标签数组 |
| notes | TEXT DEFAULT '' | 备注 |
| created_at / updated_at | TEXT | 时间戳 |

### 3.8 entity_links（通用实体关系）

支撑引用关系、删除影响提示与 v0.2 知识图谱。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT (PK) | UUID |
| source_type | TEXT NOT NULL | setting / character / outline / chapter / asset |
| source_id | TEXT NOT NULL | 源实体 ID |
| target_type | TEXT NOT NULL | 同上 |
| target_id | TEXT NOT NULL | 目标实体 ID |
| relation_type | TEXT DEFAULT 'refers_to' | 关系类型（refers_to / appears_in / belongs_to ...） |
| created_at | TEXT | 时间戳 |

索引：`(source_type, source_id)`、`(target_type, target_id)`。

MVP 用法：正文/大纲引用设定时写入关系；删除设定前查询所有指向它的关系并展示影响范围。

### 3.9 project_settings（作品级配置）

| 字段 | 类型 | 说明 |
|---|---|---|
| key | TEXT (PK) | 设置键 |
| value | TEXT | JSON 值 |
| updated_at | TEXT | 时间戳 |

存放作品级 AI skill/提示词（v0.2）、导出选项、封面配置等。

---

## 4. v0.2 扩展表

### 4.1 ai_sessions / ai_messages（设定讨论）

```text
ai_sessions(id, project_id 隐含于库内, title, created_at, updated_at)
ai_messages(id, session_id FK CASCADE, role, content, sources JSON, created_at)
```

`sources` 记录回答引用的设定/章节 ID 列表，用于"来源可见"与"纳入设定"溯源。

### 4.2 cover_tasks（封面任务）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT (PK) | UUID |
| prompt | TEXT NOT NULL | 用户需求 |
| optimized_prompt | TEXT DEFAULT '' | 优化后的提示词 |
| params | TEXT DEFAULT '{}' | JSON：模型标识、尺寸、风格等 |
| status | TEXT NOT NULL | queued / running / success / failed / cancelled |
| idempotency_key | TEXT NOT NULL | 幂等键，失败重试复用 |
| result_path | TEXT NULL | 生成图相对路径 |
| error | TEXT DEFAULT '' | 失败原因（脱敏） |
| created_at / updated_at | TEXT | 时间戳 |

封面排版产物不覆盖原图，另存为排版图文件；封面图片可复制为素材。

---

## 5. 关系总览（ER）

```text
projects 1 ─── * (作品库隔离，app.db 不存业务关系)

setting_categories 1 ─── * settings
outline_nodes * ─── 1 outline_nodes        (parent_id，三级树)
outline_nodes 1 ─── 0..1 chapters          (章纲 ↔ 正文)
chapters 1 ─── * chapter_snapshots

entity_links 是任意实体之间的多对多关系：
  setting/character/outline/chapter/asset  ── * entity_links * ──  同集合
```

---

## 6. 状态机

### 6.1 章节

```text
draft ──提交──> committed ──归档──> archived
  │                                  │
  └────── 继续编辑（仍为 draft/committed 均可改）──────┘
```

`committed` 表示"作者确认完成"，供导出、统计与 v0.4 提交链使用；不冻结编辑。

### 6.2 设定 / 人物

```text
draft ──作者确认──> confirmed
confirmed ──编辑──> confirmed（修改后仍为 confirmed，但记录 updated_at 与来源）
```

`confirmed` 是 AI 的硬约束来源；AI 建议的候选事实在确认前只能是 draft。

### 6.3 大纲节点

```text
draft ──写作中──> active ──完成──> done
```

---

## 7. 删除与引用规则

| 操作 | 规则 |
|---|---|
| 删除设定/人物 | 查询 entity_links，展示影响范围；确认后删除节点并保留关系日志（软删字段 `deleted_at`，v0.4 前可硬删） |
| 删除大纲父节点 | 有子节点时禁止删除，必须逐级处理 |
| 删除章纲 | 只解除 `chapters.outline_node_id`（SET NULL），不删正文 |
| 删除章节 | 关联快照级联删除；正文文件移入回收站 |
| 删除作品 | 仅标记 archived；数据目录移入回收站，不物理清空 |

---

## 8. 迁移与版本

- `novel.db` 与 `app.db` 各维护 `schema_version`（整数，记录在 `alembic_version` 表）。
- Alembic 双链：`alembic/app`、`alembic/novel`；新建作品时对空库执行 `upgrade head`。
- 打开作品时校验版本；版本落后于当前代码时提示迁移或恢复，禁止静默写入。
- 字段类型约束：所有时间戳统一 ISO8601 字符串（UTC），展示层转本地时区。

---

## 9. 与前端共享类型的映射

`packages/shared-types/novel.ts` 中的类型与本文表一一对应（camelCase），由 Codex 生成后保持同步：

```text
Project / SettingCategory / Setting / Character / OutlineNode
/ Chapter / ChapterSnapshot / Asset / EntityLink / AiSession / CoverTask
```

新增字段必须同步：本文档 → SQLAlchemy 模型 → Alembic 迁移 → shared-types → API Schema → 页面。

---

> 相关文档：[README.md](../README.md) · [prd.md](prd.md) · [architecture.md](architecture.md) · [architecture-decisions.md](architecture-decisions.md)
