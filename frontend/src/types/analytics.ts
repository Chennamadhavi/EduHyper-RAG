export interface RecentQuestionItem {
  id?: number;
  user_query: string;
  timestamp: string;
  confidence_level?: string;
  support_score: number;
  verification_decision: string;
  student_name?: string;
  filename?: string;
  course_code?: string;
}

export interface CourseAnalyticsItem {
  course_id: number;
  course_code: string;
  title: string;
  total_queries: number;
  avg_support_score: number;
  flagged_queries: number;
  enrolled_count: number;
}

export interface TeacherAnalyticsResponse {
  total_courses: number;
  total_documents: number;
  total_queries: number;
  avg_support_score: number;
  flagged_queries: number;
  hallucination_rate_pct: number;
  courses_breakdown: CourseAnalyticsItem[];
  decisions_breakdown: Record<string, number>;
  confidence_breakdown: Record<string, number>;
  recent_questions: RecentQuestionItem[];
  flagged_questions: RecentQuestionItem[];
}

export interface StudentCourseProgressItem {
  course_id: number;
  course_code: string;
  title: string;
  queries_count: number;
  avg_support_score: number;
}

export interface StudentProgressResponse {
  student_id: number;
  student_name: string;
  total_queries: number;
  enrolled_courses_count: number;
  avg_support_score: number;
  verified_rate_pct: number;
  decisions_breakdown: Record<string, number>;
  confidence_breakdown: Record<string, number>;
  course_progress: StudentCourseProgressItem[];
  recent_activity: RecentQuestionItem[];
}

export interface BenchmarkRow {
  architecture: string;
  correctness: number;
  faithfulness: number;
  context_recall: number;
  kmr: number;
  her: number;
  latency_ms: number;
}

export interface BenchmarkResponse {
  title: string;
  dataset_size: number;
  rows: BenchmarkRow[];
}
