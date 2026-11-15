import apiClient from './api';
import {
  BenchmarkResponse,
  StudentProgressResponse,
  TeacherAnalyticsResponse,
} from '../types/analytics';

export const analyticsService = {
  /**
   * Fetches classroom quality metrics, hallucination rates, and audit logs for the teacher.
   */
  async getTeacherAnalytics(): Promise<TeacherAnalyticsResponse> {
    const response = await apiClient.get<TeacherAnalyticsResponse>('/api/analytics/teacher');
    return response.data;
  },

  /**
   * Fetches personalized learning progress, mastery scores, and query activity for the student.
   */
  async getStudentProgress(): Promise<StudentProgressResponse> {
    const response = await apiClient.get<StudentProgressResponse>('/api/analytics/student');
    return response.data;
  },

  /**
   * Fetches Phase 9 comparative benchmark evaluation results across all retrieval architectures.
   */
  async getBenchmark(): Promise<BenchmarkResponse> {
    const response = await apiClient.get<BenchmarkResponse>('/api/analytics/benchmark');
    return response.data;
  },
};

export default analyticsService;
