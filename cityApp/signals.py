from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import ComplaintsTable, Notification

@receiver(pre_save, sender=ComplaintsTable)
def complaint_status_changed(sender, instance, **kwargs):
    """
    Signal to create a Notification when the Status of a Complaint changes.
    """
    if instance.pk:  # Check if this is an update (not creation)
        try:
            previous_complaint = ComplaintsTable.objects.get(pk=instance.pk)
            if previous_complaint.Status != instance.Status:
                # Status has changed, create a notification
                Notification.objects.create(ComplaintsId=instance)
        except ComplaintsTable.DoesNotExist:
            pass
