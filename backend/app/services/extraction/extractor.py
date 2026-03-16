import logging
import asyncio
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from .processors.pdf_processor import PDFProcessor
from .processors.docx_processor import DOCXProcessor
from .processors.txt_processor import TXTProcessor
from .processors.html_processor import HTMLProcessor
from .processors.image_processor import ImageProcessor
from .processors.url_processor import URLProcessor
from .result import ConversionResult
from .exceptions import UnsupportedFormatError
from .config import ExtractionConfig

logger = logging.getLogger(__name__)

class DocumentExtractor:
    def __init__(
        self,
        preserve_layout: bool = None,
        include_images: bool = None,
        ocr_enabled: bool = None,
    ):
        self.config = ExtractionConfig()
        # Initialize processors
        self.processors = [
            PDFProcessor(preserve_layout, include_images, ocr_enabled),
            DOCXProcessor(preserve_layout, include_images, ocr_enabled),
            TXTProcessor(preserve_layout, include_images, ocr_enabled),
            HTMLProcessor(preserve_layout, include_images, ocr_enabled),
            ImageProcessor(preserve_layout, include_images, ocr_enabled),
            URLProcessor(preserve_layout, include_images, ocr_enabled),
        ]
        self._executor = ThreadPoolExecutor(max_workers=4)

    def _get_processor(self, file_path: str):
        for p in self.processors:
            if p.can_process(file_path):
                return p
        return None

    async def extract(self, file_path: str, output_type: str = "json") -> Dict[str, Any]:
        """
        Async extraction method that offloads CPU-bound processing to a thread pool.
        Returns a dictionary with 'content' and metadata.
        """
        loop = asyncio.get_running_loop()
        
        processor = self._get_processor(file_path)
        if not processor:
            raise UnsupportedFormatError(f"No processor found for file: {file_path}")

        logger.info(f"Using processor {processor.__class__.__name__} for {file_path}")

        try:
            # Run the synchronous processor.process() in a separate thread
            result: ConversionResult = await loop.run_in_executor(
                self._executor, 
                processor.process, 
                file_path
            )
            
            content = result.content
            metadata = result.metadata
            
            # Structure the output
            return {
                "success": True,
                "content": content,
                "metadata": metadata,
                "format": output_type,
                "extractor": "local_toronto_engine"
            }

        except Exception as e:
            logger.error(f"Extraction failed for {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "extractor": "local_toronto_engine"
            }
