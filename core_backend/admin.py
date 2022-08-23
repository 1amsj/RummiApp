from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from nested_admin.nested import NestedStackedInline, NestedModelAdmin, NestedGenericTabularInline

from core_backend.models import *


def stacked_inline(*models):
    classes = []
    for m in models:
        class Stacked(NestedStackedInline):
            model = m
            extra = 0
        classes.append(Stacked)
    return classes


class AdditionalPropertyInline(NestedGenericTabularInline):
    model = AdditionalProperty
    extra = 0
    ordering = ("business", "key")
    ct_fk_field = 'parent_id'
    ct_field = 'parent_ct'


class ExtendableAdmin(NestedModelAdmin):
    inlines = [AdditionalPropertyInline]


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


class ProviderAdmin(NestedModelAdmin):
    inlines = [AdditionalPropertyInline]
    inlines += stacked_inline(ProviderService)


class ServiceAdmin(NestedModelAdmin):
    inlines = stacked_inline(Category)


class LedgerAdmin(NestedModelAdmin):
    inlines = stacked_inline(Invoice)


class EventInline(NestedStackedInline):
    model = Event
    inlines = [AdditionalPropertyInline]
    extra = 0


class BookingAdmin(NestedModelAdmin):
    inlines = [AdditionalPropertyInline]
    inlines += stacked_inline(Ledger)
    inlines += [EventInline]


admin.site.register(Contact)
admin.site.register(Company)
admin.site.register(Location)

admin.site.register(User, UserAdmin)
admin.site.register(Operator)
admin.site.register(Payer)
admin.site.register(Provider, ProviderAdmin)
admin.site.register(Recipient, ExtendableAdmin)
admin.site.register(Requestor)

admin.site.register(Category)
admin.site.register(Service)
admin.site.register(Event, ExtendableAdmin)

admin.site.register(Booking, BookingAdmin)

# admin.site.register(Rule)
