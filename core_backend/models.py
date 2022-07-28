from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField


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
class AdditionalParty(AbstractPerson):
    role = models.CharField(_('role'), max_length=128)

    class Meta:
        verbose_name = _('additional party')
        verbose_name_plural = _('additional parties')


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
    def is_consumer(self):
        return hasattr(self, 'as_consumer') and self.as_consumer is not None

    @property
    def is_provider(self):
        return hasattr(self, 'as_provider') and self.as_provider is not None

    @property
    def is_payer(self):
        return hasattr(self, 'as_payer') and self.as_payer is not None

    @property
    def is_agent(self):
        return hasattr(self, 'as_agent') and self.as_agent is not None


class Provider(models.Model):
    """Who provides the service"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_provider', primary_key=True)

    class Meta:
        verbose_name = verbose_name_plural = _('provider data')

    @property
    def is_certified(self):
        return hasattr(self, 'certificates') and self.certificates is not None

    def __str__(self):
        return '[Provider] %s' % self.user


class Consumer(models.Model):
    """Who receives the service case"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_consumer', primary_key=True)

    class Meta:
        verbose_name = verbose_name_plural = _('consumer data')

    def __str__(self):
        return '[Consumer] %s' % self.user


class Payer(models.Model):
    """Who pays the service bill"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_payer', primary_key=True)

    class Meta:
        verbose_name = verbose_name_plural = _('payer data')

    def __str__(self):
        return '[Payer] %s' % self.user


class Agent(models.Model):
    """Who requests the service case for the Customer"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='as_agent', primary_key=True)

    class Meta:
        verbose_name = verbose_name_plural = _('agent data')

    def __str__(self):
        return '[Agent] %s' % self.user


# Service models
class Certificate(models.Model):
    certificant = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='certificates')
    type = models.CharField(_('type'), max_length=128)
    code = models.CharField(_('code'), max_length=128)

    class Meta:
        verbose_name = _('certificate')
        verbose_name_plural = _('certificates')

    def __str__(self):
        return F"{self.type} - {self.certificant.user}"


class Claim(models.Model):
    additional_parties = models.ForeignKey(AdditionalParty, on_delete=models.PROTECT, related_name='additional_parties')
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name='consumer')

    class Meta:
        verbose_name = _('claim')
        verbose_name_plural = _('claims')


class Rule(models.Model):
    class Meta:
        verbose_name = _('rule')
        verbose_name_plural = _('rules')


class Service(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.PROTECT, related_name='services')
    rules = models.ManyToManyField(Rule, blank=False, related_name='services')
    description = models.CharField(_('description'), max_length=256, blank=True)

    class Meta:
        verbose_name = _('service')
        verbose_name_plural = _('services')


class Event(models.Model):
    claims = models.ManyToManyField(Claim, related_name='events')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='events')
    description = models.CharField(_('description'), max_length=256, blank=True)

    class Meta:
        verbose_name = _('event')
        verbose_name_plural = _('events')


class Case(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name='cases')
    consumers = models.ManyToManyField(Consumer, related_name='cases')
    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name='cases')
    location = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, blank=True, related_name='cases')
    date = models.DateField(_('date'))
    time = models.TimeField(_('time'))
    observations = models.CharField(_('observations'), max_length=256, blank=True)
    url = models.CharField(_('video URL'), max_length=2048, blank=True)

    class Meta:
        verbose_name = _('case')
        verbose_name_plural = _('cases')
    
    @property
    def is_on_site(self):
        return self.location is not None
    
    @property
    def is_online(self):
        return bool(self.url)


# Bill models
class Bill(models.Model):
    case = models.ForeignKey(Case, on_delete=models.PROTECT, related_name='bills')
    payer = models.ForeignKey(Payer, on_delete=models.PROTECT, related_name='bills')

    class Meta:
        verbose_name = _('bill')
        verbose_name_plural = _('bills')


# Interpreter models
class Interpreter(Provider):
    class Meta:
        verbose_name = _('interpreter')
        verbose_name_plural = _('interpreters')


class Patient(Consumer):
    class Meta:
        verbose_name = _('patient')
        verbose_name_plural = _('patients')


class Insurance(Payer):
    class Meta:
        verbose_name = _('insurance carrier')
        verbose_name_plural = _('insurance carriers')

    def clean(self):
        if self.user.company is None:
            raise ValidationError('A related company is required for an insurance carrier.')

    @property
    def company(self):
        return self.user.company


class ClinicStaff(Agent):
    agent_ptr = models.OneToOneField(Agent, on_delete=models.CASCADE, related_name='clinic_staff', parent_link=True)

    class Meta:
        verbose_name = _('clinic staff')
        verbose_name_plural = _('clinic staves')

    def clean(self):
        if self.user.company is None:
            raise ValidationError('A related clinic (company) is required for an insurance carrier.')

    @property
    def clinic(self):
        return self.user.company
