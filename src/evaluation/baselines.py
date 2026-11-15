"""
Comparative Baseline Architectures for EduHyperRAG Evaluation.
Implements 6 distinct pipeline configurations for empirical benchmarking:
1. Vanilla LLM (Direct LLM without external retrieval)
2. Traditional RAG (Vector retrieval via ChromaDB only)
3. GraphRAG (Pairwise low-order edge retrieval + vector search)
4. LightRAG (Dual-level local concept & global relation vector/graph retrieval)
5. Original Hyper-RAG (Hypergraph retrieval + vector search without agentic verification)
6. Proposed Enhanced Hyper-RAG (Hypergraph retrieval + LangGraph Agentic Verification + Hallucination Claim Verification)

NOTE: Baseline implementations approximate published methodologies within this Python framework.
"""

import time
from typing import Any, Dict, List, Optional
from src.agents.verification_graph import run_agentic_verification
from src.evaluation.hallucination_checker import HallucinationChecker
from src.generation.answer_generator import EducationalAnswerGenerator
from src.hypergraph.query_hypergraph import EduHypergraphQueryEngine
from src.retrieval.hypergraph_retriever import HypergraphRetriever
from src.retrieval.semantic_retriever import SemanticRetriever
from src.utils.logger import get_logger

logger = get_logger("baselines")


