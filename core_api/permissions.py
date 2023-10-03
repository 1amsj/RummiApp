from typing import Type

from rest_framework import permissions

class CanPushFaxNotifications(permissions.BasePermission):
    """
    Custom permission to only allow fax service providers to push fax notifications.
    """

    def has_permission(self, request, view):
        return request.user.has_perm('core_backend.can_push_fax_notifications')


def can_manage_model_basic_permissions(model_name: str) -> Type[permissions.BasePermission]:
    """
    Custom permission to only allow users with the appropriate permissions to manage a model.
    """

    class CanManageModel(permissions.BasePermission):
        message = 'You do not have permission to perform this operation'

        def has_permission(self, request, view):
            method = request.method
            user = request.user
            return (method == 'GET' and user.has_perm(F'core_backend.view_{model_name}')) \
                or (method == 'POST' and user.has_perm(F'core_backend.add_{model_name}')) \
                or (method == 'PUT' and user.has_perm(F'core_backend.change_{model_name}')) \
                or (method == 'PATCH' and user.has_perm(F'core_backend.change_{model_name}')) \
                or (method == 'DELETE' and user.has_perm(F'core_backend.delete_{model_name}'))

    return CanManageModel


class CanManageOperators(permissions.BasePermission):
    """
    Custom permission to only allow users with the appropriate permissions to manage operators.
    """

    message = 'You do not have permission to perform this operation'

    def has_permission(self, request, view):
        method = request.method
        user = request.user
        return (method == 'GET' and user.is_authenticated and user.has_perm('core_backend.view_operator')) \
            or (method == 'POST') \
            or (method == 'PUT' and user.is_authenticated and user.has_perm('core_backend.change_operator')) \
            or (method == 'PATCH' and user.is_authenticated and user.has_perm('core_backend.change_operator')) \
            or (method == 'DELETE' and user.is_authenticated and user.has_perm('core_backend.delete_operator'))
