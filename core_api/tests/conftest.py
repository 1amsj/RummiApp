import os
import sys
import django
import uuid
from datetime import datetime, timezone

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_backend.settings')
django.setup()

import pytest
from django.contrib.auth import get_user_model
from core_backend.models import (
    Event, User, Operator, Provider, Admin, Booking, Business, 
    Requester, Service, Affiliation, Recipient, Agent
)

User = get_user_model()

def generate_unique_username(prefix="user"):
    """Generate a unique username using UUID."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def generate_unique_public_id(prefix="B"):
    """Generate a unique public ID using UUID."""
    return f"{prefix}{uuid.uuid4().hex[:6].upper()}"

@pytest.fixture
@pytest.mark.django_db
def base_user():
    """Create a basic user without any roles."""
    return User.objects.create_user(
        username=generate_unique_username("test_user"),
        password="password123"
    )

@pytest.fixture
@pytest.mark.django_db
def operator_user():
    """Create a user with operator role."""
    user = User.objects.create_user(
        username=generate_unique_username("operator_user"),
        password="password123"
    )
    Operator.objects.create(
        user=user,
        hiring_date=datetime.strptime('2025-01-05', '%Y-%m-%d').date()
    )
    return user

@pytest.fixture
@pytest.mark.django_db
def provider_user():
    """Create a user with provider role."""
    user = User.objects.create_user(
        username=generate_unique_username("provider_user"),
        password="password123"
    )
    Provider.objects.create(
        user=user,
        contract_type=Provider.ContractType.CONTRACTOR
    )
    return user

@pytest.fixture
@pytest.mark.django_db
def admin_user():
    """Create a user with admin role."""
    user = User.objects.create_user(
        username=generate_unique_username("admin_user"),
        password="password123",
        is_staff=True,
        is_superuser=True
    )
    Admin.objects.create(user=user)
    return user

@pytest.fixture
@pytest.mark.django_db
def multi_role_user():
    """Create a user with multiple roles (operator and provider)."""
    user = User.objects.create_user(
        username=generate_unique_username("multi_role_user"),
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
    return user

@pytest.fixture
@pytest.mark.django_db
def business():
    """Create a test business."""
    return Business.objects.create(name=f"Test Business {uuid.uuid4().hex[:6]}")

@pytest.fixture
@pytest.mark.django_db
def requester(operator_user):
    """Create a requester associated with operator user."""
    return Requester.objects.create(user=operator_user)

@pytest.fixture
@pytest.mark.django_db
def booking(operator_user, business):
    """Create a test booking."""
    return Booking.objects.create(
        public_id=generate_unique_public_id("B"),
        created_by=operator_user,
        business=business
    )

@pytest.fixture
@pytest.mark.django_db
def recipient_user():
    """Create a user for recipient/patient."""
    return User.objects.create_user(
        username=generate_unique_username("patient_user"),
        password="password123"
    )

@pytest.fixture
@pytest.mark.django_db
def recipient(recipient_user):
    """Create a recipient."""
    return Recipient.objects.create(user=recipient_user)

@pytest.fixture
@pytest.mark.django_db
def affiliate(recipient):
    """Create an affiliation."""
    return Affiliation.objects.create(
        recipient=recipient,
        company=None
    )

@pytest.fixture
@pytest.mark.django_db
def agent_user():
    """Create a user for agent."""
    return User.objects.create_user(
        username=generate_unique_username("agent_user"),
        password="password123"
    )

@pytest.fixture
@pytest.mark.django_db
def agent(agent_user):
    """Create an agent."""
    return Agent.objects.create(
        user=agent_user,
        role="Test Role"
    )

@pytest.fixture
@pytest.mark.django_db
def service(provider_user, business):
    """Create a service associated with provider and business."""
    provider = Provider.objects.get(user=provider_user)
    return Service.objects.create(
        provider=provider,
        business=business
    )

@pytest.fixture
@pytest.mark.django_db
def event(booking, requester):
    """Create a basic event."""
    return Event.objects.create(
        booking=booking,
        start_at=datetime(2025, 5, 1, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2025, 5, 1, 12, 0, tzinfo=timezone.utc),
        requester=requester,
    )

@pytest.fixture
@pytest.mark.django_db
def complete_event(event, affiliate, agent):
    """Create an event with all relationships."""
    event.affiliates.add(affiliate)
    event.agents.add(agent)
    return event

@pytest.fixture
@pytest.mark.django_db
def multiple_events(operator_user, business, requester):
    """Create multiple events for pagination testing."""
    events = []
    for i in range(15):
        booking = Booking.objects.create(
            public_id=generate_unique_public_id(f"B{i:03d}"),
            created_by=operator_user,
            business=business
        )
        event = Event.objects.create(
            booking=booking,
            start_at=datetime(2025, 5, 1, 10, 0, tzinfo=timezone.utc),
            end_at=datetime(2025, 5, 1, 12, 0, tzinfo=timezone.utc),
            requester=requester,
        )
        events.append(event)
    return events

@pytest.fixture
@pytest.mark.django_db
def multiple_bookings(operator_user, business):
    """Create multiple bookings for testing."""
    bookings = []
    for i in range(10):
        booking = Booking.objects.create(
            public_id=generate_unique_public_id(f"B{i:03d}"),
            created_by=operator_user,
            business=business
        )
        bookings.append(booking)
    return bookings

@pytest.fixture
@pytest.mark.django_db
def authenticated_client(operator_user):
    """Create an authenticated API client with operator user."""
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=operator_user)
    return client

@pytest.fixture
@pytest.mark.django_db
def provider_authenticated_client(provider_user):
    """Create an authenticated API client with provider user."""
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=provider_user)
    return client

@pytest.fixture
@pytest.mark.django_db
def admin_authenticated_client(admin_user):
    """Create an authenticated API client with admin user."""
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client

@pytest.fixture
@pytest.mark.django_db
def unauthenticated_client():
    """Create an unauthenticated API client."""
    from rest_framework.test import APIClient
    return APIClient()

# Factory fixtures for creating multiple instances
@pytest.fixture
def user_factory():
    """Factory for creating users with custom parameters."""
    def _create_user(username=None, **kwargs):
        if username is None:
            username = generate_unique_username("user")
        
        defaults = {
            'password': 'password123'
        }
        defaults.update(kwargs)
        
        return User.objects.create_user(username=username, **defaults)
    return _create_user

@pytest.fixture
def booking_factory(business):
    """Factory for creating bookings with custom parameters."""
    def _create_booking(public_id=None, created_by=None, **kwargs):
        if public_id is None:
            public_id = generate_unique_public_id("B")
        
        if created_by is None:
            created_by = User.objects.create_user(
                username=generate_unique_username("user"),
                password="password123"
            )
        
        defaults = {
            'business': business
        }
        defaults.update(kwargs)
        
        return Booking.objects.create(
            public_id=public_id,
            created_by=created_by,
            **defaults
        )
    return _create_booking

@pytest.fixture
def event_factory():
    """Factory for creating events with custom parameters."""
    def _create_event(booking=None, requester=None, **kwargs):
        defaults = {
            'start_at': datetime(2025, 5, 1, 10, 0, tzinfo=timezone.utc),
            'end_at': datetime(2025, 5, 1, 12, 0, tzinfo=timezone.utc),
        }
        defaults.update(kwargs)
        
        return Event.objects.create(
            booking=booking,
            requester=requester,
            **defaults
        )
    return _create_event