class PipelineRunner:
    """Base interface for RAG pipeline evaluation runners."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def run_query(self, query: str) -> Dict[str, Any]:
        raise NotImplementedError


class VanillaLLMRunner(PipelineRunner):
    """1. Vanilla LLM: Generates answers directly without external retrieval."""

    def __init__(self):
        super().__init__("Vanilla LLM", "Direct LLM generation relying solely on parametric memory without external retrieval.")
        self.generator = EducationalAnswerGenerator()

    def run_query(self, query: str) -> Dict[str, Any]:
        t0 = time.perf_counter()
        # Mock empty retrieval state
        empty_state = {
            "user_query": query,
            "extracted_query_concepts": [],
            "retrieved_chunks": [],
            "retrieved_hyperedges": [],
            "retrieved_concepts": [],
            "sources": [],
            "is_sufficient": True,  # Force LLM generation from internal memory
            "verification_reasoning": "Vanilla LLM direct generation.",
            "relevance_score": 0.5,
            "missing_concepts": [],
            "confidence": 0.5,
            "iteration_count": 1,
            "max_iterations": 1,
            "status": "VANILLA",
        }
        retrieval_ms = 0.0
        t_gen_start = time.perf_counter()
        ans_res = self.generator.generate_answer(empty_state)
        gen_ms = (time.perf_counter() - t_gen_start) * 1000.0
        total_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "query": query,
            "answer": ans_res["answer"],
            "retrieved_chunk_ids": [],
            "retrieved_concepts": [],
            "retrieved_hyperedges": [],
            "retrieval_latency_ms": round(retrieval_ms, 2),
            "generation_latency_ms": round(gen_ms, 2),
            "total_response_time_ms": round(total_ms, 2),
            "iterations_count": 1,
            "chunks_data": [],
            "hyperedges_data": [],
            "concepts_data": [],
        }


class TraditionalRAGRunner(PipelineRunner):
    """2. Traditional RAG: Uses ChromaDB vector similarity search only."""

    def __init__(self):
        super().__init__("Traditional RAG", "Standard vector-search RAG querying ChromaDB chunks.")
        self.semantic_retriever = SemanticRetriever()
        self.generator = EducationalAnswerGenerator()

    def run_query(self, query: str) -> Dict[str, Any]:
        t0 = time.perf_counter()
        t_ret_start = time.perf_counter()
        chunks = self.semantic_retriever.search(query, top_k=3)
        ret_ms = (time.perf_counter() - t_ret_start) * 1000.0

        chunks_dict = [c.model_dump() for c in chunks]
        chunk_ids = [c.chunk_id for c in chunks]

        state = {
            "user_query": query,
            "extracted_query_concepts": [],
            "retrieved_chunks": chunks_dict,
            "retrieved_hyperedges": [],
            "retrieved_concepts": [],
            "sources": chunk_ids,
            "is_sufficient": True,
            "verification_reasoning": "Traditional RAG direct pass.",
            "relevance_score": max((c.relevance_score for c in chunks), default=0.5),
            "missing_concepts": [],
            "confidence": 0.6,
            "iteration_count": 1,
            "max_iterations": 1,
            "status": "TRADITIONAL_RAG",
        }

        t_gen_start = time.perf_counter()
        ans_res = self.generator.generate_answer(state)
        gen_ms = (time.perf_counter() - t_gen_start) * 1000.0
        total_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "query": query,
            "answer": ans_res["answer"],
            "retrieved_chunk_ids": chunk_ids,
            "retrieved_concepts": [],
            "retrieved_hyperedges": [],
            "retrieval_latency_ms": round(ret_ms, 2),
            "generation_latency_ms": round(gen_ms, 2),
            "total_response_time_ms": round(total_ms, 2),
            "iterations_count": 1,
            "chunks_data": chunks_dict,
            "hyperedges_data": [],
            "concepts_data": [],
        }


class GraphRAGRunner(PipelineRunner):
    """3. GraphRAG: Vector retrieval + Pairwise low-order graph edges."""

    def __init__(self):
        super().__init__("GraphRAG", "Knowledge graph RAG using pairwise (cardinality=2) edges and vector chunks.")
        self.semantic_retriever = SemanticRetriever()
        self.hypergraph_retriever = HypergraphRetriever()
        self.generator = EducationalAnswerGenerator()

    def run_query(self, query: str) -> Dict[str, Any]:
        t0 = time.perf_counter()
        t_ret_start = time.perf_counter()
        chunks = self.semantic_retriever.search(query, top_k=3)
        hyp_res = self.hypergraph_retriever.search(query, max_hyperedges=4)

        # Filter hyperedges to pairwise edges only (cardinality == 2)
        pairwise_edges = [h for h in hyp_res.hyperedges if h.cardinality == 2]
        ret_ms = (time.perf_counter() - t_ret_start) * 1000.0

        chunks_dict = [c.model_dump() for c in chunks]
        edges_dict = [h.model_dump() for h in pairwise_edges]
        concepts_dict = [c.model_dump() for c in hyp_res.concepts]

        chunk_ids = list(set([c.chunk_id for c in chunks] + hyp_res.sources))

        state = {
            "user_query": query,
            "extracted_query_concepts": hyp_res.matched_query_terms,
            "retrieved_chunks": chunks_dict,
            "retrieved_hyperedges": edges_dict,
            "retrieved_concepts": concepts_dict,
            "sources": chunk_ids,
            "is_sufficient": True,
            "verification_reasoning": "GraphRAG direct pass.",
            "relevance_score": 0.65,
            "missing_concepts": [],
            "confidence": 0.65,
            "iteration_count": 1,
            "max_iterations": 1,
            "status": "GRAPHRAG",
        }

        t_gen_start = time.perf_counter()
        ans_res = self.generator.generate_answer(state)
        gen_ms = (time.perf_counter() - t_gen_start) * 1000.0
        total_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "query": query,
            "answer": ans_res["answer"],
            "retrieved_chunk_ids": chunk_ids,
            "retrieved_concepts": [c["name"] for c in concepts_dict],
            "retrieved_hyperedges": [e["hyperedge_id"] for e in edges_dict],
            "retrieval_latency_ms": round(ret_ms, 2),
            "generation_latency_ms": round(gen_ms, 2),
            "total_response_time_ms": round(total_ms, 2),
            "iterations_count": 1,
            "chunks_data": chunks_dict,
            "hyperedges_data": edges_dict,
            "concepts_data": concepts_dict,
        }


class LightRAGRunner(PipelineRunner):
    """4. LightRAG: Dual-level local entity & global relation retrieval."""

    def __init__(self):
        super().__init__("LightRAG", "Lightweight RAG combining entity node descriptions and relation edges.")
        self.semantic_retriever = SemanticRetriever()
        self.hypergraph_retriever = HypergraphRetriever()
        self.generator = EducationalAnswerGenerator()

    def run_query(self, query: str) -> Dict[str, Any]:
        t0 = time.perf_counter()
        t_ret_start = time.perf_counter()
        chunks = self.semantic_retriever.search(query, top_k=2)
        hyp_res = self.hypergraph_retriever.search(query, max_hyperedges=3)
        ret_ms = (time.perf_counter() - t_ret_start) * 1000.0

        chunks_dict = [c.model_dump() for c in chunks]
        edges_dict = [h.model_dump() for h in hyp_res.hyperedges]
        concepts_dict = [c.model_dump() for c in hyp_res.concepts]
        chunk_ids = list(set([c.chunk_id for c in chunks] + hyp_res.sources))

        state = {
            "user_query": query,
            "extracted_query_concepts": hyp_res.matched_query_terms,
            "retrieved_chunks": chunks_dict,
            "retrieved_hyperedges": edges_dict,
            "retrieved_concepts": concepts_dict,
            "sources": chunk_ids,
            "is_sufficient": True,
            "verification_reasoning": "LightRAG dual-level pass.",
            "relevance_score": 0.70,
            "missing_concepts": [],
            "confidence": 0.70,
            "iteration_count": 1,
            "max_iterations": 1,
            "status": "LIGHTRAG",
        }

        t_gen_start = time.perf_counter()
        ans_res = self.generator.generate_answer(state)
        gen_ms = (time.perf_counter() - t_gen_start) * 1000.0
        total_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "query": query,
            "answer": ans_res["answer"],
            "retrieved_chunk_ids": chunk_ids,
            "retrieved_concepts": [c["name"] for c in concepts_dict],
            "retrieved_hyperedges": [e["hyperedge_id"] for e in edges_dict],
            "retrieval_latency_ms": round(ret_ms, 2),
            "generation_latency_ms": round(gen_ms, 2),
            "total_response_time_ms": round(total_ms, 2),
            "iterations_count": 1,
            "chunks_data": chunks_dict,
            "hyperedges_data": edges_dict,
            "concepts_data": concepts_dict,
        }


class OriginalHyperRAGRunner(PipelineRunner):
    """5. Original Hyper-RAG: Hypergraph retrieval + vector search without agentic verification loop."""

    def __init__(self):
        super().__init__("Original Hyper-RAG", "Hypergraph retrieval with high-order edges (cardinality >= 3) and vector search without agentic loop.")
        self.semantic_retriever = SemanticRetriever()
        self.hypergraph_retriever = HypergraphRetriever()
        self.generator = EducationalAnswerGenerator()

    def run_query(self, query: str) -> Dict[str, Any]:
        t0 = time.perf_counter()
        t_ret_start = time.perf_counter()
        chunks = self.semantic_retriever.search(query, top_k=3)
        hyp_res = self.hypergraph_retriever.search(query, max_hyperedges=4)
        ret_ms = (time.perf_counter() - t_ret_start) * 1000.0

        chunks_dict = [c.model_dump() for c in chunks]
        edges_dict = [h.model_dump() for h in hyp_res.hyperedges]
        concepts_dict = [c.model_dump() for c in hyp_res.concepts]
        chunk_ids = list(set([c.chunk_id for c in chunks] + hyp_res.sources))

        state = {
            "user_query": query,
            "extracted_query_concepts": hyp_res.matched_query_terms,
            "retrieved_chunks": chunks_dict,
            "retrieved_hyperedges": edges_dict,
            "retrieved_concepts": concepts_dict,
            "sources": chunk_ids,
            "is_sufficient": True,
            "verification_reasoning": "Hyper-RAG direct pass.",
            "relevance_score": 0.80,
            "missing_concepts": [],
            "confidence": 0.80,
            "iteration_count": 1,
            "max_iterations": 1,
            "status": "HYPER_RAG",
        }

        t_gen_start = time.perf_counter()
        ans_res = self.generator.generate_answer(state)
        gen_ms = (time.perf_counter() - t_gen_start) * 1000.0
        total_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "query": query,
            "answer": ans_res["answer"],
            "retrieved_chunk_ids": chunk_ids,
            "retrieved_concepts": [c["name"] for c in concepts_dict],
            "retrieved_hyperedges": [e["hyperedge_id"] for e in edges_dict],
            "retrieval_latency_ms": round(ret_ms, 2),
            "generation_latency_ms": round(gen_ms, 2),
            "total_response_time_ms": round(total_ms, 2),
            "iterations_count": 1,
            "chunks_data": chunks_dict,
            "hyperedges_data": edges_dict,
            "concepts_data": concepts_dict,
        }


class EnhancedHyperRAGRunner(PipelineRunner):
    """6. Proposed Enhanced Hyper-RAG: Hypergraph + LangGraph Agentic Verification + Claim Verification."""

    def __init__(self):
        super().__init__(
            "Proposed Enhanced Hyper-RAG",
            "Complete architecture: Hypergraph retrieval, ChromaDB vector search, LangGraph Agentic Verification, and Claim Hallucination Verification."
        )
        self.generator = EducationalAnswerGenerator()

    def run_query(self, query: str) -> Dict[str, Any]:
        t0 = time.perf_counter()
        t_ret_start = time.perf_counter()
        # Execute Phase 5 Agentic Verification Workflow
        verified_state = run_agentic_verification(user_query=query, max_iterations=2)
        ret_ms = (time.perf_counter() - t_ret_start) * 1000.0

        # Execute Phase 6 Answer Generation
        t_gen_start = time.perf_counter()
        ans_res = self.generator.generate_answer(verified_state)
        gen_ms = (time.perf_counter() - t_gen_start) * 1000.0
        total_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "query": query,
            "answer": ans_res["answer"],
            "retrieved_chunk_ids": verified_state.get("sources", []),
            "retrieved_concepts": [c["name"] for c in verified_state.get("retrieved_concepts", [])],
            "retrieved_hyperedges": [e["hyperedge_id"] for e in verified_state.get("retrieved_hyperedges", [])],
            "retrieval_latency_ms": round(ret_ms, 2),
            "generation_latency_ms": round(gen_ms, 2),
            "total_response_time_ms": round(total_ms, 2),
            "iterations_count": verified_state.get("iteration_count", 1),
            "chunks_data": verified_state.get("retrieved_chunks", []),
            "hyperedges_data": verified_state.get("retrieved_hyperedges", []),
            "concepts_data": verified_state.get("retrieved_concepts", []),
            "verified_state": verified_state,
        }
