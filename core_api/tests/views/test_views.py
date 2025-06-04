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
from core_backend.models import Event, User, Operator, Provider, Admin, Booking, Business, Requester,Service, Affiliation
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
import uuid
from rest_framework.test import APIClient
from django.urls import reverse
from core_backend.models import Booking, Business, User, ServiceRoot, Company, Operator, Provider, Service
from datetime import datetime


@pytest.mark.django_db
class TestManageBooking:
    def test_get_booking(self, base_user, booking):
        client = APIClient()
        client.force_authenticate(user=base_user)
        url = reverse("manage_booking", kwargs={"booking_id": booking.id})
        response = client.get(url)
        assert response.status_code == 200
        assert response.data is not None
        assert response.data["public_id"] == booking.public_id

    def test_create_booking(self, operator_user, business, service_root, company, operator, provider, service, base_user):
        client = APIClient()
        client.force_authenticate(user=operator_user)
        parent_booking = Booking.objects.create(
            business=business,
            service_root=service_root,
            public_id="BPARENT",
            created_by=base_user,
            status="pending"
        )
        parent_booking.companies.add(company)
        parent_booking.operators.add(operator)
        parent_booking.services.add(service)
        booking_data = {
            "business": business.id,
            "service_root": service_root.id,
            "companies": [company.id],
            "operators": [operator.id],
            "parent": parent_booking.id,
            "services": [service.id],
            "public_id": "B002",
            "created_by": base_user.id,
            "status": "pending"
        }
        url = reverse("manage_booking", kwargs={"business_name": business.name})
        response = client.post(url, booking_data, format="json")
        assert response.status_code == 201
        assert "booking_id" in response.data
        booking_id = response.data["booking_id"]
        booking = Booking.objects.get(id=booking_id)
        assert booking.business == business
        assert booking.service_root == service_root
        assert booking.public_id == "B002"
        assert booking.created_by == base_user
        assert booking.status == "pending"
        assert company in booking.companies.all()
        assert operator in booking.operators.all()
        assert service in booking.services.all()
        assert booking.parent == parent_booking

    def test_update_booking(self):
        """
        Verifica que un Booking pueda ser actualizado correctamente.
        """
        client = APIClient()

        # Crear datos de prueba
        user = User.objects.create_user(username="test_user_update", password="password123")
        business = Business.objects.create(name="Test Business Update")
        service_root = ServiceRoot.objects.create(name="Test Service Root", description="Test Description")
        company = Company.objects.create(name="Test Company", type="agency", send_method="email", on_hold=False)
        booking = Booking.objects.create(
            business=business,
            service_root=service_root,
            public_id="B003",
            created_by=user,
            status="pending"
        )
        booking.companies.add(company)

        # Autenticar al usuario
        client.force_authenticate(user=user)

        # Datos para la actualización del Booking
        updated_data = {
            "business": business.id,
            "service_root": service_root.id,
            "public_id": "B003",
            "status": "confirmed"
        }

        # Realizar la solicitud PUT
        url = reverse("manage_booking", kwargs={"booking_id": booking.id})
        response = client.put(url, updated_data, format="json")

        # Verificar la respuesta
        assert response.status_code == 204

        # Verificar que el Booking se haya actualizado correctamente
        booking.refresh_from_db()
        assert booking.status == "confirmed"


    def test_delete_booking(self):
        """
        Verifica que un Booking pueda ser eliminado correctamente.
        """
        client = APIClient()

        # Crear datos de prueba
        user = User.objects.create_user(username="test_user_delete", password="password123")
        business = Business.objects.create(name="Test Business Delete")
        service_root = ServiceRoot.objects.create(name="Test Service Root", description="Test Description")
        company = Company.objects.create(name="Test Company", type="agency", send_method="email", on_hold=False)
        booking = Booking.objects.create(
            business=business,
            service_root=service_root,
            public_id="B004",
            created_by=user,
            status="pending"
        )
        booking.companies.add(company)

        # Autenticar al usuario
        client.force_authenticate(user=user)

        # Realizar la solicitud DELETE
        url = reverse("manage_booking", kwargs={"booking_id": booking.id})
        response = client.delete(url)

        # Verificar la respuesta
        assert response.status_code == 204

        # Verificar que el Booking se haya eliminado correctamente
        booking.refresh_from_db()
        assert booking.is_deleted is True

    def test_get_booking_list_with_pagination(self):
        client = APIClient()
        user = User.objects.create_user(username=f"test_user_list_{uuid.uuid4()}", password="password123")
        business = Business.objects.create(name=f"Test Business List {uuid.uuid4()}")
        service_root = ServiceRoot.objects.create(name="Test Service Root", description="Test Description")
        company = Company.objects.create(name="Test Company", type="agency", send_method="email", on_hold=False)
        client.force_authenticate(user=user)
        # Crear varios bookings
        for i in range(5):
            booking = Booking.objects.create(
                business=business,
                service_root=service_root,
                public_id=f"B00{i+10}",
                created_by=user,
                status="pending"
            )
            booking.companies.add(company)
        url = reverse("manage_booking", kwargs={}) + f"?page_size=2&page=1"
        response = client.get(url)
        assert response.status_code == 200
        assert "results" in response.data
        assert len(response.data["results"]) <= 2

    def test_get_booking_not_found(self):
        client = APIClient()
        user = User.objects.create_user(username=f"test_user_nf_{uuid.uuid4()}", password="password123")
        client.force_authenticate(user=user)
        url = reverse("manage_booking", kwargs={"booking_id": 999999})
        response = client.get(url)
        assert response.status_code == 404 or response.status_code == 400

    def test_create_booking_invalid_data(self):
        client = APIClient()
        user = User.objects.create_user(username=f"test_user_invalid_{uuid.uuid4()}", password="password123")
        business = Business.objects.create(name=f"Test Business Invalid {uuid.uuid4()}")
        client.force_authenticate(user=user)
        # Falta service_root y companies
        booking_data = {
            "business": business.id,
            "public_id": "B100",
            "created_by": user.id,
            "status": "pending"
        }
        url = reverse("manage_booking", kwargs={"business_name": business.name})
        response = client.post(url, booking_data, format="json")
        assert response.status_code == 400

    def test_update_booking_not_found(self):
        client = APIClient()
        user = User.objects.create_user(username=f"test_user_up_nf_{uuid.uuid4()}", password="password123")
        client.force_authenticate(user=user)
        updated_data = {"status": "confirmed"}
        url = reverse("manage_booking", kwargs={"booking_id": 999999})
        response = client.put(url, updated_data, format="json")
        assert response.status_code == 404 or response.status_code == 400

    def test_delete_booking_not_found(self):
        client = APIClient()
        user = User.objects.create_user(username=f"test_user_del_nf_{uuid.uuid4()}", password="password123")
        client.force_authenticate(user=user)
        url = reverse("manage_booking", kwargs={"booking_id": 999999})
        response = client.delete(url)
        assert response.status_code == 404 or response.status_code == 400

    def test_permissions_required(self):
        client = APIClient()
        url = reverse("manage_booking", kwargs={"booking_id": 1})
        response = client.get(url)
        assert response.status_code in [401, 403]

    def test_create_booking_missing_companies(self):
        client = APIClient()
        user = User.objects.create_user(username=f"test_user_nocomp_{uuid.uuid4()}", password="password123")
        business = Business.objects.create(name=f"Test Business NoComp {uuid.uuid4()}")
        service_root = ServiceRoot.objects.create(name="Test Service Root", description="Test Description")
        client.force_authenticate(user=user)
        booking_data = {
            "business": business.id,
            "service_root": service_root.id,
            "public_id": "B200",
            "created_by": user.id,
            "status": "pending"
        }
        url = reverse("manage_booking", kwargs={"business_name": business.name})
        response = client.post(url, booking_data, format="json")
        assert response.status_code == 400

    def test_create_booking_missing_required_fields(self):
        client = APIClient()
        user = User.objects.create_user(username=f"test_user_noreq_{uuid.uuid4()}", password="password123")
        business = Business.objects.create(name=f"Test Business NoReq {uuid.uuid4()}")
        client.force_authenticate(user=user)
        booking_data = {
            "business": business.id,
            # Falta service_root, companies, public_id, created_by, status
        }
        url = reverse("manage_booking", kwargs={"business_name": business.name})
        response = client.post(url, booking_data, format="json")
        assert response.status_code == 400

    def test_get_booking_empty_list(self):
        client = APIClient()
        user = User.objects.create_user(username=f"test_user_empty_{uuid.uuid4()}", password="password123")
        client.force_authenticate(user=user)
        url = reverse("manage_booking", kwargs={}) + "?page_size=10&page=1"
        response = client.get(url)
        assert response.status_code == 200
        assert response.data["count"] == 0 or len(response.data.get("results", [])) == 0

    def test_get_booking_with_query_params(self):
        client = APIClient()
        user = User.objects.create_user(username=f"test_user_qp_{uuid.uuid4()}", password="password123")
        business = Business.objects.create(name=f"Test Business QP {uuid.uuid4()}")
        service_root = ServiceRoot.objects.create(name="Test Service Root", description="Test Description")
        company = Company.objects.create(name="Test Company", type="agency", send_method="email", on_hold=False)
        booking = Booking.objects.create(
            business=business,
            service_root=service_root,
            public_id="BQP1",
            created_by=user,
            status="pending"
        )
        booking.companies.add(company)
        client.force_authenticate(user=user)
        url = reverse("manage_booking", kwargs={}) + f"?id={booking.id}"
        response = client.get(url)
        assert response.status_code == 200
        assert response.data["public_id"] == "BQP1"