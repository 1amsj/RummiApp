from core_backend.models import Event
from core_backend.serializers.serializers_update import EventUpdateSerializer
from core_backend.services.core_services import manage_extra_attrs, sync_m2m, update_model_unique_field


class EventPatchSerializer(EventUpdateSerializer):
    def __init__(self, *args, **kwargs):
        kwargs['partial'] = True
        super(EventPatchSerializer, self).__init__(*args, **kwargs)

    def patch(self, instance: Event, business, validated_data=None):
        data: dict = validated_data or self.validated_data
        affiliates = data.pop('affiliates', None)
        agents = data.pop('agents', None)
        extras = data.pop('extra', None)

        for (k, v) in data.items():
            setattr(instance, k, v)
        instance.save()

        if affiliates is not None:
            sync_m2m(instance.affiliates, affiliates)

        if agents is not None:
            sync_m2m(instance.agents, agents)

        if extras is not None:
            manage_extra_attrs(business, instance, extras)

        update_model_unique_field(business, instance)
