import enum
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DocumentStatus(str, enum.Enum):
    """
    Why enum instead of just a string?
    - DB enforces only these values (can't accidentally set status="reday")
    - Code gets autocomplete: DocumentStatus.PROCESSING
    - str inheritance lets it serialize to JSON automatically
    """
    UPLOADING = "uploading"      # file saved, not yet processed
    PROCESSING = "processing"    # Celery worker is working on it
    READY = "ready"              # chunks embedded and stored in Qdrant
    FAILED = "failed"            # something went wrong


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Which user uploaded this — FK to users table
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),  # delete user → delete their docs
        nullable=False,
        index=True,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Status tracking — frontend polls this
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus),
        default=DocumentStatus.UPLOADING,
        nullable=False,
    )

    # Error message if processing failed
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Set after processing completes
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
