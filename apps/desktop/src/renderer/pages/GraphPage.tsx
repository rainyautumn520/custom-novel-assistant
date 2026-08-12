import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { EntityLink } from '@ai-novel-ide/shared-types';

import { api } from '../api';

interface NodeDatum {
  id: string;
  label: string;
  type: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface LinkDatum {
  id: string;
  source: string;
  target: string;
}

const TYPE_COLOR: Record<string, string> = {
  setting: '#7c6ff0',
  character: '#4aa3ff',
  chapter: '#4caf7d',
  asset: '#d9a13b',
  outline: '#e05d5d',
};

const TYPE_LABEL: Record<string, string> = {
  setting: '设定',
  character: '人物',
  chapter: '章节',
  asset: '素材',
  outline: '大纲',
};

function posKey(projectId: string, nodeId: string) {
  return `graph-pos:${projectId}:${nodeId}`;
}

export default function GraphPage({
  projectId,
  onNavigate,
}: {
  projectId: string;
  onNavigate: (type: string, id: string) => void;
}) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const selectedRef = useRef<string[]>([]);
  const [info, setInfo] = useState<NodeDatum | null>(null);
  const [busy, setBusy] = useState(false);
  const nodesRef = useRef<NodeDatum[]>([]);
  const linksRef = useRef<LinkDatum[]>([]);
  const clickTimerRef = useRef<number | null>(null);

  selectedRef.current = selected;

  const load = async () => {
    const [settings, characters, chapters, assets, links] = await Promise.all([
      api.listSettings(projectId),
      api.listCharacters(projectId),
      api.listChapters(projectId),
      api.listAssets(projectId),
      api.listAllLinks(projectId),
    ]);
    const nodes: NodeDatum[] = [
      ...settings.map((s) => ({ id: `setting:${s.id}`, label: s.title, type: 'setting' })),
      ...characters.map((c) => ({ id: `character:${c.id}`, label: c.name, type: 'character' })),
      ...chapters.map((c) => ({ id: `chapter:${c.id}`, label: c.title, type: 'chapter' })),
      ...assets.map((a) => ({ id: `asset:${a.id}`, label: a.title, type: 'asset' })),
    ];
    for (const node of nodes) {
      const raw = localStorage.getItem(posKey(projectId, node.id));
      if (raw) {
        try {
          const pos = JSON.parse(raw) as { x: number; y: number };
          node.x = pos.x;
          node.y = pos.y;
        } catch {
          /* 忽略损坏的位置数据 */
        }
      }
    }
    const idSet = new Set(nodes.map((n) => n.id));
    const edges: LinkDatum[] = links
      .filter(
        (l: EntityLink) =>
          idSet.has(`${l.sourceType}:${l.sourceId}`) &&
          idSet.has(`${l.targetType}:${l.targetId}`),
      )
      .map((l) => ({
        id: l.id,
        source: `${l.sourceType}:${l.sourceId}`,
        target: `${l.targetType}:${l.targetId}`,
      }));
    nodesRef.current = nodes;
    linksRef.current = edges;
    render(svgRef.current, nodes, edges);
  };

