import time
from datetime import datetime
from typing import Optional, Tuple

from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from simple_history.models import HistoricalRecords

from core_backend.datastructures import QueryParams


# Query sets
class SoftDeletionQuerySet(models.QuerySet):
    def deleted(self, *fields: Tuple[str, ...]):
        return self.filter(
            is_deleted=True,
            **{
                F'{field}__is_deleted': True
                for field in fields
            }
        )

    def not_deleted(self, *fields: Tuple[str, ...]):
        return self.filter(
            is_deleted=False,
            **{
                F'{field}__is_deleted': False
                for field in fields
            }
        )

    def delete(self):
        for obj in self:
            obj.delete()

    def hard_delete(self):
        return super().delete()


class ExtraQuerySet(SoftDeletionQuerySet):
    def prefetch_extra(self, business: Optional["Business"] = None):
        ct = ContentType.objects.get_for_model(self.model)
        query = Q(extra__parent_ct=ct)

        if business:
            query &= Q(extra__business=business)

        return self.prefetch_related('extra').filter(query)

    def filter_by_extra(self, related_prefix='', **fields):
        from core_backend.services.core_services import iter_extra_attrs

        queryset = self

        for (k, v) in iter_extra_attrs(self.model, fields):
            params = k.split('__')

            query_key = F'{related_prefix}extra__key'
            query_value = F'{related_prefix}extra__data'

            if len(params) > 1:
                query_value += F'__{params[1]}'

            queryset = queryset.filter(**{query_key: params[0], query_value: v})

        return queryset

    def filter_by_extra_query_params(self, extra_params: QueryParams, related_prefix=''):
        from core_backend.services.core_services import collect_queryset_filters_by_query_params

        queryset = self

        filters_collection = collect_queryset_filters_by_query_params(extra_params, related_prefix)
        for filters in filters_collection:
            queryset = self.filter(**filters)

        return queryset


# Managers
class SoftDeletionManager(
    models.Manager.from_queryset(SoftDeletionQuerySet)
):
    pass


class ExtraManager(
    models.Manager.from_queryset(ExtraQuerySet),
):
    pass

class CoreUserManager(UserManager):
    def get_queryset(self):
        return SoftDeletionQuerySet(
            model=self.model,
            using=self._db,
            hints=self._hints
        )


# Abstract models
class SoftDeletableModel(models.Model):
    is_deleted = models.BooleanField(default=False)

    objects = SoftDeletionManager()

    class Meta:
        abstract = True

    def delete_related(self):
        pass

    @transaction.atomic
    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.save()
        self.delete_related()

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using, keep_parents)


class ExtendableModel(SoftDeletableModel):
    extra = GenericRelation("Extra", 'parent_id', 'parent_ct', verbose_name=_('extra data'))

    objects = ExtraManager()

    class Meta:
        abstract = True

    def get_extra_attrs(self, business: Optional["Business"] = None) -> dict:
        queryset = self.extra.all()
        if business:
            queryset = queryset.filter(business=business)
        return {
            e.key: e.data
            for e in queryset
        }


class HistoricalModel(models.Model):
    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True


class UniquifiableModel(models.Model):
    unique_field = models.TextField(unique=True, blank=True, null=True, default=None)

    class Meta:
        abstract = True


# General data models
class Extra(SoftDeletableModel):
    parent_id = models.PositiveIntegerField()
    parent_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    parent = GenericForeignKey('parent_ct', 'parent_id')
    business = models.ForeignKey("Business", on_delete=models.CASCADE)
    key = models.TextField(_('key'))
    data = models.JSONField(_('data'))

    class Meta:
        verbose_name = verbose_name_plural = _('extra data')
        indexes = [
            models.Index(fields=["parent_ct", "business", "key"]),
            models.Index(fields=["parent_id", "key"]),
        ]
        unique_together = ["parent_ct", "parent_id", "business", "key"]

    def __str__(self):
        return F"[{self.parent_ct} {self.parent_id}] {self.business}, {self.key}: {self.data}"


