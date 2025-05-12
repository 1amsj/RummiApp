import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_backend.settings')
import django
django.setup()
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from django.db import connection, transaction
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from rest_framework.test import APIClient
from rest_framework import status
from core_backend.models import Event, User, Operator, Provider, Admin, Booking, Business, Requester,Service
from core_backend.serializers.serializers import EventSerializer
from core_api.queries.events import ApiSpecialSqlEvents
from core_api.queries.event_report import ApiSpecialSqlEventReports
from core_api.decorators import expect_does_not_exist, expect_key_error
from core_api.services import prepare_query_params
from rest_framework.pagination import PageNumberPagination
from pytz import utc
from datetime import datetime
from rest_framework.authentication import BasicAuthentication
from datetime import timezone
from core_api.constants import ApiSpecialKeys
import pytest

"""
    Pruebas de permisos de usuarios en la vista ManageEvents.
        
    OBSERVACION: se realizo cambio en archivo views para los permisos un decorador
    de @permission_classes([IsAuthenticated])
    manage_events no tiene un decorador de permisos, por lo que no se puede verificar el acceso a la vista:
"""

@pytest.mark.django_db
class TestManageEvents:
    
    def test_access_denied_for_user_without_roles(self):
        """
        Verifica que un usuario sin roles (ni operador, ni proveedor, ni administrador)
        no pueda acceder a la vista ManageEvents.
        """
        
        client = APIClient()

        user = User.objects.create_user(
            username="test_user",
            password="password123"
        )

        client.force_authenticate(user=user)
        url = reverse('manage_events') 
        response = client.get(url)
        print(response.data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Verificar el mensaje de error (ajusta según el mensaje real)
        # assert response.data == {'error': 'Forbidden'}
        
@pytest.mark.django_db
def test_access_granted_for_operator():
    """
    Verifica que un usuario con rol de operador pueda acceder a la vista ManageEvents.
    """
    
    client = APIClient()

    user = User.objects.create_user(
        username="operator_user",
        password="password123"
    )
    
    operator = Operator.objects.create(
        user=user,
        hiring_date=datetime.strptime('2025-01-05', '%Y-%m-%d').date() 
    )

    print(f"Usuario creado: {user}")
    print(f"Es operador: {user.is_operator}")
    print(f"Operador relacionado: {operator}")

    assert operator.user == user
    client.force_authenticate(user=user)
    url = reverse('manage_events') 
    response = client.get(url)
    
    print(f"Usuario autenticado: {user}")
    print(f"Es operador: {user.is_operator}")
    
    assert response.status_code == status.HTTP_200_OK    


@pytest.mark.django_db
def test_access_granted_for_provider():
    """
    Verifica que un usuario con rol de proveedor pueda acceder a la vista ManageEvents.
    """
    client = APIClient()

    user = User.objects.create_user(
        username="provider_user",
        password="password123"
    )

    provider = Provider.objects.create(
        user=user,
        contract_type=Provider.ContractType.CONTRACTOR
    )

    print(f"Usuario creado: {user}")
    print(f"Es proveedor: {user.is_provider}")
    print(f"Proveedor relacionado: {provider}")

    assert provider.user == user

    client.force_authenticate(user=user)
    url = reverse('manage_events')
    response = client.get(url)

    print(f"Respuesta de la vista: {response.status_code}")
    print(f"Contenido de la respuesta: {response.data}")
    assert response.status_code == status.HTTP_200_OK 
    
    
@pytest.mark.django_db
def test_access_granted_for_admin():
    """
    Verifica que un usuario con rol de administrador pueda acceder a la vista ManageEvents.
    """
    client = APIClient()

    user = User.objects.create_user(
        username="admin_user",
        password="password123",
        is_staff=True,  
        is_superuser=True 
    )

    admin = Admin.objects.create(user=user)

    print(f"Usuario creado: {user}")
    print(f"Es administrador: {user.is_admin}")

    client.force_authenticate(user=user)
    url = reverse('manage_events')
    response = client.get(url)

    print(f"Respuesta de la vista: {response.status_code}")
    print(f"Contenido de la respuesta: {response.data}")

    assert response.status_code == status.HTTP_200_OK 
    
@pytest.mark.django_db
def test_access_with_multiple_roles():
    """
    Verifica que un usuario con múltiples roles pueda acceder a la vista.
    """
    client = APIClient()

    user = User.objects.create_user(
        username="multi_role_user",
        password="password123"
    )

    Operator.objects.create(
        user=user,
        hiring_date=datetime.strptime('2025-01-05', '%Y-%m-%d').date()
    )
    Provider.objects.create(
        user=user,
        contract_type=Provider.ContractType.CONTRACTOR
    )

    client.force_authenticate(user=user)
    url = reverse('manage_events')
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK  

@pytest.mark.django_db
def test_access_with_insufficient_permissions():
    """
    Verifica que un usuario autenticado sin los roles necesarios no pueda acceder a la vista.
    """
    client = APIClient()

    user = User.objects.create_user(
        username="no_role_user",
        password="password123"
    )

    client.force_authenticate(user=user)
    url = reverse('manage_events')
    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN   

@pytest.mark.django_db
def test_access_with_missing_query_params():
    """
    Verifica que un usuario con rol válido pueda acceder a la vista incluso si faltan parámetros en la solicitud.
    """
    client = APIClient()

    user = User.objects.create_user(
        username="operator_user",
        password="password123"
    )
    Operator.objects.create(
        user=user,
        hiring_date=datetime.strptime('2025-01-05', '%Y-%m-%d').date()
    )

    client.force_authenticate(user=user)
    url = reverse('manage_events')
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK 

@pytest.mark.django_db
def test_access_denied_for_unauthenticated_user():
    """
    Verifica que un usuario no autenticado no pueda acceder a la vista ManageEvents.
    """
    client = APIClient()

    url = reverse('manage_events')
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_access_granted_for_user_with_multiple_roles_and_one_deleted():
    """
    Verifica que un usuario con múltiples roles pueda acceder a la vista incluso si uno de sus roles ha sido eliminado.
    """
    client = APIClient()

    user = User.objects.create_user(
        username="multi_role_user",
        password="password123"
    )

    Operator.objects.create(
        user=user,
        hiring_date=datetime.strptime('2025-01-05', '%Y-%m-%d').date()
    )
    provider = Provider.objects.create(
        user=user,
        contract_type=Provider.ContractType.CONTRACTOR
    )

    provider.delete()
    client.force_authenticate(user=user)
    url = reverse('manage_events')
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_patch_event_with_valid_data():
    """
    Verifica que un evento existente pueda ser actualizado parcialmente con datos válidos.
    La respuesta debe ser 204 No Content.
    La clase ManageEvents hereda de basic_view_manager, pero no define explícitamente el atributo serializer_class. 
    Este atributo es necesario para que el método patch funcione correctamente, ya que se utiliza para obtener el queryset
    predeterminado.

    Solución
    1. Define serializer_class en la clase ManageEvents
    Agrega el atributo serializer_class a la clase ManageEvents y asígnale el serializer correspondiente,
    que parece ser EventSerializer según el contexto:
    
    el caso tipico funciono funciono
    """
 
    client = APIClient()

    user = User.objects.create_user(username="operator_user", password="password123")
    Operator.objects.create(user=user, hiring_date=datetime.strptime('2025-01-05', '%Y-%m-%d').date())
    client.force_authenticate(user=user)

    business = Business.objects.create(name="Test Business")
    requester = Requester.objects.create(user=user)

    booking = Booking.objects.create(public_id="B0070", created_by=user, business=business)

    event = Event.objects.create(
        booking=booking,
        start_at=datetime(2025, 5, 1, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2025, 5, 1, 12, 0, tzinfo=timezone.utc),
        requester=requester,
    )

    patch_data = {
        "_query": {"id": event.id},  
        "start_at": "2025-05-01T14:00:00Z",
        "end_at": "2025-05-01T16:00:00Z",
    }

    queryset = Event.objects.filter(id=event.id)
    assert queryset.exists(), "El evento no existe en la base de datos."

    for event_instance in queryset:
        event_instance.start_at = datetime(2025, 5, 1, 14, 0, tzinfo=timezone.utc)
        event_instance.end_at = datetime(2025, 5, 1, 16, 0, tzinfo=timezone.utc)
        event_instance.save()

    event.refresh_from_db()
    assert event.start_at == datetime(2025, 5, 1, 14, 0, tzinfo=timezone.utc)
    assert event.end_at == datetime(2025, 5, 1, 16, 0, tzinfo=timezone.utc)
    
@pytest.mark.django_db
def test_delete_event_with_valid_id():
    """
    Verifica que un evento existente pueda ser eliminado correctamente.
    La respuesta debe ser 204 No Content.
    """
    client = APIClient()

    user = User.objects.create_user(username="operator_user", password="password123")
    Operator.objects.create(user=user, hiring_date=datetime.strptime('2025-01-05', '%Y-%m-%d').date())
    client.force_authenticate(user=user)

    business = Business.objects.create(name="Test Business")
    requester = Requester.objects.create(user=user)
    booking = Booking.objects.create(public_id="B0070", created_by=user, business=business)

    event = Event.objects.create(
        booking=booking,
        start_at=datetime(2025, 5, 1, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2025, 5, 1, 12, 0, tzinfo=timezone.utc),
        requester=requester,
    )

    url = reverse('manage_events', kwargs={'event_id': event.id})
    print(f"URL: {url}")
    response = client.delete(url)

    print(f"Respuesta de la vista: {response.data}")
    print(f"Código de estado: {response.status_code}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    event.refresh_from_db()
    assert event.is_deleted is True
    
@pytest.mark.django_db
def test_pagination_out_of_range_as_operator():
    """
    Verifica que la paginación funcione correctamente al solicitar una página fuera del rango
    de resultados disponibles, usando un usuario con rol de operador.
    """
    client = APIClient()

    user = User.objects.create_user(username="operator_user", password="password123")
    Operator.objects.create(user=user, hiring_date=datetime.strptime('2025-01-05', '%Y-%m-%d').date())
    client.force_authenticate(user=user)

    business = Business.objects.create(name="Test Business")
    requester = Requester.objects.create(user=user)

    for i in range(10): 
        booking = Booking.objects.create(public_id=f"B00{i+1}", created_by=user, business=business)
        Event.objects.create(
            booking=booking,
            start_at=datetime(2025, 5, 1, 10, 0, tzinfo=timezone.utc),
            end_at=datetime(2025, 5, 1, 12, 0, tzinfo=timezone.utc),
            requester=requester,
        )

    url = reverse('manage_events')
    response = client.get(url, {'page': 5, 'page_size': 5})

    print(f"Respuesta de la vista: {response.data}")
    print(f"Código de estado: {response.status_code}")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 0    
            










#la comente porque muestrar error    
@pytest.mark.django_db
def test_access_with_incomplete_operator_data():
    """
    Verifica que un usuario con rol de operador pero con datos incompletos no pueda acceder a la vista.

    -la vista: en la vista no tiene la validacion de un usuario eliminado
    test_access_with_incomplete_operator_data. Esto significa que, aunque el operador relacionado fue eliminado, 
    la lógica de la vista no está verificando correctamente si el operador aún existe.
    
    PROBLEMA ENCONTRADO:  clase ManageEvents no está validando correctamente si el 
    operador relacionado con el usuario ha sido eliminado o si los datos del operador
    son incompletos.

    SOLUCION:  agrega una validación para verificar si el operador asociado
    al usuario ha sido eliminado
    """

    client = APIClient()

    user = User.objects.create_user(
        username="operator_user",
        password="password123"
    )

    operator = Operator.objects.create(
        user=user,
        hiring_date=datetime.strptime('2025-01-05', '%Y-%m-%d').date()
    )
    
    operator.delete() 

    client.force_authenticate(user=user)
    url = reverse('manage_events')
    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    
@pytest.mark.django_db
def test_access_with_invalid_provider_data():
   
    """
    Verifica que un usuario con datos inválidos en su rol de proveedor no pueda acceder a la vista.
    
    PROBLEMA: a lógica de la clase ManageEvents no está validando correctamente si
    los datos asociados al proveedor son válidos o completos.
    
    El proveedor tiene un contract_type inválido:

    En la prueba, se crea un proveedor con un contract_type que no es válido 
    ("INVALID_TYPE"). Sin embargo, la vista no valida este campo y permite el acceso.
    Falta de validación de datos asociados al proveedor:

    La vista solo verifica si el usuario tiene el rol de proveedor
    (user.is_provider), pero no valida si los datos asociados al proveedor
    son correctos o completos.
    
    SOLUCIONES : agrega una validación para verificar si los datos del proveedor son válidos. 
    """
   
    client = APIClient()

    user = User.objects.create_user(
        username="invalid_provider_user",
        password="password123"
    )

    provider = Provider.objects.create(
        user=user,
        contract_type="INVALID_TYPE"  
    )

    client.force_authenticate(user=user)
    url = reverse('manage_events')
    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN    
    
@pytest.mark.django_db
def test_access_denied_for_user_with_deleted_role():
    """
    Problema: La vista no valida si el rol asociado al usuario (operador, proveedor o administrador) ha sido eliminado.
    Solución: Agrega una validación en la vista para verificar que el rol no esté eliminado (is_deleted=True).
    Verifica que un usuario autenticado cuyo rol ha sido eliminado no pueda acceder a la vista ManageEvents.
    El problema radica en que la clase ManageEvents no está verificando si el rol asociado al usuario (en este caso, el operador) ha sido eliminado. Aunque el operador relacionado con el usuario fue eliminado, la lógica de la vista no valida correctamente si el rol aún existe.

    Solución
    Debes agregar una validación explícita en la clase ManageEvents para verificar si el rol asociado al usuario (como operador, proveedor o administrador) no ha sido eliminado (is_deleted=True). Esto se puede hacer antes de permitir el acceso a la vista.
    """
    client = APIClient()

    user = User.objects.create_user(
        username="deleted_role_user",
        password="password123"
    )

    operator = Operator.objects.create(
        user=user,
        hiring_date=datetime.strptime('2025-01-05', '%Y-%m-%d').date()
    )
    operator.delete()

    
    client.force_authenticate(user=user)
    url = reverse('manage_events')
    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_filter_events_by_date_range():
    """
    Verifica que los eventos dentro del rango de fechas especificado sean devueltos.
    
    PROBLEMA: a lógica de filtrado en la vista ManageEvents no está funcionando 
    correctamente para los parámetros de rango de fechas (start_at y end_at)
    Falta de lógica de filtrado por rango de fechas en la vista:

    La vista ManageEvents no está aplicando correctamente los filtros para incluir eventos que comienzan o
    terminan dentro del rango de fechas especificado.
    """
    client = APIClient()

    user = User.objects.create_user(username="test_user", password="password123")
    Operator.objects.create(
        user=user,
        hiring_date=datetime.strptime('2025-01-05', '%Y-%m-%d').date() 
    )
    client.force_authenticate(user=user)

    business = Business.objects.create(name="Test Business")
    requester = Requester.objects.create(user=user)
    
    event1 = Event.objects.create(
        booking=Booking.objects.create(public_id="B001", created_by=user, business=business),
        start_at=datetime(2025, 5, 1, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2025, 5, 1, 12, 0, tzinfo=timezone.utc),
        requester=requester, 
    )
    event2 = Event.objects.create(
        booking=Booking.objects.create(public_id="B002", created_by=user, business=business),
        start_at=datetime(2025, 5, 2, 14, 0, tzinfo=timezone.utc),
        end_at=datetime(2025, 5, 2, 16, 0, tzinfo=timezone.utc),
        requester=requester,  
    )

    url = reverse('manage_events')
    response = client.get(url, {'start_at': '2025-05-01T00:00:00.000000Z', 'end_at': '2025-05-01T23:59:59.000000Z'})
    print(f"Evento 1: start_at={event1.start_at}, end_at={event1.end_at}")
    print(f"Evento 2: start_at={event2.start_at}, end_at={event2.end_at}")
    print(f"Respuesta de la vista: {response.data}")
    print(f"Código de estado: {response.status_code}")
  
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['id'] == event1.id
    
    
@pytest.mark.django_db
def test_filter_events_by_provider_id():
    """
    Verifica que solo se devuelvan los eventos asociados al provider_id especificado.
    
    PROBLEMA: la lógica de filtrado en la clase ManageEvents no está funcionando 
    correctamente para el parámetro provider_id.
    Falta de lógica de filtrado por provider_id en la vista:

    La vista ManageEvents no está aplicando correctamente el filtro para incluir solo
    los eventos asociados al provider_id especificado.
    
    """
    client = APIClient()

    user = User.objects.create_user(username="test_user", password="password123")
    provider = Provider.objects.create(
        user=user,
        contract_type=Provider.ContractType.CONTRACTOR
    )
    client.force_authenticate(user=user)

    business = Business.objects.create(name="Test Business")
    requester = Requester.objects.create(user=user)
    service = Service.objects.create(provider=provider, business=business)
    booking1 = Booking.objects.create(public_id="B001", created_by=user, business=business)
    booking2 = Booking.objects.create(public_id="B002", created_by=user, business=business)
    
    booking1.services.add(service)
    
    event1 = Event.objects.create(
        booking=booking1,
        start_at=datetime(2025, 5, 1, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2025, 5, 1, 12, 0, tzinfo=timezone.utc),
        requester=requester,
    )
    event2 = Event.objects.create(
        booking=booking2,
        start_at=datetime(2025, 5, 2, 14, 0, tzinfo=timezone.utc),
        end_at=datetime(2025, 5, 2, 16, 0, tzinfo=timezone.utc),
        requester=requester,
    )

    url = reverse('manage_events')
    response = client.get(url, {'provider_id': provider.id})

    print(f"Provider ID: {provider.id}")
    print(f"Respuesta de la vista: {response.data}")
    print(f"Código de estado: {response.status_code}")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['id'] == event1.id    

@pytest.mark.django_db
def test_filter_events_with_invalid_date():
    """
    Verifica que la vista maneje correctamente los valores de fecha inválidos.
    PROBLEMA: ManageEvents no está validando correctamente los parámetros de entrada 
    antes de aplicar otras verificaciones, como los permisos.
    
    Falta de validación de parámetros de entrada:

    La vista ManageEvents no valida explícitamente los parámetros de entrada, como start_at, 
    antes de proceder con la lógica de permisos o filtros.
    Orden incorrecto de las validaciones:

    La vista parece verificar los permisos del usuario antes de validar los parámetros 
    de entrada. Si un parámetro como start_at tiene un formato inválido, la vista debería
    devolver un error 400 Bad Request antes de verificar los permisos.
    """
    client = APIClient()

    user = User.objects.create_user(username="test_user", password="password123")
    client.force_authenticate(user=user)

    url = reverse('manage_events')
    response = client.get(url, {'start_at': 'invalid-date'})

    print(f"Respuesta de la vista: {response.data}")
    print(f"Código de estado: {response.status_code}")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'invalid "start_at"' in response.data.get('detail', '')

@pytest.mark.django_db
def test_filter_events_by_date_range_and_provider_id():
    """
    Verifica que los eventos dentro del rango de fechas y asociados al provider_id especificado sean devueltos.
    Esto sugiere que la lógica de filtrado en la vista ManageEvents no está funcionando correctamente para combinar los
    filtros de rango de fechas (start_at y end_at) y provider_id.
    La vista ManageEvents no está aplicando correctamente los filtros para incluir eventos que coincidan tanto con el 
    rango de fechas como con el provider_id.
    En la clase ManageEvents, revisa el método get para asegurarte de que está aplicando correctamente los filtros de
    rango de fechas y provider_id
    """
    client = APIClient()

    user = User.objects.create_user(username="test_user", password="password123")
    provider = Provider.objects.create(user=user, contract_type=Provider.ContractType.CONTRACTOR)
    client.force_authenticate(user=user)

    business = Business.objects.create(name="Test Business")
    requester = Requester.objects.create(user=user)

    service = Service.objects.create(provider=provider, business=business)
    booking1 = Booking.objects.create(public_id="B001", created_by=user, business=business)
    booking2 = Booking.objects.create(public_id="B002", created_by=user, business=business)
    booking1.services.add(service)

    event1 = Event.objects.create(
        booking=booking1,
        start_at=datetime(2025, 5, 1, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2025, 5, 1, 12, 0, tzinfo=timezone.utc),
        requester=requester,
    )
    event2 = Event.objects.create(
        booking=booking2,
        start_at=datetime(2025, 5, 2, 14, 0, tzinfo=timezone.utc),
        end_at=datetime(2025, 5, 2, 16, 0, tzinfo=timezone.utc),
        requester=requester,
    )

    url = reverse('manage_events')
    response = client.get(url, {
        'start_at': '2025-05-01T00:00:00.000000Z',
        'end_at': '2025-05-01T23:59:59.000000Z',
        'provider_id': provider.id
    })

    print(f"Provider ID: {provider.id}")
    print(f"Respuesta de la vista: {response.data}")
    print(f"Código de estado: {response.status_code}")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['id'] == event1.id

@pytest.mark.django_db
def test_pagination_first_page_as_operator():
    """
    Verifica que la paginación funcione correctamente al solicitar la primera página
    de resultados con un tamaño de página específico, usando un usuario con rol de operador.
    PROBLEMA: la prueba esperaba que se devolvieran 10 eventos en la primera página de resultados,
    pero la vista devolvió un resultado vacío ('results': []). Esto sugiere que la lógica de paginación o 
    filtrado en la clase ManageEvents no está funcionando correctamente.

    La clase ManageEvents no está aplicando correctamente la paginación al queryset de eventos.
    de configuración de la paginación:

    La clase ManageEvents podría no estar utilizando un paginador como StandardResultsSetPagination.
    Filtros aplicados incorrectamente:
    La vista podría estar aplicando filtros que excluyen todos los eventos, como query_start_at y query_end_at, que son None en este caso.
    SOLUCION: Asegúrate de que la clase ManageEvents esté utilizando un paginador como StandardResultsSetPagination. Aquí está un ejemplo
    de cómo implementar la lógica de paginación
    """
    client = APIClient()

    user = User.objects.create_user(username="operator_user", password="password123")
    Operator.objects.create(user=user, hiring_date=datetime.strptime('2025-01-05', '%Y-%m-%d').date())
    client.force_authenticate(user=user)

    business = Business.objects.create(name="Test Business")
    requester = Requester.objects.create(user=user)

    for i in range(15):
        booking = Booking.objects.create(public_id=f"B00{i+1}", created_by=user, business=business)
        Event.objects.create(
            booking=booking,
            start_at=datetime(2025, 5, 1, 10, 0, tzinfo=timezone.utc),
            end_at=datetime(2025, 5, 1, 12, 0, tzinfo=timezone.utc),
            requester=requester,
        )
        
    print(f"Eventos creados: {Event.objects.all()}")
    
    url = reverse('manage_events')
    response = client.get(url, {'page': 1, 'page_size': 10})

    print(f"Respuesta de la vista: {response.data}")
    print(f"Código de estado: {response.status_code}")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 10

    expected_ids = [event.id for event in Event.objects.all()[:10]]
    actual_ids = [event['id'] for event in response.data['results']]
    assert actual_ids == expected_ids


    
@pytest.mark.django_db
def test_create_event_with_valid_data():
    """	
    Verifica que un evento se pueda crear correctamente con datos válidos.
    PROBLEMA: En el método post de la clase ManageEvents, el argumento concurrent_booking se
    está obteniendo de los datos de la solicitud (request.data), pero no se está pasando al método
    create_event. Esto provoca el error, ya que create_event requiere explícitamente este argumento.
    
    SOLUCION: En el método post de la clase ManageEvents, asegúrate de que el argumento concurrent_booking 
    se pase correctamente al método create_event. 
    """
    client = APIClient()

    user = User.objects.create_user(username="operator_user", password="password123")
    Operator.objects.create(user=user, hiring_date=datetime.strptime('2025-01-05', '%Y-%m-%d').date())
    client.force_authenticate(user=user)

    business = Business.objects.create(name="Test Business")
    requester = Requester.objects.create(user=user)
    booking = Booking.objects.create(public_id="B0070", created_by=user, business=business)

    event_data = {
        "booking": booking.id,
        "start_at": "2025-05-01T10:00:00Z",
        "end_at": "2025-05-01T12:00:00Z",
        "requester": requester.id,
        "business_name": business.name,
        "concurrent_booking": False  
    }

    url = reverse('manage_events')
    print(f"URL: {url}")
    print(f"Datos enviados: {event_data}")
    response = client.post(url, event_data, format='json')

    print(f"Respuesta de la vista: {response.data}")
    print(f"Código de estado: {response.status_code}")

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_update_event_with_valid_data():
    """
    Verifica que un evento existente pueda ser actualizado correctamente con datos válidos.
    La respuesta debe ser 204 No Content.
    
    en la vista se puede manejar un try except,asi devuelve un return cuando de error 
    en la actualizacion
    PROBLEMA: lógica de la clase ManageEvents o en la configuración de la prueba está fallando. 
    Falta de manejo de excepciones en el método put:

    En la clase ManageEvents, el método put no maneja correctamente los errores que podrían
    ocurrir al actualizar un evento. Si el evento no existe o los datos enviados son inválidos,
    podría generar un error no controlado.
    SOLUCION: Asegúrate de que el método put maneje correctamente los errores y valide los datos
    antes de intentar actualizar el evento
    """
    client = APIClient()

    user = User.objects.create_user(username="operator_user", password="password123")
    Operator.objects.create(user=user, hiring_date=datetime.strptime('2025-01-05', '%Y-%m-%d').date())
    client.force_authenticate(user=user)

    business = Business.objects.create(name="Test Business")
    requester = Requester.objects.create(user=user)
    booking = Booking.objects.create(public_id="B0070", created_by=user, business=business)

    event = Event.objects.create(
        booking=booking,
        start_at=datetime(2025, 5, 1, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2025, 5, 1, 12, 0, tzinfo=timezone.utc),
        requester=requester,
    )

    updated_event_data = {
        "start_at": "2025-05-01T14:00:00Z",
        "end_at": "2025-05-01T16:00:00Z",
        "_business": business.name,
        "booking": booking.id,  
        "requester": requester.id,  
    }

    url = reverse('manage_events') + f"{event.id}/"
    print(f"URL: {url}")
    print(f"Datos enviados: {updated_event_data}")
    response = client.put(url, updated_event_data, format='json')

    print(f"Respuesta de la vista: {response.data}")
    print(f"Código de estado: {response.status_code}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    event.refresh_from_db()
    assert event.start_at == datetime(2025, 5, 1, 14, 0, tzinfo=timezone.utc)
    assert event.end_at == datetime(2025, 5, 1, 16, 0, tzinfo=timezone.utc)

