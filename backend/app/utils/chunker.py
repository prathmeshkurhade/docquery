from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_pages(pages: list[dict], chunk_size: int = 512, chunk_overlap: int = 50) -> list[dict]:
    """
    Take extracted pages and split them into overlapping chunks.

    Input:  [{"page_number": 1, "text": "..."}, {"page_number": 2, "text": "..."}]
    Output: [{"text": "...", "page_number": 1, "chunk_index": 0}, ...]

    RecursiveCharacterTextSplitter tries to split at natural boundaries:
    1. First tries paragraphs (\\n\\n)
    2. Then sentences (\\n)
    3. Then words (" ")
    4. Last resort: character-level split

    This is better than naive splitting every 512 chars because it
    keeps sentences and paragraphs intact when possible.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,  # count characters (not tokens — simpler, close enough)
        separators=["\n\n", "\n", " ", ""],
    )

    chunks = []
    chunk_index = 0

    for page in pages:
        # Split this page's text into chunks
        page_chunks = splitter.split_text(page["text"])

        for chunk_text in page_chunks:
            chunks.append({
                "text": chunk_text,
                "page_number": page["page_number"],
                "chunk_index": chunk_index,
            })
            chunk_index += 1

    return chunks
