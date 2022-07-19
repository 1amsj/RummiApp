from django.contrib.auth.models import AbstractUser
from django.db import models


# User models
class User(AbstractUser):
    @property
    def is_consumer(self):
        return hasattr(self, 'as_consumer')

    @property
    def is_provider(self):
        return hasattr(self, 'as_provider')

    @property
    def is_payer(self):
        return hasattr(self, 'as_payer')

    @property
    def is_agent(self):
        return hasattr(self, 'as_agent')


class Provider(models.Model):
    """Who provides the service"""
    user = models.OneToOneField(User, models.CASCADE, related_name='as_provider', primary_key=True)

    class Meta:
        verbose_name = 'Provider data'

    def __str__(self):
        return '[Provider] %s' % self.user


class Consumer(models.Model):
    """Who receives the service case"""
    user = models.OneToOneField(User, models.CASCADE, related_name='as_consumer', primary_key=True)

    class Meta:
        verbose_name = 'Consumer data'

    def __str__(self):
        return '[Consumer] %s' % self.user


class Payer(models.Model):
    """Who pays the service bill"""
    user = models.OneToOneField(User, models.CASCADE, related_name='as_payer', primary_key=True)

    class Meta:
        verbose_name = 'Payer data'

    def __str__(self):
        return '[Payer] %s' % self.user


class Agent(models.Model):
    """Who requests the service case for the Customer"""
    user = models.OneToOneField(User, models.CASCADE, related_name='as_agent', primary_key=True)

    class Meta:
        verbose_name = 'Agent data'

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
