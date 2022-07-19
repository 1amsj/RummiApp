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
    user = models.OneToOneField(User, models.CASCADE, 'as_provider', primary_key=True, parent_link=True)


class Consumer(models.Model):
    """Who receives the service case"""
    user = models.OneToOneField(User, models.CASCADE, 'as_consumer', primary_key=True, parent_link=True)


class Payer(models.Model):
    """Who pays the service bill"""
    user = models.OneToOneField(User, models.CASCADE, 'as_payer', primary_key=True, parent_link=True)


class Agent(models.Model):
    """Who requests the service case for the Customer"""
    user = models.OneToOneField(User, models.CASCADE, 'as_agent', primary_key=True, parent_link=True)


# Service models
class Rule(models.Model):
    pass


class Service(models.Model):
    provider = models.ForeignKey(Provider, models.PROTECT, related_name='services')
    rules = models.ManyToManyField(Rule, models.PROTECT, related_name='services')


class Event(models.Model):
    service = models.ForeignKey(Service, models.PROTECT, related_name='events')


class Case(models.Model):
    agent = models.ForeignKey(Agent, models.PROTECT, related_name='cases')
    consumers = models.ManyToManyField(Consumer, models.PROTECT, related_name='cases')
    event = models.ForeignKey(Event, models.PROTECT, related_name='cases')


# Bill models
class Bill(models.Model):
    case = models.ForeignKey(Case, models.PROTECT, related_name='bills')
    payer = models.ForeignKey(Payer, models.PROTECT, related_name='bills')


# Interpreter models
class InterpreterCase(Case):
    pass
