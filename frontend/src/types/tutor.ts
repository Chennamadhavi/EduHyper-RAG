export interface TutorQueryPayload {
  query: string;
  doc_id: string;
  course_id: number;
  max_iterations?: number;
  min_support_score?: number;
}

export interface ChunkDetail {
  chunk_id: string;
  content: string;
  score: number;
  source: string;
  page?: number;
}

export interface TutorQueryResponse {
  query: string;
  answer: string;
  confidence_level: 'High' | 'Medium' | 'Low' | string;
  support_score: number;
  verification_decision: 'VERIFIED' | 'PARTIALLY_SUPPORTED' | 'UNSUPPORTED' | string;
  verification_reasoning?: string;
  supporting_chunks: string[];
  supporting_hyperedges: string[];
  retrieved_concepts: string[];
  retrieved_chunk_details: ChunkDetail[];
  hallucination_report?: Record<string, any>;
  explainability_report?: Record<string, any>;
  doc_id: string;
  course_id: number;
}

export interface QAHistoryItem {
  id: number;
  student_id: number;
  doc_id: string;
  course_id: number;
  user_query: string;
  generated_answer: string;
  confidence_level?: string;
  support_score?: number;
  verification_decision?: string;
  filename?: string;
  course_code?: string;
  created_at?: string;
}
