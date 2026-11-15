import apiClient from './api';
import { QAHistoryItem, TutorQueryPayload, TutorQueryResponse } from '../types/tutor';

export const tutorService = {
  /**
   * Retrieves curated sample questions for quick testing and exploration.
   */
  async getSampleQuestions(): Promise<string[]> {
    const response = await apiClient.get<string[]>('/api/tutor/sample-questions');
    return response.data;
  },

  /**
   * Submits a question to the AI Tutor for grounded retrieval, verification, and answer generation.
   */
  async askTutor(payload: TutorQueryPayload): Promise<TutorQueryResponse> {
    const response = await apiClient.post<TutorQueryResponse>('/api/tutor/query', payload, {
      timeout: 60000, // Multi-phase retrieval and LLM verification may take up to 60s
    });
    return response.data;
  },

  /**
   * Retrieves personal question and answer history for the authenticated student.
   */
  async getHistory(): Promise<QAHistoryItem[]> {
    const response = await apiClient.get<QAHistoryItem[]>('/api/tutor/history');
    return response.data;
  },
};

export default tutorService;
