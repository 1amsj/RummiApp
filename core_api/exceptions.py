from rest_framework import status
from rest_framework.exceptions import APIException


class BadRequestException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Bad request'
    default_code = 'bad_request'


class NotFoundException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Not found'
    default_code = 'not_found'


class NotImplementedAPIException(APIException):
    status_code = status.HTTP_501_NOT_IMPLEMENTED
    default_detail = 'Not implemented'
    default_code = 'not_implemented'


class BusinessNotProvidedException(BadRequestException):
    default_detail = 'Bad request: business not provided'
