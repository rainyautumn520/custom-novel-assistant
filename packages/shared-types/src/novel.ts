/**
 * 与 docs/data-model.md 一一对应的共享类型（camelCase）。
 * 新增字段必须同步：本文档 → SQLAlchemy 模型 → Alembic 迁移 → shared-types → API Schema。
 */

export type ProjectStatus = 'active' | 'archived';
export type SettingStatus = 'draft' | 'confirmed';
export type OutlineLevel = 'volume' | 'chapter' | 'beat';
export type OutlineStatus = 'draft' | 'active' | 'done';
export type ChapterStatus = 'draft' | 'committed' | 'archived';
export type AssetKind = 'text' | 'file';
export type EntityType = 'setting' | 'character' | 'outline' | 'chapter' | 'asset';
export type CoverTaskStatus = 'queued' | 'running' | 'success' | 'failed' | 'cancelled';

export interface Project {
  id: string;
  name: string;
  genre: string;
  synopsis: string;
  targetWords: number;
  status: ProjectStatus;
  dataDir: string;
  createdAt: string;
  updatedAt: string;
}

export interface SettingCategory {
  id: string;
  parentId: string | null;
  name: string;
  sortOrder: number;
  createdAt: string;
  updatedAt: string;
}

export interface Setting {
  id: string;
  categoryId: string | null;
  title: string;
  contentMd: string;
  tags: string[];
  status: SettingStatus;
  createdAt: string;
  updatedAt: string;
}

export interface Character {
  id: string;
  name: string;
  aliases: string[];
  identity: string;
  personality: string;
  appearance: string;
  background: string;
  goals: string;
  tags: string[];
  notes: string;
  status: SettingStatus;
  createdAt: string;
  updatedAt: string;
}

export interface OutlineNode {
  id: string;
  parentId: string | null;
  level: OutlineLevel;
  sortOrder: number;
  title: string;
  goal: string;
  mustCover: string[];
  forbidden: string[];
  status: OutlineStatus;
  targetWords: number;
  chapterId: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface Chapter {
  id: string;
  title: string;
  outlineNodeId: string | null;
  wordCount: number;
  filePath: string;
  fileHash: string;
  status: ChapterStatus;
  createdAt: string;
  updatedAt: string;
}

export interface ChapterSnapshot {
  id: string;
  chapterId: string;
  snapshotPath: string;
  fileHash: string;
  wordCount: number;
  note: string;
  createdAt: string;
}

export interface Asset {
  id: string;
  title: string;
  kind: AssetKind;
  contentMd: string;
  filePath: string | null;
  source: string;
  tags: string[];
  notes: string;
  createdAt: string;
  updatedAt: string;
}

export interface EntityLink {
  id: string;
  sourceType: EntityType;
  sourceId: string;
  targetType: EntityType;
  targetId: string;
  relationType: string;
  createdAt: string;
}

export interface AiSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

export interface AiMessage {
  id: string;
  sessionId: string;
  role: 'user' | 'assistant';
  content: string;
  sources: string[];
  createdAt: string;
}

export interface CoverTask {
  id: string;
  prompt: string;
  optimizedPrompt: string;
  params: Record<string, unknown>;
  status: CoverTaskStatus;
  idempotencyKey: string;
  resultPath: string | null;
  error: string;
  createdAt: string;
  updatedAt: string;
}

export interface HealthStatus {
  status: 'ok';
  version: string;
  dataDir: string;
}
