import io
import logging

logger = logging.getLogger(__name__)

def extract_text_from_file(contents: bytes, content_type: str, filename: str = "") -> str:
    """
    Extract text from various file formats (PDF, DOCX, TXT).
    """
    try:
        # Text or JSON
        if content_type.startswith("text/") or content_type in ("application/json",):
            return contents.decode("utf-8", errors="ignore")

        # PDF
        # PDF
        if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
            text = ""
            # Strategy 1: pdfminer.six (High Quality)
            try:
                from pdfminer.high_level import extract_text
                text = extract_text(io.BytesIO(contents))
                if text and text.strip(): return text
            except Exception as e:
                logger.warning(f"PDF Strategy 1 (pdfminer) failed for {filename}: {e}")

            # Strategy 2: pypdf (Robust)
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(contents))
                # Attempt to fix common issues
                if reader.is_encrypted:
                    try:
                        reader.decrypt("")
                    except:
                        pass
                pages = []
                for p in reader.pages:
                    extracted = p.extract_text()
                    if extracted: pages.append(extracted)
                text = "\n".join(pages)
                if text and text.strip(): return text
            except Exception as e:
                logger.warning(f"PDF Strategy 2 (pypdf) failed for {filename}: {e}")

            # Strategy 3: pdfplumber (Layout/Corrupt Fallback)
            try:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(contents)) as pdf:
                    pages = []
                    for p in pdf.pages:
                        extracted = p.extract_text()
                        if extracted: pages.append(extracted)
                    text = "\n".join(pages)
                if text and text.strip(): return text
            except Exception as e:
                logger.warning(f"PDF Strategy 3 (pdfplumber) failed for {filename}: {e}")
            
            # Strategy 4: Fallback to Text/HTML (for mismatched extensions)
            try:
                text = contents.decode("utf-8", errors="ignore")
                # Heuristic: If > 90% chars are printable, treat as text
                printable_ratio = sum(c.isprintable() or c.isspace() for c in text) / len(text) if text else 0
                if text.strip() and printable_ratio > 0.9:
                    logger.info(f"Fallback: Treated {filename} as text/HTML due to PDF failure (Printable ratio: {printable_ratio:.2f}).")
                    return text
            except Exception:
                pass

            logger.warning(f"Skipping invalid/corrupt document: {filename} (All extraction strategies failed)")
            return ""

        # DOCX
        if content_type in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",) or filename.lower().endswith(".docx"):
            try:
                from docx import Document
                document = Document(io.BytesIO(contents))
                return "\n".join([p.text for p in document.paragraphs]).strip()
            except Exception as e:
                logger.error(f"DOCX extraction failed: {e}")
                return ""

        # Fallback for other binary types if they are just text
        try:
            return contents.decode("utf-8", errors="ignore")
        except:
            return ""

    except Exception as e:
        logger.error(f"Text extraction error for {filename}: {e}")
        return ""
