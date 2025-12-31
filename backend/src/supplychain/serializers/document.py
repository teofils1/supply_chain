from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from ..models.document import Document


class DocumentListSerializer(serializers.ModelSerializer):
    """Serializer for document list views - minimal fields."""

    entity_type = serializers.CharField(read_only=True)
    file_url = serializers.CharField(read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "category",
            "file_name",
            "file_size",
            "file_type",
            "file_url",
            "entity_type",
            "object_id",
            "version_number",
            "is_latest",
            "uploaded_by_name",
            "created_at",
        ]

    def get_uploaded_by_name(self, obj) -> str:
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
        return ""


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Serializer for document detail views - all fields."""

    entity_type = serializers.CharField(read_only=True)
    file_url = serializers.CharField(read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()
    versions = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "description",
            "category",
            "file_name",
            "file_size",
            "file_type",
            "file_hash",
            "file_url",
            "entity_type",
            "object_id",
            "version_number",
            "is_latest",
            "parent_document",
            "uploaded_by",
            "uploaded_by_name",
            "created_at",
            "updated_at",
            "versions",
        ]

    def get_uploaded_by_name(self, obj) -> str:
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
        return ""

    def get_versions(self, obj) -> list:
        """Get all versions of this document."""
        # Find root document
        root = obj
        while root.parent_document:
            root = root.parent_document

        # Get all versions including root
        all_versions = [root]
        all_versions.extend(
            Document.objects.filter(parent_document=root).order_by("version_number")
        )

        # Also get nested versions
        def get_child_versions(doc):
            children = Document.objects.filter(parent_document=doc).order_by(
                "version_number"
            )
            for child in children:
                if child not in all_versions:
                    all_versions.append(child)
                    get_child_versions(child)

        get_child_versions(root)

        return [
            {
                "id": v.id,
                "version_number": v.version_number,
                "is_latest": v.is_latest,
                "created_at": v.created_at,
            }
            for v in sorted(all_versions, key=lambda x: x.version_number)
        ]


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading new documents."""

    entity_type = serializers.CharField(write_only=True)
    entity_id = serializers.IntegerField(write_only=True)
    file = serializers.FileField()

    class Meta:
        model = Document
        fields = [
            "file",
            "title",
            "description",
            "category",
            "entity_type",
            "entity_id",
        ]

    def validate_entity_type(self, value):
        """Validate that entity_type is a valid model."""
        allowed_types = ["product", "batch", "pack", "shipment"]
        if value.lower() not in allowed_types:
            raise serializers.ValidationError(
                f"entity_type must be one of: {', '.join(allowed_types)}"
            )
        return value.lower()

    def validate_file(self, value):
        """Validate file size and type."""
        max_size = getattr(settings, "MAX_UPLOAD_SIZE", 50 * 1024 * 1024)
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size exceeds maximum allowed ({max_size // (1024*1024)}MB)"
            )

        allowed_types = getattr(
            settings,
            "ALLOWED_DOCUMENT_TYPES",
            [
                "application/pdf",
                "image/png",
                "image/jpeg",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ],
        )
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                f"File type '{value.content_type}' is not allowed. "
                f"Allowed types: {', '.join(allowed_types)}"
            )

        return value

    def validate(self, data):
        """Validate that the referenced entity exists."""
        entity_type = data["entity_type"]
        entity_id = data["entity_id"]

        # Get content type
        try:
            content_type = ContentType.objects.get(
                app_label="supplychain", model=entity_type
            )
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(
                {"entity_type": f"Invalid entity type: {entity_type}"}
            )

        # Check if entity exists
        model_class = content_type.model_class()
        if not model_class.objects.filter(pk=entity_id).exists():
            raise serializers.ValidationError(
                {"entity_id": f"{entity_type.title()} with id {entity_id} does not exist"}
            )

        data["content_type"] = content_type
        return data

    def create(self, validated_data):
        """Create document with file metadata."""
        file = validated_data["file"]
        content_type = validated_data.pop("content_type")
        entity_id = validated_data.pop("entity_id")
        validated_data.pop("entity_type")

        # Get current user from request
        request = self.context.get("request")
        uploaded_by = request.user if request and request.user.is_authenticated else None

        document = Document(
            content_type=content_type,
            object_id=entity_id,
            file=file,
            title=validated_data.get("title", file.name),
            description=validated_data.get("description", ""),
            category=validated_data.get("category", Document.Category.OTHER),
            file_name=file.name,
            file_size=file.size,
            file_type=file.content_type,
            uploaded_by=uploaded_by,
        )
        # Compute file hash
        document.file_hash = document.compute_file_hash()
        document.save()
        return document


class DocumentVersionSerializer(serializers.Serializer):
    """Serializer for creating a new version of a document."""

    file = serializers.FileField()
    title = serializers.CharField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate_file(self, value):
        """Validate file size and type."""
        max_size = getattr(settings, "MAX_UPLOAD_SIZE", 50 * 1024 * 1024)
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size exceeds maximum allowed ({max_size // (1024*1024)}MB)"
            )
        return value
