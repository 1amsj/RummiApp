from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField


# Generic helpers
class AdditionalProperty(models.Model):
    parent_id = models.PositiveIntegerField()
    parent_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    parent = GenericForeignKey('parent_ct', 'parent_id')
    business = models.CharField(_('business'), max_length=128)
    key = models.CharField(_('key'), max_length=256)
    value = models.CharField(_('value'), max_length=512)

    class Meta:
        verbose_name = _('additional property')
        verbose_name_plural = _('additional properties')
        indexes = [
            models.Index(fields=["parent_ct", "business", "key"]),
            models.Index(fields=["parent_id", "key"]),
        ]
        unique_together = ["parent_id", "business", "key"]


class ExtendableModel(models.Model):
    extra = GenericRelation(AdditionalProperty, 'parent_id', 'parent_ct', verbose_name=_('extra data'))

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
class Contact(models.Model):
    phone = PhoneNumberField(_('phone number'), blank=True)
    fax = PhoneNumberField(_('fax number'), blank=True)

    class Meta:
        verbose_name = _('contact')
        verbose_name_plural = _('contacts')


class Company(models.Model):
    contact = models.OneToOneField(Contact, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.OneToOneField("Location", on_delete=models.SET_NULL, related_name='owner', null=True, blank=True)
    name = models.CharField(_('name'), max_length=128)
    type = models.CharField(_('type'), max_length=128)  # TODO review
    send_method = models.CharField(_('send method'), max_length=128)  # TODO review, probably change to an enum
    on_hold = models.BooleanField(_('on hold'))

    class Meta:
        verbose_name = _('company')
        verbose_name_plural = _('companies')

    def __str__(self):
        return F"{self.name} ({self.type})"


class Location(models.Model):
    address = models.CharField(_('address'), max_length=128, blank=True)
    city = models.CharField(_('city'), max_length=128, blank=True)
    state = models.CharField(_('state or province'), max_length=128, blank=True)
    country = models.CharField(_('country'), max_length=128, blank=True)
    zip = models.CharField(_('ZIP code'), max_length=10, blank=True)

    class Meta:
        verbose_name = _('location')
        verbose_name_plural = _('locations')

    def __str__(self):
        return F"{self.country}, {self.state}, {self.city}, {self.address}"


# User models
class User(AbstractUser, AbstractPerson):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees', null=True, blank=True)
    # TODO check if "role" column referes to consumer/provider/payer/agent or something else, and add it

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
    def is_requestor(self):
        return hasattr(self, 'as_requestor') and self.as_requestor is not None

    @property
    def is_payer(self):
        return hasattr(self, 'as_payer') and self.as_payer is not None


class Agent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='as_agents')
    role = models.CharField(_('role'), max_length=64)

    class Meta:
        verbose_name = _('agent')
        verbose_name_plural = _('agents')
        unique_together = ('user', 'role',)

    def __str__(self):
        return '[%s (agent)] %s' % (self.role, self.user)


class Operator(models.Model):
    """Staff who maintain the platform"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_operator')
    hiring_date = models.DateField(_('hiring date'))

    class Meta:
        verbose_name = verbose_name_plural = _('operator data')

    def __str__(self):
        return '[Operator] %s' % self.user


class Payer(models.Model):
    """Who pays the service invoice"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_payer')
    method = models.CharField(_('paying method'), max_length=64)

    class Meta:
        verbose_name = verbose_name_plural = _('payer data')

    def __str__(self):
        return '[Payer] %s' % self.user


class Provider(ExtendableModel):
    """Who provides the service"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_provider')

    class Meta:
        verbose_name = verbose_name_plural = _('provider data')

    def __str__(self):
        return '[Provider] %s' % self.user


class Recipient(ExtendableModel):
    """Who receives the service"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_recipient')

    class Meta:
        verbose_name = verbose_name_plural = _('recipient data')

    def __str__(self):
        return '[Recipient] %s' % self.user


class Requestor(models.Model):
    """Who requests the service case for the Recipient"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_requestor')

    class Meta:
        verbose_name = verbose_name_plural = _('requestor data')

    def __str__(self):
        return '[Requestor] %s' % self.user


# Service models
class Rule(models.Model):
    # TODO many to many to all

    class Meta:
        verbose_name = _('rule')
        verbose_name_plural = _('rules')


class Category(models.Model):
    name = models.CharField(_('name'), max_length=64)
    supercategory = models.ForeignKey('self', on_delete=models.CASCADE, related_name='subcategories',
                                      null=True, blank=True)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    @property
    def is_root(self):
        return self.supercategory is None

    @property
    def has_children(self):
        return hasattr(self, 'subcategories') and self.subcategories is not None

    @property
    def has_services(self):
        return hasattr(self, 'services') and self.services is not None


class ProviderService(ExtendableModel):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='providers')
    service = models.ForeignKey("Service", on_delete=models.CASCADE, related_name='services')

    class Meta:
        verbose_name = _('provider service')
        verbose_name_plural = _('provider services')


class Service(models.Model):
    categories = models.ManyToManyField(Category, related_name='services')
    providers = models.ManyToManyField(Provider, through=ProviderService)

    class Meta:
        verbose_name = _('service')
        verbose_name_plural = _('services')


class Booking(ExtendableModel):
    operator = models.ManyToManyField(Operator, related_name='bookings')
    payer = models.ForeignKey(Payer, on_delete=models.PROTECT, related_name='bookings')
    provider_services = models.ManyToManyField(ProviderService, related_name='bookings')
    recipients = models.ManyToManyField(Recipient, related_name='bookings')
    requestor = models.ForeignKey(Requestor, on_delete=models.PROTECT, related_name='bookings')

    class Meta:
        verbose_name = _('booking')
        verbose_name_plural = _('bookings')


class Event(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='events')
    location = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, blank=True, related_name='events')
    meeting_url = models.URLField(_('meeting URL'), null=True, blank=True)
    date = models.DateField(_('date'))
    start_time = models.TimeField(_('start time'))
    end_time = models.TimeField(_('end time'))
    observations = models.CharField(_('observations'), max_length=256, blank=True)

    class Meta:
        verbose_name = _('event')
        verbose_name_plural = _('events')

    @property
    def is_onsite(self):
        return self.location is not None

    @property
    def is_online(self):
        return bool(self.meeting_url)


class Ledger(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='ledgers')
    invoice = models.ForeignKey("Invoice", on_delete=models.PROTECT, related_name='ledgers')

    class Meta:
        verbose_name = _('ledger')
        verbose_name_plural = _('ledgers')


class Invoice(models.Model):
    class Meta:
        verbose_name = _('invoice')
        verbose_name_plural = _('invoices')
