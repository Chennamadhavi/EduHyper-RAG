"""
Semantic Vector Retriever for EduHyperRAG using ChromaDB.

Responsibilities:
- Embed document chunks
- Store chunks in ChromaDB
- Preserve document/course/teacher metadata
- Perform semantic similarity search
- Support document-level filtering
- Support course-level filtering
- Prevent accidental cross-document retrieval

The retriever is fully subject-agnostic.
No subject, topic, or document is hard-coded.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import chromadb
from pydantic import BaseModel, Field

from src.config import config
from src.preprocessing.chunker import Chunk
from src.utils.file_io import read_json
from src.utils.logger import get_logger


logger = get_logger("semantic_retriever")


# ============================================================
# Retrieved chunk model
# ============================================================

class SemanticChunkResult(BaseModel):
    """
    Schema for a semantically retrieved document chunk.
    """

    chunk_id: str

    content: str

    relevance_score: float = Field(
        ...,
        description="Normalized similarity score from 0.0 to 1.0",
    )

    retrieval_method: str = "semantic"

    source_file: str = ""

    metadata: Dict[str, Any] = Field(
        default_factory=dict
    )


# ============================================================
# Semantic Retriever
# ============================================================

class SemanticRetriever:
    """
    Vector database retriever using ChromaDB.

    Supports:

    - document-specific retrieval
    - course-specific retrieval
    - teacher metadata
    - metadata-preserving indexing
    - filtered semantic search

    Production retrieval should normally specify either
    doc_id or course_id.
    """

    def __init__(
        self,
        collection_name: str = "eduhyperrag_chunks",
        persist_directory: Optional[
            Union[str, Path]
        ] = None,
    ):
        self.collection_name = collection_name

        # ----------------------------------------------------
        # ChromaDB persistence directory
        # ----------------------------------------------------

        self.persist_dir = (
            Path(persist_directory)
            if persist_directory
            else (
                config.knowledge_base_dir
                / "chroma_db"
            )
        )

        self.persist_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ----------------------------------------------------
        # Initialize persistent ChromaDB
        # ----------------------------------------------------

        self.client = chromadb.PersistentClient(
            path=str(
                self.persist_dir
            )
        )

        self.collection = (
            self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "hnsw:space": "cosine"
                },
            )
        )

        logger.info(
            f"Initialized ChromaDB collection "
            f"'{self.collection_name}' at "
            f"{self.persist_dir}"
        )

    # ========================================================
    # INDEX CHUNKS
    # ========================================================

    def index_chunks(
        self,
        chunks: List[Chunk],
        course_id: Optional[
            Union[int, str]
        ] = None,
        teacher_id: Optional[
            Union[int, str]
        ] = None,
    ) -> int:
        """
        Index Chunk objects into ChromaDB.

        Explicit course_id and teacher_id values take priority
        over metadata stored inside each chunk.

        This ensures that the document processing service can
        enforce the correct ownership/scope.
        """

        if not chunks:
            logger.warning(
                "No chunks supplied for indexing."
            )
            return 0

        ids: List[str] = []

        documents: List[str] = []

        metadatas: List[
            Dict[str, Any]
        ] = []

        for chunk in chunks:

            # =================================================
            # Resolve document ID
            # =================================================

            chunk_metadata = (
                chunk.metadata
                if isinstance(
                    chunk.metadata,
                    dict,
                )
                else {}
            )

            doc_id = str(
                getattr(
                    chunk,
                    "doc_id",
                    "",
                )
                or chunk_metadata.get(
                    "doc_id",
                    "",
                )
            ).strip()

            if not doc_id:
                raise ValueError(
                    "Every chunk must have a valid "
                    "doc_id before indexing."
                )

            # =================================================
            # Resolve course ID
            # =================================================

            resolved_course_id = (
                course_id
                if course_id is not None
                else chunk_metadata.get(
                    "course_id",
                    "",
                )
            )

            # =================================================
            # Resolve teacher ID
            # =================================================

            resolved_teacher_id = (
                teacher_id
                if teacher_id is not None
                else chunk_metadata.get(
                    "teacher_id",
                    "",
                )
            )

            # =================================================
            # Validate course scope
            # =================================================

            if (
                resolved_course_id is None
                or str(
                    resolved_course_id
                ).strip() == ""
            ):
                logger.warning(
                    f"Chunk '{chunk.chunk_id}' "
                    f"has no course_id."
                )

            # =================================================
            # Build Chroma metadata
            # =================================================

            metadata: Dict[str, Any] = {
                # ------------------------------------------------
                # Access/scope metadata
                # ------------------------------------------------

                "doc_id": doc_id,

                "course_id": str(
                    resolved_course_id
                    if resolved_course_id is not None
                    else ""
                ),

                "teacher_id": str(
                    resolved_teacher_id
                    if resolved_teacher_id is not None
                    else ""
                ),

                # ------------------------------------------------
                # Chunk identity
                # ------------------------------------------------

                "chunk_id": str(
                    chunk.chunk_id
                ),

                "chunk_index": int(
                    chunk.chunk_index
                ),

                # ------------------------------------------------
                # Chunk statistics
                # ------------------------------------------------

                "word_count": int(
                    chunk.word_count
                ),

                "token_count_approx": int(
                    chunk.token_count_approx
                ),

                # ------------------------------------------------
                # Chunking strategy
                # ------------------------------------------------

                "strategy": str(
                    chunk.chunking_strategy.value
                ),

                # ------------------------------------------------
                # Source
                # ------------------------------------------------

                "source_file": str(
                    chunk_metadata.get(
                        "source_file",
                        "",
                    )
                ),
            }

            # =================================================
            # Preserve semantic section information
            # =================================================

            if "section" in chunk_metadata:

                metadata["section"] = str(
                    chunk_metadata[
                        "section"
                    ]
                )

            # =================================================
            # Add Chroma records
            # =================================================

            ids.append(
                str(
                    chunk.chunk_id
                )
            )

            documents.append(
                str(
                    chunk.content
                )
            )

            metadatas.append(
                metadata
            )

        # =====================================================
        # Upsert into ChromaDB
        # =====================================================

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(
            f"Indexed {len(chunks)} chunk(s) "
            f"into ChromaDB."
        )

        return len(chunks)

    # ========================================================
    # INDEX FROM JSON FILE
    # ========================================================

    def index_from_file(
        self,
        chunks_json_path: Union[str, Path],
        course_id: Optional[
            Union[int, str]
        ] = None,
        teacher_id: Optional[
            Union[int, str]
        ] = None,
    ) -> int:
        """
        Index chunks from a saved JSON file.
        """

        path = Path(
            chunks_json_path
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Chunks file not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Chunks path is not a file: {path}"
            )

        raw_chunks = read_json(
            path
        )

        if not isinstance(
            raw_chunks,
            list,
        ):
            raise ValueError(
                "Chunk JSON must contain "
                "a list of chunks."
            )

        chunks: List[Chunk] = []

        for raw_chunk in raw_chunks:

            try:
                chunks.append(
                    Chunk(
                        **raw_chunk
                    )
                )

            except Exception as exc:

                raise ValueError(
                    f"Invalid chunk data in "
                    f"{path}: {exc}"
                ) from exc

        return self.index_chunks(
            chunks,
            course_id=course_id,
            teacher_id=teacher_id,
        )

    # ========================================================
    # SEMANTIC SEARCH
    # ========================================================

    def search(
        self,
        query: str,
        top_k: int = 3,
        where_filter: Optional[
            Dict[str, Any]
        ] = None,
        require_scope: bool = False,
    ) -> List[
        SemanticChunkResult
    ]:
        """
        Perform semantic similarity search.

        Parameters
        ----------
        query:
            User's natural-language question.

        top_k:
            Maximum number of chunks to retrieve.

        where_filter:
            ChromaDB metadata filter.

            Examples:

                {"doc_id": "doc_abc123"}

                {"course_id": "5"}

                {
                    "$and": [
                        {"course_id": "5"},
                        {"teacher_id": "2"}
                    ]
                }

        require_scope:
            If True, reject unrestricted searches.

            Production student retrieval should set this to True.
        """

        # =====================================================
        # Validate query
        # =====================================================

        if not query or not query.strip():
            return []

        query = query.strip()

        # =====================================================
        # Validate top_k
        # =====================================================

        if top_k <= 0:
            return []

        # =====================================================
        # Security/scope check
        # =====================================================

        if require_scope and not where_filter:
            raise ValueError(
                "Scoped retrieval requires a "
                "doc_id or course_id filter."
            )

        # =====================================================
        # Build Chroma query
        # =====================================================

        query_kwargs: Dict[
            str,
            Any,
        ] = {
            "query_texts": [
                query
            ],
            "n_results": int(
                top_k
            ),
        }

        if where_filter:

            query_kwargs[
                "where"
            ] = where_filter

        # =====================================================
        # Execute search
        # =====================================================

        try:

            results = (
                self.collection.query(
                    **query_kwargs
                )
            )

        except Exception as exc:

            logger.exception(
                f"ChromaDB semantic search failed: "
                f"{exc}"
            )

            raise

        retrieved_chunks: List[
            SemanticChunkResult
        ] = []

        # =====================================================
        # Validate result structure
        # =====================================================

        if not results:
            return []

        ids_groups = results.get(
            "ids"
        )

        if not ids_groups:
            return []

        if not ids_groups[0]:
            return []

        ids = ids_groups[0]

        documents = (
            results.get(
                "documents",
                [[]],
            )[0]
        )

        distances = (
            results.get(
                "distances",
                [[]],
            )[0]
            if results.get(
                "distances"
            )
            else [
                0.0
            ] * len(ids)
        )

        metadatas = (
            results.get(
                "metadatas",
                [[]],
            )[0]
            if results.get(
                "metadatas"
            )
            else [
                {}
            ] * len(ids)
        )

        # =====================================================
        # Convert Chroma results
        # =====================================================

        for (
            chunk_id,
            document,
            distance,
            metadata,
        ) in zip(
            ids,
            documents,
            distances,
            metadatas,
        ):

            metadata = (
                metadata
                if isinstance(
                    metadata,
                    dict,
                )
                else {}
            )

            # -------------------------------------------------
            # Chroma cosine distance:
            #
            # similarity ≈ 1 - distance
            # -------------------------------------------------

            try:

                similarity = (
                    1.0
                    - float(
                        distance
                    )
                )

            except (
                TypeError,
                ValueError,
            ):

                similarity = 0.0

            similarity = max(
                0.0,
                min(
                    1.0,
                    similarity,
                ),
            )

            # -------------------------------------------------
            # Build result
            # -------------------------------------------------

            retrieved_chunks.append(
                SemanticChunkResult(
                    chunk_id=str(
                        chunk_id
                    ),

                    content=str(
                        document
                    ),

                    relevance_score=round(
                        similarity,
                        4,
                    ),

                    retrieval_method=(
                        "semantic"
                    ),

                    source_file=str(
                        metadata.get(
                            "source_file",
                            "",
                        )
                    ),

                    metadata=metadata,
                )
            )

        # =====================================================
        # Logging
        # =====================================================

        logger.info(
            f"Semantic search for "
            f"'{query}' retrieved "
            f"{len(retrieved_chunks)} "
            f"chunk(s)."
        )

        if where_filter:

            logger.info(
                f"Applied ChromaDB filter: "
                f"{where_filter}"
            )

        else:

            logger.warning(
                "Semantic search executed "
                "without a metadata filter."
            )

        return retrieved_chunks