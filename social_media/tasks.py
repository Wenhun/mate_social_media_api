from celery import shared_task
from django.utils import timezone
from .models import ScheduledPost


@shared_task
def publish_post_task(scheduled_id: int) -> None:
    if not scheduled_id:
        return
    try:
        scheduled = ScheduledPost.objects.get(pk=scheduled_id)
    except ScheduledPost.DoesNotExist:
        return

    if scheduled.status != ScheduledPost.StatusChoices.SCHEDULED:
        return

    scheduled.status = ScheduledPost.StatusChoices.PUBLISHED
    scheduled.save()
