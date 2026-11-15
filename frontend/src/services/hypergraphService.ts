import apiClient from './api';
import {
  ConceptDetailResponse,
  HypergraphGraphResponse,
} from '../types/hypergraph';

export const hypergraphService = {
  /**
   * Fetches complete hypergraph structure (nodes, hyperedges, complexity metrics) for a document.
   */
  async getDocumentHypergraph(docId: string): Promise<HypergraphGraphResponse> {
    const response = await apiClient.get<HypergraphGraphResponse>(
      `/api/hypergraph/documents/${encodeURIComponent(docId)}`
    );
    return response.data;
  },

  /**
   * Fetches specific concept node inspection details, connected hyperedges, and neighbors.
   */
  async getConceptDetails(docId: string, conceptName: string): Promise<ConceptDetailResponse> {
    const response = await apiClient.get<ConceptDetailResponse>(
      `/api/hypergraph/documents/${encodeURIComponent(docId)}/concepts/${encodeURIComponent(conceptName)}`
    );
    return response.data;
  },

  /**
   * Returns URL for fetching static HyperNetX/matplotlib rendering plot.
   */
  getHypergraphImageUrl(docId: string): string {
    const base = apiClient.defaults.baseURL || 'http://127.0.0.1:8000';
    return `${base}/api/hypergraph/documents/${encodeURIComponent(docId)}/image`;
  },
};

export default hypergraphService;
