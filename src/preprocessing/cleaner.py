"""
Text cleaner and normalizer module for educational document processing.
"""

import re
import unicodedata
from src.utils.logger import get_logger

logger = get_logger("cleaner")

class TextCleaner:
    """Cleans and normalizes educational text while preserving document structure."""

    def __init__(self, strip_page_numbers: bool = True, normalize_unicode: bool = True):
        self.strip_page_numbers = strip_page_numbers
        self.normalize_unicode = normalize_unicode

    def clean(self, raw_text: str) -> str:
        """
        Cleans the input text string.

        Args:
            raw_text: Raw string input from PDF or text file.

        Returns:
            Cleaned and normalized text string.
        """
        if not raw_text or not isinstance(raw_text, str):
            return ""

        text = raw_text

        # 1. Normalize Unicode characters (NFC format)
        if self.normalize_unicode:
            text = unicodedata.normalize("NFC", text)

        # 2. Replace non-standard whitespace and control characters (keep newlines)
        text = re.sub(r"[\r\t\f\v]", " ", text)

        # 3. Strip page numbers or header/footer patterns like "Page 12 of 45" or "--- Page 3 ---"
        if self.strip_page_numbers:
            text = re.sub(r"(?i)page\s+\d+(\s+of\s+\d+)?", "", text)
            text = re.sub(r"-{2,}\s*page\s*\d+\s*-{2,}", "", text)

        # 4. Fix hyphenated word breaks at line ends (e.g., "photosyn-\nthesis" -> "photosynthesis")
        text = re.sub(r"(\w+)-\n+(\w+)", r"\1\2", text)

        # 5. Normalize multiple spaces into single space
        text = re.sub(r"[ ]{2,}", " ", text)

        # 6. Normalize multiple newlines (3 or more newlines reduced to 2 for paragraph separation)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # 7. Strip leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)

        logger.debug(f"Cleaned text: raw length={len(raw_text)}, cleaned length={len(text)}")
        return text.strip()
