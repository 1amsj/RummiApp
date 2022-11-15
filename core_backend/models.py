from typing import Optional

from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from simple_history.models import HistoricalRecords


# Generic helpers
class Extra(models.Model):
    parent_id = models.PositiveIntegerField()
    parent_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    parent = GenericForeignKey('parent_ct', 'parent_id')
    business = models.ForeignKey("Business", on_delete=models.CASCADE)
    key = models.CharField(_('key'), max_length=256)
    value = models.CharField(_('value'), max_length=512)

    class Meta:
        verbose_name = verbose_name_plural = _('extra data')
        indexes = [
            models.Index(fields=["parent_ct", "business", "key"]),
            models.Index(fields=["parent_id", "key"]),
        ]
        unique_together = ["parent_ct", "parent_id", "business", "key"]

    def __str__(self):
        return F"[{self.parent_ct} {self.parent_id}] {self.business}, {self.key}: {self.value}"


class ExtraQuerySet(models.QuerySet):
    def prefetch_extra(self, business: Optional["Business"] = None):
        ct = ContentType.objects.get_for_model(self.model)
        query = Q(extra__parent_ct=ct)
        if business:
            query &= Q(extra__business=business)
        return self.prefetch_related('extra').filter(query)

    def filter_by_extra(self, related_prefix='', **fields):
        from core_backend.services import iter_extra_attrs
        queryset = self
        for (k, v) in iter_extra_attrs(self.model, fields):
            params = k.split('__')
            query_key = F'{related_prefix}extra__key'
            query_value = F'{related_prefix}extra__value'
            if len(params) > 1:
                query_value += F'__{params[1]}'
            queryset = queryset.filter(**{query_key: params[0], query_value: v})
        return queryset


class ExtendableModel(models.Model):
    extra = GenericRelation(Extra, 'parent_id', 'parent_ct', verbose_name=_('extra data'))

    objects = ExtraQuerySet.as_manager()

    class Meta:
        abstract = True

    def get_extra_attrs(self, business: Optional["Business"] = None) -> dict:
        queryset = self.extra.all()
        if business:
            queryset = queryset.filter(business=business)
        return {
            e.key: e.value
            for e in queryset
        }


class HistoricalModel(models.Model):
    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True


# Abstract models
class AbstractPerson(models.Model):
    contact = models.OneToOneField("Contact", on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    national_id = models.CharField(_('national ID'), max_length=50, blank=True)
    ssn = models.CharField(_('social security number'), max_length=50, blank=True)

    class Meta:
        abstract = True
        ordering = ['last_name', 'first_name']
        verbose_name = _('person')
        verbose_name_plural = _('people')


# General data models
class Contact(HistoricalModel):
    email = models.EmailField(_("email address"), blank=True)
    phone = PhoneNumberField(_('phone number'), blank=True)
    fax = PhoneNumberField(_('fax number'), blank=True)

    class Meta:
        verbose_name = _('contact')
        verbose_name_plural = _('contacts')

    def __str__(self):
        return F"{self.email}, {self.phone}, {self.fax}"


class Company(HistoricalModel):
    contact = models.OneToOneField(Contact, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.OneToOneField("Location", on_delete=models.SET_NULL, related_name='owner', null=True, blank=True)
    name = models.CharField(_('name'), max_length=128)
    type = models.CharField(_('type'), max_length=128)
    send_method = models.CharField(_('send method'), max_length=128)
    on_hold = models.BooleanField(_('on hold'))

    class Meta:
        verbose_name = _('company')
        verbose_name_plural = _('companies')

    def __str__(self):
        return F"{self.name} ({self.type})"


class Location(models.Model):
    address = models.CharField(_('address'), max_length=128)
    city = models.CharField(_('city'), max_length=128)
    state = models.CharField(_('state or province'), max_length=128)
    country = models.CharField(_('country'), max_length=128)
    zip = models.CharField(_('ZIP code'), max_length=10, blank=True)

    class Meta:
        verbose_name = _('location')
        verbose_name_plural = _('locations')

    def __str__(self):
        return F"{self.country}, {self.state}, {self.city}, {self.address}, {self.zip}"


# User models
class User(AbstractUser, AbstractPerson, HistoricalModel):
    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    @property
    def is_operator(self):
        return hasattr(self, 'as_operator') and self.as_operator is not None

    @property
    def is_provider(self):
        return hasattr(self, 'as_provider') and self.as_provider is not None

    @property
    def is_recipient(self):
        return hasattr(self, 'as_recipient') and self.as_recipient is not None

    @property
    def is_requester(self):
        return hasattr(self, 'as_requester') and self.as_requester is not None

    @property
    def is_payer(self):
        return hasattr(self, 'as_payer') and self.as_payer is not None


class Agent(ExtendableModel, HistoricalModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='as_agents')
    companies = models.ManyToManyField(Company, related_name='agents')
    role = models.CharField(_('role'), max_length=64)

    class Meta:
        verbose_name = _('agent')
        verbose_name_plural = _('agents')
        unique_together = ('user', 'role',)

    def __str__(self):
        return F"[{self.role} (agent)] {self.user}"


class Operator(HistoricalModel):
    """Staff who maintain the platform"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_operator')
    companies = models.ManyToManyField(Company, related_name='operators')
    hiring_date = models.DateField(_('hiring date'))

    class Meta:
        verbose_name = verbose_name_plural = _('operator data')

    def __str__(self):
        return F"[Operator] {self.user}"


class Payer(HistoricalModel):
    """Who pays the service invoice"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_payer')
    companies = models.ManyToManyField(Company, related_name='payers')
    method = models.CharField(_('paying method'), max_length=64)

    class Meta:
        verbose_name = verbose_name_plural = _('payer data')

    def __str__(self):
        return F"[Payer] {self.user}"


class Provider(ExtendableModel, HistoricalModel):
    """Who provides the service"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_provider')
    companies = models.ManyToManyField(Company, related_name='providers')

    class Meta:
        verbose_name = verbose_name_plural = _('provider data')

    def __str__(self):
        return F"[Provider] {self.user}"


class Recipient(ExtendableModel, HistoricalModel):
    """Who receives the service"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_recipient')
    companies = models.ManyToManyField(Company, related_name='recipients', through="Affiliation")

    class Meta:
        verbose_name = verbose_name_plural = _('recipient data')

    def __str__(self):
        return F"[Recipient] {self.user}"


class Affiliation(ExtendableModel, HistoricalModel):
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE, related_name='affiliations')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='affiliations')

    class Meta:
        verbose_name = _('affiliation')
        verbose_name_plural = _('affiliations')

    def __str__(self):
        return F"[Affiliation] {self.recipient.user} with {self.company or 'no company'}"


