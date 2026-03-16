import pytest
import os
import tempfile
import asyncio
from unittest.mock import MagicMock, patch, mock_open
from app.services.extraction.extractor import DocumentExtractor
from app.services.extraction.result import ConversionResult

# Mock the config to ensure defaults
@pytest.fixture
def mock_config():
    with patch("app.services.extraction.config.ExtractionConfig") as MockConfig:
        MockConfig.PRESERVE_LAYOUT = True
        MockConfig.INCLUDE_IMAGES = True
        MockConfig.OCR_ENABLED = True
        yield MockConfig

@pytest.mark.asyncio
async def test_txt_extraction():
    # Real file test for TXT
    with tempfile.NamedTemporaryFile(suffix=".txt", mode='w+', delete=False) as f:
        f.write("Hello World from Text File")
        f.flush()
        temp_path = f.name
    
    try:
        extractor = DocumentExtractor()
        result = await extractor.extract(temp_path)
        
        assert result['success'] is True
        assert "Hello World from Text File" in result['content']
        assert result['metadata']['file_type'] == '.txt'
    finally:
        os.remove(temp_path)

@pytest.mark.asyncio
async def test_pdf_extraction_mocked():
    # Mocking fitz (PyMuPDF)
    with patch("app.services.extraction.processors.pdf_processor.fitz") as mock_fitz:
        # Create a mock document and page
        mock_doc = MagicMock()
        mock_page = MagicMock()
        
        # Setup page.get_text to return dummy text
        mock_page.get_text.return_value = "Extracted PDF Content"
        mock_page.get_links.return_value = []
        
        # Setup doc iteration/loading
        mock_doc.__len__.return_value = 1
        mock_doc.load_page.return_value = mock_page
        
        # Setup fitz.open to return our mock doc
        mock_fitz.open.return_value = mock_doc
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"dummy pdf content")
            temp_path = f.name
            
        try:
            extractor = DocumentExtractor()
            result = await extractor.extract(temp_path)
            
            assert result['success'] is True
            assert "Extracted PDF Content" in result['content']
            assert result['metadata']['file_type'] == 'pdf'
        finally:
            os.remove(temp_path)

@pytest.mark.asyncio
async def test_image_extraction_ocr_mocked():
    # Mocking pytesseract and Image
    with patch("app.services.extraction.processors.image_processor.pytesseract") as mock_tesseract, \
         patch("app.services.extraction.processors.image_processor.Image") as mock_image:
        
        mock_tesseract.image_to_string.return_value = "OCR Extracted Text"
        mock_image.open.return_value = MagicMock() # Mock image object
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"dummy image content")
            temp_path = f.name
            
        try:
            extractor = DocumentExtractor()
            result = await extractor.extract(temp_path)
            
            assert result['success'] is True
            assert "OCR Extracted Text" in result['content']
            assert result['metadata']['file_type'] == 'image'
        finally:
            os.remove(temp_path)

@pytest.mark.asyncio
async def test_scanned_pdf_fallback_mocked():
    # Test OCR fallback for scanned PDF
    with patch("app.services.extraction.processors.pdf_processor.fitz") as mock_fitz, \
         patch("app.services.extraction.processors.pdf_processor.pytesseract") as mock_tesseract, \
         patch("app.services.extraction.processors.pdf_processor.Image") as mock_image:
            
            mock_doc = MagicMock()
            mock_page = MagicMock()
            
            # Scenario: get_text returns empty string (scanned page)
            mock_page.get_text.return_value = ""
            mock_page.get_links.return_value = []
            
            mock_doc.__len__.return_value = 1
            mock_doc.load_page.return_value = mock_page
            mock_fitz.open.return_value = mock_doc
            
            # OCR returns text
            mock_tesseract.image_to_string.return_value = "Fallback OCR Text"
            
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(b"dummy pdf")
                temp_path = f.name
                
            try:
                extractor = DocumentExtractor(ocr_enabled=True)
                # We need to ensure ocr_enabled is True in the processor
                # The Extractor __init__ passes it down.
                
                result = await extractor.extract(temp_path)
                
                assert result['success'] is True
                assert "Fallback OCR Text" in result['content']
                assert "[OCR extracted]" in result['content']
            finally:
                os.remove(temp_path)
