export interface HypergraphNode {
  id: string;
  name: string;
  entity_type: string;
  description?: string;
  source_chunk_ids: string[];
  degree: number;
}

export interface HypergraphEdge {
  hyperedge_id: string;
  label: string;
  concepts: string[];
  cardinality: number;
  description?: string;
  source_chunk_ids: string[];
  is_high_order: boolean;
}

export interface HypergraphMetadata {
  num_nodes: number;
  num_hyperedges: number;
  largest_hyperedge_id?: string;
  largest_hyperedge_size: number;
  num_high_order: number;
  num_pairwise: number;
}

export interface HypergraphGraphResponse {
  doc_id: string;
  filename?: string;
  metadata: HypergraphMetadata;
  nodes: HypergraphNode[];
  hyperedges: HypergraphEdge[];
  has_image: boolean;
}

export interface ConceptDetailResponse {
  concept: HypergraphNode;
  connected_hyperedges: HypergraphEdge[];
  neighbors: string[];
}
