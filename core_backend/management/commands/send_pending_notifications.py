from datetime import datetime

from django.core.management import BaseCommand

from core_backend.models import Notification
from core_backend.services.concord.concord_interfaces import FaxJobFile, FaxJobRecipient, FileFormats
from core_backend.services.concord.concord_service import ConcordService


def send_fax(data: dict, fax_service: ConcordService):
    recipient = FaxJobRecipient(
        fax_number=data['fax_number'],
        name=data['fax_name'],
        title=data['title'],
    )

    file = FaxJobFile(
        file_index=0,
        file_type_id=FileFormats.MHTML,
        file_data=data['body'].encode('utf-8'),
    )

    fax_job_ids, job_begin_time = fax_service.send_fax(
        fax_recipients=[recipient],
        fax_files=[file],
    )

    return fax_job_ids[0], job_begin_time


class Command(BaseCommand):
    help = 'Send notifications marked as PENDING'

    def handle(self, *args, **options):
        notification_queryset = (
            Notification.objects
            .filter(status=Notification.Status.PENDING)
            .order_by('-priority')
        )

        for notification in notification_queryset:
            if notification.send_method != Notification.SendMethod.FAX:
                self.stdout.write(F"Would send notification {notification}")
                notification.status = Notification.Status.SENT
                notification.save()
                continue


            try:
                fax_service = ConcordService()
                job_id, job_begin_time = send_fax(notification.data, fax_service)

            except Exception as e:
                self.stdout.write(F"Failed to send notification {notification}: {e}")
                notification.status = Notification.Status.FAILED
                notification.status_message = f'Failed to send notification due to unknown error: {e}'
                notification.save()
                continue

            notification.job_id = job_id
            notification.status = Notification.Status.SUBMITTED
            notification.submitted_at = datetime.now()
            notification.expected_send_at = datetime.fromtimestamp(job_begin_time)
            notification.save()

        self.stdout.write(self.style.SUCCESS('Successfully sent notifications'))
