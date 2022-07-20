from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField


# General data models
class Contact(models.Model):
    phone = PhoneNumberField(_('phone number'), blank=True)
    fax = PhoneNumberField(_('fax number'), blank=True)
    address = models.CharField(_('address'), max_length=126, blank=True)
    city = models.CharField(_('city'), max_length=126, blank=True)
    state = models.CharField(_('state or province'), max_length=126, blank=True)
    country = models.CharField(_('country'), max_length=126, blank=True)
    zip = models.CharField(_('ZIP code'), max_length=10, blank=True)


class Company(models.Model):
    name = models.CharField(_('name'), max_length=126)
    type = models.CharField(_('type'), max_length=126)  # TODO review
    send_method = models.CharField(_('send method'), max_length=126)  # TODO review, probably change to an enum
    on_hold = models.BooleanField(_('on hold'))
    # TODO probably add fax and email here

    class Meta:
        verbose_name = _('company')
        verbose_name_plural = _('companies')

    def __str__(self):
        return F"{self.name} ({self.type})"


# User models
class User(AbstractUser):
    contact = models.OneToOneField(Contact, on_delete=models.SET_NULL, related_name='user', null=True, blank=True, verbose_name=_('contact'))
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='members', null=True, blank=True, verbose_name=_('company'))
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
    user = models.OneToOneField(User, models.CASCADE, related_name='as_provider', primary_key=True)

    class Meta:
        verbose_name = _('provider data')

    @property
    def is_certified(self):
        return hasattr(self, 'certificates') and self.certificates is not None

    def __str__(self):
        return '[Provider] %s' % self.user


class Certificate(models.Model):
    certificant = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='certificates')
    type = models.CharField(_('type'), max_length=126)
    code = models.CharField(_('code'), max_length=126)

    class Meta:
        verbose_name = _('certificate')
        verbose_name_plural = _('certificates')

    def __str__(self):
        return F"{self.type} - {self.certificant.user}"


class Consumer(models.Model):
    """Who receives the service case"""
    user = models.OneToOneField(User, models.CASCADE, related_name='as_consumer', primary_key=True)

    class Meta:
        verbose_name = _('consumer data')

    def __str__(self):
        return '[Consumer] %s' % self.user


class Payer(models.Model):
    """Who pays the service bill"""
    user = models.OneToOneField(User, models.CASCADE, related_name='as_payer', primary_key=True)

    class Meta:
        verbose_name = _('payer data')

    def __str__(self):
        return '[Payer] %s' % self.user


class Agent(models.Model):
    """Who requests the service case for the Customer"""
    user = models.OneToOneField(User, models.CASCADE, related_name='as_agent', primary_key=True)

    class Meta:
        verbose_name = _('agent data')

    def __str__(self):
        return '[Agent] %s' % self.user


# Service models
class Rule(models.Model):
    pass


class Service(models.Model):
    provider = models.ForeignKey(Provider, models.PROTECT, related_name='services')
    rules = models.ManyToManyField(Rule, blank=False, related_name='services')


class Event(models.Model):
    service = models.ForeignKey(Service, models.PROTECT, related_name='events')


class Case(models.Model):
    agent = models.ForeignKey(Agent, models.PROTECT, related_name='cases')
    consumers = models.ManyToManyField(Consumer, blank=False, related_name='cases')
    event = models.ForeignKey(Event, models.PROTECT, related_name='cases')


# Bill models
class Bill(models.Model):
    case = models.ForeignKey(Case, models.PROTECT, related_name='bills')
    payer = models.ForeignKey(Payer, models.PROTECT, related_name='bills')


# Interpreter models
class InterpreterCase(Case):
    pass
