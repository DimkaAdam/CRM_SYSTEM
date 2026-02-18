# -----------------------------
# EXPORT MODELS (standalone)
# -----------------------------
import os
from django.db import models  # ORM
from django.conf import settings  # AUTH_USER_MODEL / settings
from django.utils.text import slugify  # safe folder names
import uuid  # stable folder id


class ExportLane(models.Model):
    name = models.CharField(max_length=120)
    timezone = models.CharField(max_length=64, default="America/Vancouver")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name  # lane label


class VesselSchedule(models.Model):
    lane = models.ForeignKey(
        ExportLane,
        on_delete=models.PROTECT,
        related_name="schedules",
    )  # schedule belongs to lane

    bkg_number = models.CharField(max_length=64)  # booking number
    vessel = models.CharField(max_length=128)  # vessel name

    doc_cutoff_at = models.DateTimeField(null=True, blank=True)  # DOC C/O
    erd_at = models.DateTimeField(null=True, blank=True)  # ERD
    cargo_cutoff_at = models.DateTimeField(null=True, blank=True)  # Cargo C/O

    notes = models.TextField(blank=True, default="")  # optional notes
    is_active = models.BooleanField(default=True)  # archive switch

    created_at = models.DateTimeField(auto_now_add=True)  # created timestamp
    updated_at = models.DateTimeField(auto_now=True)  # updated timestamp

    class Meta:
        ordering = ["lane__name", "doc_cutoff_at", "erd_at", "cargo_cutoff_at"]  # table ordering

    def __str__(self):
        return f"{self.lane.name} | {self.bkg_number} | {self.vessel}"  # readable row


def export_document_upload_to(instance, filename):
    shipment = instance.export_shipment  # parent shipment
    folder = f"ship_{shipment.folder_uid}"  # stable UUID folder
    doc_type_slug = slugify(instance.doc_type)[:40] or "docs"  # doc type folder
    return f"exports/{folder}/{doc_type_slug}/{filename}"  # MEDIA_ROOT relative path


class ExportShipment(models.Model):
    # Mode choices
    MODE_TRUCK = "truck"
    MODE_RAIL = "rail"
    MODE_OCEAN = "ocean"
    MODE_AIR = "air"
    MODE_COURIER = "courier"

    MODE_CHOICES = [
        (MODE_TRUCK, "Truck"),
        (MODE_RAIL, "Rail"),
        (MODE_OCEAN, "Ocean"),
        (MODE_AIR, "Air"),
        (MODE_COURIER, "Courier"),
    ]

    # Status choices
    STATUS_DRAFT = "draft"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_READY = "ready"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CLOSED = "closed"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_READY, "Ready"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CLOSED, "Closed"),
    ]

    folder_uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)  # stable folder key

    date = models.DateField(null=True, blank=True)  # table "Date"

    lane = models.ForeignKey(
        ExportLane,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shipments",
    )  # Vancouver/Toronto

    schedule = models.ForeignKey(
        VesselSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shipments",
    )  # selected schedule row


    hs_code = models.CharField(max_length=32, blank=True, default="")  # table "HS Code"

    mode = models.CharField(max_length=16, choices=MODE_CHOICES, default=MODE_OCEAN)  # table "Mode"
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)  # table "Status"

    export_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # table "Export Price"
    export_currency = models.CharField(max_length=10, default="USD")  # currency label

    etd = models.DateField(null=True, blank=True)  # optional planning
    eta = models.DateField(null=True, blank=True)  # optional planning

    container_number = models.CharField(max_length=32, blank=True, default="")  # optional
    seal_number = models.CharField(max_length=32, blank=True, default="")  # optional

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )  # audit

    created_at = models.DateTimeField(auto_now_add=True)  # audit
    updated_at = models.DateTimeField(auto_now=True)  # audit

    class Meta:
        ordering = ["-created_at"]  # newest first

    def __str__(self):
        return f"Shipment #{self.id} | {self.get_status_display()}"  # label


class ExportDocument(models.Model):
    DOC_COMMERCIAL_INVOICE = "commercial_invoice"
    DOC_PACKING_LIST = "packing_list"
    DOC_BILL_OF_LADING = "bill_of_lading"
    DOC_CUSTOMS = "customs_docs"
    DOC_OTHER = "other"

    DOC_TYPE_CHOICES = [
        (DOC_COMMERCIAL_INVOICE, "Commercial Invoice"),
        (DOC_PACKING_LIST, "Packing List"),
        (DOC_BILL_OF_LADING, "Bill of Lading (BOL)"),
        (DOC_CUSTOMS, "Customs / Broker Docs"),
        (DOC_OTHER, "Other"),
    ]

    export_shipment = models.ForeignKey(
        ExportShipment,
        on_delete=models.CASCADE,
        related_name="documents",
    )  # parent shipment

    doc_type = models.CharField(max_length=32, choices=DOC_TYPE_CHOICES, default=DOC_OTHER)  # doc category
    file = models.FileField(upload_to=export_document_upload_to)  # stored in stable folder

    deadline = models.DateTimeField(null=True, blank=True)  # optional for reminders
    notes = models.TextField(blank=True, default="")  # notes

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )  # audit

    uploaded_at = models.DateTimeField(auto_now_add=True)  # audit

    class Meta:
        ordering = ["-uploaded_at"]  # newest file first

    def __str__(self):
        return f"{self.export_shipment_id} | {self.get_doc_type_display()}"  # label


class ExportDocRequirement(models.Model):
    mode = models.CharField(max_length=16, choices=ExportShipment.MODE_CHOICES)  # mode
    doc_type = models.CharField(max_length=32, choices=ExportDocument.DOC_TYPE_CHOICES)  # doc type
    is_required = models.BooleanField(default=True)  # requirement flag

    class Meta:
        unique_together = ("mode", "doc_type")  # one row per (mode, doc_type)

    def __str__(self):
        return f"{self.mode}: {self.doc_type} required={self.is_required}"  # label


def export_doc_path(instance, filename):
    export = instance.export
    lane = slugify(export.lane.name) if export.lane else "no-lane"
    bkg = slugify(export.bkg_number) if getattr(export, "bkg_number", "") else f"export-{export.id}"
    return os.path.join("exports", lane, bkg, filename)


class ExportShipmentDocument(models.Model):
    export = models.ForeignKey(
        "ExportShipment",
        related_name="shipment_documents",
        on_delete=models.CASCADE,
    )
    file = models.FileField(upload_to=export_doc_path)
    doc_type = models.CharField(max_length=50, blank=True, default="other")
    uploaded_at = models.DateTimeField(auto_now_add=True)