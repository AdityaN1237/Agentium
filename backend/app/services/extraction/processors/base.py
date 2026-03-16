from abc import ABC, abstractmethod
from typing import Any, Dict
import os
import logging

from ..config import ExtractionConfig
from ..result import ConversionResult

logger = logging.getLogger(__name__)

class BaseProcessor(ABC):
    def __init__(self, preserve_layout: bool = None, include_images: bool = None, ocr_enabled: bool = None):
        self.preserve_layout = preserve_layout if preserve_layout is not None else ExtractionConfig.PRESERVE_LAYOUT
        self.include_images = include_images if include_images is not None else ExtractionConfig.INCLUDE_IMAGES
        self.ocr_enabled = ocr_enabled if ocr_enabled is not None else ExtractionConfig.OCR_ENABLED

    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        pass

    @abstractmethod
    def process(self, file_path: str) -> ConversionResult:
        pass

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        try:
            stat = os.stat(file_path)
            file_path_str = str(file_path)
            return {
                "file_size": stat.st_size,
                "file_extension": os.path.splitext(file_path_str)[1].lower(),
                "file_name": os.path.basename(file_path_str),
                "processor": self.__class__.__name__,
                "preserve_layout": self.preserve_layout,
                "include_images": self.include_images,
                "ocr_enabled": self.ocr_enabled
            }
        except Exception as e:
            logger.warning(f"Failed to get metadata for {file_path}: {e}")
            return {
                "processor": self.__class__.__name__,
                "preserve_layout": self.preserve_layout,
                "include_images": self.include_images,
                "ocr_enabled": self.ocr_enabled
            }