class UniqueCondition(models.Model):
    business = models.ForeignKey("Business", on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    fields = ArrayField(models.TextField(), default=list, blank=False)

    class Meta:
        verbose_name = _('unique condition')
        verbose_name_plural = _('unique conditions')
        unique_together = ['business', 'content_type']

    def __str__(self):
        return F"{self.content_type} - {self.fields}"


class Contact(SoftDeletableModel, HistoricalModel):
    class Via(models.TextChoices):
        EMAIL = 'email', _('email')
        PHONE = 'phone', _('phone')
        FAX = 'fax', _('fax')

    email = models.EmailField(_("email address"), blank=True)
    phone = PhoneNumberField(_('phone number'), blank=True)
    fax = PhoneNumberField(_('fax number'), blank=True)
    phone_context = models.CharField(_('phone context'), max_length=150, blank=True)
    email_context = models.CharField(_('email context'), max_length=150, blank=True)
    fax_context = models.CharField(_('fax context'), max_length=150, blank=True)

    class Meta:
        verbose_name = _('contact')
        verbose_name_plural = _('contacts')

    def __str__(self):
        return F"{self.email}, {self.phone}, {self.fax}"


class Company(ExtendableModel, SoftDeletableModel, HistoricalModel):
    contacts = models.ManyToManyField(Contact, blank=True)
    locations = models.ManyToManyField("Location", related_name='owner', blank=True)
    name = models.CharField(_('name'), max_length=128)
    type = models.CharField(_('type'), max_length=128)
    send_method = models.CharField(_('send method'), max_length=128)
    on_hold = models.BooleanField(_('on hold'))
    parent_company = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE, related_name = 'children_companies')

    class Meta:
        ordering = ['name']
        verbose_name = _('company')
        verbose_name_plural = _('companies')

    def __str__(self):
        return F"{self.name} ({self.type})"

    def delete_related(self):
        # TODO review
        # self.contacts.all().delete()
        # self.locations.all().delete()
        self.affiliations.all().delete()
        self.notes.all().delete()
        pass

class CompanyRelationship(SoftDeletableModel, HistoricalModel):
    company_from = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='company_relationships_from', blank=True, null=True)
    company_to = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='company_relationships_to', blank=True, null=True)
    relationship = models.TextField(_('relationship'), null=True, blank=True)

    class Meta:
        unique_together = ('company_from', 'company_to', 'relationship')
        verbose_name = _('company relationship')
        verbose_name_plural = _('company relationships')

    def __str__(self):
        return F"{self.company_to} has a {self.relationship} relationship with {self.company_from}"
class Language(SoftDeletableModel, HistoricalModel):
    alpha2 = models.CharField(_('alpha2'), max_length=2, null=True, blank=True)
    alpha3 = models.CharField(_('alpha3'), max_length=6)
    available = models.BooleanField(_('available'), default=True)
    common = models.BooleanField(_('common'), default=False)
    description = models.TextField(_('description'), null=True, blank=True)
    name = models.CharField(_('name'), max_length=128)

    class Meta:
        verbose_name = _('language')
        verbose_name_plural = _('languages')
        ordering = ['-common', 'name']

    def __str__(self):
        return F"{self.name} [{self.alpha2}|{self.alpha3}] ({self.id})"


class Location(SoftDeletableModel, HistoricalModel):
    address = models.TextField(_('address'), null=True, blank=True)
    unit_number = models.TextField(_('unit number'), null=True, blank=True)
    city = models.TextField(_('city'), null=True, blank=True)
    state = models.TextField(_('state or province'), null=True, blank=True)
    country = models.TextField(_('country'), null=True, blank=True)
    zip = models.TextField(_('ZIP code'), null=True, blank=True)

    class Meta:
        verbose_name = _('location')
        verbose_name_plural = _('locations')

    def __str__(self):
        return F"{self.country}, {self.state}, {self.city}, {self.address}{F' {self.unit_number}' if self.unit_number else ''}, {self.zip}"
    
class GlobalSetting(ExtendableModel, HistoricalModel):
    client = models.CharField(_('client'), max_length=128, blank=True)
    business = models.ForeignKey("Business", on_delete=models.CASCADE, related_name='setting')

    class Meta:
        verbose_name = _('global setting')
        verbose_name_plural = _('global settings')

    def __str__(self):
        return F"{self.client} - {self.business}"

