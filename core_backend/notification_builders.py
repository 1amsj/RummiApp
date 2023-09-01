from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _


class Renderer:
    template = 'unknown'

    def get_template_name(self):
        return F"notifications/{self.template}.html"

    def render(self, data: dict) -> str:
        return render_to_string(self.get_template_name(), data)

    def build(self, data: dict) -> dict:
        return {
            "body": self.render(data),
        }


class PlaceholderNotificationBuilder(Renderer):
    template = 'placeholder'

    def build(self, data):
        return {
            "title": _("Placeholder"),
            "body": self.render(data),
        }


class ClinicDailyReminderBookings(Renderer):
    template = 'clinic_daily_reminder_bookings'

    def build(self, data):
        return {
            "title": _("CORE Booking Daily Reminder") + F" - {data['date']}",
            "body": self.render(data),
        }


class InterpreterDailyReminderBookings(Renderer):
    template = 'interpreter_daily_reminder_bookings'

    def build(self, data):
        return {
            "title": _("CORE Booking Daily Reminder") + F" - {data['date']}",
            "body": self.render(data),
        }


def build_from_template(template: str, data: dict) -> dict:
    builders = [
        PlaceholderNotificationBuilder,
        ClinicDailyReminderBookings,
        InterpreterDailyReminderBookings,
    ]

    try:
        builder = next(b for b in builders if b.template == template)
        return builder().build(data)

    except StopIteration:
        raise ValueError(F"Unknown template: {template}")
