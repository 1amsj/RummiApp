from datetime import datetime
from django.db import models

class DailyUniqueIdentifierField(models.CharField):
    # This is a pre_save, therefore this will not be called on bulk_create, a for loop with .save() should be used instead
    def pre_save(self, model_instance, add):
        if add:
            # Get the current date
            date = datetime.now().date()
            
            # Get the last object with the same date prefix
            qs = model_instance.__class__.objects.filter(**{
                F"{self.name}__startswith": date.strftime('%Y%m%d')
            })
            last_object = qs.order_by(F"-{self.name}").first()

            # Increment the sequence number
            sequence_number = 1
            if last_object:
                last_sequence_number = int(last_object.__dict__[self.name][9:])
                sequence_number = last_sequence_number + 1

            # Set the unique identifier field value
            model_instance.__dict__[self.name] = '{}-{:03d}'.format(date.strftime('%Y%m%d'), sequence_number)

        return model_instance.__dict__[self.name]