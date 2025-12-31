from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from django.http import FileResponse, HttpResponse
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import models as m
from .. import permissions as p
from ..models.document import Document
from ..serializers.document import (
    DocumentDetailSerializer,
    DocumentListSerializer,
    DocumentUploadSerializer,
    DocumentVersionSerializer,
)
from ..services.pdf_generator import PDFGeneratorService


class DocumentListCreateView(generics.ListCreateAPIView):
    """List all documents or upload a new document."""

    queryset = Document.objects.select_related(
        "content_type", "uploaded_by", "parent_document"
    ).all()
    permission_classes = [IsAuthenticated, p.RoleBasedCRUDPermission]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DocumentUploadSerializer
        return DocumentListSerializer

    def get_queryset(self):
        """Filter documents based on query parameters."""
        queryset = super().get_queryset()

        # Filter by entity type
        entity_type = self.request.query_params.get("entity_type", None)
        if entity_type:
            try:
                content_type = ContentType.objects.get(
                    app_label="supplychain", model=entity_type.lower()
                )
                queryset = queryset.filter(content_type=content_type)
            except ContentType.DoesNotExist:
                queryset = queryset.none()

        # Filter by entity ID
        entity_id = self.request.query_params.get("entity_id", None)
        if entity_id:
            queryset = queryset.filter(object_id=entity_id)

        # Filter by category
        category = self.request.query_params.get("category", None)
        if category:
            queryset = queryset.filter(category=category)

        # Filter by latest version only
        latest_only = self.request.query_params.get("latest_only", "true")
        if latest_only.lower() in {"true", "1", "yes"}:
            queryset = queryset.filter(is_latest=True)

        # Search by title or description
        search = self.request.query_params.get("search", None)
        if search:
            from django.db.models import Q

            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(file_name__icontains=search)
            )

        return queryset.order_by("-created_at")


class DocumentDetailView(generics.RetrieveAPIView):
    """Retrieve a specific document."""

    queryset = Document.objects.select_related(
        "content_type", "uploaded_by", "parent_document"
    ).all()
    serializer_class = DocumentDetailSerializer
    permission_classes = [IsAuthenticated, p.RoleBasedCRUDPermission]


class DocumentDeleteView(generics.DestroyAPIView):
    """Soft delete a document."""

    queryset = Document.objects.all()
    permission_classes = [IsAuthenticated, p.IsOperatorOrAdmin]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()  # Soft delete
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentDownloadView(APIView):
    """Download a document file."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if not document.file:
            return Response(
                {"error": "No file attached to this document"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Return signed URL for MinIO/S3
        return Response(
            {
                "download_url": document.file.url,
                "file_name": document.file_name,
                "file_type": document.file_type,
                "file_size": document.file_size,
            }
        )


class DocumentNewVersionView(APIView):
    """Upload a new version of an existing document."""

    permission_classes = [IsAuthenticated, p.IsOperatorOrAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = DocumentVersionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        file = serializer.validated_data["file"]
        new_doc = document.create_new_version(
            file=file,
            uploaded_by=request.user if request.user.is_authenticated else None,
            title=serializer.validated_data.get("title"),
            description=serializer.validated_data.get("description"),
            file_type=file.content_type,
        )

        # Compute and save file hash
        new_doc.file_hash = new_doc.compute_file_hash()
        new_doc.save(update_fields=["file_hash"])

        return Response(
            DocumentDetailSerializer(new_doc).data, status=status.HTTP_201_CREATED
        )


class EntityDocumentsView(APIView):
    """Get all documents for a specific entity (product, batch, shipment, pack)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, entity_type, entity_id):
        try:
            content_type = ContentType.objects.get(
                app_label="supplychain", model=entity_type.lower()
            )
        except ContentType.DoesNotExist:
            return Response(
                {"error": f"Invalid entity type: {entity_type}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if entity exists
        model_class = content_type.model_class()
        if not model_class.objects.filter(pk=entity_id).exists():
            return Response(
                {"error": f"{entity_type.title()} with id {entity_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get documents
        documents = Document.objects.filter(
            content_type=content_type, object_id=entity_id, is_latest=True
        ).select_related("uploaded_by")

        # Filter by category if provided
        category = request.query_params.get("category", None)
        if category:
            documents = documents.filter(category=category)

        serializer = DocumentListSerializer(documents, many=True)
        return Response(serializer.data)


class ShipmentGenerateLabelView(APIView):
    """Generate a shipping label PDF for a shipment."""

    permission_classes = [IsAuthenticated, p.IsOperatorOrAdmin]

    def post(self, request, pk):
        try:
            shipment = m.Shipment.objects.get(pk=pk)
        except m.Shipment.DoesNotExist:
            return Response(
                {"error": "Shipment not found"}, status=status.HTTP_404_NOT_FOUND
            )

        save_as_document = request.query_params.get("save", "true").lower() in {
            "true",
            "1",
            "yes",
        }

        result = PDFGeneratorService.generate_shipping_label(
            shipment, save_as_document=save_as_document
        )

        if save_as_document:
            return Response(
                DocumentDetailSerializer(result).data, status=status.HTTP_201_CREATED
            )
        else:
            response = HttpResponse(result, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="shipping_label_{shipment.tracking_number}.pdf"'
            )
            return response


class ShipmentGeneratePackingListView(APIView):
    """Generate a packing list PDF for a shipment."""

    permission_classes = [IsAuthenticated, p.IsOperatorOrAdmin]

    def post(self, request, pk):
        try:
            shipment = m.Shipment.objects.prefetch_related(
                "shipment_packs__pack__batch__product"
            ).get(pk=pk)
        except m.Shipment.DoesNotExist:
            return Response(
                {"error": "Shipment not found"}, status=status.HTTP_404_NOT_FOUND
            )

        save_as_document = request.query_params.get("save", "true").lower() in {
            "true",
            "1",
            "yes",
        }

        result = PDFGeneratorService.generate_packing_list(
            shipment, save_as_document=save_as_document
        )

        if save_as_document:
            return Response(
                DocumentDetailSerializer(result).data, status=status.HTTP_201_CREATED
            )
        else:
            response = HttpResponse(result, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="packing_list_{shipment.tracking_number}.pdf"'
            )
            return response


class BatchGenerateCoaView(APIView):
    """Generate a Certificate of Analysis (CoA) PDF for a batch."""

    permission_classes = [IsAuthenticated, p.IsOperatorOrAdmin]

    def post(self, request, pk):
        try:
            batch = m.Batch.objects.select_related("product").get(pk=pk)
        except m.Batch.DoesNotExist:
            return Response(
                {"error": "Batch not found"}, status=status.HTTP_404_NOT_FOUND
            )

        save_as_document = request.query_params.get("save", "true").lower() in {
            "true",
            "1",
            "yes",
        }

        result = PDFGeneratorService.generate_coa(batch, save_as_document=save_as_document)

        if save_as_document:
            return Response(
                DocumentDetailSerializer(result).data, status=status.HTTP_201_CREATED
            )
        else:
            response = HttpResponse(result, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="coa_{batch.lot_number}.pdf"'
            )
            return response
