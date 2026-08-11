import type {
  Asset,
  AiMessage,
  AiSession,
  Chapter,
  ChapterDetail,
  Character,
  CoverTask,
  EntityLink,
  OutlineNode,
  Project,
  Setting,
  SettingCategory,
} from '@ai-novel-ide/shared-types';

export interface ExportResult {
  path: string;
  wordCount: number;
  chaptersExported: number;
  chaptersSkipped: number;
  skippedTitles: string[];
}

export interface ExportPreviewItem {
  volumeTitle: string;
  chapterTitle: string;
  chapterId: string | null;
  wordCount: number;
  status: string;
}

export interface ExportPreview {
  totalWords: number;
  exportedCount: number;
  skippedCount: number;
  items: ExportPreviewItem[];
}

export interface SearchResult {
  type: string;
  id: string;
  title: string;
  snippet: string;
}

export interface ChapterDetailWithIntegrity extends ChapterDetail {
  fileIntegrity: string;
}

export const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!resp.ok) {
    let detail = `请求失败（${resp.status}）`;
    try {
      const body = await resp.json();
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* 保留默认错误 */
    }
    throw new Error(detail);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json() as Promise<T>;
}

export const api = {
  listProjects: () => request<Project[]>('/api/projects'),
  createProject: (name: string) =>
    request<Project>('/api/projects', { method: 'POST', body: JSON.stringify({ name }) }),

  listSettings: (pid: string) => request<Setting[]>(`/api/projects/${pid}/settings`),
  createSetting: (pid: string, data: Partial<Setting>) =>
    request<Setting>(`/api/projects/${pid}/settings`, {
      method: 'POST',
      body: JSON.stringify({ title: '未命名设定', ...data }),
    }),
  updateSetting: (pid: string, id: string, data: Partial<Setting>) =>
    request<Setting>(`/api/projects/${pid}/settings/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteSetting: (pid: string, id: string) =>
    request<void>(`/api/projects/${pid}/settings/${id}`, { method: 'DELETE' }),

  listCategories: (pid: string) =>
    request<SettingCategory[]>(`/api/projects/${pid}/categories`),
  createCategory: (pid: string, name: string) =>
    request<SettingCategory>(`/api/projects/${pid}/categories`, {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),
  updateCategory: (pid: string, id: string, data: Partial<SettingCategory>) =>
    request<SettingCategory>(`/api/projects/${pid}/categories/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteCategory: (pid: string, id: string) =>
    request<void>(`/api/projects/${pid}/categories/${id}`, { method: 'DELETE' }),

  listOutline: (pid: string) => request<OutlineNode[]>(`/api/projects/${pid}/outline`),
  createOutlineNode: (pid: string, data: Partial<OutlineNode> & { level: string; title: string }) =>
    request<OutlineNode>(`/api/projects/${pid}/outline`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateOutlineNode: (pid: string, id: string, data: Partial<OutlineNode>) =>
    request<OutlineNode>(`/api/projects/${pid}/outline/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteOutlineNode: (pid: string, id: string) =>
    request<void>(`/api/projects/${pid}/outline/${id}`, { method: 'DELETE' }),
  createChapterFromNode: (pid: string, nodeId: string) =>
    request<Chapter>(`/api/projects/${pid}/outline/${nodeId}/create-chapter`, { method: 'POST' }),

  listChapters: (pid: string) => request<Chapter[]>(`/api/projects/${pid}/chapters`),
  createChapter: (pid: string, title: string) =>
    request<Chapter>(`/api/projects/${pid}/chapters`, {
      method: 'POST',
      body: JSON.stringify({ title }),
    }),
  getChapter: (pid: string, id: string) =>
    request<ChapterDetailWithIntegrity>(`/api/projects/${pid}/chapters/${id}`),
  saveChapter: (pid: string, id: string, data: { title?: string; contentMd?: string }) =>
    request<ChapterDetailWithIntegrity>(`/api/projects/${pid}/chapters/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteChapter: (pid: string, id: string) =>
    request<void>(`/api/projects/${pid}/chapters/${id}`, { method: 'DELETE' }),

  listCharacters: (pid: string) => request<Character[]>(`/api/projects/${pid}/characters`),
  createCharacter: (pid: string, name: string) =>
    request<Character>(`/api/projects/${pid}/characters`, {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),
  updateCharacter: (pid: string, id: string, data: Partial<Character>) =>
    request<Character>(`/api/projects/${pid}/characters/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteCharacter: (pid: string, id: string) =>
    request<void>(`/api/projects/${pid}/characters/${id}`, { method: 'DELETE' }),
  listCharacterLinks: (pid: string, characterId: string) =>
    request<EntityLink[]>(`/api/projects/${pid}/characters/${characterId}/links`),
  replaceCharacterLinks: (pid: string, characterId: string, settingIds: string[]) =>
    request<EntityLink[]>(`/api/projects/${pid}/characters/${characterId}/links`, {
      method: 'PUT',
      body: JSON.stringify({ settingIds }),
    }),

  exportPreview: (pid: string) =>
    request<ExportPreview>(`/api/projects/${pid}/exports/preview`),
  exportSingle: (
    pid: string,
    chapterId: string,
    includeTitle: boolean,
    outputPath?: string,
  ) =>
    request<ExportResult>(`/api/projects/${pid}/exports/single`, {
      method: 'POST',
      body: JSON.stringify({ chapterId, includeTitle, outputPath: outputPath || null }),
    }),
  exportBook: (
    pid: string,
    includeVolume: boolean,
    includeChapter: boolean,
    outputPath?: string,
  ) =>
    request<ExportResult>(`/api/projects/${pid}/exports/book`, {
      method: 'POST',
      body: JSON.stringify({ includeVolume, includeChapter, outputPath: outputPath || null }),
    }),

  listAssets: (pid: string) => request<Asset[]>(`/api/projects/${pid}/assets`),
  createAsset: (pid: string, data: Partial<Asset>) =>
    request<Asset>(`/api/projects/${pid}/assets`, {
      method: 'POST',
      body: JSON.stringify({ title: '未命名素材', ...data }),
    }),
  updateAsset: (pid: string, id: string, data: Partial<Asset>) =>
    request<Asset>(`/api/projects/${pid}/assets/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteAsset: (pid: string, id: string) =>
    request<void>(`/api/projects/${pid}/assets/${id}`, { method: 'DELETE' }),

  listAiSessions: (pid: string) => request<AiSession[]>(`/api/projects/${pid}/ai/sessions`),
  createAiSession: (pid: string, title?: string) =>
    request<AiSession>(`/api/projects/${pid}/ai/sessions`, {
      method: 'POST',
      body: JSON.stringify({ title: title || '新讨论' }),
    }),
  deleteAiSession: (pid: string, sessionId: string) =>
    request<void>(`/api/projects/${pid}/ai/sessions/${sessionId}`, { method: 'DELETE' }),
  listAiMessages: (pid: string, sessionId: string) =>
    request<AiMessage[]>(`/api/projects/${pid}/ai/sessions/${sessionId}/messages`),
  aiChat: (pid: string, sessionId: string, content: string) =>
    request<{ reply: string }>(`/api/projects/${pid}/ai/sessions/${sessionId}/chat`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),
  getAiPrompt: (pid: string) => request<{ prompt: string }>(`/api/projects/${pid}/ai/prompt`),
  setAiPrompt: (pid: string, prompt: string) =>
    request<{ prompt: string }>(`/api/projects/${pid}/ai/prompt`, {
      method: 'PUT',
      body: JSON.stringify({ prompt }),
    }),

  listCovers: (pid: string) => request<CoverTask[]>(`/api/projects/${pid}/covers`),
  createCover: (pid: string, prompt: string, params: Record<string, unknown>) =>
    request<CoverTask>(`/api/projects/${pid}/covers`, {
      method: 'POST',
      body: JSON.stringify({ prompt, params }),
    }),

  listAllLinks: (pid: string) => request<EntityLink[]>(`/api/projects/${pid}/links`),
  search: (pid: string, query: string) =>
    request<SearchResult[]>(`/api/projects/${pid}/search`, {
      method: 'POST',
      body: JSON.stringify({ query }),
    }),
};
