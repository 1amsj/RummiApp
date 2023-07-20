from typing import Type

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from nested_admin.nested import NestedGenericTabularInline, NestedModelAdmin, NestedStackedInline, NestedTabularInline
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
        *BaseUserAdmin.fieldsets[:1],
        (
            _('Personal Information'),
            {
                'fields': ('title', 'first_name', 'last_name', 'suffix', 'email',)
            }
        ),
        (
            _('Contact'),
            {
                'fields': ('contacts',)
            }
        ),
        (
            _('Location'),
            {
                'fields': ('location',)
            }
        ),
        (
            _('Information'),
            {
                'fields': ('national_id', 'ssn', 'date_of_birth', 'is_operator', 'is_payer', 'is_provider', 'is_recipient', 'is_requester', 'is_deleted')
            }
        ),
        *BaseUserAdmin.fieldsets[2:],
    )

    def delete_model(self, request, obj):
        obj.hard_delete()


def stacked_inline(inline_model: Type[models.Model], extendable=False):
    class Stacked(NestedStackedInline):
        model = inline_model
        extra = 0
        if extendable:
            inlines = [ExtraInline]

    return Stacked


def basic_register(admin_model: Type[models.Model], readonly=(), extendable=False, historical=False, admin_inlines: list = None):
    parents = [SimpleHistoryAdmin] if historical else []

    class BasicAdmin(NestedModelAdmin, *parents):
        readonly_fields = readonly
        model = admin_model
        inlines = []
        if extendable:
            inlines = [ExtraInline]
            extra = 0
        if admin_inlines:
            inlines += admin_inlines

        def delete_model(self, request, obj):
            obj.hard_delete()

        def bulk_delete_model(self, request, queryset, obj=None ):
             if obj is None:
                for obj in queryset:
                    self.delete_model(request, obj)
             else:
                self.delete_model(request, obj)

        def get_actions(self, request):
            actions = super().get_actions(request)
            actions['bulk_delete_model'] = (
                self.bulk_delete_model,
                'bulk_delete_model',
                'Bulk Delete (Hard Delete)'
            )
            return actions


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
basic_register(ServiceRoot, admin_inlines=[stacked_inline(Service, extendable=True)])
basic_register(Booking, extendable=True, admin_inlines=[stacked_inline(Ledger), stacked_inline(Expense, extendable=True), stacked_inline(Event, extendable=True)])
basic_register(Event, extendable=True, historical=True, admin_inlines=[stacked_inline(Authorization.events.through)])
basic_register(Expense, historical=True)

basic_register(Authorization, historical=True, readonly=('last_updated_at',))
basic_register(Extra, historical=True)
basic_register(Note, historical=True)

# admin.site.register(Rule)
