import os
import logging
from .base import BaseProcessor
from ..result import ConversionResult
from ..exceptions import ConversionError, FileNotFoundError

logger = logging.getLogger(__name__)

class TXTProcessor(BaseProcessor):
    def can_process(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            logger.debug(f"File not found for TXTProcessor: {file_path}")
            return False
        _, ext = os.path.splitext(str(file_path).lower())
        return ext in ['.txt', '.text']

    def process(self, file_path: str) -> ConversionResult:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        logger.info(f"Processing text file: {file_path}")
        try:
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            content = None
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            if content is None:
                logger.error(f"Could not decode file {file_path} with any supported encoding")
                raise ConversionError(f"Could not decode file {file_path} with any supported encoding")
            content = self._clean_content(content)
            metadata = self.get_metadata(file_path)
            metadata.update({
                "encoding": encoding,
                "line_count": len(content.split('\n')),
                "word_count": len(content.split())
            })
            logger.info(f"Successfully processed text file: {file_path}")
            return ConversionResult(content, metadata)
        except Exception as e:
            logger.error(f"Failed to process text file {file_path}: {str(e)}")
            raise ConversionError(f"Failed to process text file {file_path}: {str(e)}")

    def _clean_content(self, content: str) -> str:
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.rstrip()
            cleaned_lines.append(line)
        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        return '\n'.join(cleaned_lines)
