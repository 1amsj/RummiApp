from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core_backend.models import Booking
from core_backend.serializers.serializers_utils import extendable_serializer
from core_backend.serializers.serializers import EventNoBookingSerializer, BookingSerializer, EventSerializer

class BookingLightNoEventsSerializer(extendable_serializer(Booking)):
    public_id = serializers.ReadOnlyField()

    class Meta:
        model = Booking
        fields = ['id', 'business', 'public_id']
        
    @staticmethod
    def get_default_queryset():
        return (
            Booking.objects
            .all()
            .not_deleted('business')
        )

class BookingLightSerializer(BookingLightNoEventsSerializer):
    events = EventNoBookingSerializer(many=True)

    @staticmethod
    def get_default_queryset():
        return (
            super(BookingSerializer, BookingSerializer)
            .get_default_queryset()
            .prefetch_related(
                Prefetch(
                    'events',
                    queryset=EventNoBookingSerializer.get_default_queryset(),
                ),
            )
        )
        
class EventLightSerializer(EventNoBookingSerializer):
    booking = BookingLightNoEventsSerializer()

    @staticmethod
    def get_default_queryset():
        return (
            super(EventSerializer, EventSerializer)
            .get_default_queryset()
            .prefetch_related(
                Prefetch(
                    'booking',
                    queryset=BookingLightNoEventsSerializer.get_default_queryset(),
                ),
            )
        )