class Requester(HistoricalModel):
    """Who requests the service case for the Recipient"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_requester')
    companies = models.ManyToManyField(Company, related_name='requesters')

    class Meta:
        verbose_name = verbose_name_plural = _('requester data')

    def __str__(self):
        return F"[Requester] {self.user}"


# Service models
class Rule(models.Model):
    # TODO many to many to all

    class Meta:
        verbose_name = _('rule')
        verbose_name_plural = _('rules')


class Business(models.Model):
    name = models.CharField(_('business'), max_length=128, unique=True)

    class Meta:
        verbose_name = _('business')
        verbose_name_plural = _('businesses')

    def __str__(self):
        return self.name


class Category(ExtendableModel):
    name = models.CharField(_('name'), max_length=64)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self):
        return self.name

    @property
    def has_services(self):
        return hasattr(self, 'services') and self.services is not None


class Service(ExtendableModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='services')
    categories = models.ManyToManyField(Category, related_name='services')
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='services')

    class Meta:
        verbose_name = _('service')
        verbose_name_plural = _('services')

    def __str__(self):
        return F"{self.business} by {self.provider}"


class Booking(ExtendableModel, HistoricalModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='bookings')
    operators = models.ManyToManyField(Operator, related_name='bookings')
    services = models.ManyToManyField(Service, related_name='bookings')

    # Constraints
    categories = models.ManyToManyField(Category, related_name='bookings')
    agents_companies = models.ManyToManyField(Company, related_name='cstr_booking_agents')
    operators_companies = models.ManyToManyField(Company, related_name='cstr_booking_operators')
    payers_companies = models.ManyToManyField(Company, related_name='cstr_booking_payers')
    providers_companies = models.ManyToManyField(Company, related_name='cstr_booking_providers')
    recipients_companies = models.ManyToManyField(Company, related_name='cstr_booking_recipients')
    requesters_companies = models.ManyToManyField(Company, related_name='cstr_booking_requesters')

    class Meta:
        verbose_name = _('booking')
        verbose_name_plural = _('bookings')

    def __str__(self):
        return super(Booking, self).__str__()


class Event(HistoricalModel):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='events')

    affiliates = models.ManyToManyField(Affiliation, related_name='events')
    agents = models.ManyToManyField(Agent, related_name='events')
    payer = models.ForeignKey(Payer, on_delete=models.PROTECT, related_name='events')
    requester = models.ForeignKey(Requester, on_delete=models.PROTECT, related_name='events')

    location = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, blank=True, related_name='events')
    meeting_url = models.URLField(_('meeting URL'), null=True, blank=True)
    start_at = models.DateTimeField(_('start date and time'))
    end_at = models.DateTimeField(_('end date and time'))
    observations = models.CharField(_('observations'), max_length=256, blank=True)

    class Meta:
        verbose_name = _('event')
        verbose_name_plural = _('events')

    def __str__(self):
        return F"From {self.start_at} to {self.end_at}, {'onsite' if self.is_onsite else 'online'}"

    @property
    def is_onsite(self):
        return self.location is not None

    @property
    def is_online(self):
        return bool(self.meeting_url)


class Ledger(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='ledgers')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name='ledgers')
    invoice = models.ForeignKey("Invoice", on_delete=models.PROTECT, related_name='ledgers')

    class Meta:
        verbose_name = _('ledger')
        verbose_name_plural = _('ledgers')


class Invoice(models.Model):
    class Meta:
        verbose_name = _('invoice')
        verbose_name_plural = _('invoices')
