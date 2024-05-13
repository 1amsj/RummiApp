# update_data.py
import os
from django.core.management.base import BaseCommand
from django.db.models import Q

class Command(BaseCommand):
    def handle(self, *args, **options):
        from core_backend.models import ServiceRoot, Service, Booking

        # Update ServiceRoot
        ServiceRoot.objects.filter(id=1).update(name='Onsite Interpretation Medical Legal')
        ServiceRoot.objects.filter(id=3).update(name='Onsite Interpretation Medical Standard')
        ServiceRoot.objects.filter(id=5).update(name='Telephonic Interpretation Medical Certified')
        ServiceRoot.objects.filter(id=2).update(name='Telephonic Interpretation Medical Standard')
        ServiceRoot.objects.filter(id=7).update(name='Videochat Interpretation Medical Certified')
        ServiceRoot.objects.filter(id=4).update(name='Videochat Interpretation Medical Standard')
        ServiceRoot.objects.filter(id=28).update(name='Onsite Interpretation Medical Certified')

        # Update Service
        Service.objects.filter(Q(root_id=13) | Q(root_id=6) | Q(root_id=18) | Q(root_id=26) | Q(root_id=21) | Q(root_id=20) | Q(root_id=16) | Q(root_id=22) | Q(root_id=12) | Q(root_id=9)).update(root_id=28)
        Service.objects.filter(Q(root_id=23) | Q(root_id=25)).update(root_id=3)
        Service.objects.filter(Q(root_id=19) | Q(root_id=17) | Q(root_id=10) | Q(root_id=24)).update(root_id=5)
        Service.objects.filter(root_id=15).update(root_id=2)
        Service.objects.filter(Q(root_id=11) | Q(root_id=8)).update(root_id=7)
        Service.objects.filter(root_id=14).update(root_id=4)

        # Update Booking
        Booking.objects.filter(Q(service_root_id=13) | Q(service_root_id=6) | Q(service_root_id=18) | Q(service_root_id=26) | Q(service_root_id=21) | Q(service_root_id=20) | Q(service_root_id=16) | Q(service_root_id=22) | Q(service_root_id=12) | Q(service_root_id=9)).update(service_root_id=28)
        Booking.objects.filter(Q(service_root_id=23) | Q(service_root_id=25)).update(service_root_id=3)
        Booking.objects.filter(Q(service_root_id=19) | Q(service_root_id=17) | Q(service_root_id=10) | Q(service_root_id=24)).update(service_root_id=5)
        Booking.objects.filter(service_root_id=15).update(service_root_id=2)
        Booking.objects.filter(Q(service_root_id=11) | Q(service_root_id=8)).update(service_root_id=7)
        Booking.objects.filter(service_root_id=14).update(service_root_id=4)

        # Delete ServiceRootCategories
        for serviceroot in ServiceRoot.objects.filter(Q(id=13) | Q(id=6) | Q(id=18) | Q(id=26) | Q(id=21) | Q(id=20) | Q(id=16) | Q(id=22) | Q(id=12) | Q(id=9) | \
            Q(id=23) | Q(id=25) | Q(id=19) | Q(id=17) | Q(id=10) | Q(id=24) | Q(id=15) | Q(id=11) | Q(id=8) | Q(id=14)):
            serviceroot.categories.clear()

        # Delete ServiceRoot
        ServiceRoot.objects.filter(Q(id=13) | Q(id=6) | Q(id=18) | Q(id=26) | Q(id=21) | Q(id=20) | Q(id=16) | Q(id=22) | Q(id=12) | Q(id=9) \
        | Q(id=23) | Q(id=25) | Q(id=19) | Q(id=17) | Q(id=10) | Q(id=24) | Q(id=15) | Q(id=11) | Q(id=8) | Q(id=14)).delete()

        self.stdout.write(self.style.SUCCESS('Data updated successfully!'))