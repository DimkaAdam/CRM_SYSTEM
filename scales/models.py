from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


def business_day(dt):
    """
    Calculates business day from a datetime object.

    Business logic: Records belong to the calendar date they were created on.
    No adjustment needed since we're using natural calendar days.

    Args:
        dt: datetime object (timezone-aware or naive)

    Returns:
        date object representing the business day
    """
    if dt is None:
        dt = timezone.now()

    # If dt is timezone-aware, convert to local time
    if timezone.is_aware(dt):
        # Convert to local timezone
        dt = timezone.localtime(dt)

    # Return the date portion (no adjustment needed)
    return dt.date()


class ReceivedMaterial(models.Model):
    """
    Model for tracking received materials (Flexible Plastic, Mix Container, Baled Cardboard).

    Fields:
        date: Date when material was received (auto-set on creation)
        report_day: Business day for reporting purposes (calculated from created_at)
        material: Type of material (CB/SOP/OCC etc)
        gross_kg: Gross weight in kilograms
        net_kg: Net weight in kilograms
        supplier: Supplier name
        tag: Tag/reference number
        company_slug: Company identifier for multi-tenancy
        created_by: User who created the record
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    # Date when material was received
    date = models.DateField(auto_now_add=True)

    # Business day for reporting (indexed for performance)
    report_day = models.DateField(db_index=True, null=True, blank=True)

    # Material type (short name: CB, SOP, OCC, etc)
    material = models.CharField(max_length=64)  # Increased from 32 for longer names

    # Weights in kilograms
    gross_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,  # Changed from 1 to 2 for more precision
        help_text="Gross weight in kilograms"
    )
    net_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Net weight in kilograms"
    )

    # Supplier information
    supplier = models.CharField(max_length=100)  # Increased from 64

    # Tag/reference number
    tag = models.CharField(max_length=50)  # Increased from 32

    # Multi-tenancy: company identifier
    company_slug = models.SlugField(max_length=100, db_index=True)

    # Audit trail: who created this record
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_materials'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Received Material"
        verbose_name_plural = "Received Materials"
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['report_day', 'company_slug']),
            models.Index(fields=['company_slug', '-created_at']),
        ]

    def save(self, *args, **kwargs):
        """
        Override save to automatically set report_day based on created_at.

        Business logic:
        - If report_day is not set, calculate it from created_at (or current time for new objects)
        - Uses the calendar date without any cutoff adjustments
        """
        if not self.report_day:
            # For new objects (no pk yet), use current time
            # For existing objects being updated, use their original created_at
            if self.pk:
                # Object already exists, use its created_at
                dt = self.created_at if self.created_at else timezone.now()
            else:
                # New object, use current time
                dt = timezone.now()

            self.report_day = business_day(dt)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.report_day or self.date} {self.material} {self.net_kg}kg [{self.supplier}]"

    @property
    def gross(self):
        """Alias for gross_kg to maintain compatibility with frontend"""
        return self.gross_kg

    @property
    def net(self):
        """Alias for net_kg to maintain compatibility with frontend"""
        return self.net_kg