# User models
class User(SoftDeletableModel, AbstractUser, HistoricalModel):
    contacts = models.ManyToManyField(Contact, blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='location', blank=True, null=True)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    national_id = models.CharField(_('national ID'), max_length=50, blank=True)
    ssn = models.CharField(_('social security number'), max_length=50, blank=True)
    title = models.CharField(_('title'), max_length=150, blank=True)
    suffix = models.CharField(_('suffix'), max_length=150, blank=True)

    objects = CoreUserManager()

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
            return F"{self.title} {self.first_name} {self.last_name} {self.suffix} - {self.username} ({self.id})"


    @property
    def full_name(self):
        return F"{self.title or ''} {self.first_name} {self.last_name} {self.suffix or ''}".strip()

    @property
    def is_agent(self):
        return getattr(self, 'as_agents', None) is not None

    @property
    def is_operator(self):
        return getattr(self, 'as_operator', None) is not None

    @property
    def is_provider(self):
        return getattr(self, 'as_provider', None) is not None

    @property
    def is_recipient(self):
        return getattr(self, 'as_recipient', None) is not None

    @property
    def is_requester(self):
        return getattr(self, 'as_requester', None) is not None

    @property
    def is_payer(self):
        return getattr(self, 'as_payer', None) is not None

    @property
    def is_provider(self):
        return getattr(self, 'as_provider', None) is not None
    
    @property
    def is_admin(self):
        return getattr(self, 'as_admin', None) is not None

    def delete_related(self):
        if self.is_agent:
            self.as_agents.all().delete()

        if self.is_operator:
            self.as_operator.delete()

        if self.is_provider:
            self.as_provider.delete()

        if self.is_recipient:
            self.as_recipient.delete()

        if self.is_requester:
            self.as_requester.delete()

        if self.is_payer:
            self.as_payer.delete()
            
        if self.is_admin:
            self.as_admin.delete()

        self.location.delete()

class Admin(ExtendableModel, HistoricalModel, SoftDeletableModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='as_admin')
    
    class Meta:
        ordering = ['user__first_name', 'user__last_name']
        verbose_name = _('admin')
    
    def __str__(self):
        return F"[Admin] {self.user}"

    def delete_related(self):
        pass

class Agent(ExtendableModel, HistoricalModel, SoftDeletableModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='as_agents')
    companies = models.ManyToManyField(Company, related_name='agents')
    role = models.CharField(_('role'), max_length=64)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']
        verbose_name = _('agent')
        verbose_name_plural = _('agents')

    def __str__(self):
        return F"[{self.role} (agent)] {self.user}"

    def delete_related(self):
        pass


class Operator(HistoricalModel, SoftDeletableModel):
    """Staff who maintain the platform"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_operator')
    companies = models.ManyToManyField(Company, related_name='operators', blank=True)
    hiring_date = models.DateField(_('hiring date'))

    class Meta:
        verbose_name = verbose_name_plural = _('operator data')

    def __str__(self):
        return F"[Operator] {self.user}"

    def delete_related(self):
        pass


class Payer(HistoricalModel, SoftDeletableModel):
    """Who pays the service invoice"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_payer')
    companies = models.ManyToManyField(Company, related_name='payers')
    method = models.CharField(_('paying method'), max_length=64, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = _('payer data')

    def __str__(self):
        return F"[Payer] {self.user}"

    def delete_related(self):
        self.notes.all().delete()
        pass


class Provider(ExtendableModel, SoftDeletableModel, HistoricalModel):
    """Who provides the service"""

    class ContractType(models.TextChoices):
        CONTRACTOR = 'CONTRACTOR', _('Contractor')
        SALARIED = 'SALARIED', _('Salaried')
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_provider')
    companies = models.ManyToManyField(Company, related_name='providers')
    contract_type = models.CharField(max_length=255, choices=ContractType.choices, default=ContractType.CONTRACTOR)
    salary = models.DecimalField(max_digits=32, decimal_places=2, blank=True, null=True)
    payment_via = models.CharField(max_length=255, blank=True, null=True)
    payment_account = models.CharField(max_length=255, blank=True, null=True)
    payment_routing = models.CharField(max_length=255, blank=True, null=True)
    payment_account_type = models.CharField(max_length=255, blank=True, null=True)
    minimum_bookings = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']
        verbose_name = verbose_name_plural = _('provider data')

    def __str__(self):
        return F"[Provider] {self.user}"

    def delete_related(self):
        self.services.all().delete()
        self.notes.all().delete()


class Recipient(ExtendableModel, HistoricalModel, SoftDeletableModel):
    """Who receives the service"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_recipient')
    companies = models.ManyToManyField(Company, related_name='recipients', through="Affiliation")

    class Meta:
        verbose_name = verbose_name_plural = _('recipient data')

    def __str__(self):
        return F"[Recipient] {self.user}"

    def delete_related(self):
        self.affiliations.all().delete()
        self.notes.all().delete()


class Affiliation(ExtendableModel, HistoricalModel, SoftDeletableModel):
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE, related_name='affiliations')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='affiliations')

    class Meta:
        ordering = ['recipient__user__first_name', 'recipient__user__last_name']
        verbose_name = _('affiliation')
        verbose_name_plural = _('affiliations')

    def __str__(self):
        return F"[Affiliation] {self.recipient.user} with {self.company or 'no company'}"

    def delete_related(self):
        pass


class Requester(HistoricalModel, SoftDeletableModel):
    """Who requests the service case for the Recipient"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_requester')
    companies = models.ManyToManyField(Company, related_name='requesters')

    class Meta:
        ordering = ['user__first_name', 'user__last_name']
        verbose_name = verbose_name_plural = _('requester data')

    def __str__(self):
        return F"[Requester] {self.user}"

    def delete_related(self):
        pass


# Service models
class Business(SoftDeletableModel):
    name = models.CharField(_('business'), max_length=128, unique=True)

    class Meta:
        verbose_name = _('business')
        verbose_name_plural = _('businesses')

    def __str__(self):
        return self.name

    def delete_related(self):
        self.bookings.all().delete()
        self.services.all().delete()


class Category(SoftDeletableModel, HistoricalModel):
    description = models.CharField(_('description'), max_length=256)
    name = models.CharField(_('name'), max_length=64)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self):
        return self.name

    def delete_related(self):
        pass


