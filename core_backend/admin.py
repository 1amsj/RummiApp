from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from nested_admin.nested import NestedStackedInline, NestedModelAdmin

from core_backend.models import *


def stacked_inline(*models):
    classes = []
    for m in models:
        class Stacked(NestedStackedInline):
            model = m
            extra = 0
        classes.append(Stacked)
    return classes


class UserAdmin(NestedModelAdmin, BaseUserAdmin):
    readonly_fields = ('is_operator', 'is_payer', 'is_provider', 'is_recipient', 'is_requestor')
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
                'fields': ('is_operator', 'is_payer', 'is_provider', 'is_recipient', 'is_requestor')
            }
        ),
        *BaseUserAdmin.fieldsets[2:],
    )


class ServiceAdmin(NestedModelAdmin):
    inlines = stacked_inline(Category, ProviderService)


class LedgerAdmin(NestedModelAdmin):
    inlines = stacked_inline(Invoice)


class BookingAdmin(NestedModelAdmin):
    inlines = stacked_inline(Event, Ledger)


admin.site.register(Contact)
admin.site.register(Company)
admin.site.register(Location)

admin.site.register(User, UserAdmin)
admin.site.register(Operator)
admin.site.register(Payer)
admin.site.register(Provider)
admin.site.register(Recipient)
admin.site.register(Requestor)

admin.site.register(Category)
admin.site.register(Service)
admin.site.register(Event)

admin.site.register(Booking)

# admin.site.register(Rule)
