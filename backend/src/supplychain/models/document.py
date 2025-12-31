from __future__ import annotations

import hashlib
import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .base import BaseModel


def document_upload_path(instance: "Document", filename: str) -> str:
    """Generate upload path for documents: documents/<entity_type>/<entity_id>/<uuid>_<filename>"""
    entity_type = instance.content_type.model if instance.content_type else "general"
    entity_id = instance.object_id or "0"
    unique_id = uuid.uuid4().hex[:8]
    return f"documents/{entity_type}/{entity_id}/{unique_id}_{filename}"


class Document(BaseModel):
    """
    Document model for storing files attached to products, batches, shipments, etc.
    Supports versioning and generic relations to any entity.
    """

    class Category(models.TextChoices):
        CERTIFICATE = "certificate", "Certificate"
        INVOICE = "invoice", "Invoice"
        PACKING_LIST = "packing_list", "Packing List"
        SHIPPING_LABEL = "shipping_label", "Shipping Label"
        COA = "coa", "Certificate of Analysis"
        MSDS = "msds", "Material Safety Data Sheet"
        QUALITY_REPORT = "quality_report", "Quality Report"
        PHOTO = "photo", "Photo"
        OTHER = "other", "Other"

    # Generic foreign key to link to any entity (Product, Batch, Shipment, Pack)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="The type of entity this document is attached to",
    )
    object_id = models.PositiveIntegerField(
        help_text="The ID of the entity this document is attached to"
    )
    content_object = GenericForeignKey("content_type", "object_id")

    # File storage
    file = models.FileField(
        upload_to=document_upload_path,
        help_text="The uploaded file",
    )

    # Metadata
    title = models.CharField(
        max_length=255,
        help_text="Document title",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Optional description of the document",
    )
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
        default=Category.OTHER,
        db_index=True,
        help_text="Document category",
    )

    # File info (stored for quick access without hitting storage)
    file_name = models.CharField(
        max_length=255,
        help_text="Original filename",
    )
    file_size = models.PositiveIntegerField(
        help_text="File size in bytes",
    )
    file_type = models.CharField(
        max_length=100,
        help_text="MIME type of the file",
    )
    file_hash = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="SHA-256 hash of file content for integrity verification",
    )

    # Versioning
    version_number = models.PositiveIntegerField(
        default=1,
        help_text="Version number of this document",
    )
    parent_document = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="versions",
        help_text="Parent document if this is a new version",
    )
    is_latest = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this is the latest version",
    )

    # Upload info
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_documents",
        help_text="User who uploaded the document",
    )

    class Meta:
        db_table = "supplychain_document"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["category"]),
            models.Index(fields=["is_latest"]),
            models.Index(fields=["uploaded_by"]),
        ]
        verbose_name = "Document"
        verbose_name_plural = "Documents"

    def __str__(self) -> str:
        return f"{self.title} (v{self.version_number})"

    def save(self, *args, **kwargs):
        # Auto-populate file metadata if file is provided
        if self.file and not self.file_name:
            self.file_name = self.file.name.split("/")[-1]
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    def compute_file_hash(self) -> str:
        """Compute SHA-256 hash of file content."""
        if not self.file:
            return ""
        sha256_hash = hashlib.sha256()
        self.file.seek(0)
        for chunk in iter(lambda: self.file.read(8192), b""):
            sha256_hash.update(chunk)
        self.file.seek(0)
        return sha256_hash.hexdigest()

    def create_new_version(self, file, uploaded_by=None, **kwargs) -> "Document":
        """Create a new version of this document."""
        # Mark current as not latest
        self.is_latest = False
        self.save(update_fields=["is_latest"])

        # Create new version
        new_doc = Document(
            content_type=self.content_type,
            object_id=self.object_id,
            file=file,
            title=kwargs.get("title", self.title),
            description=kwargs.get("description", self.description),
            category=self.category,
            file_name=file.name,
            file_size=file.size,
            file_type=kwargs.get("file_type", self.file_type),
            version_number=self.version_number + 1,
            parent_document=self,
            is_latest=True,
            uploaded_by=uploaded_by,
        )
        new_doc.save()
        return new_doc

    @property
    def entity_type(self) -> str:
        """Return the type of entity this document is attached to."""
        return self.content_type.model if self.content_type else ""

    @property
    def file_url(self) -> str:
        """Return the URL to access the file."""
        if self.file:
            return self.file.url
        return ""