class ServiceRoot(SoftDeletableModel, HistoricalModel):
    categories = models.ManyToManyField(Category, related_name='roots', blank=True)
    description = models.TextField(_('description'), blank=True, default='')
    name = models.TextField(_('name'))

    class Meta:
        verbose_name = _('service root')
        verbose_name_plural = _('service roots')
        ordering = ['description']

    def __str__(self):
        return self.name

    @property
    def has_services(self):
        return hasattr(self, 'services') and self.services is not None

    def delete_related(self):
        if self.has_services:
            self.services.all().delete()


class Service(ExtendableModel, HistoricalModel, SoftDeletableModel):
    class RateType(models.TextChoices):
        FLAT = 'FLAT', _('Flat')
        PER_ASSIGNATION = 'PER_ASSIGNATION', _('Per Assignation')
        PER_HOURS = 'PER_HOURS', _('Per Hours')
        PER_MINUTES = 'PER_MINUTES', _('Per Minutes')
        QUANTITY = 'QUANTITY', _('Quantity')

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='services')
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='services')
    root = models.ForeignKey(ServiceRoot, null=True, blank=True, on_delete=models.PROTECT, related_name='services')
    bill_amount = models.PositiveIntegerField(_('billing amount'), default=1, help_text='Is how many `bill_rate_type` will get charged, ex: 3 hours, 15 mins, etc.')
    bill_rate_type = models.CharField(_('billing rate type'), max_length=255, choices=RateType.choices, default=RateType.FLAT, blank=True, help_text='Is the type of pricing model')
    bill_min_payment = models.DecimalField(_('billing minimum payment'), max_digits=32, decimal_places=2, default=0, help_text='Defines the minimum that the provider will charge for this service')
    bill_no_show_fee = models.DecimalField(_('billing no show fee'), max_digits=32, decimal_places=2, default=0, help_text='Defines the fee that the provider will charge if the service is not completed')
    bill_rate = models.DecimalField(_('billing rate'), max_digits=32, decimal_places=2, default=0, help_text='Is how much the provider charges per `bill_rate_type`')
    bill_rate_minutes_threshold = models.DecimalField(_('billing minutes rate threshold'), max_digits=32, decimal_places=2, default=None, null=True, blank=True, help_text='Defines the minimum amount of minutes that will count as a full hour if `bill_rate_type` is hourly')

    class Meta:
        verbose_name = _('service')
        verbose_name_plural = _('services')

    def __str__(self):
        return F"{self.business} by {self.provider}"

    def delete_related(self):
        # TODO review since this is a m2m
        self.bookings.all().delete()

