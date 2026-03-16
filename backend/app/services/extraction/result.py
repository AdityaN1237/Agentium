import csv
import io
import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class MarkdownToJSONParser:
    def __init__(self):
        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.list_item_pattern = re.compile(r'^(\s*)[*\-+]\s+(.+)$', re.MULTILINE)
        self.ordered_list_pattern = re.compile(r'^(\s*)\d+\.\s+(.+)$', re.MULTILINE)
        self.code_block_pattern = re.compile(r'```(\w+)?\n(.*?)```', re.DOTALL)
        self.inline_code_pattern = re.compile(r'`([^`]+)`')
        self.link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        self.image_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
        self.table_pattern = re.compile(r'\|(.+)\|\s*\n\|[-\s|:]+\|\s*\n((?:\|.+\|\s*\n?)*)', re.MULTILINE)
        self.blockquote_pattern = re.compile(r'^>\s+(.+)$', re.MULTILINE)
        self.bold_pattern = re.compile(r'\*\*(.+?)\*\*')
        self.italic_pattern = re.compile(r'\*(.+?)\*')

    def parse(self, markdown_text: str) -> Dict[str, Any]:
        if not markdown_text or not markdown_text.strip():
            return {"document": {"sections": [], "metadata": {"total_sections": 0}}}
        lines = markdown_text.split('\n')
        sections = []
        current_section = None
        current_content = []
        for line in lines:
            line = line.rstrip()
            header_match = self.header_pattern.match(line)
            if header_match:
                if current_section is not None:
                    current_section['content'] = self._parse_content('\n'.join(current_content))
                    sections.append(current_section)
                header_level = len(header_match.group(1))
                header_text = header_match.group(2).strip()
                current_section = {"title": header_text, "level": header_level, "type": "section", "content": {}}
                current_content = []
            else:
                if line.strip() or current_content:
                    current_content.append(line)
        if current_section is not None:
            current_section['content'] = self._parse_content('\n'.join(current_content))
            sections.append(current_section)
        elif current_content:
            sections.append({"title": "Content", "level": 1, "type": "section", "content": self._parse_content('\n'.join(current_content))})
        structured_sections = self._create_hierarchy(sections)
        return {
            "document": {
                "sections": structured_sections,
                "metadata": {
                    "total_sections": len(sections),
                    "max_heading_level": max([s.get('level', 1) for s in sections]) if sections else 0,
                    "has_tables": any('tables' in s.get('content', {}) for s in sections),
                    "has_code_blocks": any('code_blocks' in s.get('content', {}) for s in sections),
                    "has_lists": any('lists' in s.get('content', {}) for s in sections),
                    "has_images": any('images' in s.get('content', {}) for s in sections)
                }
            }
        }

    def _parse_content(self, content: str) -> Dict[str, Any]:
        if not content.strip():
            return {}
        result = {}
        paragraphs = self._extract_paragraphs(content)
        if paragraphs:
            result['paragraphs'] = paragraphs
        lists = self._extract_lists(content)
        if lists:
            result['lists'] = lists
        code_blocks = self._extract_code_blocks(content)
        if code_blocks:
            result['code_blocks'] = code_blocks
        tables = self._extract_tables(content)
        if tables:
            result['tables'] = tables
        return result

    def _extract_paragraphs(self, content: str) -> List[str]:
        clean_content = content
        clean_content = self.code_block_pattern.sub('', clean_content)
        clean_content = re.sub(r'\|.*\|', '', clean_content)
        clean_content = self.list_item_pattern.sub('', clean_content)
        clean_content = self.ordered_list_pattern.sub('', clean_content)
        clean_content = self.blockquote_pattern.sub('', clean_content)
        paragraphs = []
        for para in clean_content.split('\n\n'):
            para = para.strip()
            if para and not para.startswith('#'):
                para = self._clean_inline_formatting(para)
                paragraphs.append(para)
        return paragraphs

    def _extract_lists(self, content: str) -> List[Dict[str, Any]]:
        lists = []
        lines = content.split('\n')
        current_list = None
        for line in lines:
            line = line.rstrip()
            unordered_match = self.list_item_pattern.match(line)
            if unordered_match:
                indent_level = len(unordered_match.group(1)) // 2
                item_text = self._clean_inline_formatting(unordered_match.group(2))
                if current_list is None or current_list['type'] != 'unordered':
                    if current_list:
                        lists.append(current_list)
                    current_list = {'type': 'unordered', 'items': []}
                current_list['items'].append({'text': item_text, 'level': indent_level})
                continue
            ordered_match = self.ordered_list_pattern.match(line)
            if ordered_match:
                indent_level = len(ordered_match.group(1)) // 2
                item_text = self._clean_inline_formatting(ordered_match.group(2))
                if current_list is None or current_list['type'] != 'ordered':
                    if current_list:
                        lists.append(current_list)
                    current_list = {'type': 'ordered', 'items': []}
                current_list['items'].append({'text': item_text, 'level': indent_level})
                continue
            if current_list and line.strip():
                lists.append(current_list)
                current_list = None
        if current_list:
            lists.append(current_list)
        return lists

    def _extract_code_blocks(self, content: str) -> List[Dict[str, str]]:
        code_blocks = []
        for match in self.code_block_pattern.finditer(content):
            language = match.group(1) or 'text'
            code = match.group(2).strip()
            code_blocks.append({'language': language, 'code': code})
        return code_blocks

    def _extract_tables(self, content: str) -> List[Dict[str, Any]]:
        tables = []
        for match in self.table_pattern.finditer(content):
            header_row = match.group(1).strip()
            body_rows = match.group(2).strip()
            headers = [cell.strip() for cell in header_row.split('|') if cell.strip()]
            rows = []
            for row_line in body_rows.split('\n'):
                if row_line.strip() and '|' in row_line:
                    cells = [cell.strip() for cell in row_line.split('|') if cell.strip()]
                    if cells:
                        rows.append(cells)
            if headers and rows:
                tables.append({'headers': headers, 'rows': rows, 'columns': len(headers)})
        return tables

    def _clean_inline_formatting(self, text: str) -> str:
        text = self.bold_pattern.sub(r'\1', text)
        text = self.italic_pattern.sub(r'\1', text)
        text = self.inline_code_pattern.sub(r'\1', text)
        return text.strip()

    def _create_hierarchy(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not sections:
            return []
        result = []
        stack = []
        for section in sections:
            level = section['level']
            while stack and stack[-1]['level'] >= level:
                stack.pop()
            if stack:
                parent = stack[-1]
                if 'subsections' not in parent:
                    parent['subsections'] = []
                parent['subsections'].append(section)
            else:
                result.append(section)
            stack.append(section)
        return result

class MarkdownToHTMLConverter:
    def __init__(self):
        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.bold_pattern = re.compile(r'\*\*(.+?)\*\*')
        self.italic_pattern = re.compile(r'\*(.+?)\*')
        self.inline_code_pattern = re.compile(r'`([^`]+)`')
        self.link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        self.image_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

    def convert(self, markdown_text: str) -> str:
        html = markdown_text
        html = self._process_code_blocks(html)
        html = self._process_tables(html)
        html = self._process_headers(html)
        html = self._process_lists(html)
        html = self._process_inline_elements(html)
        html = self._process_paragraphs(html)
        return html

    def _process_code_blocks(self, text: str) -> str:
        def replace_code_block(match):
            language = match.group(1) or ''
            code = match.group(2)
            lang_class = f' class="language-{language}"' if language else ''
            return f'<pre><code{lang_class}>{self._escape_html(code)}</code></pre>'
        text = re.sub(r'```(\w+)?\n(.*?)\n```', replace_code_block, text, flags=re.DOTALL)
        return text

    def _process_tables(self, text: str) -> str:
        lines = text.split('\n')
        result_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if '|' in line and i + 1 < len(lines) and '|' in lines[i + 1]:
                next_line = lines[i + 1]
                if re.match(r'^\s*\|[\s\-:|]+\|\s*$', next_line):
                    table_lines = [line]
                    j = i + 1
                    while j < len(lines) and '|' in lines[j]:
                        table_lines.append(lines[j])
                        j += 1
                    html_table = self._convert_table_to_html(table_lines)
                    result_lines.append(html_table)
                    i = j
                    continue
            result_lines.append(line)
            i += 1
        return '\n'.join(result_lines)

    def _convert_table_to_html(self, table_lines: List[str]) -> str:
        if len(table_lines) < 2:
            return table_lines[0] if table_lines else ''
        html_parts = ['<table>']
        header_cells = [cell.strip() for cell in table_lines[0].split('|')[1:-1]]
        html_parts.append('<thead><tr>')
        for cell in header_cells:
            html_parts.append(f'<th>{self._escape_html(cell)}</th>')
        html_parts.append('</tr></thead>')
        html_parts.append('<tbody>')
        for line in table_lines[2:]:
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            html_parts.append('<tr>')
            for cell in cells:
                html_parts.append(f'<td>{self._escape_html(cell)}</td>')
            html_parts.append('</tr>')
        html_parts.append('</tbody>')
        html_parts.append('</table>')
        return '\n'.join(html_parts)

    def _process_headers(self, text: str) -> str:
        def replace_header(match):
            level = len(match.group(1))
            content = match.group(2)
            return f'<h{level}>{self._escape_html(content)}</h{level}>'
        return self.header_pattern.sub(replace_header, text)

    def _process_lists(self, text: str) -> str:
        lines = text.split('\n')
        result_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if re.match(r'^[\s]*[-*+]\s+', line):
                list_lines = self._collect_list_items(lines, i, r'^[\s]*[-*+]\s+')
                html_list = self._convert_list_to_html(list_lines, 'ul')
                result_lines.append(html_list)
                i += len(list_lines)
                continue
            elif re.match(r'^[\s]*\d+\.\s+', line):
                list_lines = self._collect_list_items(lines, i, r'^[\s]*\d+\.\s+')
                html_list = self._convert_list_to_html(list_lines, 'ol')
                result_lines.append(html_list)
                i += len(list_lines)
                continue
            result_lines.append(line)
            i += 1
        return '\n'.join(result_lines)

    def _collect_list_items(self, lines: List[str], start_idx: int, pattern: str) -> List[str]:
        items = []
        i = start_idx
        while i < len(lines):
            line = lines[i]
            if re.match(pattern, line):
                items.append(line)
                i += 1
            elif line.strip() == '':
                items.append(line)
                i += 1
            else:
                break
        return items

    def _convert_list_to_html(self, list_lines: List[str], list_type: str) -> str:
        html_parts = [f'<{list_type}>']
        for line in list_lines:
            if line.strip() == '':
                continue
            if list_type == 'ul':
                content = re.sub(r'^[\s]*[-*+]\s+', '', line)
            else:
                content = re.sub(r'^[\s]*\d+\.\s+', '', line)
            content = self._process_inline_elements(content)
            html_parts.append(f'<li>{content}</li>')
        html_parts.append(f'</{list_type}>')
        return '\n'.join(html_parts)

    def _process_inline_elements(self, text: str) -> str:
        text = self.bold_pattern.sub(r'<strong>\1</strong>', text)
        text = self.italic_pattern.sub(r'<em>\1</em>', text)
        text = self.inline_code_pattern.sub(r'<code>\1</code>', text)
        text = self.link_pattern.sub(r'<a href="\2">\1</a>', text)
        text = self.image_pattern.sub(r'<img src="\2" alt="\1">', text)
        return text

    def _process_paragraphs(self, text: str) -> str:
        lines = text.split('\n')
        result_lines = []
        current_paragraph = []
        for line in lines:
            if line.strip() == '':
                if current_paragraph:
                    paragraph_content = ' '.join(current_paragraph)
                    result_lines.append(f'<p>{paragraph_content}</p>')
                    current_paragraph = []
            else:
                if re.match(r'^<(h[1-6]|p|div|blockquote|pre|table|ul|ol|li|hr)', line.strip()):
                    if current_paragraph:
                        paragraph_content = ' '.join(current_paragraph)
                        result_lines.append(f'<p>{paragraph_content}</p>')
                        current_paragraph = []
                    result_lines.append(line)
                else:
                    current_paragraph.append(line)
        if current_paragraph:
            paragraph_content = ' '.join(current_paragraph)
            result_lines.append(f'<p>{paragraph_content}</p>')
        return '\n'.join(result_lines)

    def _escape_html(self, text: str) -> str:
        return (text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;'))

class ConversionResult:
    def __init__(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        self.content = content
        self.metadata = metadata or {}
        self._html_converter = MarkdownToHTMLConverter()
        self._json_parser = MarkdownToJSONParser()

    def extract_markdown(self) -> str:
        return self.content

    def extract_html(self) -> str:
        html_content = self._html_converter.convert(self.content)
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Converted Document</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3, h4, h5, h6 {{ color: #2c3e50; margin-top: 1.5em; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""

    def extract_text(self) -> str:
        return self.content

    def extract_csv(self, table_index: int = 0, include_all_tables: bool = False) -> str:
        json_data = self._json_parser.parse(self.content)
        tables = []
        def extract_tables_from_sections(sections):
            for section in sections:
                content = section.get('content', {})
                if 'tables' in content:
                    tables.extend(content['tables'])
                if 'subsections' in section:
                    extract_tables_from_sections(section['subsections'])
        if 'document' in json_data and 'sections' in json_data['document']:
            extract_tables_from_sections(json_data['document']['sections'])
        if not tables:
            tables = self._extract_markdown_tables_directly(self.content)
        if not tables:
            raise ValueError("No tables found in the document content")
        if include_all_tables:
            csv_output = io.StringIO()
            writer = csv.writer(csv_output)
            for i, table in enumerate(tables):
                if i > 0:
                    writer.writerow([])
                    writer.writerow([f"=== Table {i + 1} ==="])
                    writer.writerow([])
                if 'headers' in table and table['headers']:
                    writer.writerow(table['headers'])
                if 'rows' in table:
                    for row in table['rows']:
                        writer.writerow(row)
            return csv_output.getvalue()
        else:
            if table_index >= len(tables):
                raise ValueError(f"Table index {table_index} out of range. Found {len(tables)} table(s)")
            table = tables[table_index]
            csv_output = io.StringIO()
            writer = csv.writer(csv_output)
            if 'headers' in table and table['headers']:
                writer.writerow(table['headers'])
            if 'rows' in table:
                for row in table['rows']:
                    writer.writerow(row)
            return csv_output.getvalue()

    def _extract_markdown_tables_directly(self, content: str) -> List[Dict[str, Any]]:
        tables = []
        table_pattern = re.compile(r'\|(.+)\|\s*\n\|[-\s|:]+\|\s*\n((?:\|.+\|\s*\n?)*)', re.MULTILINE)
        for match in table_pattern.finditer(content):
            header_row = match.group(1).strip()
            body_rows = match.group(2).strip()
            headers = [cell.strip() for cell in header_row.split('|') if cell.strip()]
            rows = []
            for row_line in body_rows.split('\n'):
                if row_line.strip() and '|' in row_line:
                    cells = [cell.strip() for cell in row_line.split('|') if cell.strip()]
                    if cells:
                        rows.append(cells)
            if headers and rows:
                tables.append({'headers': headers, 'rows': rows, 'columns': len(headers)})
        return tables

    def __str__(self) -> str:
        return self.content

    def __repr__(self) -> str:
        return f"ConversionResult(content='{self.content[:50]}...', metadata={self.metadata})"
