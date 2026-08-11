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

export default function GraphPage({ projectId }: { projectId: string }) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    void (async () => {
      try {
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
        const idSet = new Set(nodes.map((n) => n.id));
        const edges: LinkDatum[] = links
          .filter((l: EntityLink) => idSet.has(`${l.sourceType}:${l.sourceId}`) && idSet.has(`${l.targetType}:${l.targetId}`))
          .map((l) => ({ source: `${l.sourceType}:${l.sourceId}`, target: `${l.targetType}:${l.targetId}` }));
        render(svgRef.current, nodes, edges);
      } catch (e) {
        setError(String(e));
      }
    })();
  }, [projectId]);

  return (
    <div className="page-fill">
      <div className="page-head">
        <h1>知识图谱</h1>
        <div className="spacer" />
        <div className="legend">
          {Object.entries(TYPE_COLOR).map(([type, color]) => (
            <span key={type}><i style={{ background: color }} />{type}</span>
          ))}
        </div>
      </div>
      {error && <div className="page-error">{error}</div>}
      <div className="graph-wrap">
        <svg ref={svgRef} width="100%" height="100%" />
      </div>
    </div>
  );
}

function render(svg: SVGSVGElement | null, nodes: NodeDatum[], edges: LinkDatum[]) {
  if (!svg) return;
  const width = svg.clientWidth || 900;
  const height = svg.clientHeight || 520;
  svg.innerHTML = '';

  const simulation = d3
    .forceSimulation(nodes as unknown as d3.SimulationNodeDatum[])
    .force('link', d3.forceLink(edges as unknown as d3.SimulationLinkDatum<d3.SimulationNodeDatum>[]).id((d: any) => d.id).distance(90))
    .force('charge', d3.forceManyBody().strength(-220))
    .force('center', d3.forceCenter(width / 2, height / 2));

  const g = d3.select(svg);
  const link = g
    .append('g')
    .selectAll('line')
    .data(edges)
    .join('line')
    .attr('stroke', '#34343d')
    .attr('stroke-width', 1);

  const node = g
    .append('g')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .call(
      d3
        .drag<SVGGElement, NodeDatum>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x; d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x; d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null; d.fy = null;
        }) as any,
    );

  node
    .append('circle')
    .attr('r', 7)
    .attr('fill', (d) => TYPE_COLOR[d.type] ?? '#6f6f7a');

  node
    .append('text')
    .text((d) => d.label)
    .attr('x', 10)
    .attr('y', 4)
    .attr('fill', '#a0a0ac')
    .attr('font-size', 12);

  node.append('title').text((d) => `${d.type} · ${d.label}`);

  simulation.on('tick', () => {
    link
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y);
    node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
  });
}
