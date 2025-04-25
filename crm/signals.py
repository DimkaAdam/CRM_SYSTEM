from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Company, PipeLine

@receiver(post_save, sender=Company)
def add_company_to_pipeline(sender, instance, created, **kwargs):
    if created:  # Только если компания новая
        PipeLine.objects.create(company=instance, stage='new')
