import { useCallback, useEffect, useMemo, useState } from 'react';

import { api, type ExportPreview, type ExportResult } from '../api';

type Mode = 'single' | 'book';

export default function ExportPage({ projectId }: { projectId: string }) {
  const [chapters, setChapters] = useState<Awaited<ReturnType<typeof api.listChapters>>>([]);
  const [preview, setPreview] = useState<ExportPreview | null>(null);
  const [mode, setMode] = useState<Mode>('book');
  const [chapterId, setChapterId] = useState('');
  const [includeVolume, setIncludeVolume] = useState(true);
  const [includeChapter, setIncludeChapter] = useState(true);
  const [includeTitle, setIncludeTitle] = useState(true);
  const [outputPath, setOutputPath] = useState('');
  const [result, setResult] = useState<ExportResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    const [chs, prev] = await Promise.all([
      api.listChapters(projectId),
      api.exportPreview(projectId),
    ]);
    setChapters(chs);
    setPreview(prev);
    setChapterId((cur) => cur || chs[0]?.id || '');
  }, [projectId]);

  useEffect(() => {
    void load().catch((e) => setError(String(e)));
  }, [load]);

  const previewWords = useMemo(
    () => preview?.items.reduce((sum, item) => sum + item.wordCount, 0) ?? 0,
    [preview],
  );

  const runExport = async () => {
    if (!outputPath.trim()) {
      const ok = window.confirm('导出到作品目录 exports/ 下，继续？');
      if (!ok) return;
    }
    setBusy(true);
    setError('');
    setResult(null);
    try {
      const r =
        mode === 'single'
          ? await api.exportSingle(projectId, chapterId, includeTitle, outputPath || undefined)
          : await api.exportBook(projectId, includeVolume, includeChapter, outputPath || undefined);
      setResult(r);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page-fill">
      <div className="page-head">
        <h1>导出中心</h1>
        <div className="spacer" />
      </div>

      {error && <div className="page-error">{error}</div>}

      <div className="export-wrap">
        <div className="radio-row">
          <button
            className={`radio-pill ${mode === 'book' ? 'active' : ''}`}
            onClick={() => setMode('book')}
          >
            全书
          </button>
          <button
            className={`radio-pill ${mode === 'single' ? 'active' : ''}`}
            onClick={() => setMode('single')}
          >
            单章
          </button>
        </div>

        {mode === 'single' ? (
          <div className="opt-row">
            <span className="lbl">选择章节</span>
            <select
              className="export-select"
              value={chapterId}
              onChange={(e) => setChapterId(e.target.value)}
            >
              {chapters.length === 0 && <option value="">（还没有章节）</option>}
              {chapters.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title}（{c.wordCount} 字）
                </option>
              ))}
            </select>
          </div>
        ) : (
          <div className="export-preview">
            <div className="opt-row">
              <span className="lbl">包含卷名</span>
              <input
                type="checkbox"
                checked={includeVolume}
                onChange={(e) => setIncludeVolume(e.target.checked)}
              />
            </div>
            <div className="opt-row">
              <span className="lbl">包含章名</span>
              <input
                type="checkbox"
                checked={includeChapter}
                onChange={(e) => setIncludeChapter(e.target.checked)}
              />
            </div>
            {preview && (
              <div className="preview-list">
                {preview.items.map((item, i) => (
                  <div key={i} className="preview-item">
                    <span className="pv-vol">{item.volumeTitle}</span>
                    <span className="pv-ch">{item.chapterTitle}</span>
                    {item.chapterId ? (
                      <span className="pv-words mono">{item.wordCount.toLocaleString()} 字</span>
                    ) : (
                      <span className="pv-skip">未写正文</span>
                    )}
                  </div>
                ))}
                <div className="preview-summary">
                  预计 <span className="num mono">{previewWords.toLocaleString()}</span> 字 ·
                  <span className="num mono">{preview.exportedCount}</span> 章已写 ·
                  <span className="num mono">{preview.skippedCount}</span> 章未写
                </div>
              </div>
            )}
          </div>
        )}

        {mode === 'single' && (
          <div className="opt-row">
            <span className="lbl">包含章节标题</span>
            <input
              type="checkbox"
              checked={includeTitle}
              onChange={(e) => setIncludeTitle(e.target.checked)}
            />
          </div>
        )}

        <div className="opt-row">
          <span className="lbl">目标路径（留空 = 作品目录 exports/）</span>
          <input
            className="export-path"
            value={outputPath}
            onChange={(e) => setOutputPath(e.target.value)}
            placeholder="例如 D:\Novels\大梦山海.txt"
          />
        </div>

        {result && (
          <div className="export-summary">
            <div>已导出：<span className="num mono">{result.path}</span></div>
            <div>
              {result.chaptersExported} 章 · {result.wordCount.toLocaleString()} 字
              {result.chaptersSkipped > 0 && ` · 跳过 ${result.chaptersSkipped} 章（未写正文）`}
            </div>
            {result.skippedTitles.length > 0 && (
              <div className="muted">跳过：{result.skippedTitles.join('、')}</div>
            )}
          </div>
        )}

        <div className="export-actions">
          <button
            className="btn primary"
            disabled={busy || (mode === 'single' && !chapterId)}
            onClick={() => void runExport()}
          >
            {busy ? '导出中…' : '开始导出'}
          </button>
        </div>
      </div>
    </div>
  );
}
