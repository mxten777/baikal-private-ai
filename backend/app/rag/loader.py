"""
Document Loader - 텍스트 추출
"""
import logging

logger = logging.getLogger("baikal.loader")


def extract_text(filepath: str, file_type: str) -> str:
    """파일에서 텍스트 추출"""
    extractors = {
        "pdf": extract_pdf,
        "docx": extract_docx,
        "xlsx": extract_xlsx,
    }

    extractor = extractors.get(file_type)
    if extractor is None:
        raise ValueError(f"지원하지 않는 파일 형식: {file_type}")

    try:
        text = extractor(filepath)
        logger.info(f"텍스트 추출 완료: {filepath} ({len(text)} chars)")
        return text
    except Exception as e:
        logger.error(f"텍스트 추출 실패: {filepath} - {e}")
        raise


def extract_pdf(filepath: str) -> str:
    """PDF에서 텍스트 추출"""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        raise ImportError("PyPDF2가 설치되지 않았습니다: pip install PyPDF2")

    reader = PdfReader(filepath)
    text_parts = []
    for i, page in enumerate(reader.pages):
        try:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        except Exception as e:
            logger.warning(f"PDF 페이지 {i + 1} 추출 실패: {e}")
            continue

    if not text_parts:
        logger.warning(f"PDF에서 텍스트를 추출할 수 없습니다 (이미지 PDF일 수 있음): {filepath}")

    return "\n\n".join(text_parts)


def extract_docx(filepath: str) -> str:
    """DOCX에서 텍스트 추출"""
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx가 설치되지 않았습니다: pip install python-docx")

    doc = Document(filepath)
    text_parts = []

    # 본문 텍스트
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text_parts.append(paragraph.text)

    # 테이블 내용
    for table in doc.tables:
        for row in table.rows:
            row_text = "\t".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                text_parts.append(row_text)

    # 헤더/푸터
    for section in doc.sections:
        header = section.header
        if header and header.paragraphs:
            for p in header.paragraphs:
                if p.text.strip():
                    text_parts.insert(0, p.text)

    return "\n".join(text_parts)


def extract_xlsx(filepath: str) -> str:
    """XLSX에서 텍스트 추출"""
    try:
        from openpyxl import load_workbook
    except ImportError:
        raise ImportError("openpyxl이 설치되지 않았습니다: pip install openpyxl")

    wb = load_workbook(filepath, read_only=True, data_only=True)
    text_parts = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        text_parts.append(f"[시트: {sheet_name}]")

        row_count = 0
        for row in ws.iter_rows(values_only=True):
            row_text = "\t".join(
                str(cell) if cell is not None else "" for cell in row
            )
            if row_text.strip():
                text_parts.append(row_text)
                row_count += 1

            # 대용량 시트 제한 (10000행)
            if row_count > 10000:
                text_parts.append(f"... ({sheet_name} 시트: 10000행까지만 처리)")
                break

    wb.close()
    return "\n".join(text_parts)
