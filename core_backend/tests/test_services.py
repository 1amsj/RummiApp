from django.test import TestCase

from core_api.constants import EXACT_MATCH_KEY
from core_backend.models import Booking
from core_backend.services import filter_extra_attrs


class ExtrasTestCase(TestCase):
    def test_filter_extra(self):
        fields = {
            'operators': 0,
            'services': 0,
        }

        filtered = filter_extra_attrs(Booking, fields)
        self.assertFalse(filtered)

        fields['operator_id'] = 7
        fields['random_field'] = ':D'
        filtered = filter_extra_attrs(Booking, fields)
        self.assertTrue(('operator_id', 7) in filtered.items())
        self.assertTrue(('random_field', ':D') in filtered.items())
        self.assertFalse('operators' in filtered.keys())
        self.assertFalse('services' in filtered.keys())

        fields[EXACT_MATCH_KEY] = '???'
        filtered = filter_extra_attrs(Booking, fields)
        self.assertFalse(EXACT_MATCH_KEY in filtered.keys())
