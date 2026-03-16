import os
import logging
import pytesseract
from PIL import Image
from .base import BaseProcessor
from ..result import ConversionResult
from ..exceptions import ConversionError, FileNotFoundError

logger = logging.getLogger(__name__)

class ImageProcessor(BaseProcessor):
    def can_process(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            logger.debug(f"File not found for ImageProcessor: {file_path}")
            return False
        _, ext = os.path.splitext(str(file_path).lower())
        return ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif']

    def process(self, file_path: str) -> ConversionResult:
        try:
            if not os.path.exists(file_path):
                logger.error(f"Image file not found: {file_path}")
                raise FileNotFoundError(f"Image file not found: {file_path}")
            
            logger.info(f"Processing image file with Tesseract OCR: {file_path}")
            
            # Open image using Pillow
            try:
                img = Image.open(file_path)
            except Exception as e:
                raise ConversionError(f"Failed to open image: {e}")

            # Extract text using pytesseract
            try:
                text = pytesseract.image_to_string(img)
            except Exception as e:
                # If tesseract fails (e.g. not installed), raise distinct error or return empty
                logger.error(f"Tesseract OCR failed: {e}")
                raise ConversionError(f"Tesseract OCR failed: {e}. Ensure Tesseract is installed.")

            metadata = self.get_metadata(file_path)
            metadata.update({
                'file_type': 'image',
                'extractor': 'pytesseract_ocr',
                'image_size': img.size,
                'image_mode': img.mode
            })

            logger.info(f"Successfully extracted {len(text)} chars from image using OCR.")
            return ConversionResult(content=text, metadata=metadata)
            
        except Exception as e:
            logger.error(f"Failed to process image file {file_path}: {e}")
            raise ConversionError(f"Image processing failed: {e}")