class Rate(ExtendableModel, HistoricalModel, SoftDeletableModel):
    class RateType(models.TextChoices):
        FLAT = 'FLAT', _('Flat')
        PER_ASSIGNATION = 'PER_ASSIGNATION', _('Per Assignation')
        PER_HOURS = 'PER_HOURS', _('Per Hours')
        PER_MINUTES = 'PER_MINUTES', _('Per Minutes')
        QUANTITY = 'QUANTITY', _('Quantity')

    global_setting = models.ForeignKey(GlobalSetting, on_delete=models.CASCADE, related_name='rates', null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='rates', null=True, blank=True)
    root = models.ForeignKey(ServiceRoot, null=True, blank=True, on_delete=models.PROTECT, related_name='rates')
    bill_amount = models.PositiveIntegerField(_('billing amount'), default=1, help_text='Is how many `bill_rate_type` will get charged, ex: 3 hours, 15 mins, etc.')
    bill_rate_type = models.CharField(_('billing rate type'), max_length=255, choices=RateType.choices, default=RateType.FLAT, blank=True, help_text='Is the type of pricing model')
    bill_min_payment = models.DecimalField(_('billing minimum payment'), max_digits=32, decimal_places=2, default=0, help_text='Defines the minimum that the provider will charge for this service')
    bill_no_show_fee = models.DecimalField(_('billing no show fee'), max_digits=32, decimal_places=2, default=0, help_text='Defines the fee thatr will be charge if the rate is not completed')
    bill_rate = models.DecimalField(_('billing rate'), max_digits=32, decimal_places=2, default=0, help_text='Is how much it is charged per `bill_rate_type`')
    bill_rate_minutes_threshold = models.DecimalField(_('billing minutes rate threshold'), max_digits=32, decimal_places=2, default=None, null=True, blank=True, help_text='Defines the minimum amount of minutes that will count as a full hour if `bill_rate_type` is hourly')

    class Meta:
        verbose_name = _('rate')
        verbose_name_plural = _('rates')

    def __str__(self):
        return F"{self.id} - {self.root}"

    def delete_related(self):
        # TODO review since this is a m2m
        self.bookings.all().delete()

class CompanyRate(ExtendableModel, HistoricalModel, SoftDeletableModel):
    class RateType(models.TextChoices):
        FLAT = 'FLAT', _('Flat')
        PER_ASSIGNATION = 'PER_ASSIGNATION', _('Per Assignation')
        PER_HOURS = 'PER_HOURS', _('Per Hours')
        PER_MINUTES = 'PER_MINUTES', _('Per Minutes')
        QUANTITY = 'QUANTITY', _('Quantity')

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='company_rates')
    language = models.CharField(_('language'), max_length=255, null=True, blank=True, default=None, help_text='Defines the language that the company will charge for this rate')
    root = models.ForeignKey(ServiceRoot, null=True, blank=True, on_delete=models.PROTECT, related_name='company_rates')
    bill_amount = models.PositiveIntegerField(_('billing amount'), default=1, help_text='Is how many `bill_rate_type` will get charged, ex: 3 hours, 15 mins, etc.')
    bill_rate_type = models.CharField(_('billing rate type'), max_length=255, choices=RateType.choices, default=RateType.FLAT, blank=True, help_text='Is the type of pricing model')
    bill_min_payment = models.DecimalField(_('billing minimum payment'), max_digits=32, decimal_places=2, default=0, help_text='Defines the minimum that the company will charge for this service')
    bill_no_show_fee = models.DecimalField(_('billing no show fee'), max_digits=32, decimal_places=2, default=0, help_text='Defines the fee that the company will charge if the service is not completed')
    bill_rate = models.DecimalField(_('billing rate'), max_digits=32, decimal_places=2, default=0, help_text='Is how much the company charges per `bill_rate_type`')
    bill_rate_minutes_threshold = models.DecimalField(_('billing minutes rate threshold'), max_digits=32, decimal_places=2, default=None, null=True, blank=True, help_text='Defines the minimum amount of minutes that will count as a full hour if `bill_rate_type` is hourly')

    class Meta:
        verbose_name = _('company rate')
        verbose_name_plural = _('company rates')

    def __str__(self):
        return F"{self.root} by {self.company}"

    def delete_related(self):
        # TODO review since this is a m2m
        self.bookings.all().delete()

