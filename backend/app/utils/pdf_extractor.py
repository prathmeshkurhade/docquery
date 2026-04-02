import fitz  # PyMuPDF — imported as "fitz" for historical reasons


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """
    Extract text from a PDF file, page by page.

    Returns a list of dicts:
    [
        {"page_number": 1, "text": "Page 1 content..."},
        {"page_number": 2, "text": "Page 2 content..."},
    ]

    PyMuPDF reads the PDF's rendering instructions and reconstructs
    the text. It handles multi-column layouts better than PyPDF2
    and is significantly faster.

    Note: scanned PDFs (images of text) will return empty strings.
    For those you'd need OCR (Tesseract) — out of scope for now.
    """
    doc = fitz.open(file_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        # Clean up: remove excessive whitespace but keep paragraph structure
        text = text.strip()

        if text:  # skip completely empty pages
            pages.append({
                "page_number": page_num + 1,  # 1-indexed for humans
                "text": text,
            })

    doc.close()
    return pages
