# CORE BE EXTRAS SYSTEM

## Concept

Due to the system's desired generic behavior, there's some information that needs to be stored in the database that does not belong to the field of any model. To solve this issue we implemented a system to be able to handle non-generic fields in a specific model, `Extra`.

In these docs and in the code, we will say that a model that supports extras is **extendable**.

The `Extra` model consists of:
- a [generic foreign key](https://docs.djangoproject.com/en/4.2/ref/contrib/contenttypes/#generic-relations),
- a relationship to the `Business` model, to be able to allow key overlap across several businesses,
- a `key` field, used to identify the extra field,
- a `data` JSON field, used to store the information.


## Usage

### Extendable model

To make a model extendable, we make it inherit the abstract model `ExtendableModel`. This provides the model knowledge of the relation with `Extra` and overrides its default [queryset](https://docs.djangoproject.com/en/5.0/ref/models/querysets/) for `ExtraQuerySet`.

Please note that all extendable models are assumed to be [soft deletable](_soft_deletion.md) for simplicity in inheritance.

### Extendable serializer

If a model is extendable, we may want to make its serializer support this behavior too; for this the serializer should inherit `ExtendableSerializer`, built from `extendable_serializer`.

This serializer supertype will add a serializer method field `extra` to be populated with the fields that do not match the model's fields.

It is noteworthy that we need take this `extra` field into account when dealing with serialized data. 

To handle extras, we should call the service function `manage_extra_attrs`, this will compare the extras provided from the serializer to those already in the model if it already exists and create, update or delete them accordingly, while also preserving the JSON structure of the extra data.

See for example:

```python
class MyExtendableCreateSerializer(extendable_serializer(MyExtendableModel)):
    def create(self, validated_data=None):
        data: dict = validated_data or self.validated_data
        my_extendable_instance = MyExtendableModel.objects.create(**data)
        return my_extendable_instance.id
```

The example will fail because data has the `extra` key that has not been dealt with and will return an error. Even if no error was raised, the extras will not be properly handled. The proper usage would be:

```diff
class MyExtendableCreateSerializer(extendable_serializer(MyExtendableModel)):
    def create(self, business, validated_data=None):
        data: dict = validated_data or self.validated_data
+        extras = data.pop('extra', [])
        my_extendable_instance = MyExtendableModel.objects.create(**data)
+        manage_extra_attrs(business, my_extendable_instance, extras)
        return my_extendable_instance.id
```

Same usage applies for update and patch serializers as well; however note that in patch if no extras are passed, we must avoid calling `manage_extra_attrs` altogether to prevent clearing all extras unexpectedly.

### Querying extras

Given an extendable model's queryset, we can filter it like we would for any other model field as long as we query shallow extras (neither array nor object) using `filter_by_extra`.

To allow more flexibility, we can filter an extendable queryset using [query params](_api_query_params.md) with the `filter_by_extra_query_params` function.

For example, let's say for some reason we care about documenting in an event a dog's attributes, garden information and main toy, so our events would be linked to `Extra` instances with the following values (written as JSON for easy visualization):

```json
{
  "toy": "chewable squeaky bone",
  "garden": {
    "size": "250m2",
    "floor": "grass"
  },
  "dog": {
    "breed": "gsd",
    "age": 4,
    "name": "Pan de miga"
  }
}
```

- We can query for all previous events with "bone" toys like
```python
# Simple way assuming shallow extras, this will fail if toy is an object
filtered_events = (
    Event.objects
    .all()
    .filter(end_at__lt=date.today())
    .filter_by_extra(toy__icontains="bone")
)

# More flexible way using query params
qp = QueryParams()
qp["toy__icontains"] = "bone"
filtered_events = (
    Event.objects
    .all()
    .filter(end_at__lt=date.today())
    .filter_by_extra_query_params(qp)
)
```


- If we wanted to query all previous events where there was a dog older than 3 years old and in grass gardens, the easiest way would be to do it as follows
```python
qp = QueryParams()
qp["garden.floor"] = "grass"
qp["dog.age__gt"] = 3
filtered_events = (
    Event.objects
    .all()
    .filter(end_at__lt=date.today())
    .filter_by_extra_query_params(qp)
)
```

Note that we need to query `end_at` separatedly because it is **not** an extra field.
Also note that in `QueryParams`, we use `.` to access an object value's field for an extra and `__` to specify the [lookup](https://docs.djangoproject.com/en/5.0/topics/db/queries/#field-lookups).
