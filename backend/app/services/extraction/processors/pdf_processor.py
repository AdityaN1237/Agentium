import os
import logging
import fitz  # PyMuPDF
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytesseract
from PIL import Image
import io
import re

from .base import BaseProcessor
from ..result import ConversionResult
from ..exceptions import FileNotFoundError

logger = logging.getLogger(__name__)

class PDFProcessor(BaseProcessor):
    def __init__(self, preserve_layout: bool = None, include_images: bool = None, ocr_enabled: bool = None):
        super().__init__(preserve_layout, include_images, ocr_enabled)
        self._ocr_available = False
        try:
            # Check if tesseract is available
            pytesseract.get_tesseract_version()
            self._ocr_available = True
        except Exception:
            logger.warning("Tesseract not found or not in PATH. OCR for scanned documents will be skipped.")

    def can_process(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            logger.debug(f"File not found for PDFProcessor: {file_path}")
            return False
        _, ext = os.path.splitext(str(file_path).lower())
        return ext == '.pdf'

    def process(self, file_path: str) -> ConversionResult:
        if not os.path.exists(file_path):
            logger.error(f"PDF file not found: {file_path}")
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        logger.info(f"Processing PDF file: {file_path}")
        raw_content = self._extract_with_pymupdf_parallel(file_path)
        if not raw_content.strip():
            logger.warning(f"No content extracted from PDF: {file_path}")
            return ConversionResult("", {"error": "No content could be extracted from the PDF."})
        logger.info(f"Successfully processed PDF file: {file_path}")
        return ConversionResult(
            content=raw_content,
            metadata={
                'file_path': file_path,
                'file_type': 'pdf',
                'extraction_method': 'parallel_pymupdf_ocr',
                'status': 'success'
            }
        )

    def _extract_single_page(self, file_path: str, page_num: int) -> tuple:
        """Extract text from a single page (thread-safe - opens its own document)."""
        try:
            doc = fitz.open(file_path)
            page = doc.load_page(page_num)
            
            # 1. Try direct text extraction
            text = page.get_text("text")
            
            # 2. If text is empty or very sparse (scanned?), try OCR
            if self.ocr_enabled and self._ocr_available and (not text or len(text.strip()) < 50):
                logger.debug(f"Page {page_num+1} has little text, attempting OCR...")
                try:
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))
                    ocr_text = pytesseract.image_to_string(image)
                    if ocr_text and len(ocr_text.strip()) > len(text.strip()):
                        text = f"[OCR extracted]\n{ocr_text}"
                except Exception as e:
                    logger.warning(f"OCR failed for page {page_num+1}: {e}")

            links = page.get_links()
            hyperlinks = set()
            for link in links:
                if link.get('uri'):
                    hyperlinks.add(link['uri'])
            doc.close()
            return (page_num, text, hyperlinks)
        except Exception as e:
            logger.error(f"Error extracting page {page_num + 1}: {e}")
            return (page_num, "", set())

    def _extract_with_pymupdf_parallel(self, file_path: str) -> str:
        """Extract PDF content using parallel page processing."""
        try:
            # Get total page count
            doc = fitz.open(file_path)
            total_pages = len(doc)
            doc.close()

            if total_pages == 0:
                return ""

            logger.info(f"Starting PARALLEL extraction of {total_pages} pages with up to 8 threads")

            # Process all pages in parallel
            page_results = {}
            all_hyperlinks = set()

            with ThreadPoolExecutor(max_workers=min(8, total_pages)) as executor:
                # Submit all page extraction tasks
                futures = {
                    executor.submit(self._extract_single_page, file_path, page_num): page_num
                    for page_num in range(total_pages)
                }

                # Collect results as they complete
                completed = 0
                for future in as_completed(futures):
                    page_num, text, hyperlinks = future.result()
                    page_results[page_num] = text
                    all_hyperlinks.update(hyperlinks)
                    completed += 1
                    if completed % 10 == 0 or completed == total_pages:
                        logger.info(f"Extracted {completed}/{total_pages} pages")

            # Combine results in correct page order
            full_text = []
            for page_num in range(total_pages):
                text = page_results.get(page_num, "")
                if text:
                    # Clean up excessive whitespace
                    text = re.sub(r'\n{3,}', '\n\n', text)
                    text = re.sub(r' {2,}', ' ', text)
                    full_text.append(f"--- Page {page_num + 1} ---\n{text}")

            combined_content = "\n\n".join(full_text)
            
            # Additional cleanup
            combined_content = re.sub(r'\n{3,}', '\n\n', combined_content)
            
            logger.info(f"Content size after cleanup: {len(combined_content)} chars")

            if all_hyperlinks:
                hyperlinks_text = "\n\n--- Hyperlinks Found ---\n" + "\n".join(sorted(list(all_hyperlinks)))
                combined_content += hyperlinks_text

            logger.info(f"PARALLEL extraction completed: {total_pages} pages")
            return combined_content

        except Exception as e:
            logger.error(f"Parallel PDF extraction failed for {file_path}: {e}")
            return ""
