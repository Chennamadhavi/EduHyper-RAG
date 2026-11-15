export interface DocumentItem {
  id: number;
  doc_id: string;
  filename: string;
  course_id: number;
  course_code?: string;
  course_title?: string;
  uploaded_by: number;
  status: 'READY' | 'PROCESSING' | 'ERROR';
  num_chunks: number;
  num_concepts: number;
  num_hyperedges: number;
  created_at?: string;
}

export interface DocumentUploadResult {
  doc_id: string;
  filename: string;
  status: string;
  num_chunks: number;
  num_concepts: number;
  num_hyperedges: number;
  hypergraph_json_path?: string;
  message: string;
}
