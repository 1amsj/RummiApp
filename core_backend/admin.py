from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from core_backend.models import User, Provider, Consumer, Payer, Agent, Case, Rule, Service, Event, Bill, \
    InterpreterCase


def stacked_inline_all(models):
    classes = []
    for m in models:
        class Stacked(admin.StackedInline):
            model = m
        classes.append(Stacked)
    return classes


class UserAdmin(BaseUserAdmin):
    inlines = stacked_inline_all([Provider, Consumer, Payer, Agent])


class EventAdmin(admin.ModelAdmin):
    inlines = stacked_inline_all([Case])


admin.site.register(User, UserAdmin)

admin.site.register(Rule)
admin.site.register(Service)
admin.site.register(Event, EventAdmin)

admin.site.register(Bill)

admin.site.register(InterpreterCase)
