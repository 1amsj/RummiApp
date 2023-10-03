from datetime import timedelta

from django.core.management import BaseCommand
from django.utils import timezone

from core_api.constants import CONCORD_DEBUG_JOB_PREFIX, CONCORD_EXPECTED_SEND_WAIT_THRESHOLD_IN_DAYS
from core_backend.models import Notification
from core_backend.services.concord.concord_interfaces import FaxStatusCode
from core_backend.services.concord.concord_service import ConcordService
from core_backend.settings import CONCORD_DEBUG


def check_faxes(job_ids, fax_service: ConcordService):
    return fax_service.get_fax_status(job_ids)


class Command(BaseCommand):
    help = 'Check the status of submitted notifications'

    def handle_fax(self):
        threshold_for_wait = timezone.now() - timedelta(days=CONCORD_EXPECTED_SEND_WAIT_THRESHOLD_IN_DAYS)

        notification_queryset = (
            Notification.objects
            .filter(
                send_method=Notification.SendMethod.FAX,
                status=Notification.Status.SUBMITTED,
                expected_send_at__lte=threshold_for_wait,
                job_id__isnull=False,
            )
            .order_by('expected_send_at')
        )

        if CONCORD_DEBUG:
            notification_queryset = notification_queryset.filter(job_id__startswith=CONCORD_DEBUG_JOB_PREFIX)

        else:
            notification_queryset = notification_queryset.exclude(job_id__startswith=CONCORD_DEBUG_JOB_PREFIX)

        fax_job_ids = notification_queryset.values_list('job_id', flat=True)

        if not fax_job_ids:
            self.stdout.write(self.style.SUCCESS('No faxes to check'))
            return

        try:
            fax_service = ConcordService()
            fax_job_statuses = check_faxes(fax_job_ids, fax_service)

        except Exception as e:
            self.stdout.write(F"Failed to check fax status due to error: {e}")
            return

        for fax_job_status in fax_job_statuses:
            job_id = fax_job_status.job_id
            status = fax_job_status.status_code

            if status == FaxStatusCode.IN_PROGRESS:
                continue

            notification = Notification.objects.get(job_id=job_id, send_method=Notification.SendMethod.FAX)
            notification.status = (
                Notification.Status.SENT
                if status in (FaxStatusCode.SUCCESS, FaxStatusCode.DEBUG)
                else Notification.Status.FAILED
            )
            notification.status_message = fax_job_status.status_message
            notification.sent_at = timezone.now()  # Notice that this is not the actual time of sending
            notification.save()

        self.stdout.write(self.style.SUCCESS('Successfully checked fax status'))

    def handle(self, *args, **options):
        self.handle_fax()

        self.stdout.write(self.style.SUCCESS('Successfully checked status'))
