from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from nested_admin.nested import NestedStackedInline, NestedModelAdmin

from core_backend.models import User, Provider, Consumer, Payer, Agent, Case, Rule, Service, Event, Bill, Company, \
    Certificate, Contact, Location, Interpreter, Patient, Insurance, ClinicStaff, Claim


def stacked_inline_all(models):
    classes = []
    for m in models:
        class Stacked(NestedStackedInline):
            model = m
            extra = 0
        classes.append(Stacked)
    return classes


class ProviderInline(NestedStackedInline):
    model = Provider
    inlines = stacked_inline_all([Certificate])
    extra = 0


class UserAdmin(NestedModelAdmin, BaseUserAdmin):
    inlines = [ProviderInline]
    inlines += stacked_inline_all([Consumer, Payer, Agent])
    readonly_fields = ('is_provider', 'is_consumer', 'is_payer', 'is_agent')
    fieldsets = (
        *BaseUserAdmin.fieldsets[:2],
        (
            _('Contact'),
            {
                'fields': ('contact', 'company')
            }
        ),
        (
            _('Information'),
            {
                'fields': ('is_provider', 'is_consumer', 'is_payer', 'is_agent')
            }
        ),
        *BaseUserAdmin.fieldsets[2:],
    )


class EventAdmin(NestedModelAdmin):
    inlines = stacked_inline_all([Case, Event.claims.through])


admin.site.register(Contact)
admin.site.register(Company)
admin.site.register(Location)

admin.site.register(User, UserAdmin)

admin.site.register(Certificate)
admin.site.register(Claim)
admin.site.register(Rule)
admin.site.register(Service)
admin.site.register(Event, EventAdmin)

admin.site.register(Bill)

admin.site.register(Interpreter)
admin.site.register(Patient)
admin.site.register(Insurance)
admin.site.register(ClinicStaff)
