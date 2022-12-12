from django.urls import path, register_converter
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.views import TokenRefreshView

from . import converters, views

register_converter(converters.NumericIdConverter, 'id')


def path_optional(route, param: str, *args, **kwargs) -> list:
    def build_path(r):
        return path(r, *args, **kwargs)

    if route[-1] != '/':
        route += '/'

    return [
        build_path(route),
        build_path(route + param + '/'),
    ]


def path_optionals_xor(route, params: list, *args, **kwargs) -> list:
    def build_path(r):
        return path(r, *args, **kwargs)

    if route[-1] != '/':
        route += '/'

    return [
       build_path(route),
    ] + [
       build_path(route + p + '/')
       for p in params
    ]


urlpatterns = [
    path('token/', csrf_exempt(views.CustomTokenObtainPairView.as_view()), name='token_obtain_pair'),
    path('token/refresh/', csrf_exempt(TokenRefreshView.as_view()), name='token_refresh'),
    path('register/', views.RegisterView.as_view(), name='auth_register'),
    path('test/', views.test_end_point, name='test'),
    path('version/', views.get_version, name='test'),

    *path_optional('users/', '<id:user_id>', views.ManageUsers.as_view(), name='manage_users'),
    path('agents/', views.ManageAgents.as_view(), name='manage_agents'),
    path('operators/', views.ManageOperators.as_view(), name='manage_operators'),
    path('payers/', views.ManagePayers.as_view(), name='manage_payers'),
    *path_optionals_xor('providers/', ['<id:provider_id>', '<str:business_name>'], views.ManageProviders.as_view(), name='manage_providers'),
    path('recipients/', views.ManageRecipients.as_view(), name='manage_recipients'),
    path('requesters/', views.ManageRequesters.as_view(), name='manage_requesters'),
    path('affiliations/', views.ManageAffiliations.as_view(), name='manage_affiliations'),

    *path_optionals_xor('bookings/', ['<id:booking_id>', '<str:business_name>'], views.ManageBooking.as_view(), name='manage_booking'),
    *path_optional('companies/', '<id:company_id>', views.ManageCompany.as_view(), name='manage_companies'),
    *path_optionals_xor('events/', ['<id:event_id>', '<str:business_name>'], views.ManageEvents.as_view(), name='manage_events'),
    *path_optional('services/', '<str:business_name>', views.ManageService.as_view(), name='manage_services'),

    path('', views.get_routes)
]
