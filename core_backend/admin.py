from typing import Type

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from nested_admin.nested import NestedGenericTabularInline, NestedModelAdmin, NestedStackedInline
from simple_history.admin import SimpleHistoryAdmin

from core_backend.models import *


class ExtraInline(NestedGenericTabularInline):
    model = Extra
    extra = 0
    ordering = ("business", "key")
    ct_fk_field = 'parent_id'
    ct_field = 'parent_ct'


class ExtendableAdmin(NestedModelAdmin):
    inlines = [ExtraInline]


class UserAdmin(NestedModelAdmin, BaseUserAdmin, SimpleHistoryAdmin):
    readonly_fields = ('is_operator', 'is_payer', 'is_provider', 'is_recipient', 'is_requester')
    fieldsets = (
        *BaseUserAdmin.fieldsets[:2],
        (
            _('Contact'),
            {
                'fields': ('contacts',)
            }
        ),
        (
            _('Information'),
            {
                'fields': ('national_id', 'ssn', 'is_operator', 'is_payer', 'is_provider', 'is_recipient', 'is_requester')
            }
        ),
        *BaseUserAdmin.fieldsets[2:],
    )


def stacked_inline(inline_model: Type[models.Model], extendable=False):
    class Stacked(NestedStackedInline):
        model = inline_model
        extra = 0
        if extendable:
            inlines = [ExtraInline]

    return Stacked


def basic_register(admin_model: Type[models.Model], extendable=False, historical=False, admin_inlines: list = None):
    parents = [SimpleHistoryAdmin] if historical else []

    class BasicAdmin(NestedModelAdmin, *parents):
        model = admin_model
        inlines = []
        if extendable:
            inlines = [ExtraInline]
            extra = 0
        if admin_inlines:
            inlines += admin_inlines

    admin.site.register(admin_model, BasicAdmin)


basic_register(Contact, historical=True)
basic_register(Company, historical=True)
basic_register(Location)

admin.site.register(User, UserAdmin)
basic_register(Agent, extendable=True)
basic_register(Operator, historical=True)
basic_register(Payer, historical=True)
basic_register(Provider, extendable=True, admin_inlines=[stacked_inline(Service, extendable=True)])
basic_register(Recipient, extendable=True, admin_inlines=[stacked_inline(Affiliation, extendable=True)])
basic_register(Affiliation, extendable=True, historical=True)
basic_register(Requester, historical=True)

basic_register(Business)
basic_register(Category)
basic_register(Service, extendable=True)
basic_register(Booking, extendable=True, admin_inlines=[stacked_inline(Ledger), stacked_inline(Expense, extendable=True), stacked_inline(Event, extendable=True)])
basic_register(Event, historical=True)
basic_register(Expense, historical=True)

basic_register(Extra, historical=True)

# admin.site.register(Rule)
