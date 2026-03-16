import os
import logging
import re
from typing import Dict, Any
from urllib.parse import urlparse
from .base import BaseProcessor
from ..result import ConversionResult
from ..exceptions import ConversionError, NetworkError

logger = logging.getLogger(__name__)

class URLProcessor(BaseProcessor):
    def can_process(self, file_path: str) -> bool:
        return self._is_url(file_path)

    def process(self, file_path: str) -> ConversionResult:
        try:
            import requests
            from bs4 import BeautifulSoup
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            logger.info(f"Fetching URL: {file_path}")
            response = requests.get(file_path, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            content_parts = []
            title = soup.find('title')
            if title:
                content_parts.append(f"# {title.get_text().strip()}\n")
            main_content = self._extract_main_content(soup)
            if main_content:
                content_parts.append(main_content)
            else:
                body = soup.find('body')
                if body:
                    content_parts.append(body.get_text())
            content = '\n'.join(content_parts)
            content = self._clean_content(content)
            metadata = {
                "url": file_path,
                "status_code": response.status_code,
                "content_type": response.headers.get('content-type', ''),
                "content_length": len(response.content),
                "processor": self.__class__.__name__
            }
            logger.info(f"Successfully processed URL: {file_path}")
            return ConversionResult(content, metadata)
        except ImportError:
            logger.error("requests and beautifulsoup4 are required for URL processing. Install them with: pip install requests beautifulsoup4")
            raise ConversionError("requests and beautifulsoup4 are required for URL processing. Install them with: pip install requests beautifulsoup4")
        except requests.RequestException as e:
            logger.error(f"Failed to fetch URL {file_path}: {str(e)}")
            raise NetworkError(f"Failed to fetch URL {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to process URL {file_path}: {str(e)}")
            raise ConversionError(f"Failed to process URL {file_path}: {str(e)}")

    def _is_url(self, text: str) -> bool:
        try:
            result = urlparse(text)
            return all([result.scheme, result.netloc])
        except:
            return False

    def _extract_main_content(self, soup) -> str:
        main_selectors = [
            'main',
            '[role="main"]',
            '.main-content',
            '.content',
            '#content',
            'article',
            '.post-content',
            '.entry-content'
        ]
        for selector in main_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text()
        return ""

    def _clean_content(self, content: str) -> str:
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            line = ' '.join(line.split())
            if line.strip():
                cleaned_lines.append(line)
        content = '\n'.join(cleaned_lines)
        content = content.replace('# ', '\n# ')
        content = content.replace('## ', '\n## ')
        return content.strip()
