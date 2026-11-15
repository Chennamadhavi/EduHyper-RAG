"""
Preprocessing Pipeline for EduHyperRAG.

Handles:

1. Document loading
2. Text cleaning
3. Fixed-length chunking
4. Semantic chunking
5. Document-specific metadata
6. Intermediate JSON persistence

This pipeline is fully subject-agnostic.

No subject, topic, filename, or document is hard-coded.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.config import config
from src.preprocessing.cleaner import TextCleaner
from src.preprocessing.chunker import (
    Chunk,
    FixedLengthChunker,
    SemanticChunker,
)
from src.utils.file_io import (
    read_pdf_file,
    read_text_file,
    save_json,
    save_text_file,
)
from src.utils.logger import get_logger


logger = get_logger("preprocessing_pipeline")


class PreprocessingPipeline:
    """
    Orchestrates document preprocessing and chunking.

    The pipeline works with any uploaded academic document,
    regardless of subject or domain.
    """

    def __init__(
        self,
        cleaner: Optional[TextCleaner] = None,
        fixed_chunker: Optional[FixedLengthChunker] = None,
        semantic_chunker: Optional[SemanticChunker] = None,
    ):
        # -----------------------------------------------------
        # Text cleaner
        # -----------------------------------------------------

        self.cleaner = (
            cleaner
            or TextCleaner()
        )

        # -----------------------------------------------------
        # Fixed-length chunker
        # -----------------------------------------------------

        self.fixed_chunker = (
            fixed_chunker
            or FixedLengthChunker(
                chunk_size=config.default_chunk_size,
                chunk_overlap=config.default_chunk_overlap,
            )
        )

        # -----------------------------------------------------
        # Semantic chunker
        # -----------------------------------------------------

        self.semantic_chunker = (
            semantic_chunker
            or SemanticChunker(
                target_chunk_size=350,
                max_chunk_size=600,
            )
        )

    # =========================================================
    # Process single document
    # =========================================================

    def process_file(
        self,
        file_path: Union[str, Path],
        doc_id: Optional[str] = None,
        course_id: Optional[Union[int, str]] = None,
        teacher_id: Optional[Union[int, str]] = None,
    ) -> Dict[str, Any]:
        """
        Process a single raw text or PDF document.

        Parameters
        ----------
        file_path:
            Path to the uploaded PDF/text document.

        doc_id:
            Unique document identifier.

        course_id:
            Course to which the document belongs.

        teacher_id:
            Teacher/user who uploaded the document.

        Returns
        -------
        Dict[str, Any]
            Processing summary and generated file paths.
        """

        # =====================================================
        # 1. Validate input file
        # =====================================================

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Input file not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Input path is not a file: {path}"
            )

        # =====================================================
        # 2. Determine document ID
        # =====================================================

        doc_identifier = (
            str(doc_id)
            if doc_id
            else path.stem
        )

        logger.info(
            f"Starting Phase 1 processing for document "
            f"'{doc_identifier}' "
            f"({path.suffix.lower()})"
        )

        # =====================================================
        # 3. Extract raw text
        # =====================================================

        suffix = path.suffix.lower()

        if suffix == ".pdf":
            raw_text = read_pdf_file(path)

        elif suffix in {
            ".txt",
            ".md",
        }:
            raw_text = read_text_file(path)

        else:
            raise ValueError(
                f"Unsupported file type: {suffix}. "
                f"Supported types are .pdf, .txt and .md."
            )

        # =====================================================
        # 4. Validate extracted text
        # =====================================================

        if raw_text is None:
            raise ValueError(
                f"No text could be extracted from "
                f"'{path.name}'."
            )

        raw_text = str(raw_text)

        if not raw_text.strip():
            raise ValueError(
                f"The document '{path.name}' "
                f"contains no readable text."
            )

        logger.info(
            f"Extracted {len(raw_text)} characters "
            f"from '{path.name}'"
        )

        # =====================================================
        # 5. Clean text
        # =====================================================

        cleaned_text = self.cleaner.clean(
            raw_text
        )

        if not cleaned_text or not cleaned_text.strip():
            raise ValueError(
                f"Text cleaning produced empty output "
                f"for '{path.name}'."
            )

        logger.info(
            f"Cleaned document '{doc_identifier}': "
            f"{len(cleaned_text)} characters"
        )

        # =====================================================
        # 6. Create document metadata
        # =====================================================

        metadata: Dict[str, Any] = {
            "doc_id": doc_identifier,
            "source_file": str(path.name),
            "source_path": str(path),
        }

        # Add course scope when available.
        if course_id is not None:
            metadata["course_id"] = str(course_id)

        # Add teacher scope when available.
        if teacher_id is not None:
            metadata["teacher_id"] = str(teacher_id)

        # =====================================================
        # 7. Create safe output prefix
        # =====================================================

        # The document ID generated by DocumentProcessingService
        # is already safe, but this additional sanitization makes
        # the preprocessing pipeline safe when called directly.
        safe_identifier = "".join(
            character
            if (
                character.isalnum()
                or character in {
                    "_",
                    "-",
                }
            )
            else "_"
            for character in doc_identifier
        )

        if not safe_identifier:
            safe_identifier = "document"

        # =====================================================
        # 8. Save cleaned text
        # =====================================================

        cleaned_output_path = (
            config.processed_data_dir
            / f"{safe_identifier}_cleaned.txt"
        )

        save_text_file(
            cleaned_text,
            cleaned_output_path,
        )

        # =====================================================
        # 9. Fixed-length chunking
        # =====================================================

        fixed_chunks: List[Chunk] = (
            self.fixed_chunker.chunk(
                cleaned_text,
                doc_id=doc_identifier,
                metadata=metadata,
            )
        )

        # -----------------------------------------------------
        # Ensure every fixed chunk has document metadata
        # -----------------------------------------------------

        for chunk in fixed_chunks:
            if hasattr(chunk, "metadata") and chunk.metadata is not None:
                chunk.metadata.update(metadata)

        fixed_json_path = (
            config.chunks_data_dir
            / f"{safe_identifier}_fixed_chunks.json"
        )

        save_json(
            [
                chunk.model_dump()
                for chunk in fixed_chunks
            ],
            fixed_json_path,
        )

        logger.info(
            f"Generated {len(fixed_chunks)} fixed chunks "
            f"for '{doc_identifier}'"
        )

        # =====================================================
        # 10. Semantic chunking
        # =====================================================

        semantic_chunks: List[Chunk] = (
            self.semantic_chunker.chunk(
                cleaned_text,
                doc_id=doc_identifier,
                metadata=metadata,
            )
        )

        # -----------------------------------------------------
        # Ensure every semantic chunk has document metadata
        # -----------------------------------------------------

        for chunk in semantic_chunks:

            if hasattr(chunk, "metadata") and chunk.metadata is not None:

                chunk.metadata.update(
                    metadata
                )

        semantic_json_path = (
            config.chunks_data_dir
            / f"{safe_identifier}_semantic_chunks.json"
        )

        save_json(
            [
                chunk.model_dump()
                for chunk in semantic_chunks
            ],
            semantic_json_path,
        )

        logger.info(
            f"Generated {len(semantic_chunks)} semantic chunks "
            f"for '{doc_identifier}'"
        )

        # =====================================================
        # 11. Processing summary
        # =====================================================

        summary: Dict[str, Any] = {
            "doc_id": doc_identifier,
            "course_id": (
                str(course_id)
                if course_id is not None
                else None
            ),
            "teacher_id": (
                str(teacher_id)
                if teacher_id is not None
                else None
            ),
            "source_file": str(path),
            "raw_char_count": len(raw_text),
            "cleaned_char_count": len(cleaned_text),
            "fixed_chunks_count": len(fixed_chunks),
            "semantic_chunks_count": len(semantic_chunks),
            "cleaned_text_path": str(
                cleaned_output_path
            ),
            "fixed_chunks_path": str(
                fixed_json_path
            ),
            "semantic_chunks_path": str(
                semantic_json_path
            ),
        }

        logger.info(
            f"Completed Phase 1 for "
            f"'{doc_identifier}': "
            f"{len(fixed_chunks)} fixed chunks, "
            f"{len(semantic_chunks)} semantic chunks."
        )

        return summary

    # =========================================================
    # Process directory
    # =========================================================

    def process_directory(
        self,
        dir_path: Optional[
            Union[str, Path]
        ] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process all supported documents in a directory.

        Supported:
        - .txt
        - .md
        - .pdf

        This method is primarily intended for batch/legacy
        processing. Production uploads should normally use
        process_file() through DocumentProcessingService.
        """

        target_dir = (
            Path(dir_path)
            if dir_path
            else config.raw_data_dir
        )

        if not target_dir.exists():
            raise FileNotFoundError(
                f"Raw data directory does not exist: "
                f"{target_dir}"
            )

        if not target_dir.is_dir():
            raise ValueError(
                f"Path is not a directory: "
                f"{target_dir}"
            )

        supported_extensions = {
            ".txt",
            ".md",
            ".pdf",
        }

        files = [
            file_path
            for file_path in target_dir.iterdir()
            if (
                file_path.is_file()
                and file_path.suffix.lower()
                in supported_extensions
                and not file_path.name.startswith(".")
            )
        ]

        logger.info(
            f"Found {len(files)} supported document(s) "
            f"in {target_dir}"
        )

        summaries: List[Dict[str, Any]] = []

        for file_path in files:

            try:
                summary = self.process_file(
                    file_path
                )

                summaries.append(
                    summary
                )

            except Exception as exc:

                logger.exception(
                    f"Failed to process "
                    f"'{file_path.name}': {exc}"
                )

                # Continue processing other files
                # rather than stopping the entire batch.
                continue

        return summaries