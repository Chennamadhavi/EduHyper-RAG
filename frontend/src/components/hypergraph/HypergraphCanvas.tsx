import React, { useEffect, useRef, useState, useMemo } from 'react';
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  Filter,
  Layers,
  Sparkles,
} from 'lucide-react';
import { HypergraphEdge, HypergraphNode } from '../../types/hypergraph';
import Badge from '../common/Badge';

interface HypergraphCanvasProps {
  nodes: HypergraphNode[];
  hyperedges: HypergraphEdge[];
  selectedConcept: string | null;
  onSelectConcept: (conceptName: string) => void;
  searchFilter?: string;
  cardinalityFilter?: 'all' | 'high_order' | 'pairwise';
}

interface CanvasNode {
  id: string;
  name: string;
  entityType: string;
  degree: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  color: string;
}

export const HypergraphCanvas: React.FC<HypergraphCanvasProps> = ({
  nodes,
  hyperedges,
  selectedConcept,
  onSelectConcept,
  searchFilter = '',
  cardinalityFilter = 'all',
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Pan and Zoom transform
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDraggingCanvas, setIsDraggingCanvas] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [draggedNode, setDraggedNode] = useState<CanvasNode | null>(null);

  // Simulation nodes state
  const canvasNodesRef = useRef<Map<string, CanvasNode>>(new Map());

  // Palette generator based on entity type
  const getTypeColor = (type: string): string => {
    switch (type.toLowerCase()) {
      case 'concept':
        return '#3b82f6'; // blue
      case 'algorithm':
      case 'process':
        return '#8b5cf6'; // purple
      case 'architecture':
      case 'model':
        return '#10b981'; // emerald
      case 'metric':
      case 'evaluation':
        return '#f59e0b'; // amber
      default:
        return '#6366f1'; // indigo
    }
  };

  // Filter hyperedges based on cardinalityFilter
  const visibleEdges = useMemo(() => {
    return hyperedges.filter((edge) => {
      if (cardinalityFilter === 'high_order') return edge.is_high_order;
      if (cardinalityFilter === 'pairwise') return !edge.is_high_order;
      return true;
    });
  }, [hyperedges, cardinalityFilter]);

  // Initialize or update node positions in circle / force layout
  useEffect(() => {
    const canvas = canvasRef.current;
    const width = canvas ? canvas.width : 800;
    const height = canvas ? canvas.height : 500;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.38;

    const map = new Map<string, CanvasNode>();
    nodes.forEach((n, idx) => {
      const existing = canvasNodesRef.current.get(n.id);
      if (existing) {
        existing.degree = n.degree;
        map.set(n.id, existing);
      } else {
        const angle = (idx / Math.max(1, nodes.length)) * 2 * Math.PI;
        const jitter = (Math.random() - 0.5) * 50;
        const r = radius * (0.4 + 0.6 * Math.random());
        map.set(n.id, {
          id: n.id,
          name: n.name,
          entityType: n.entity_type,
          degree: n.degree,
          x: centerX + Math.cos(angle) * r + jitter,
          y: centerY + Math.sin(angle) * r + jitter,
          vx: 0,
          vy: 0,
          radius: Math.max(7, Math.min(18, 6 + n.degree * 1.5)),
          color: getTypeColor(n.entity_type),
        });
      }
    });

    canvasNodesRef.current = map;
  }, [nodes]);

  // Center view on selection
  useEffect(() => {
    if (selectedConcept && canvasRef.current) {
      const node = canvasNodesRef.current.get(selectedConcept);
      if (node) {
        const width = canvasRef.current.width;
        const height = canvasRef.current.height;
        setOffset({
          x: width / 2 - node.x * zoom,
          y: height / 2 - node.y * zoom,
        });
      }
    }
  }, [selectedConcept]);

  // Render loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      ctx.save();
      ctx.translate(offset.x, offset.y);
      ctx.scale(zoom, zoom);

      const nodesMap = canvasNodesRef.current;

      // 1. Draw Hyperedges
      visibleEdges.forEach((edge, edgeIdx) => {
        const edgeNodes = edge.concepts
          .map((c) => nodesMap.get(c))
          .filter((n): n is CanvasNode => !!n);

        if (edgeNodes.length < 2) return;

        const isHighOrder = edge.is_high_order;
        const isConnectedToSelected =
          selectedConcept && edge.concepts.some((c) => c === selectedConcept);

        // High-order hyperedges: Draw translucent polygon connecting all concepts
        if (isHighOrder && edgeNodes.length >= 3) {
          ctx.beginPath();
          ctx.moveTo(edgeNodes[0].x, edgeNodes[0].y);
          for (let i = 1; i < edgeNodes.length; i++) {
            ctx.lineTo(edgeNodes[i].x, edgeNodes[i].y);
          }
          ctx.closePath();

          ctx.fillStyle = isConnectedToSelected
            ? 'rgba(168, 85, 247, 0.22)' // purple highlight
            : 'rgba(99, 102, 241, 0.08)'; // soft indigo
          ctx.fill();

          ctx.strokeStyle = isConnectedToSelected
            ? 'rgba(168, 85, 247, 0.7)'
            : 'rgba(99, 102, 241, 0.3)';
          ctx.lineWidth = isConnectedToSelected ? 2 : 1;
          ctx.setLineDash([4, 4]);
          ctx.stroke();
          ctx.setLineDash([]);
        } else {
          // Pairwise connections: Draw smooth lines
          for (let i = 0; i < edgeNodes.length; i++) {
            for (let j = i + 1; j < edgeNodes.length; j++) {
              ctx.beginPath();
              ctx.moveTo(edgeNodes[i].x, edgeNodes[i].y);
              ctx.lineTo(edgeNodes[j].x, edgeNodes[j].y);
              ctx.strokeStyle = isConnectedToSelected
                ? 'rgba(59, 130, 246, 0.8)'
                : 'rgba(148, 163, 184, 0.25)';
              ctx.lineWidth = isConnectedToSelected ? 2 : 1;
              ctx.stroke();
            }
          }
        }
      });

      // 2. Draw Concept Nodes
      nodesMap.forEach((node) => {
        const isSelected = selectedConcept === node.id;
        const isMatch =
          searchFilter.trim() !== '' &&
          node.name.toLowerCase().includes(searchFilter.toLowerCase());

        // Outer glow for selected or search match
        if (isSelected || isMatch) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius + 6, 0, 2 * Math.PI);
          ctx.fillStyle = isSelected
            ? 'rgba(59, 130, 246, 0.35)'
            : 'rgba(245, 158, 11, 0.35)';
          ctx.fill();
        }

        // Main node circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);
        ctx.fillStyle = node.color;
        ctx.fill();

        ctx.strokeStyle = isSelected ? '#1d4ed8' : '#ffffff';
        ctx.lineWidth = isSelected ? 2.5 : 1.5;
        ctx.stroke();

        // Node Label
        ctx.font = isSelected
          ? 'bold 11px Inter, system-ui, sans-serif'
          : '9px Inter, system-ui, sans-serif';
        ctx.fillStyle = isSelected ? '#0f172a' : '#475569';
        ctx.textAlign = 'center';
        ctx.fillText(node.name, node.x, node.y + node.radius + 12);
      });

      ctx.restore();
      animationId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animationId);
  }, [visibleEdges, selectedConcept, searchFilter, offset, zoom]);

  // Mouse interaction handlers
  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;
    return {
      x: (clientX - offset.x) / zoom,
      y: (clientY - offset.y) / zoom,
    };
  };

  const findNodeAtCoords = (x: number, y: number): CanvasNode | null => {
    for (const node of canvasNodesRef.current.values()) {
      const dist = Math.hypot(node.x - x, node.y - y);
      if (dist <= node.radius + 5) return node;
    }
    return null;
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const { x, y } = getCanvasCoords(e);
    const clicked = findNodeAtCoords(x, y);

    if (clicked) {
      setDraggedNode(clicked);
      onSelectConcept(clicked.id);
    } else {
      setIsDraggingCanvas(true);
      setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (draggedNode) {
      const { x, y } = getCanvasCoords(e);
      draggedNode.x = x;
      draggedNode.y = y;
    } else if (isDraggingCanvas) {
      setOffset({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDraggingCanvas(false);
    setDraggedNode(null);
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.1 : 0.9;
    const newZoom = Math.max(0.3, Math.min(3.5, zoom * factor));
    setZoom(newZoom);
  };

  const resetView = () => {
    setZoom(1);
    setOffset({ x: 0, y: 0 });
  };

  return (
    <div className="relative border border-slate-200 rounded-xl overflow-hidden bg-slate-50 shadow-inner">
      {/* Top Overlay Controls */}
      <div className="absolute top-3 right-3 flex items-center gap-1.5 bg-white/90 backdrop-blur-xs p-1 rounded-lg border border-slate-200 shadow-xs z-10">
        <button
          type="button"
          onClick={() => setZoom((z) => Math.min(3.5, z * 1.2))}
          className="p-1.5 text-slate-600 hover:text-blue-600 hover:bg-slate-100 rounded transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => setZoom((z) => Math.max(0.3, z * 0.8))}
          className="p-1.5 text-slate-600 hover:text-blue-600 hover:bg-slate-100 rounded transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={resetView}
          className="p-1.5 text-slate-600 hover:text-blue-600 hover:bg-slate-100 rounded transition-colors"
          title="Center Graph"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
      </div>

      {/* Legend Badge Overlay */}
      <div className="absolute bottom-3 left-3 flex flex-wrap items-center gap-2 bg-white/95 backdrop-blur-xs px-3 py-1.5 rounded-lg border border-slate-200 text-xs shadow-xs z-10">
        <div className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block" />
          <span className="text-slate-600">Concepts</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-purple-500 inline-block" />
          <span className="text-slate-600">High-Order Hyperedge (&ge;3)</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-slate-400 inline-block" />
          <span className="text-slate-600">Pairwise Edge (=2)</span>
        </div>
      </div>

      {/* Canvas */}
      <canvas
        ref={canvasRef}
        width={850}
        height={500}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
        className="w-full h-[500px] cursor-grab active:cursor-grabbing block"
      />
    </div>
  );
};

export default HypergraphCanvas;
