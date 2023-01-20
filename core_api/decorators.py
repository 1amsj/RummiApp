from functools import wraps
from typing import Type

from django.db import models
from django.utils.translation import gettext_lazy as _

from core_api.exceptions import BadRequestException, NotFoundException


def raise_instead(exception: Type[Exception], expected: Type[Exception], msg='', append_error=True):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except expected as e:
                raise exception(f"{msg}{str(e) if append_error else ''}")
        return wrapper
    return decorate


expect_key_error = raise_instead(BadRequestException, KeyError, _('Missing argument: '), True)


def expect_does_not_exist(model: Type[models.Model]):
    # noinspection PyTypeChecker
    return raise_instead(NotFoundException, model.DoesNotExist, F'{model._meta.verbose_name} {_("does not exist")}', False)
