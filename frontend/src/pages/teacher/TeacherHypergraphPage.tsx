import React, { useEffect, useState } from 'react';
import {
  Network,
  RefreshCw,
  Search,
  Layers,
  FileText,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Filter,
  Image as ImageIcon,
  Table as TableIcon,
  Info,
  Maximize2,
  Tag,
  ArrowRight,
} from 'lucide-react';
import PageHeader from '../../components/common/PageHeader';
import Card, { CardContent } from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import LoadingState from '../../components/common/LoadingState';
import EmptyState from '../../components/common/EmptyState';
import HypergraphCanvas from '../../components/hypergraph/HypergraphCanvas';
import documentService from '../../services/documentService';
import hypergraphService from '../../services/hypergraphService';
import { DocumentItem } from '../../types/document';
import {
  ConceptDetailResponse,
  HypergraphGraphResponse,
} from '../../types/hypergraph';

export const TeacherHypergraphPage: React.FC = () => {
  // Document selection
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('');

  // Hypergraph data & inspection
  const [graphData, setGraphData] = useState<HypergraphGraphResponse | null>(null);
  const [selectedConcept, setSelectedConcept] = useState<string | null>(null);
  const [conceptDetail, setConceptDetail] = useState<ConceptDetailResponse | null>(null);

  // UI state
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);
  const [isLoadingGraph, setIsLoadingGraph] = useState(false);
  const [isLoadingConcept, setIsLoadingConcept] = useState(false);
  const [activeTab, setActiveTab] = useState<'canvas' | 'image' | 'table'>('canvas');
  const [searchQuery, setSearchQuery] = useState('');
  const [cardinalityFilter, setCardinalityFilter] = useState<'all' | 'high_order' | 'pairwise'>('all');
  const [error, setError] = useState<string | null>(null);

  // Load initial document list
  useEffect(() => {
    loadDocuments();
  }, []);

  // Load hypergraph whenever selectedDocId changes
  useEffect(() => {
    if (selectedDocId) {
      loadGraph(selectedDocId);
    }
  }, [selectedDocId]);

  // Load concept details whenever selectedConcept changes
  useEffect(() => {
    if (selectedDocId && selectedConcept) {
      loadConceptDetail(selectedDocId, selectedConcept);
    } else {
      setConceptDetail(null);
    }
  }, [selectedConcept, selectedDocId]);

  const loadDocuments = async () => {
    setIsLoadingDocs(true);
    setError(null);
    try {
      const docs = await documentService.listDocuments();
      const readyDocs = docs.filter((d) => d.status === 'READY');
      setDocuments(readyDocs);
      if (readyDocs.length > 0) {
        // Prefer document with hyperedges if available
        const withEdges = readyDocs.find((d) => d.num_hyperedges > 0);
        setSelectedDocId(withEdges ? withEdges.doc_id : readyDocs[0].doc_id);
      }
    } catch {
      setError('Failed to load documents. Please check backend connection.');
    } finally {
      setIsLoadingDocs(false);
    }
  };

  const loadGraph = async (docId: string) => {
    setIsLoadingGraph(true);
    setError(null);
    try {
      const data = await hypergraphService.getDocumentHypergraph(docId);
      setGraphData(data);
      if (data.nodes.length > 0) {
        setSelectedConcept(data.nodes[0].id);
      } else {
        setSelectedConcept(null);
        setConceptDetail(null);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load hypergraph for this document.');
      setGraphData(null);
    } finally {
      setIsLoadingGraph(false);
    }
  };

  const loadConceptDetail = async (docId: string, conceptName: string) => {
    setIsLoadingConcept(true);
    try {
      const detail = await hypergraphService.getConceptDetails(docId, conceptName);
      setConceptDetail(detail);
    } catch {
      setConceptDetail(null);
    } finally {
      setIsLoadingConcept(false);
    }
  };

  // Filtered hyperedges for table view
  const filteredHyperedges = React.useMemo(() => {
    if (!graphData) return [];
    return graphData.hyperedges.filter((edge) => {
      // Cardinality filter
      if (cardinalityFilter === 'high_order' && !edge.is_high_order) return false;
      if (cardinalityFilter === 'pairwise' && edge.is_high_order) return false;

      // Search filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesLabel = edge.label.toLowerCase().includes(q);
        const matchesConcepts = edge.concepts.some((c) => c.toLowerCase().includes(q));
        const matchesDesc = edge.description?.toLowerCase().includes(q);
        return matchesLabel || matchesConcepts || matchesDesc;
      }
      return true;
    });
  }, [graphData, cardinalityFilter, searchQuery]);

  if (isLoadingDocs) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Hypergraph Knowledge Explorer"
          description="Inspect multi-concept hyperedges, concept centrality, and high-order incidence graphs."
          breadcrumbs={[{ label: 'Teacher', path: '/teacher/dashboard' }, { label: 'Hypergraph' }]}
        />
        <LoadingState message="Loading educational document repository..." />
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Hypergraph Knowledge Explorer"
          description="Inspect multi-concept hyperedges, concept centrality, and high-order incidence graphs."
          breadcrumbs={[{ label: 'Teacher', path: '/teacher/dashboard' }, { label: 'Hypergraph' }]}
        />
        <EmptyState
          icon={<Network className="w-8 h-8 text-blue-600" />}
          title="No Processed Documents Found"
          description="Upload a course textbook or lecture PDF in the Documents manager to automatically construct and index high-order hypergraphs."
          action={
            <Button
              variant="primary"
              size="sm"
              onClick={() => (window.location.href = '/teacher/documents')}
              rightIcon={<ExternalLink className="w-4 h-4" />}
            >
              Go to Document Upload
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl">
      <PageHeader
        title="Hypergraph Knowledge Explorer"
        description="Inspect multi-concept hyperedges (>= 3 entities), concept centrality, and high-order incidence structures."
        breadcrumbs={[{ label: 'Teacher', path: '/teacher/dashboard' }, { label: 'Hypergraph' }]}
        badge={<Badge variant="purple">HyperNetX Visualizer</Badge>}
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => selectedDocId && loadGraph(selectedDocId)}
            leftIcon={<RefreshCw className="w-4 h-4" />}
          >
            Refresh Graph
          </Button>
        }
      />

      {/* Document Selector Ribbon */}
      <Card className="border border-slate-200 bg-white">
        <div className="p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex-1 w-full sm:max-w-md">
            <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-blue-600" />
              Inspected Document
            </label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
            >
              {documents.map((doc) => (
                <option key={doc.doc_id} value={doc.doc_id}>
                  {doc.filename} ({doc.num_concepts} concepts, {doc.num_hyperedges} hyperedges)
                </option>
              ))}
            </select>
          </div>

          {/* Quick Stats Pill */}
          {graphData && (
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="font-semibold text-slate-700">{graphData.filename}</span>
              <span>•</span>
              <span>ID: <code className="text-slate-600">{graphData.doc_id}</code></span>
            </div>
          )}
        </div>
      </Card>

      {/* Structural Metrics Ribbon */}
      {graphData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="border border-slate-200">
            <CardContent className="p-4">
              <div className="text-xs font-medium text-slate-500 flex items-center gap-1">
                <Network className="w-3.5 h-3.5 text-blue-600" />
                Concept Nodes (|V|)
              </div>
              <div className="text-2xl font-bold text-slate-900 mt-1">
                {graphData.metadata.num_nodes}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">Entity vertices in graph</div>
            </CardContent>
          </Card>

          <Card className="border border-slate-200">
            <CardContent className="p-4">
              <div className="text-xs font-medium text-slate-500 flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-purple-600" />
                Total Hyperedges (|E|)
              </div>
              <div className="text-2xl font-bold text-purple-700 mt-1">
                {graphData.metadata.num_hyperedges}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">Multi-concept relationships</div>
            </CardContent>
          </Card>

          <Card className="border border-slate-200">
            <CardContent className="p-4">
              <div className="text-xs font-medium text-slate-500 flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                High-Order (&ge; 3 Concepts)
              </div>
              <div className="text-2xl font-bold text-emerald-700 mt-1">
                {graphData.metadata.num_high_order}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                {graphData.metadata.num_hyperedges > 0
                  ? `${Math.round((graphData.metadata.num_high_order / graphData.metadata.num_hyperedges) * 100)}% of all relationships`
                  : '0%'}
              </div>
            </CardContent>
          </Card>

          <Card className="border border-slate-200">
            <CardContent className="p-4">
              <div className="text-xs font-medium text-slate-500 flex items-center gap-1">
                <Tag className="w-3.5 h-3.5 text-amber-600" />
                Max Cardinality
              </div>
              <div className="text-2xl font-bold text-amber-700 mt-1">
                {graphData.metadata.largest_hyperedge_size}
              </div>
              <div className="text-[11px] text-slate-500 mt-0.5">Concepts in largest hyperedge</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Toolbar: Search, Filters, and View Tabs */}
      <Card className="border border-slate-200 bg-white">
        <div className="p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          {/* Search Input */}
          <div className="relative w-full md:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search concepts or hyperedge labels..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Cardinality Filters */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-xs font-semibold text-slate-500 mr-1 flex items-center gap-1">
              <Filter className="w-3 h-3" />
              Order:
            </span>
            <button
              type="button"
              onClick={() => setCardinalityFilter('all')}
              className={`text-xs px-2.5 py-1.5 rounded-lg font-medium transition-colors ${
                cardinalityFilter === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              All Edges
            </button>
            <button
              type="button"
              onClick={() => setCardinalityFilter('high_order')}
              className={`text-xs px-2.5 py-1.5 rounded-lg font-medium transition-colors ${
                cardinalityFilter === 'high_order'
                  ? 'bg-purple-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              High-Order (&ge; 3)
            </button>
            <button
              type="button"
              onClick={() => setCardinalityFilter('pairwise')}
              className={`text-xs px-2.5 py-1.5 rounded-lg font-medium transition-colors ${
                cardinalityFilter === 'pairwise'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              Pairwise (= 2)
            </button>
          </div>

          {/* View Tab Toggle */}
          <div className="flex items-center border border-slate-200 rounded-lg p-1 bg-slate-50">
            <button
              type="button"
              onClick={() => setActiveTab('canvas')}
              className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === 'canvas'
                  ? 'bg-white text-blue-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Network className="w-3.5 h-3.5" />
              Interactive Canvas
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('image')}
              className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === 'image'
                  ? 'bg-white text-blue-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <ImageIcon className="w-3.5 h-3.5" />
              HyperNetX Plot
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('table')}
              className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === 'table'
                  ? 'bg-white text-blue-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <TableIcon className="w-3.5 h-3.5" />
              Hyperedges ({filteredHyperedges.length})
            </button>
          </div>
        </div>
      </Card>

      {/* Main Workspace Grid: Visualizer + Concept Inspector */}
      {isLoadingGraph ? (
        <LoadingState message="Reconstructing HyperNetX hypergraph and concept indices..." />
      ) : error ? (
        <Card className="p-6 text-center text-red-600 border-red-200 bg-red-50/50">
          <p className="text-sm font-medium">{error}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => loadGraph(selectedDocId)}>
            Retry Loading Graph
          </Button>
        </Card>
      ) : !graphData || graphData.nodes.length === 0 ? (
        <EmptyState
          icon={<Network className="w-8 h-8 text-slate-400" />}
          title="Empty Hypergraph"
          description="This document does not currently contain extracted concepts or hyperedges. Check that Phase 2 extractions completed successfully."
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* Main Visualizer Area (2 Columns) */}
          <div className="lg:col-span-2 space-y-4">
            {activeTab === 'canvas' && (
              <HypergraphCanvas
                nodes={graphData.nodes}
                hyperedges={graphData.hyperedges}
                selectedConcept={selectedConcept}
                onSelectConcept={(name) => setSelectedConcept(name)}
                searchFilter={searchQuery}
                cardinalityFilter={cardinalityFilter}
              />
            )}

            {activeTab === 'image' && (
              <Card className="border border-slate-200 overflow-hidden">
                <CardContent className="p-4 text-center">
                  <div className="text-xs font-semibold text-slate-600 mb-2">
                    HyperNetX Static Matplotlib Layout
                  </div>
                  <img
                    src={hypergraphService.getHypergraphImageUrl(selectedDocId)}
                    alt="HyperNetX Render"
                    className="max-h-[500px] mx-auto rounded-lg border border-slate-200 object-contain"
                    onError={(e) => {
                      (e.target as HTMLElement).style.display = 'none';
                    }}
                  />
                  <div className="mt-3 text-xs text-slate-500">
                    High-resolution publication plot generated using HyperNetX dual bipartite projection.
                  </div>
                </CardContent>
              </Card>
            )}

            {activeTab === 'table' && (
              <Card className="border border-slate-200">
                <div className="p-4 border-b border-slate-200 flex items-center justify-between">
                  <div className="text-xs font-bold text-slate-800">
                    Constructed Hyperedges ({filteredHyperedges.length})
                  </div>
                  <Badge variant="purple" size="sm">
                    {cardinalityFilter.toUpperCase()}
                  </Badge>
                </div>
                <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-500">
                      <tr>
                        <th className="px-4 py-2.5 font-semibold">Hyperedge ID</th>
                        <th className="px-4 py-2.5 font-semibold">Label</th>
                        <th className="px-4 py-2.5 font-semibold">Size</th>
                        <th className="px-4 py-2.5 font-semibold">Incident Concepts</th>
                        <th className="px-4 py-2.5 font-semibold">Description</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {filteredHyperedges.map((edge) => (
                        <tr key={edge.hyperedge_id} className="hover:bg-slate-50/80 transition-colors">
                          <td className="px-4 py-2.5 font-mono text-slate-700 font-semibold">
                            {edge.hyperedge_id}
                          </td>
                          <td className="px-4 py-2.5 text-blue-700 font-medium">{edge.label}</td>
                          <td className="px-4 py-2.5">
                            <Badge variant={edge.is_high_order ? 'purple' : 'default'} size="sm">
                              {edge.cardinality}
                            </Badge>
                          </td>
                          <td className="px-4 py-2.5">
                            <div className="flex flex-wrap gap-1 max-w-xs">
                              {edge.concepts.map((c, i) => (
                                <button
                                  key={i}
                                  type="button"
                                  onClick={() => {
                                    setSelectedConcept(c);
                                    setActiveTab('canvas');
                                  }}
                                  className="text-[10px] bg-slate-100 hover:bg-blue-100 text-slate-700 hover:text-blue-800 px-1.5 py-0.5 rounded cursor-pointer transition-colors"
                                >
                                  {c}
                                </button>
                              ))}
                            </div>
                          </td>
                          <td className="px-4 py-2.5 text-slate-600 max-w-sm truncate" title={edge.description}>
                            {edge.description || '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}
          </div>

          {/* Right Column: Concept Inspector */}
          <div className="space-y-4">
            <Card className="border border-slate-200 shadow-xs">
              <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                  <Info className="w-4 h-4 text-blue-600" />
                  Concept Inspector
                </div>
                {conceptDetail && (
                  <Badge variant="primary" size="sm">
                    Degree: {conceptDetail.concept.degree}
                  </Badge>
                )}
              </div>

              <CardContent className="p-5 space-y-4">
                {!selectedConcept ? (
                  <div className="text-center py-8 text-xs text-slate-400">
                    Click any concept node on the canvas or table to inspect its properties and connected hyperedges.
                  </div>
                ) : isLoadingConcept ? (
                  <div className="py-8 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                    Loading concept metadata...
                  </div>
                ) : conceptDetail ? (
                  <div className="space-y-4">
                    {/* Header: Concept Name and Entity Type */}
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="purple" size="sm">
                          {conceptDetail.concept.entity_type}
                        </Badge>
                      </div>
                      <h3 className="text-base font-bold text-slate-900 leading-snug">
                        {conceptDetail.concept.name}
                      </h3>
                      {conceptDetail.concept.description && (
                        <p className="text-xs text-slate-600 mt-2 leading-relaxed bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                          {conceptDetail.concept.description}
                        </p>
                      )}
                    </div>

                    {/* Source Chunk Citations */}
                    {conceptDetail.concept.source_chunk_ids.length > 0 && (
                      <div>
                        <div className="text-[11px] font-semibold text-slate-500 mb-1 flex items-center gap-1">
                          <FileText className="w-3 h-3 text-blue-600" />
                          Source Textbook Chunks:
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {conceptDetail.concept.source_chunk_ids.map((chk, i) => (
                            <span
                              key={i}
                              className="text-[10px] font-mono bg-blue-50 text-blue-700 border border-blue-200 px-1.5 py-0.5 rounded"
                            >
                              {chk}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 1-Hop Neighbor Concepts */}
                    {conceptDetail.neighbors.length > 0 && (
                      <div className="pt-2 border-t border-slate-100">
                        <div className="text-[11px] font-semibold text-slate-500 mb-1.5 flex items-center gap-1">
                          <Network className="w-3 h-3 text-emerald-600" />
                          1-Hop Neighbor Concepts ({conceptDetail.neighbors.length}):
                        </div>
                        <div className="flex flex-wrap gap-1 max-h-36 overflow-y-auto">
                          {conceptDetail.neighbors.map((neighbor, nIdx) => (
                            <button
                              key={nIdx}
                              type="button"
                              onClick={() => setSelectedConcept(neighbor)}
                              className="text-[11px] bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded-md font-medium transition-colors cursor-pointer"
                            >
                              {neighbor}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Incident Hyperedges */}
                    <div className="pt-2 border-t border-slate-100">
                      <div className="text-[11px] font-semibold text-slate-500 mb-2 flex items-center gap-1">
                        <Layers className="w-3 h-3 text-purple-600" />
                        Incident Hyperedges ({conceptDetail.connected_hyperedges.length}):
                      </div>
                      <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                        {conceptDetail.connected_hyperedges.map((edge, eIdx) => (
                          <div
                            key={eIdx}
                            className="bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-xs space-y-1.5"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-purple-800 font-mono text-[11px]">
                                {edge.hyperedge_id}
                              </span>
                              <Badge variant={edge.is_high_order ? 'purple' : 'default'} size="sm">
                                Size: {edge.cardinality}
                              </Badge>
                            </div>
                            <div className="text-[11px] text-slate-600 font-medium">
                              Label: <span className="text-slate-800">{edge.label}</span>
                            </div>
                            {edge.description && (
                              <p className="text-[10px] text-slate-500 leading-normal">
                                {edge.description}
                              </p>
                            )}
                            <div className="flex flex-wrap gap-1 pt-1">
                              {edge.concepts.map((c, ci) => (
                                <button
                                  key={ci}
                                  type="button"
                                  onClick={() => setSelectedConcept(c)}
                                  className={`text-[10px] px-1.5 py-0.5 rounded transition-colors ${
                                    c === selectedConcept
                                      ? 'bg-blue-600 text-white font-bold'
                                      : 'bg-white border border-slate-200 text-slate-700 hover:bg-blue-50'
                                  }`}
                                >
                                  {c}
                                </button>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-6 text-xs text-slate-500">
                    Concept information could not be retrieved.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeacherHypergraphPage;
