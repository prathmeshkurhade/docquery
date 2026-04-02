import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services.vector_store import delete_document_chunks
from app.utils.deps import get_current_user, get_db
from app.workers.pdf_pipeline import process_pdf

router = APIRouter(prefix="/documents", tags=["documents"])

# Where PDFs get saved on disk
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a PDF file.

    Flow:
    1. Validate it's a PDF
    2. Save file to disk as {document_id}.pdf
    3. Create DB row with status=UPLOADING
    4. (Later: trigger Celery task to process it)
    5. Return document info

    The file is saved with the document's UUID as filename, not the original name.
    Why? Avoids filename collisions and path traversal attacks.
    Original filename is stored in the DB for display purposes.
    """
    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    # Create document record first (to get the UUID)
    doc = Document(
        user_id=user.id,
        filename=file.filename or "untitled.pdf",
        status=DocumentStatus.UPLOADING,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Save file to disk: uploads/{doc_id}.pdf
    file_path = UPLOAD_DIR / f"{doc.id}.pdf"
    content = await file.read()
    file_path.write_bytes(content)

    # Trigger Celery task to process the PDF in background
    # .delay() sends the task message to Redis → worker picks it up
    process_pdf.delay(str(doc.id), str(file_path))

    return doc


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documents for the current user, newest first."""
    result = await db.execute(
        select(Document)
        .where(Document.user_id == user.id)
        .order_by(Document.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single document by ID.
    Frontend polls this to check processing status.
    """
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == user.id,  # can only see your own docs
        )
    )
    doc = result.scalar_one_or_none()

    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document — removes DB row, PDF file, and Qdrant vectors."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == user.id,
        )
    )
    doc = result.scalar_one_or_none()

    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Delete vectors from Qdrant
    delete_document_chunks(str(doc.id))

    # Delete PDF file from disk
    file_path = UPLOAD_DIR / f"{doc.id}.pdf"
    if file_path.exists():
        file_path.unlink()

    # Delete DB row
    await db.delete(doc)
    await db.commit()
