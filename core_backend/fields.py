from django.db import models
from pytz import timezone


class DailyUniqueIdentifierField(models.CharField):
    # This is a pre_save, therefore this will not be called on bulk_create, a for loop with .save() should be used instead
    def pre_save(self, model_instance, add):
        if not add:
            return model_instance.__dict__[self.name]

        # Get date in pst, this will only work for Booking model
        pst = timezone('US/Pacific')
        date_utc = model_instance.events.first().start_at
        date_pst = date_utc.astimezone(pst)

        # Get the last object with the same date prefix
        querySet = model_instance.__class__.objects.filter(**{
            F"{self.name}__startswith": date_pst.strftime('%y%m%d')
        })
        last_object = querySet.order_by(F"-{self.name}").first()

        # Increment the sequence number
        sequence_number = 1
        if last_object:
            last_sequence_number = int(last_object.__dict__[self.name][9:])
            sequence_number = last_sequence_number + 1

        # Set the unique identifier field value
        model_instance.__dict__[self.name] = '{}-{:03d}'.format(date_pst.strftime('%y%m%d'), sequence_number)

        return model_instance.__dict__[self.name]
