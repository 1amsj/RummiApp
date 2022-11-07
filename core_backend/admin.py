from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from nested_admin.nested import NestedGenericTabularInline, NestedModelAdmin, NestedStackedInline

from core_backend.models import *


def stacked_inline(*models):
    classes = []
    for m in models:
        class Stacked(NestedStackedInline):
            model = m
            extra = 0
        classes.append(Stacked)
    return classes


class ExtraInline(NestedGenericTabularInline):
    model = Extra
    extra = 0
    ordering = ("business", "key")
    ct_fk_field = 'parent_id'
    ct_field = 'parent_ct'


class ExtendableAdmin(NestedModelAdmin):
    inlines = [ExtraInline]


class UserAdmin(NestedModelAdmin, BaseUserAdmin):
    readonly_fields = ('is_operator', 'is_payer', 'is_provider', 'is_recipient', 'is_requester')
    fieldsets = (
        *BaseUserAdmin.fieldsets[:2],
        (
            _('Contact'),
            {
                'fields': ('contact',)
            }
        ),
        (
            _('Information'),
            {
                'fields': ('is_operator', 'is_payer', 'is_provider', 'is_recipient', 'is_requester')
            }
        ),
        *BaseUserAdmin.fieldsets[2:],
    )


class ServiceInline(NestedStackedInline):
    model = Service
    inlines = [ExtraInline]
    extra = 0


class ServiceAdmin(NestedModelAdmin):
    model = Service
    inlines = [ExtraInline]


class ProviderAdmin(NestedModelAdmin):
    inlines = [ExtraInline, ServiceInline]


class AffiliationAdmin(NestedStackedInline):
    model = Affiliation
    inlines = [ExtraInline]
    extra = 0


class RecipientAdmin(NestedModelAdmin):
    inlines = [ExtraInline, AffiliationAdmin]


class LedgerAdmin(NestedModelAdmin):
    inlines = stacked_inline(Invoice)


class EventInline(NestedStackedInline):
    model = Event
    inlines = [ExtraInline]
    extra = 0


class BookingAdmin(NestedModelAdmin):
    inlines = [ExtraInline]
    inlines += stacked_inline(Ledger)
    inlines += [EventInline]


admin.site.register(Contact)
admin.site.register(Company)
admin.site.register(Location)

admin.site.register(User, UserAdmin)
admin.site.register(Agent, ExtendableAdmin)
admin.site.register(Operator)
admin.site.register(Payer)
admin.site.register(Provider, ProviderAdmin)
admin.site.register(Recipient, RecipientAdmin)
admin.site.register(Requester)

admin.site.register(Business)
admin.site.register(Category)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Event)

# admin.site.register(Rule)
