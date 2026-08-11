import type {
  Chapter,
  ChapterDetail,
  OutlineNode,
  Project,
  Setting,
  SettingCategory,
} from '@ai-novel-ide/shared-types';

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
    request<ChapterDetail>(`/api/projects/${pid}/chapters/${id}`),
  saveChapter: (pid: string, id: string, data: { title?: string; contentMd?: string }) =>
    request<ChapterDetail>(`/api/projects/${pid}/chapters/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteChapter: (pid: string, id: string) =>
    request<void>(`/api/projects/${pid}/chapters/${id}`, { method: 'DELETE' }),
};
