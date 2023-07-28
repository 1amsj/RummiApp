from django.core.management import BaseCommand

from core_backend.models import Notification


class Command(BaseCommand):
    help = 'Send notifications marked as PENDING'

    def handle(self, *args, **options):
        for notification in Notification.objects.filter(status=Notification.Status.PENDING):
            self.stdout.write(F"Would send notification {notification}")
            # TODO send notification
            notification.status = Notification.Status.SENT
            notification.save()

        self.stdout.write(self.style.SUCCESS('Successfully sent notifications'))