class ServiceArea(SoftDeletableModel, HistoricalModel):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='service_areas')
    country = models.TextField(_('country'), null=True, blank=True)
    state = models.TextField(_('state or province'), null=True, blank=True)
    county = models.TextField(_('county'), null=True, blank=True)
    city = models.TextField(_('city'), null=True, blank=True)
    zip = models.TextField(_('ZIP code'), null=True, blank=True)

    class Meta:
        verbose_name = _('service area')
        verbose_name_plural = _('service areas')

    def __str__(self):
        return F"{self.provider} works in: {self.country}, {self.state}, {self.county}, {self.city}, {self.zip}"


class Booking(ExtendableModel, HistoricalModel, SoftDeletableModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='bookings')
    companies = models.ManyToManyField(Company, related_name='bookings')
    operators = models.ManyToManyField(Operator, related_name='bookings')
    parent = models.ForeignKey("Booking", null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    service_root = models.ForeignKey(ServiceRoot, null=True, blank=True, on_delete=models.PROTECT, related_name='bookings')
    services = models.ManyToManyField(Service, related_name='bookings')
    created_at = models.DateTimeField(auto_now_add=True)
    public_id = models.CharField(max_length=30, null=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name='created_bookings')
    status = models.CharField(max_length=30, null=True)

    class Meta:
        verbose_name = _('booking')
        verbose_name_plural = _('bookings')

    def __str__(self):
        return F"Booking #{self.public_id} ({self.id})"

    def delete_related(self):
        self.events.all().delete()
        self.expenses.all().delete()
        self.notes.all().delete()
        self.offers.all().delete()


class Event(ExtendableModel, HistoricalModel, SoftDeletableModel, UniquifiableModel):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='events')

    affiliates = models.ManyToManyField(Affiliation, related_name='events')
    agents = models.ManyToManyField(Agent, related_name='events')
    payer = models.ForeignKey(Payer, on_delete=models.PROTECT, null=True, blank=True, related_name='events')
    payer_company = models.ForeignKey(Company, on_delete=models.PROTECT, null=True, blank=True, related_name='events_as_payer')
    requester = models.ForeignKey(Requester, on_delete=models.PROTECT, related_name='events')

    location = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, blank=True, related_name='events')
    meeting_url = models.URLField(_('meeting URL'), null=True, blank=True)
    start_at = models.DateTimeField(_('start date and time'))
    end_at = models.DateTimeField(_('end date and time'))
    arrive_at = models.DateTimeField(_('arrival date and time'), null=True, blank=True)
    observations = models.CharField(_('observations'), max_length=256, blank=True)
    description = models.CharField(_('description'), max_length=256, null=True, blank=True)

    class Meta:
        verbose_name = _('event')
        verbose_name_plural = _('events')

    def __str__(self):
        return F"Event #{self.id} - Booking ID: {self.booking.id} - {self.booking.public_id} - Status: {self.booking.status}"

    @property
    def is_onsite(self):
        return self.location is not None

    @property
    def is_online(self):
        return bool(self.meeting_url)

    @property
    def affiliates_ids(self):
        return list(self.affiliates.all().values_list('id', flat=True))
    
    def delete_related(self):
        self.reports.all().delete()


# Billing models
class Expense(HistoricalModel, SoftDeletableModel):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(_('amount'), max_digits=32, decimal_places=2)
    description = models.CharField(_('description'), max_length=256)
    quantity = models.IntegerField(_('quantity'))

    class Meta:
        verbose_name = _('expense')
        verbose_name_plural = _('expenses')

    def delete_related(self):
        pass


# PLACEHOLDER MODELS, review inheritance and functionality
class Rule(models.Model):
    # TODO many to many to all

    class Meta:
        verbose_name = _('rule')
        verbose_name_plural = _('rules')


class Ledger(SoftDeletableModel):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='ledgers')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name='ledgers')
    invoice = models.ForeignKey("Invoice", on_delete=models.PROTECT, related_name='ledgers')

    class Meta:
        verbose_name = _('ledger')
        verbose_name_plural = _('ledgers')

    def delete_related(self):
        raise NotImplementedError()


class Invoice(models.Model):
    class Meta:
        verbose_name = _('invoice')
        verbose_name_plural = _('invoices')


