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
        "hwp": extract_hwp,
        "hwpx": extract_hwpx,
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


def extract_hwp(filepath: str) -> str:
    """HWP 파일에서 텍스트 추출 (OLE 바이너리 포맷)"""
    try:
        import olefile
        import zlib
        import struct
    except ImportError:
        raise ImportError("olefile이 설치되지 않았습니다: pip install olefile")

    if not olefile.isOleFile(filepath):
        raise ValueError("유효하지 않은 HWP 파일입니다")

    ole = olefile.OleFileIO(filepath)
    text_parts = []

    i = 1
    while True:
        stream_name = f'BodyText/Section{i:04d}'
        if not ole.exists(stream_name):
            break
        try:
            data = ole.openstream(stream_name).read()
            # zlib 압축 해제 시도
            try:
                data = zlib.decompress(data, -15)
            except Exception:
                pass

            # HWP 레코드 구조 파싱
            pos = 0
            while pos + 4 <= len(data):
                header = struct.unpack_from('<I', data, pos)[0]
                rec_type = header & 0x3FF
                size = (header >> 20) & 0xFFF
                if size == 0xFFF:
                    if pos + 8 > len(data):
                        break
                    size = struct.unpack_from('<I', data, pos + 4)[0]
                    pos += 8
                else:
                    pos += 4

                # HWPTAG_PARA_TEXT (rec_type 67 = 0x43)
                if rec_type == 67:
                    try:
                        text = data[pos:pos + size].decode('utf-16-le', errors='ignore')
                        text = ''.join(c for c in text if ord(c) >= 32 or c in '\n\t')
                        if text.strip():
                            text_parts.append(text)
                    except Exception:
                        pass
                pos += size
        except Exception as e:
            logger.warning(f"HWP Section{i} 처리 실패: {e}")
        i += 1

    ole.close()
    if not text_parts:
        logger.warning(f"HWP에서 텍스트를 추출하지 못했습니다: {filepath}")
    return "\n".join(text_parts)


def extract_hwpx(filepath: str) -> str:
    """HWPX 파일에서 텍스트 추출 (ZIP+XML 포맷)"""
    import zipfile
    import xml.etree.ElementTree as ET

    text_parts = []
    with zipfile.ZipFile(filepath, 'r') as z:
        section_files = sorted([
            f for f in z.namelist()
            if 'section' in f.lower() and f.endswith('.xml')
        ])
        for section_file in section_files:
            try:
                xml_data = z.read(section_file)
                root = ET.fromstring(xml_data)
                for elem in root.iter():
                    if elem.text and elem.text.strip():
                        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                        if tag in ('t', 'run', 'text', 'para'):
                            text_parts.append(elem.text.strip())
            except Exception as e:
                logger.warning(f"HWPX 섹션 파싱 실패 {section_file}: {e}")
    return "\n".join(text_parts)
