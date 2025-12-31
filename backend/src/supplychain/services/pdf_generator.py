from __future__ import annotations

import io
from datetime import datetime
from typing import TYPE_CHECKING

from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.template import engines
from weasyprint import HTML

from ..models.document import Document

if TYPE_CHECKING:
    from ..models import Batch, Shipment


class PDFGeneratorService:
    """Service for generating PDF documents (shipping labels, packing lists, CoAs)."""

    @staticmethod
    def _render_template(template_string: str, context: dict) -> str:
        """Render a Django template string with context."""
        django_engine = engines["django"]
        template = django_engine.from_string(template_string)
        return template.render(context)

    @staticmethod
    def _generate_pdf(html_content: str) -> bytes:
        """Convert HTML to PDF using WeasyPrint."""
        html = HTML(string=html_content)
        pdf_buffer = io.BytesIO()
        html.write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        return pdf_buffer.read()

    @classmethod
    def generate_shipping_label(
        cls, shipment: "Shipment", save_as_document: bool = True
    ) -> bytes | Document:
        """
        Generate a shipping label PDF for a shipment.

        Args:
            shipment: The Shipment instance
            save_as_document: If True, save as a Document attached to the shipment

        Returns:
            PDF bytes or Document instance
        """
        html_content = cls._render_template(
            SHIPPING_LABEL_TEMPLATE,
            {
                "shipment": shipment,
                "generated_at": datetime.now(),
            },
        )
        pdf_bytes = cls._generate_pdf(html_content)

        if save_as_document:
            return cls._save_as_document(
                pdf_bytes=pdf_bytes,
                entity=shipment,
                title=f"Shipping Label - {shipment.tracking_number}",
                category=Document.Category.SHIPPING_LABEL,
                file_name=f"shipping_label_{shipment.tracking_number}.pdf",
            )
        return pdf_bytes

    @classmethod
    def generate_packing_list(
        cls, shipment: "Shipment", save_as_document: bool = True
    ) -> bytes | Document:
        """
        Generate a packing list PDF for a shipment.

        Args:
            shipment: The Shipment instance
            save_as_document: If True, save as a Document attached to the shipment

        Returns:
            PDF bytes or Document instance
        """
        # Get all packs in the shipment with related data
        shipment_packs = shipment.shipment_packs.select_related(
            "pack__batch__product"
        ).all()

        html_content = cls._render_template(
            PACKING_LIST_TEMPLATE,
            {
                "shipment": shipment,
                "shipment_packs": shipment_packs,
                "generated_at": datetime.now(),
                "total_packs": shipment_packs.count(),
            },
        )
        pdf_bytes = cls._generate_pdf(html_content)

        if save_as_document:
            return cls._save_as_document(
                pdf_bytes=pdf_bytes,
                entity=shipment,
                title=f"Packing List - {shipment.tracking_number}",
                category=Document.Category.PACKING_LIST,
                file_name=f"packing_list_{shipment.tracking_number}.pdf",
            )
        return pdf_bytes

    @classmethod
    def generate_coa(
        cls, batch: "Batch", save_as_document: bool = True
    ) -> bytes | Document:
        """
        Generate a Certificate of Analysis (CoA) PDF for a batch.

        Args:
            batch: The Batch instance
            save_as_document: If True, save as a Document attached to the batch

        Returns:
            PDF bytes or Document instance
        """
        html_content = cls._render_template(
            COA_TEMPLATE,
            {
                "batch": batch,
                "product": batch.product,
                "generated_at": datetime.now(),
            },
        )
        pdf_bytes = cls._generate_pdf(html_content)

        if save_as_document:
            return cls._save_as_document(
                pdf_bytes=pdf_bytes,
                entity=batch,
                title=f"Certificate of Analysis - {batch.lot_number}",
                category=Document.Category.COA,
                file_name=f"coa_{batch.lot_number}.pdf",
            )
        return pdf_bytes

    @staticmethod
    def _save_as_document(
        pdf_bytes: bytes,
        entity,
        title: str,
        category: str,
        file_name: str,
    ) -> Document:
        """Save PDF bytes as a Document attached to an entity."""
        content_type = ContentType.objects.get_for_model(entity)

        # Create file from bytes
        pdf_file = ContentFile(pdf_bytes, name=file_name)

        document = Document(
            content_type=content_type,
            object_id=entity.pk,
            file=pdf_file,
            title=title,
            category=category,
            file_name=file_name,
            file_size=len(pdf_bytes),
            file_type="application/pdf",
        )
        document.save()
        return document