class Authorization(ExtendableModel, HistoricalModel, SoftDeletableModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        ACCEPTED = 'ACCEPTED', _('Accepted')
        REJECTED = 'REJECTED', _('Rejected')
        REFERRED = 'REFERRED', _('Referred')
        OVERRIDE = 'OVERRIDE', _('Override')

    authorizer = models.ForeignKey(Payer, on_delete=models.CASCADE, related_name='authorizations')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='authorizations')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, blank=True, null=True, related_name='authorizations')
    contact_via = models.CharField(max_length=32, choices=Contact.Via.choices, blank=True, null=True)
    events = models.ManyToManyField(Event, related_name='authorizations')
    last_updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)

    class Meta:
        verbose_name = _('authorization')
        verbose_name_plural = _('authorizations')

    def __str__(self):
        return F'{self.id} - {list(self.events.all().values_list("id", flat=True))} - {self.authorizer} - {self.company} - {self.status}'


class Notification(HistoricalModel, SoftDeletableModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        SUBMITTED = 'SUBMITTED', _('Submitted')
        SENT = 'SENT', _('Sent')
        FAILED = 'FAILED', _('Failed')

    class SendMethod(models.TextChoices):
        EMAIL = 'EMAIL', _('Email')
        FAX = 'FAX', _('Fax')

    template = models.CharField(max_length=128)
    data = models.JSONField()
    payload = models.JSONField()
    priority = models.IntegerField(default=50)

    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(default=None, null=True, blank=True)
    expected_send_at = models.DateTimeField(default=None, null=True, blank=True)
    sent_at = models.DateTimeField(default=None, null=True, blank=True)

    send_method = models.CharField(max_length=32, choices=SendMethod.choices)
    job_id = models.CharField(max_length=128, null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    status_message = models.TextField(null=True, blank=True)

    booking_to_log = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)


    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')

    def __str__(self):
        return F'{self.id} - template {self.template} - status {self.status} - via {self.send_method} - priority {self.priority}'


class Offer(HistoricalModel, ExtendableModel, SoftDeletableModel):
    class Status(models.TextChoices):
        REQUESTED = 'REQUESTED', _('Requested')
        AVAILABLE = 'AVAILABLE', _('Available')
        NOT_AVAILABLE = 'NOT_AVAILABLE', _('Not Available')
        PENDING_OFFER = 'PENDING_OFFER', _('Pending Offer')
        ACCEPTED = 'ACCEPTED', _('Accepted')
        REJECTED = 'REJECTED', _('Rejected')

    status = models.CharField(max_length=32, choices=Status.choices, default=Status.REQUESTED)
    last_updated_at = models.DateTimeField(auto_now=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='offers')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='offers')

    class Meta:
        verbose_name = _('offer')
        verbose_name_plural = _('offers')


class Report(HistoricalModel, ExtendableModel, SoftDeletableModel):
    status = models.CharField(max_length=128, default='Unreported')
    arrive_at = models.DateTimeField(_('Arrival Time'), null=True, blank=True)
    start_at = models.DateTimeField(_('Start Time'), null=True, blank=True)
    end_at = models.DateTimeField(_('End Time'), null=True, blank=True)
    observations = models.TextField(blank=True, default='')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reports')
    
    class Meta:
        verbose_name = _('report')
        verbose_name_plural = _('reports')

    def __str__(self):
        return F'{self.id} - Status: {self.status} - Event: {self.event.id}'


class Note(SoftDeletableModel):
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner', null=True)
    text = models.TextField(blank=True, default='')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='notes', blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='notes', blank=True, null=True)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='notes', blank=True, null=True)
    payer = models.ForeignKey(Payer, on_delete=models.CASCADE, related_name='notes', blank=True, null=True)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='notes', blank=True, null=True)
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE, related_name='notes', blank=True, null=True)

    class Meta:
        verbose_name = _('note')
        verbose_name_plural = _('notes')


class ExternalApiToken(models.Model):
    api_name = models.CharField(max_length=255)
    client_id = models.CharField(max_length=255)

    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    expiration_timestamp = models.IntegerField()
    scope = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('external API token')
        verbose_name_plural = _('external API tokens')
        unique_together = ['api_name', 'client_id']

    def __str__(self):
        return F'{self.api_name} - {self.client_id}'

    @property
    def is_expired(self):
        return self.expiration_timestamp < time.time()

    @property
    def expires_at(self):
        return datetime.fromtimestamp(self.expiration_timestamp)

    def invalidate(self):
        self.access_token = None
        self.refresh_token = None
        self.expiration_timestamp = 0
        self.scope = None
        self.save()

