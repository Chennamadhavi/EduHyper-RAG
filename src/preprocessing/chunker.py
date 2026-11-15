"""
Text Chunking Module for EduHyperRAG.

Supports:

1. Fixed-length sliding-window chunking
2. Semantic paragraph/section-aware chunking
3. Document-specific chunk IDs
4. Course and teacher metadata propagation

The implementation is fully subject-agnostic.
No subject, topic, or document is hard-coded.
"""

import re
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.utils.logger import get_logger


logger = get_logger("chunker")


# ============================================================
# Optional tiktoken support
# ============================================================

try:
    import tiktoken

    _TIKTOKEN_AVAILABLE = True

except ImportError:
    _TIKTOKEN_AVAILABLE = False

    logger.warning(
        "tiktoken library not installed. "
        "Falling back to word-based token estimation."
    )


# ============================================================
# Chunking strategy
# ============================================================

class ChunkingStrategy(str, Enum):
    """
    Supported chunking strategies.
    """

    FIXED_LENGTH = "fixed_length"
    SEMANTIC = "semantic"


# ============================================================
# Chunk model
# ============================================================

class Chunk(BaseModel):
    """
    Structured representation of a text chunk.

    Every chunk belongs to exactly one source document.
    Additional metadata can contain course/teacher information.
    """

    chunk_id: str = Field(
        ...,
        description="Unique identifier for the chunk",
    )

    doc_id: str = Field(
        ...,
        description="ID of the parent source document",
    )

    chunk_index: int = Field(
        ...,
        description="Sequential index of the chunk in the document",
    )

    content: str = Field(
        ...,
        description="Text content of the chunk",
    )

    word_count: int = Field(
        ...,
        description="Number of words in the chunk",
    )

    token_count_approx: int = Field(
        ...,
        description="Estimated token count of the chunk",
    )

    start_char: int = Field(
        ...,
        description="Starting character index in the source document",
    )

    end_char: int = Field(
        ...,
        description="Ending character index in the source document",
    )

    chunking_strategy: ChunkingStrategy = Field(
        ...,
        description="Strategy used for chunking",
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Additional document metadata such as "
            "course_id, teacher_id, source file and section"
        ),
    )


# ============================================================
# Token counting
# ============================================================

def count_tokens(text: str) -> int:
    """
    Estimate the number of tokens in text.

    Uses tiktoken when available.
    Otherwise uses a lightweight word-based approximation.
    """

    if not text:
        return 0

    if _TIKTOKEN_AVAILABLE:

        try:
            encoding = tiktoken.get_encoding(
                "cl100k_base"
            )

            return len(
                encoding.encode(text)
            )

        except Exception as exc:
            logger.debug(
                f"tiktoken token counting failed: {exc}"
            )

    # --------------------------------------------------------
    # Fallback estimation
    # --------------------------------------------------------

    words = len(text.split())

    return int(words * 1.33)


# ============================================================
# Metadata helper
# ============================================================

def _build_metadata(
    metadata: Optional[Dict[str, Any]],
    doc_id: str,
) -> Dict[str, Any]:
    """
    Create a safe copy of chunk metadata.

    Ensures every chunk contains its parent document ID.
    """

    result: Dict[str, Any] = {}

    if metadata:
        result.update(metadata)

    # Document ID must always be authoritative.
    result["doc_id"] = doc_id

    return result


# ============================================================
# Fixed-length chunker
# ============================================================

