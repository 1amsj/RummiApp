from typing import Type

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from nested_admin.nested import NestedGenericTabularInline, NestedModelAdmin, NestedStackedInline
from simple_history.admin import SimpleHistoryAdmin

from core_backend.models import *
from .models import ExternalApiToken
from .services.core_services import generate_unique_field, regenerate_unique_condition_fields


class ExtraInline(NestedGenericTabularInline):
    model = Extra
    extra = 0
    ordering = ("business", "key")
    ct_fk_field = 'parent_id'
    ct_field = 'parent_ct'


class ExtendableAdmin(NestedModelAdmin):
    inlines = [ExtraInline]


class UserAdmin(SimpleHistoryAdmin, NestedModelAdmin, BaseUserAdmin):
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


class ExternalApiTokenAdmin(admin.ModelAdmin):
    list_display = ('api_name', 'client_id', 'is_valid', 'created_at', 'updated_at')
    actions = ['invalidate_tokens']

    fields = ('api_name', 'client_id', 'expires_at', 'expiration_timestamp', 'is_expired', 'access_token', 'refresh_token', 'scope', 'created_at', 'updated_at')
    readonly_fields = ('api_name', 'client_id', 'expires_at', 'is_expired', 'access_token', 'refresh_token', 'scope', 'created_at', 'updated_at')

    def is_valid(self, obj):
        return bool(obj.access_token and obj.refresh_token and not obj.is_expired)
    is_valid.boolean = True
    is_valid.short_description = _('Is Valid')

    def invalidate_tokens(self, request, queryset):
        count = 0
        for token in queryset:
            token.invalidate()
            count += 1
        self.message_user(request, _('%d tokens were invalidated.') % count)
    invalidate_tokens.short_description = _("Invalidate selected tokens")


class UniqueConditionAdmin(admin.ModelAdmin):
    list_display = ('business', 'content_type', 'fields')
    actions = ['regenerate_unique_fields', 'check_for_conflicts']

    def save_model(self, request, obj, form, change):
        model = obj.content_type.model_class()
        if not hasattr(model, 'unique_field'):
            messages.add_message(request, messages.WARNING, 'This model does not support unique field')
        super(UniqueConditionAdmin, self).save_model(request, obj, form, change)

    def regenerate_unique_fields(self, request, queryset):
        updated_models = []

        for unique_condition in queryset:
            model = unique_condition.content_type.model_class()
            if not hasattr(model, 'unique_field'):
                messages.add_message(request, messages.WARNING, 'Model %s does not support unique field' % model)
                continue

            try:
                regenerate_unique_condition_fields(unique_condition)
                updated_models.append(unique_condition.content_type.model)
            except IntegrityError as e:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _('Could not regenerate unique fields for the model %s due to a duplicate.')
                    % unique_condition.content_type.model,
                )

        if not updated_models:
            return

        self.message_user(
            request,
            _('Unique fields were regenerated for the models %s.')
            % ','.join(updated_models),
        )


    def check_for_conflicts(self, request, queryset):
        found_conflict = False

        for unique_condition in queryset:
            model = unique_condition.content_type.model_class()
            if not hasattr(model, 'unique_field'):
                messages.add_message(request, messages.WARNING, 'This model does not support unique field')
                continue

            unique_fields_dict = {}

            for instance in model.objects.all():
                unique_field = generate_unique_field(unique_condition.business, instance, unique_condition.fields)

                if unique_field in unique_fields_dict:
                    unique_fields_dict[unique_field].append(str(instance.id))
                else:
                    unique_fields_dict[unique_field] = [str(instance.id)]

            for unique_field, instances in unique_fields_dict.items():
                if len(instances) <= 1:
                    continue

                found_conflict = True
                messages.add_message(
                    request,
                    messages.ERROR,
                    _('For the model %s, the following %d instances have the same unique field %s: %s')
                    % (model._meta.model_name, len(instances), unique_field, ','.join(instances)),
                )

        if not found_conflict:
            messages.add_message(
                request,
                messages.SUCCESS,
                _('No conflicts found for the selected unique conditions. It is safe to regenerate unique fields.'),
            )


def stacked_inline(inline_model: Type[models.Model], extendable=False):
    class Stacked(NestedStackedInline):
        model = inline_model
        extra = 0
        if extendable:
            inlines = [ExtraInline]

    return Stacked


def basic_register(admin_model: Type[models.Model], readonly=(), extendable=False, historical=True, admin_inlines: list = None):
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


basic_register(Contact)
basic_register(Company)
basic_register(Language)
basic_register(Location)

admin.site.register(User, UserAdmin)
basic_register(Agent, extendable=True)
basic_register(Operator)
basic_register(Payer)
basic_register(Provider, extendable=True, admin_inlines=[stacked_inline(Service, extendable=True)])
basic_register(Recipient, extendable=True, admin_inlines=[stacked_inline(Affiliation, extendable=True)])
basic_register(Affiliation, extendable=True)
basic_register(Requester)

basic_register(Business, historical=False)
basic_register(Category)
basic_register(Service, extendable=True)
basic_register(ServiceArea)
basic_register(ServiceRoot, admin_inlines=[stacked_inline(Service, extendable=True)])
basic_register(Booking, extendable=True, admin_inlines=[stacked_inline(Ledger), stacked_inline(Expense, extendable=True), stacked_inline(Event, extendable=True)])
basic_register(Event, extendable=True, admin_inlines=[stacked_inline(Authorization.events.through)])
basic_register(Expense)
basic_register(Offer)
basic_register(Report)

basic_register(Authorization, readonly=('last_updated_at',))
basic_register(Extra)
basic_register(Note)
basic_register(Notification)
basic_register(CompanyRelationship)
admin.site.register(ExternalApiToken, ExternalApiTokenAdmin)
admin.site.register(UniqueCondition, UniqueConditionAdmin)

# admin.site.register(Rule)
