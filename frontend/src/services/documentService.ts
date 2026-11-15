import apiClient from './api';
import { DocumentItem, DocumentUploadResult } from '../types/document';

export const documentService = {
  /**
   * Fetches accessible documents, optionally filtered by course ID.
   */
  async listDocuments(courseId?: number): Promise<DocumentItem[]> {
    const response = await apiClient.get<DocumentItem[]>('/api/documents', {
      params: courseId ? { course_id: courseId } : {},
    });
    return response.data;
  },

  /**
   * Fetches document details by unique doc_id.
   */
  async getDocument(docId: string): Promise<DocumentItem> {
    const response = await apiClient.get<DocumentItem>(`/api/documents/${docId}`);
    return response.data;
  },

  /**
   * Uploads an educational document (PDF, TXT, MD) and executes dynamic ingestion.
   */
  async uploadDocument(courseId: number, file: File): Promise<DocumentUploadResult> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<DocumentUploadResult>(
      '/api/documents/upload',
      formData,
      {
        params: { course_id: courseId },
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },
};

export default documentService;
