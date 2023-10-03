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
    path('register/', views.register_user, name='auth_register'),
    path('test/', views.test_end_point, name='test'),
    path('version/', views.get_version, name='test'),

    *path_optionals_xor('users/', ['<id:user_id>', '<str:business_name>'], views.ManageUsers.as_view(), name='manage_users'),
    path('operators/', views.ManageOperators.as_view(), name='manage_operators'),
    path('payers/', views.ManagePayers.as_view(), name='manage_payers'),
    *path_optionals_xor('providers/', ['<id:provider_id>', '<str:business_name>'], views.ManageProviders.as_view(), name='manage_providers'),
    *path_optionals_xor('agents/', ['<id:agent_id>', '<str:business_name>'], views.ManageAgents.as_view(), name='manage_agents'),
    *path_optionals_xor('recipients/', ['<id:recipient_id>', '<str:business_name>'], views.ManageRecipients.as_view(), name='manage_recipients'),
    path('requesters/', views.ManageRequesters.as_view(), name='manage_requesters'),
    path('notes/', views.ManageNote.as_view(), name='manage_notes'),
    *path_optionals_xor('offers/', ['<id:offer_id>', '<str:business_name>'], views.ManageOffers.as_view(), name='manage_offers'),
    
    *path_optional('notifications/', '<id:notification_id>', views.ManageNotifications.as_view(), name='manage_notifications'),

    *path_optional('affiliations/', '<str:business_name>', views.ManageAffiliations.as_view(), name='manage_affiliations'),
    *path_optional('authorizations/', '<id:authorization_id>', views.ManageAuthorizations.as_view(), name='manage_authorizations'),
    *path_optionals_xor('bookings/', ['<id:booking_id>', '<str:business_name>'], views.ManageBooking.as_view(), name='manage_booking'),
    *path_optional('categories/', '<id:category_id>', views.ManageCategories.as_view(), name='manage_categories'),
    *path_optional('companies/', '<id:company_id>', views.ManageCompany.as_view(), name='manage_companies'),
    *path_optionals_xor('events/', ['<id:event_id>', '<str:business_name>'], views.ManageEvents.as_view(), name='manage_events'),
    *path_optional('expenses/', '<id:expense_id>', views.ManageExpenses.as_view(), name='manage_expenses'),
    *path_optional('languages/', '<id:language_id>', views.ManageLanguages.as_view(), name='manage_languages'),
    *path_optional('services/', '<str:business_name>', views.ManageService.as_view(), name='manage_services'),
    *path_optional('service_roots/', '<id:service_root_id>', views.ManageServiceRoot.as_view(), name='manage_service_roots'),

    path('search/', views.search_bookings, name='search'),

    path('notifications/fax/', views.handle_fax_push_notification, name='fax_push_notification'),

    path('', views.get_routes)
]