# HTML Templates for PDF generation
SHIPPING_LABEL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        @page { size: 4in 6in; margin: 0.25in; }
        body { font-family: Arial, sans-serif; font-size: 10pt; margin: 0; padding: 10px; }
        .header { text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 10px; }
        .header h1 { margin: 0; font-size: 14pt; }
        .section { margin-bottom: 15px; }
        .section-title { font-weight: bold; font-size: 9pt; color: #666; margin-bottom: 5px; text-transform: uppercase; }
        .address { line-height: 1.4; }
        .address-name { font-weight: bold; font-size: 12pt; }
        .barcode { text-align: center; margin: 15px 0; font-family: monospace; font-size: 14pt; letter-spacing: 2px; }
        .tracking { text-align: center; font-size: 16pt; font-weight: bold; margin: 10px 0; }
        .info-row { display: flex; justify-content: space-between; margin-bottom: 5px; }
        .info-label { color: #666; }
        .footer { border-top: 1px solid #ccc; padding-top: 10px; font-size: 8pt; color: #666; text-align: center; }
    </style>
</head>
<body>
    <div class="header">
        <h1>SHIPPING LABEL</h1>
    </div>

    <div class="section">
        <div class="section-title">From</div>
        <div class="address">
            <div class="address-name">{{ shipment.origin_name }}</div>
            <div>{{ shipment.origin_address }}</div>
            <div>{{ shipment.origin_city }}, {{ shipment.origin_state }} {{ shipment.origin_postal_code }}</div>
            <div>{{ shipment.origin_country }}</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">To</div>
        <div class="address">
            <div class="address-name">{{ shipment.destination_name }}</div>
            <div>{{ shipment.destination_address }}</div>
            <div>{{ shipment.destination_city }}, {{ shipment.destination_state }} {{ shipment.destination_postal_code }}</div>
            <div>{{ shipment.destination_country }}</div>
        </div>
    </div>

    <div class="tracking">
        {{ shipment.tracking_number }}
    </div>

    <div class="section">
        <div class="info-row">
            <span class="info-label">Carrier:</span>
            <span>{{ shipment.carrier|default:"N/A" }}</span>
        </div>
        <div class="info-row">
            <span class="info-label">Service:</span>
            <span>{{ shipment.get_service_type_display|default:"Standard" }}</span>
        </div>
        <div class="info-row">
            <span class="info-label">Weight:</span>
            <span>{{ shipment.total_weight|default:"N/A" }} {{ shipment.weight_unit|default:"kg" }}</span>
        </div>
        {% if shipment.temperature_requirement %}
        <div class="info-row">
            <span class="info-label">Temp Req:</span>
            <span>{{ shipment.get_temperature_requirement_display }}</span>
        </div>
        {% endif %}
    </div>

    <div class="footer">
        Generated: {{ generated_at|date:"Y-m-d H:i" }} | Status: {{ shipment.get_status_display }}
    </div>
</body>
</html>
"""

PACKING_LIST_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        @page { size: A4; margin: 1cm; }
        body { font-family: Arial, sans-serif; font-size: 10pt; }
        .header { text-align: center; border-bottom: 2px solid #000; padding-bottom: 15px; margin-bottom: 20px; }
        .header h1 { margin: 0; font-size: 18pt; }
        .header-info { margin-top: 10px; font-size: 11pt; }
        .section { margin-bottom: 20px; }
        .section-title { font-weight: bold; font-size: 12pt; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-bottom: 10px; }
        .address-grid { display: flex; justify-content: space-between; }
        .address-box { width: 45%; padding: 10px; border: 1px solid #ddd; }
        .address-box h3 { margin: 0 0 10px 0; font-size: 10pt; color: #666; text-transform: uppercase; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f5f5f5; font-weight: bold; }
        .totals { margin-top: 15px; text-align: right; }
        .footer { margin-top: 30px; padding-top: 15px; border-top: 1px solid #ccc; font-size: 9pt; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>PACKING LIST</h1>
        <div class="header-info">
            <strong>Tracking #:</strong> {{ shipment.tracking_number }}
            | <strong>Date:</strong> {{ shipment.shipped_at|date:"Y-m-d"|default:"Pending" }}
        </div>
    </div>

    <div class="section">
        <div class="address-grid">
            <div class="address-box">
                <h3>Ship From</h3>
                <strong>{{ shipment.origin_name }}</strong><br>
                {{ shipment.origin_address }}<br>
                {{ shipment.origin_city }}, {{ shipment.origin_state }} {{ shipment.origin_postal_code }}<br>
                {{ shipment.origin_country }}
            </div>
            <div class="address-box">
                <h3>Ship To</h3>
                <strong>{{ shipment.destination_name }}</strong><br>
                {{ shipment.destination_address }}<br>
                {{ shipment.destination_city }}, {{ shipment.destination_state }} {{ shipment.destination_postal_code }}<br>
                {{ shipment.destination_country }}
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Contents ({{ total_packs }} items)</div>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Product</th>
                    <th>Lot Number</th>
                    <th>Serial Number</th>
                    <th>Pack Type</th>
                    <th>Quantity</th>
                </tr>
            </thead>
            <tbody>
                {% for sp in shipment_packs %}
                <tr>
                    <td>{{ forloop.counter }}</td>
                    <td>{{ sp.pack.batch.product.name }}</td>
                    <td>{{ sp.pack.batch.lot_number }}</td>
                    <td>{{ sp.pack.serial_number }}</td>
                    <td>{{ sp.pack.get_pack_type_display }}</td>
                    <td>{{ sp.quantity }}</td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="6" style="text-align: center;">No items in shipment</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="section">
        <div class="section-title">Shipment Details</div>
        <table>
            <tr>
                <th>Carrier</th>
                <td>{{ shipment.carrier|default:"N/A" }}</td>
                <th>Service Type</th>
                <td>{{ shipment.get_service_type_display|default:"Standard" }}</td>
            </tr>
            <tr>
                <th>Total Weight</th>
                <td>{{ shipment.total_weight|default:"N/A" }} {{ shipment.weight_unit|default:"kg" }}</td>
                <th>Status</th>
                <td>{{ shipment.get_status_display }}</td>
            </tr>
            {% if shipment.temperature_requirement %}
            <tr>
                <th>Temperature Requirement</th>
                <td colspan="3">{{ shipment.get_temperature_requirement_display }}</td>
            </tr>
            {% endif %}
        </table>
    </div>

    <div class="footer">
        <p>Document generated: {{ generated_at|date:"Y-m-d H:i:s" }}</p>
        <p>This packing list is for informational purposes. Please verify contents upon receipt.</p>
    </div>
</body>
</html>
"""

COA_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        @page { size: A4; margin: 1.5cm; }
        body { font-family: Arial, sans-serif; font-size: 11pt; }
        .header { text-align: center; border-bottom: 3px double #000; padding-bottom: 20px; margin-bottom: 25px; }
        .header h1 { margin: 0; font-size: 22pt; letter-spacing: 2px; }
        .header h2 { margin: 10px 0 0 0; font-size: 14pt; color: #666; font-weight: normal; }
        .section { margin-bottom: 25px; }
        .section-title { font-weight: bold; font-size: 13pt; border-bottom: 2px solid #333; padding-bottom: 5px; margin-bottom: 15px; }
        .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .info-row { display: flex; margin-bottom: 8px; }
        .info-label { width: 150px; font-weight: bold; color: #555; }
        .info-value { flex: 1; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #999; padding: 10px; text-align: left; }
        th { background-color: #f0f0f0; font-weight: bold; }
        .status-badge { display: inline-block; padding: 3px 10px; border-radius: 3px; font-size: 10pt; }
        .status-released { background: #d4edda; color: #155724; }
        .status-quarantined { background: #fff3cd; color: #856404; }
        .status-expired { background: #f8d7da; color: #721c24; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccc; }
        .signature-line { margin-top: 50px; display: flex; justify-content: space-between; }
        .signature-box { width: 40%; text-align: center; }
        .signature-box .line { border-top: 1px solid #000; margin-top: 50px; padding-top: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>CERTIFICATE OF ANALYSIS</h1>
        <h2>{{ product.name }}</h2>
    </div>

    <div class="section">
        <div class="section-title">Product Information</div>
        <div class="info-grid">
            <div>
                <div class="info-row">
                    <span class="info-label">Product Name:</span>
                    <span class="info-value">{{ product.name }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">GTIN:</span>
                    <span class="info-value">{{ product.gtin }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Dosage Form:</span>
                    <span class="info-value">{{ product.get_dosage_form_display|default:"N/A" }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Strength:</span>
                    <span class="info-value">{{ product.strength|default:"N/A" }}</span>
                </div>
            </div>
            <div>
                <div class="info-row">
                    <span class="info-label">Manufacturer:</span>
                    <span class="info-value">{{ product.manufacturer|default:"N/A" }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">NDC Number:</span>
                    <span class="info-value">{{ product.ndc_number|default:"N/A" }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Storage Temp:</span>
                    <span class="info-value">
                        {% if product.min_storage_temp and product.max_storage_temp %}
                            {{ product.min_storage_temp }}°C to {{ product.max_storage_temp }}°C
                        {% else %}
                            N/A
                        {% endif %}
                    </span>
                </div>
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Batch Information</div>
        <div class="info-grid">
            <div>
                <div class="info-row">
                    <span class="info-label">Lot Number:</span>
                    <span class="info-value"><strong>{{ batch.lot_number }}</strong></span>
                </div>
                <div class="info-row">
                    <span class="info-label">Manufacturing Date:</span>
                    <span class="info-value">{{ batch.manufacturing_date|date:"Y-m-d" }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Expiry Date:</span>
                    <span class="info-value">{{ batch.expiry_date|date:"Y-m-d" }}</span>
                </div>
            </div>
            <div>
                <div class="info-row">
                    <span class="info-label">Quantity Produced:</span>
                    <span class="info-value">{{ batch.quantity_produced }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Status:</span>
                    <span class="info-value">
                        <span class="status-badge status-{{ batch.status }}">{{ batch.get_status_display }}</span>
                    </span>
                </div>
                <div class="info-row">
                    <span class="info-label">QA Approved:</span>
                    <span class="info-value">{% if batch.qa_approved %}Yes{% else %}No{% endif %}</span>
                </div>
            </div>
        </div>
    </div>

    {% if batch.manufacturing_site or batch.storage_location %}
    <div class="section">
        <div class="section-title">Location Details</div>
        <div class="info-row">
            <span class="info-label">Manufacturing Site:</span>
            <span class="info-value">{{ batch.manufacturing_site|default:"N/A" }}</span>
        </div>
        <div class="info-row">
            <span class="info-label">Storage Location:</span>
            <span class="info-value">{{ batch.storage_location|default:"N/A" }}</span>
        </div>
    </div>
    {% endif %}

    {% if batch.notes %}
    <div class="section">
        <div class="section-title">Notes</div>
        <p>{{ batch.notes }}</p>
    </div>
    {% endif %}

    <div class="footer">
        <p><strong>Certification Statement:</strong></p>
        <p>This is to certify that the above batch has been manufactured and tested in accordance with 
        applicable quality standards and specifications. The batch meets all quality requirements 
        and is approved for {% if batch.qa_approved %}release{% else %}further review{% endif %}.</p>

        <div class="signature-line">
            <div class="signature-box">
                <div class="line">Quality Assurance Manager</div>
            </div>
            <div class="signature-box">
                <div class="line">Date</div>
            </div>
        </div>

        <p style="margin-top: 30px; font-size: 9pt; color: #666; text-align: center;">
            Document generated: {{ generated_at|date:"Y-m-d H:i:s" }}
        </p>
    </div>
</body>
</html>
"""
