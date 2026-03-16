import os
import logging
from .base import BaseProcessor
from ..result import ConversionResult
from ..exceptions import ConversionError, FileNotFoundError

logger = logging.getLogger(__name__)

class HTMLProcessor(BaseProcessor):
    def can_process(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            logger.debug(f"File not found for HTMLProcessor: {file_path}")
            return False
        _, ext = os.path.splitext(str(file_path).lower())
        return ext in ['.html', '.htm']

    def process(self, file_path: str) -> ConversionResult:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        try:
            from markdownify import markdownify as md
        except ImportError:
            logger.error("markdownify is required for HTML processing. Install it with: pip install markdownify")
            raise ConversionError("markdownify is required for HTML processing. Install it with: pip install markdownify")
        metadata = self.get_metadata(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        content = md(html_content, heading_style="ATX")
        logger.info(f"Successfully processed HTML file: {file_path}")
        return ConversionResult(content, metadata)
