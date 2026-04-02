import logging

from sqlalchemy import select

from app.database import SyncSession
from app.models.user import User  # noqa: F401 — needed so FK to users resolves
from app.models.document import Document, DocumentStatus
from app.utils.pdf_extractor import extract_text_from_pdf
from app.utils.chunker import chunk_pages
from app.services.embedding import embed_texts
from app.services.vector_store import store_chunks
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def update_status(doc_id: str, status: DocumentStatus, **kwargs):
    """Update document status in the database (sync — for Celery)."""
    with SyncSession() as session:
        result = session.execute(
            select(Document).where(Document.id == doc_id)
        )
        doc = result.scalar_one()
        doc.status = status
        for key, value in kwargs.items():
            setattr(doc, key, value)
        session.commit()


@celery_app.task(name="process_pdf")
def process_pdf(document_id: str, file_path: str):
    """
    Full PDF processing pipeline:

    PDF file → Extract text → Chunk → Embed → Store in Qdrant → Done

    Each step feeds into the next:
    1. extract_text_from_pdf → list of {page_number, text}
    2. chunk_pages           → list of {text, page_number, chunk_index}
    3. embed_texts           → list of 1536-dim vectors
    4. store_chunks          → saved in Qdrant with metadata
    """
    logger.info(f"Processing PDF: {document_id}")

    try:
        # Mark as processing
        update_status(document_id, DocumentStatus.PROCESSING)

        # Step 1: Extract text from PDF
        logger.info("Step 1: Extracting text...")
        pages = extract_text_from_pdf(file_path)
        logger.info(f"  Extracted {len(pages)} pages")

        if not pages:
            update_status(
                document_id,
                DocumentStatus.FAILED,
                error_message="No text found in PDF (might be a scanned document)",
            )
            return

        # Step 2: Chunk the text
        logger.info("Step 2: Chunking text...")
        chunks = chunk_pages(pages)
        logger.info(f"  Created {len(chunks)} chunks")

        # Step 3: Generate embeddings
        logger.info("Step 3: Generating embeddings...")
        chunk_texts = [c["text"] for c in chunks]
        embeddings = embed_texts(chunk_texts)
        logger.info(f"  Generated {len(embeddings)} embeddings")

        # Step 4: Store in Qdrant
        logger.info("Step 4: Storing in Qdrant...")
        store_chunks(document_id, chunks, embeddings)

        # Done — update status
        update_status(
            document_id,
            DocumentStatus.READY,
            page_count=len(pages),
            chunk_count=len(chunks),
        )

        logger.info(f"PDF processing complete: {document_id} ({len(pages)} pages, {len(chunks)} chunks)")

    except Exception as e:
        logger.error(f"PDF processing failed: {document_id} — {e}")
        update_status(
            document_id,
            DocumentStatus.FAILED,
            error_message=str(e),
        )
        raise
