import datetime

import pytz
from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand

from core_api.constants import \
    AgentRoles, BookingReminderTargets, CompanyTypes, INTERPRETATION_BUSINESS_NAME
from core_backend.models import Booking, Company, Extra, Notification, User
from core_backend.notification_builders import ClinicDailyReminderBookings, InterpreterDailyReminderBookings
from core_backend.serializers.serializers import EventSerializer


def add_event_to_map(event_map, key, event):
    if key not in event_map:
        event_map[key] = [event]
    else:
        event_map[key].append(event)
    return event_map


def get_today_events_for_targets(events):
    clinic_events_map = {}
    interpreter_events_map = {}

    for event in events:
        reminder_targets_extra = Extra.objects.filter(
            business__name=INTERPRETATION_BUSINESS_NAME,
            parent_ct=ContentType.objects.get_for_model(Booking),
            parent_id=event.booking.id,
            key=BookingReminderTargets.EXTRA_KEY,
        ).first()

        reminder_targets = reminder_targets_extra.value if reminder_targets_extra else None

        if reminder_targets in [BookingReminderTargets.ALL, BookingReminderTargets.CLINIC]:
            clinic_id = event.booking.companies.filter(type=CompanyTypes.CLINIC).values_list('id', flat=True)[0]

            clinic_events_map = add_event_to_map(clinic_events_map, clinic_id, event)

        if (reminder_targets in [BookingReminderTargets.ALL, BookingReminderTargets.INTERPRETER]
                and (service := event.booking.services.first())):
            interpreter_user_id = service.provider.user.id

            interpreter_events_map = add_event_to_map(interpreter_events_map, interpreter_user_id, event)

    return clinic_events_map, interpreter_events_map


def prepare_notifications_for_clinics(clinic_events_map: dict, notification_list: list):
    for clinic_id, events in clinic_events_map.items():
        payload_events = []

        for event in events:
            patient = event.affiliates.first().recipient.user
            medical_provider = event.agents.filter(role=AgentRoles.MEDICAL_PROVIDER).first().user

            interpreter = None
            interpreter_contact = None

            if service := event.booking.services.first():
                interpreter = service.provider.user
                interpreter_contact = interpreter.contacts.filter(phone__isnull=False).exclude(phone__exact='').first()

            payload_events.append({
                "start_at": event.start_at.strftime("%I:%M%p"),
                "patient_name": patient.full_name,
                "medical_provider_name": medical_provider.full_name,
                "interpreter_name": interpreter.full_name if interpreter else None,
                "interpreter_phone": str(interpreter_contact.phone) if interpreter_contact else None,
            })

        notification_payload = {
            "date": datetime.date.today().strftime("%m/%d/%Y"),
            "events": payload_events,
        }

        notification_data = ClinicDailyReminderBookings().build(notification_payload)

        clinic = Company.objects.get(id=clinic_id)

        # Only fax supported
        send_method = Notification.SendMethod.FAX
        fax_contact = clinic.contacts.filter(fax__isnull=False).exclude(fax__exact='').first()

        if not fax_contact:
            continue

        notification_data['fax_number'] = str(fax_contact.fax)
        notification_data['fax_name'] = clinic.name

        notification_list.append(
            Notification(
                data=notification_data,
                payload=notification_payload,
                send_method=send_method,
                template=ClinicDailyReminderBookings.template,
            )
        )


def prepare_notifications_for_interpreters(interpreter_events_map: dict, notification_list: list):
    for interpreter_user_id, events in interpreter_events_map.items():
        payload_events = []

        for event in events:
            patient = event.affiliates.first().recipient.user
            medical_provider = event.agents.filter(role=AgentRoles.MEDICAL_PROVIDER).first().user
            clinic = event.booking.companies.filter(type=CompanyTypes.CLINIC).first()
            clinic_location = clinic.locations.first()
            clinic_contact = clinic.contacts.filter(phone__isnull=False).exclude(phone__exact='').first()

            payload_events.append({
                "start_at": event.start_at.strftime("%I:%M%p"),
                "patient_name": patient.full_name,
                "medical_provider_name": medical_provider.full_name,
                "clinic_name": clinic.name,
                "clinic_address": clinic_location.address if clinic_location else None,
                "clinic_phone": str(clinic_contact.phone) if clinic_contact else None,
            })

        interpreter_user = User.objects.get(id=interpreter_user_id)

        notification_payload = {
            "date": datetime.date.today().strftime("%m/%d/%Y"),
            "events": payload_events,
            "name": interpreter_user.first_name,
        }

        notification_data = InterpreterDailyReminderBookings().build(notification_payload)

        # Only fax supported
        send_method = Notification.SendMethod.FAX
        fax_contact = interpreter_user.contacts.filter(fax__isnull=False).exclude(fax__exact='').first()

        if not fax_contact:
            continue

        notification_data['fax_number'] = fax_contact.fax
        notification_data['fax_name'] = interpreter_user.full_name

        notification_list.append(
            Notification(
                data=notification_data,
                payload=notification_payload,
                send_method=send_method,
                template=InterpreterDailyReminderBookings.template,
            )
        )


class Command(BaseCommand):
    help = '(CORE Interpretation specific) Setup reminders for clinics and interpreters daily'

    def handle(self, *args, **options):
        today = datetime.datetime.now(pytz.utc)
        today_range = (
            datetime.datetime.combine(today, datetime.time.min),  # today 00:00
            datetime.datetime.combine(today, datetime.time.max),  # today 23:59
        )

        events = (
            EventSerializer
            .get_default_queryset()
            .filter(start_at__range=today_range)
            .order_by('start_at')
            .distinct('booking__id', 'start_at')
        )

        clinic_events_map, interpreter_events_map = get_today_events_for_targets(events)

        notification_list = []

        prepare_notifications_for_clinics(clinic_events_map, notification_list)
        prepare_notifications_for_interpreters(interpreter_events_map, notification_list)

        Notification.objects.bulk_create(notification_list)

        self.stdout.write(self.style.SUCCESS('Successfully setup today\'s reminders for clinics and interpreters'))
