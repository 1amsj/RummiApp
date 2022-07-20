from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from nested_admin.nested import NestedStackedInline, NestedModelAdmin

from core_backend.models import User, Provider, Consumer, Payer, Agent, Case, Rule, Service, Event, Bill, \
    InterpreterCase, Company, Certificate, Contact


def stacked_inline_all(models):
    classes = []
    for m in models:
        class Stacked(NestedStackedInline):
            model = m
            extra = 0
        classes.append(Stacked)
    return classes


class CertificateInline(NestedStackedInline):
    model = Certificate
    extra = 0


class ProviderInline(NestedStackedInline):
    model = Provider
    inlines = [CertificateInline]
    extra = 0


class UserAdmin(NestedModelAdmin, BaseUserAdmin):
    inlines = [ProviderInline]
    inlines += stacked_inline_all([Consumer, Payer, Agent])
    fieldsets = (
        *BaseUserAdmin.fieldsets[:2],
        (
            _('Contact'),
            {
                'fields': ('contact', 'company')
            }
        ),
        *BaseUserAdmin.fieldsets[2:],
    )


class EventAdmin(admin.ModelAdmin):
    inlines = stacked_inline_all([Case])


admin.site.register(Contact)
admin.site.register(Company)

admin.site.register(User, UserAdmin)
admin.site.register(Certificate)

admin.site.register(Rule)
admin.site.register(Service)
admin.site.register(Event, EventAdmin)

admin.site.register(Bill)

admin.site.register(InterpreterCase)
