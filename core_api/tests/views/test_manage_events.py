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
from core_backend.models import Event, User, Operator, Provider, Admin, Booking, Business, Requester,Service, Affiliation, Recipient, Agent
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
from django.utils import timezone

@pytest.mark.django_db
class TestManageEvents:
    
    def test_access_denied_for_user_without_roles(self, base_user):
        """
        Verifica que un usuario sin roles no pueda acceder a la vista ManageEvents.
        """
        client = APIClient()
        client.force_authenticate(user=base_user)
        url = reverse('manage_events') 
        response = client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_access_granted_for_operator(self, authenticated_client):
        """
        Verifica que un usuario con rol de operador pueda acceder a la vista ManageEvents.
        """
        url = reverse('manage_events') 
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK    

    def test_access_granted_for_provider(self, provider_authenticated_client):
        """
        Verifica que un usuario con rol de proveedor pueda acceder a la vista ManageEvents.
        """
        url = reverse('manage_events')
        response = provider_authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK 

    def test_access_granted_for_admin(self, admin_authenticated_client):
        """
        Verifica que un usuario con rol de administrador pueda acceder a la vista ManageEvents.
        """
        url = reverse('manage_events')
        response = admin_authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK 

    def test_access_with_multiple_roles(self, multi_role_user):
        """
        Verifica que un usuario con múltiples roles pueda acceder a la vista.
        """
        client = APIClient()
        client.force_authenticate(user=multi_role_user)
        url = reverse('manage_events')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK  

    def test_access_denied_for_unauthenticated_user(self, unauthenticated_client):
        """
        Verifica que un usuario no autenticado no pueda acceder a la vista ManageEvents.
        """
        url = reverse('manage_events')
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_event_with_valid_id(self, authenticated_client, event):
        """
        Verifica que un evento existente pueda ser eliminado correctamente.
        """
        url = reverse('manage_events', kwargs={'event_id': event.id})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        event.refresh_from_db()
        assert event.is_deleted is True

    def test_pagination_with_multiple_events(self, authenticated_client, multiple_events):
        """
        Verifica que la paginación funcione correctamente.
        """

        url = reverse('manage_events')
        url = url + "interpretation/"
        response = authenticated_client.get(url, {
            'start_date': '2025-05-01', 
            'end_date': '2025-05-01', 
            'page': 1, 
            'page_size': 10, 
            'field_to_sort': 'start_at', 
            'order_to_sort': 'asc'
        })

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 10

    def test_create_event_with_valid_data(self, authenticated_client, business, requester, affiliate, agent, booking):
        """	
        Verifica que un evento se pueda crear correctamente con datos válidos.
        """
        event_data = {
            "booking": booking.id,
            "start_at": "2025-05-01T10:00:00Z",
            "end_at": "2025-05-01T12:00:00Z",
            "business": business.id,
            "concurrent_booking": False,  
            "affiliates": [affiliate.id],  
            "agents": [agent.id],          
            "requester": requester.id
        }   
        
        url = reverse('manage_events', kwargs={'business_name': business.name})
        response = authenticated_client.post(url, event_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        event = Event.objects.get(booking=booking)
        assert event.start_at == datetime(2025, 5, 1, 10, 0, tzinfo=timezone.utc)
        assert event.end_at == datetime(2025, 5, 1, 12, 0, tzinfo=timezone.utc)

    def test_update_event_with_valid_data(self):
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

        # Crear datos de prueba
        business = Business.objects.create(name="Test Business")
        requester = Requester.objects.create(user=user)

        # Crear un paciente afiliado
        user2 = User.objects.create_user(username="patient_user", password="password123")
        recipient = Recipient.objects.create(user=user2)
        affiliate = Affiliation.objects.create(recipient = recipient, company = None)  # Ajusta según los campos reales
        
       
        # Crear un booking
        booking = Booking.objects.create(
            public_id = "B0070", 
            created_by = user,
            business = business
        )

        # Crear un evento asociado al booking y al afiliado
        event = Event.objects.create(
            booking=booking,
            start_at=datetime(2025, 5, 1, 10, 0, tzinfo=timezone.utc),
            end_at=datetime(2025, 5, 1, 12, 0, tzinfo=timezone.utc),
            requester=requester,
        )
        
        event.affiliates.add(affiliate)  # Asociar el afiliado al evento
        assert affiliate in event.affiliates.all(), "El afiliado no se asoció correctamente al evento."
        
        agent_user = User.objects.create_user(username="agent_user", password="password123")
        agent = Agent.objects.create(user=agent_user, role="Test Role")
        event.agents.add(agent)
        assert agent in event.agents.all(), "El agente no se asoció correctamente al evento."


        # Datos actualizados del evento
        updated_event_data = {
            "start_at": "2025-05-01T14:00:00Z",
            "end_at": "2025-05-01T16:00:00Z",
            "_business": business.name,
            "booking": booking.id,
            "requester": requester.id,
            "affiliates": [affiliate.id],
            "agents": [agent.id],
        }

        # Realizar la solicitud PUT
        url = reverse('manage_events') + f"{event.id}/"
        print(f"URL: {url}")
        print(f"Datos enviados: {updated_event_data}")
        response = client.put(url, updated_event_data, format='json')

        # Depuración
        print(f"Respuesta de la vista: {response.data}")
        print(f"Código de estado: {response.status_code}")

        # Verificar que la respuesta sea 204 No Content
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verificar que los datos del evento se hayan actualizado correctamente
        event.refresh_from_db()
        assert event.start_at == datetime(2025, 5, 1, 14, 0, tzinfo=timezone.utc)
        assert event.end_at == datetime(2025, 5, 1, 16, 0, tzinfo=timezone.utc)