  useEffect(() => {
    void load().catch((e) => setError(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  useEffect(() => {
    if (svgRef.current && nodesRef.current.length > 0) {
      render(svgRef.current, nodesRef.current, linksRef.current);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected]);

  const connectSelected = async () => {
    const [aId, bId] = selectedRef.current;
    if (!aId || !bId) return;
    const [aType, aReal] = aId.split(':');
    const [bType, bReal] = bId.split(':');
    setBusy(true);
    setError('');
    try {
      await api.createLink(projectId, {
        sourceType: aType,
        sourceId: aReal,
        targetType: bType,
        targetId: bReal,
        relationType: 'refers_to',
      });
      setSelected([]);
      await load();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  const deleteLink = async (linkId: string) => {
    if (!window.confirm('删除这条关系？')) return;
    setBusy(true);
    try {
      await api.deleteLink(projectId, linkId);
      await load();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page-fill">
      <div className="page-head">
        <h1>知识图谱</h1>
        <div className="spacer" />
        <div className="legend">
          {Object.entries(TYPE_COLOR).map(([type, color]) => (
            <span key={type}><i style={{ background: color }} />{TYPE_LABEL[type] ?? type}</span>
          ))}
        </div>
      </div>

      {error && <div className="page-error">{error}</div>}

      <div className="graph-toolbar">
        {info && (
          <>
            <span className="graph-info">
              {TYPE_LABEL[info.type] ?? info.type} · {info.label}
            </span>
            <button className="btn secondary" onClick={() => onNavigate(info.type, info.id.split(':')[1])}>
              打开详情 →
            </button>
          </>
        )}
        {selected.length === 2 && (
          <>
            <span className="graph-info">已选 2 个节点</span>
            <button className="btn primary" disabled={busy} onClick={() => void connectSelected()}>
              连接这两个节点
            </button>
            <button className="btn ghost" onClick={() => setSelected([])}>
              取消
            </button>
          </>
        )}
        {selected.length === 1 && info && (
          <button className="btn ghost" onClick={() => setSelected([])}>
            取消选择
          </button>
        )}
        {selected.length === 0 && !info && (
          <span className="graph-hint">
            单击选中节点（可连两个）· 双击跳转详情 · 点击连线可删除关系 · 拖拽节点自定义位置（自动保存）
          </span>
        )}
      </div>

      <div className="graph-wrap">
        <svg ref={svgRef} width="100%" height="100%" />
      </div>
    </div>
  );

  function render(svg: SVGSVGElement | null, nodes: NodeDatum[], edges: LinkDatum[]) {
    if (!svg) return;
    const width = svg.clientWidth || 900;
    const height = svg.clientHeight || 520;
    svg.innerHTML = '';

    const simulation = d3
      .forceSimulation(nodes as unknown as d3.SimulationNodeDatum[])
      .force(
        'link',
        d3
          .forceLink(edges as unknown as d3.SimulationLinkDatum<d3.SimulationNodeDatum>[])
          .id((d: any) => d.id)
          .distance(90),
      )
      .force('charge', d3.forceManyBody().strength(-220))
      .force('center', d3.forceCenter(width / 2, height / 2));

    const g = d3.select(svg);

    const link = g
      .append('g')
      .selectAll('line')
      .data(edges)
      .join('line')
      .attr('stroke', '#34343d')
      .attr('stroke-width', 1.5)
      .style('cursor', 'pointer');

    const linkHit = g
      .append('g')
      .selectAll('line')
      .data(edges)
      .join('line')
      .attr('stroke', 'transparent')
      .attr('stroke-width', 14)
      .style('cursor', 'pointer')
      .on('click', (event, d: LinkDatum) => {
        event.stopPropagation();
        void deleteLink(d.id);
      });

    const node = g
      .append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        event.stopPropagation();
        if (clickTimerRef.current) window.clearTimeout(clickTimerRef.current);
        clickTimerRef.current = window.setTimeout(() => {
          const isSelected = selectedRef.current.includes(d.id);
          const next = isSelected
            ? selectedRef.current.filter((id) => id !== d.id)
            : [...selectedRef.current, d.id].slice(-2);
          setSelected(next);
          setInfo(
            next.length === 1
              ? nodesRef.current.find((n) => n.id === next[0]) ?? null
              : null,
          );
        }, 280);
      })
      .on('dblclick', (event, d) => {
        event.stopPropagation();
        if (clickTimerRef.current) {
          window.clearTimeout(clickTimerRef.current);
          clickTimerRef.current = null;
        }
        setSelected([]);
        onNavigate(d.type, d.id.split(':')[1]);
      })
      .call(
        d3
          .drag<SVGGElement, NodeDatum>()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
            if (d.x != null && d.y != null) {
              localStorage.setItem(
                posKey(projectId, d.id),
                JSON.stringify({ x: Math.round(d.x), y: Math.round(d.y) }),
              );
            }
          }) as any,
      );

    node.append('circle').attr('r', 16).attr('fill', 'transparent');
    node
      .append('circle')
      .attr('r', 7)
      .attr('fill', (d) => TYPE_COLOR[d.type] ?? '#6f6f7a')
      .attr('stroke', (d) => (selectedRef.current.includes(d.id) ? '#fff' : 'none'))
      .attr('stroke-width', 2);

    node
      .append('text')
      .text((d) => d.label)
      .attr('x', 10)
      .attr('y', 4)
      .attr('fill', '#a0a0ac')
      .attr('font-size', 12);

    node.append('title').text((d) => `${TYPE_LABEL[d.type] ?? d.type} · ${d.label}`);

    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);
      linkHit
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);
      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });
  }
}