class FixedLengthChunker:
    """
    Sliding-window chunker.

    Supports either:

    - token-based chunking
    - word-based chunking
    """

    def __init__(
        self,
        chunk_size: int = 1200,
        chunk_overlap: int = 100,
        use_tokens: bool = True,
    ):
        """
        Parameters
        ----------
        chunk_size:
            Maximum size of a chunk in tokens or words.

        chunk_overlap:
            Number of tokens/words shared between chunks.

        use_tokens:
            If True, use sentence/token-aware chunking.
            If False, use word-based sliding windows.
        """

        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than zero"
            )

        if chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap cannot be negative"
            )

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be strictly "
                "less than chunk_size"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.use_tokens = use_tokens

    # --------------------------------------------------------
    # Main chunk method
    # --------------------------------------------------------

    def chunk(
        self,
        text: str,
        doc_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        """
        Split document text into fixed-length chunks.
        """

        if not text or not text.strip():
            return []

        if not doc_id:
            raise ValueError(
                "doc_id is required for chunking"
            )

        meta = _build_metadata(
            metadata,
            doc_id,
        )

        if not self.use_tokens:
            return self._chunk_by_words(
                text=text,
                doc_id=doc_id,
                metadata=meta,
            )

        return self._chunk_by_tokens(
            text=text,
            doc_id=doc_id,
            metadata=meta,
        )

    # --------------------------------------------------------
    # Word-based chunking
    # --------------------------------------------------------

    def _chunk_by_words(
        self,
        text: str,
        doc_id: str,
        metadata: Dict[str, Any],
    ) -> List[Chunk]:
        """
        Create overlapping word-based chunks.
        """

        words = text.split()

        if not words:
            return []

        chunks: List[Chunk] = []

        step = (
            self.chunk_size
            - self.chunk_overlap
        )

        chunk_index = 0

        for start_index in range(
            0,
            len(words),
            step,
        ):

            chunk_words = words[
                start_index:
                start_index + self.chunk_size
            ]

            if not chunk_words:
                break

            chunk_text = " ".join(
                chunk_words
            )

            # ------------------------------------------------
            # Character positions
            # ------------------------------------------------

            start_char = self._find_text_position(
                text,
                chunk_words[0],
                start_index,
            )

            end_char = (
                start_char
                + len(chunk_text)
            )

            # ------------------------------------------------
            # Chunk ID
            # ------------------------------------------------

            chunk_id = (
                f"{doc_id}_fixed_"
                f"{chunk_index:04d}"
            )

            # ------------------------------------------------
            # Chunk metadata
            # ------------------------------------------------

            chunk_metadata = dict(
                metadata
            )

            chunk_metadata.update(
                {
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                    "chunk_index": chunk_index,
                }
            )

            # ------------------------------------------------
            # Create chunk
            # ------------------------------------------------

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    chunk_index=chunk_index,
                    content=chunk_text,
                    word_count=len(chunk_words),
                    token_count_approx=count_tokens(
                        chunk_text
                    ),
                    start_char=max(
                        0,
                        start_char,
                    ),
                    end_char=max(
                        0,
                        end_char,
                    ),
                    chunking_strategy=(
                        ChunkingStrategy.FIXED_LENGTH
                    ),
                    metadata=chunk_metadata,
                )
            )

            chunk_index += 1

            # ------------------------------------------------
            # Stop when final chunk is reached
            # ------------------------------------------------

            if (
                start_index
                + self.chunk_size
                >= len(words)
            ):
                break

        logger.info(
            f"FixedLengthChunker produced "
            f"{len(chunks)} chunks for "
            f"doc '{doc_id}'"
        )

        return chunks

    # --------------------------------------------------------
    # Token/sentence-aware chunking
    # --------------------------------------------------------

    def _chunk_by_tokens(
        self,
        text: str,
        doc_id: str,
        metadata: Dict[str, Any],
    ) -> List[Chunk]:
        """
        Create chunks using sentence boundaries while
        approximately respecting token limits.
        """

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        sentences = [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

        if not sentences:
            return []

        chunks: List[Chunk] = []

        current_sentences: List[str] = []
        current_token_count = 0
        chunk_index = 0

        for sentence in sentences:

            sentence_tokens = count_tokens(
                sentence
            )

            # ------------------------------------------------
            # If current chunk is full, finalize it
            # ------------------------------------------------

            if (
                current_sentences
                and current_token_count
                + sentence_tokens
                > self.chunk_size
            ):

                chunks.append(
                    self._create_token_chunk(
                        text=text,
                        doc_id=doc_id,
                        chunk_index=chunk_index,
                        sentences=current_sentences,
                        token_count=current_token_count,
                        metadata=metadata,
                    )
                )

                chunk_index += 1

                # ------------------------------------------------
                # Retain overlapping sentences
                # ------------------------------------------------

                overlap_sentences: List[str] = []
                overlap_tokens = 0

                for previous_sentence in reversed(
                    current_sentences
                ):

                    previous_tokens = count_tokens(
                        previous_sentence
                    )

                    if (
                        overlap_tokens
                        + previous_tokens
                        <= self.chunk_overlap
                    ):

                        overlap_sentences.insert(
                            0,
                            previous_sentence,
                        )

                        overlap_tokens += (
                            previous_tokens
                        )

                    else:
                        break

                current_sentences = (
                    overlap_sentences
                )

                current_token_count = (
                    overlap_tokens
                )

            # ------------------------------------------------
            # Add sentence
            # ------------------------------------------------

            current_sentences.append(
                sentence
            )

            current_token_count += (
                sentence_tokens
            )

            # ------------------------------------------------
            # Natural chunk boundary
            # ------------------------------------------------

            if (
                current_token_count
                >= self.chunk_size
            ):

                chunks.append(
                    self._create_token_chunk(
                        text=text,
                        doc_id=doc_id,
                        chunk_index=chunk_index,
                        sentences=current_sentences,
                        token_count=current_token_count,
                        metadata=metadata,
                    )
                )

                chunk_index += 1

                # Keep overlap
                overlap_sentences = []
                overlap_tokens = 0

                for previous_sentence in reversed(
                    current_sentences
                ):

                    previous_tokens = count_tokens(
                        previous_sentence
                    )

                    if (
                        overlap_tokens
                        + previous_tokens
                        <= self.chunk_overlap
                    ):

                        overlap_sentences.insert(
                            0,
                            previous_sentence,
                        )

                        overlap_tokens += (
                            previous_tokens
                        )

                    else:
                        break

                current_sentences = (
                    overlap_sentences
                )

                current_token_count = (
                    overlap_tokens
                )

        # ----------------------------------------------------
        # Remaining sentences
        # ----------------------------------------------------

        if current_sentences:

            chunks.append(
                self._create_token_chunk(
                    text=text,
                    doc_id=doc_id,
                    chunk_index=chunk_index,
                    sentences=current_sentences,
                    token_count=current_token_count,
                    metadata=metadata,
                )
            )

        logger.info(
            f"FixedLengthChunker produced "
            f"{len(chunks)} chunks for "
            f"doc '{doc_id}'"
        )

        return chunks

    # --------------------------------------------------------
    # Create token chunk
    # --------------------------------------------------------

    def _create_token_chunk(
        self,
        text: str,
        doc_id: str,
        chunk_index: int,
        sentences: List[str],
        token_count: int,
        metadata: Dict[str, Any],
    ) -> Chunk:
        """
        Create a Chunk object from a list of sentences.
        """

        chunk_text = " ".join(
            sentences
        )

        first_text = (
            sentences[0][:50]
            if sentences
            else ""
        )

        start_char = (
            text.find(first_text)
            if first_text
            else 0
        )

        if start_char < 0:
            start_char = 0

        end_char = (
            start_char
            + len(chunk_text)
        )

        chunk_id = (
            f"{doc_id}_fixed_"
            f"{chunk_index:04d}"
        )

        chunk_metadata = dict(
            metadata
        )

        chunk_metadata.update(
            {
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "chunk_index": chunk_index,
            }
        )

        return Chunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            chunk_index=chunk_index,
            content=chunk_text,
            word_count=len(
                chunk_text.split()
            ),
            token_count_approx=token_count,
            start_char=max(
                0,
                start_char,
            ),
            end_char=max(
                0,
                end_char,
            ),
            chunking_strategy=(
                ChunkingStrategy.FIXED_LENGTH
            ),
            metadata=chunk_metadata,
        )

    # --------------------------------------------------------
    # Find text position
    # --------------------------------------------------------

    @staticmethod
    def _find_text_position(
        text: str,
        word: str,
        approximate_index: int,
    ) -> int:
        """
        Find an approximate character position for a word.

        This is only used for metadata/explainability.
        """

        if not word:
            return 0

        # Approximate character position based on
        # the word index.
        approximate_char = (
            approximate_index * 2
        )

        position = text.find(
            word,
            max(
                0,
                approximate_char - 100,
            ),
        )

        if position >= 0:
            return position

        position = text.find(word)

        return max(
            0,
            position,
        )


# ============================================================
# Semantic chunker
# ============================================================

class SemanticChunker:
    """
    Section and paragraph-aware chunker.

    Attempts to preserve logical educational units such as:

    - headings
    - sections
    - paragraphs
    - explanatory blocks

    It does not assume any particular academic subject.
    """

    def __init__(
        self,
        target_chunk_size: int = 350,
        max_chunk_size: int = 600,
    ):
        if target_chunk_size <= 0:
            raise ValueError(
                "target_chunk_size must be greater than zero"
            )

        if max_chunk_size <= 0:
            raise ValueError(
                "max_chunk_size must be greater than zero"
            )

        if target_chunk_size > max_chunk_size:
            raise ValueError(
                "target_chunk_size cannot be greater "
                "than max_chunk_size"
            )

        self.target_chunk_size = (
            target_chunk_size
        )

        self.max_chunk_size = (
            max_chunk_size
        )

    # --------------------------------------------------------
    # Main semantic chunk method
    # --------------------------------------------------------

    def chunk(
        self,
        text: str,
        doc_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        """
        Split text into semantic chunks.
        """

        if not text or not text.strip():
            return []

        if not doc_id:
            raise ValueError(
                "doc_id is required for chunking"
            )

        meta = _build_metadata(
            metadata,
            doc_id,
        )

        # ----------------------------------------------------
        # Split paragraphs
        # ----------------------------------------------------

        raw_paragraphs = re.split(
            r"\n{2,}",
            text,
        )

        paragraphs = [
            paragraph.strip()
            for paragraph in raw_paragraphs
            if paragraph.strip()
        ]

        if not paragraphs:
            return []

        chunks: List[Chunk] = []

        current_section = "General"

        current_paragraphs: List[str] = []

        current_tokens = 0

        chunk_index = 0

        # ====================================================
        # Process paragraphs
        # ====================================================

        for paragraph in paragraphs:

            # ------------------------------------------------
            # Detect generic section/header
            # ------------------------------------------------

            if self._is_section_header(
                paragraph
            ):
                current_section = (
                    paragraph
                    .lstrip("#")
                    .strip()
                )

            paragraph_tokens = count_tokens(
                paragraph
            )

            # ------------------------------------------------
            # Maximum chunk boundary
            # ------------------------------------------------

            if (
                current_paragraphs
                and current_tokens
                + paragraph_tokens
                > self.max_chunk_size
            ):

                chunks.append(
                    self._create_semantic_chunk(
                        text=text,
                        doc_id=doc_id,
                        chunk_index=chunk_index,
                        paragraphs=current_paragraphs,
                        token_count=current_tokens,
                        section=current_section,
                        metadata=meta,
                    )
                )

                chunk_index += 1

                current_paragraphs = []
                current_tokens = 0

            # ------------------------------------------------
            # Add paragraph
            # ------------------------------------------------

            current_paragraphs.append(
                paragraph
            )

            current_tokens += (
                paragraph_tokens
            )

            # ------------------------------------------------
            # Natural target boundary
            # ------------------------------------------------

            if (
                current_tokens
                >= self.target_chunk_size
            ):

                chunks.append(
                    self._create_semantic_chunk(
                        text=text,
                        doc_id=doc_id,
                        chunk_index=chunk_index,
                        paragraphs=current_paragraphs,
                        token_count=current_tokens,
                        section=current_section,
                        metadata=meta,
                    )
                )

                chunk_index += 1

                current_paragraphs = []
                current_tokens = 0

        # ====================================================
        # Remaining content
        # ====================================================

        if current_paragraphs:

            chunks.append(
                self._create_semantic_chunk(
                    text=text,
                    doc_id=doc_id,
                    chunk_index=chunk_index,
                    paragraphs=current_paragraphs,
                    token_count=current_tokens,
                    section=current_section,
                    metadata=meta,
                )
            )

        logger.info(
            f"SemanticChunker produced "
            f"{len(chunks)} chunks for "
            f"doc '{doc_id}'"
        )

        return chunks

    # --------------------------------------------------------
    # Header detection
    # --------------------------------------------------------

    @staticmethod
    def _is_section_header(
        paragraph: str,
    ) -> bool:
        """
        Detect generic educational/document section headers.

        Examples supported:

        # Introduction
        ## Methods
        1. Introduction
        2.1 Architecture
        3.2.1 Implementation
        """

        return bool(
            re.match(
                r"^#{1,6}\s+",
                paragraph,
            )
            or
            re.match(
                r"^\d+(\.\d+)*\s+[A-Z]",
                paragraph,
            )
        )

    # --------------------------------------------------------
    # Create semantic chunk
    # --------------------------------------------------------

    @staticmethod
    def _create_semantic_chunk(
        text: str,
        doc_id: str,
        chunk_index: int,
        paragraphs: List[str],
        token_count: int,
        section: str,
        metadata: Dict[str, Any],
    ) -> Chunk:
        """
        Create a semantic Chunk object.
        """

        chunk_text = "\n\n".join(
            paragraphs
        )

        first_text = (
            paragraphs[0][:50]
            if paragraphs
            else ""
        )

        start_char = (
            text.find(first_text)
            if first_text
            else 0
        )

        if start_char < 0:
            start_char = 0

        end_char = (
            start_char
            + len(chunk_text)
        )

        chunk_id = (
            f"{doc_id}_semantic_"
            f"{chunk_index:04d}"
        )

        chunk_metadata = dict(
            metadata
        )

        # ----------------------------------------------------
        # Mandatory chunk metadata
        # ----------------------------------------------------

        chunk_metadata.update(
            {
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "chunk_index": chunk_index,
                "section": section,
            }
        )

        return Chunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            chunk_index=chunk_index,
            content=chunk_text,
            word_count=len(
                chunk_text.split()
            ),
            token_count_approx=token_count,
            start_char=max(
                0,
                start_char,
            ),
            end_char=max(
                0,
                end_char,
            ),
            chunking_strategy=(
                ChunkingStrategy.SEMANTIC
            ),
            metadata=chunk_metadata,
        )