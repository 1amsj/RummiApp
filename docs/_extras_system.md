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

If a model is extendable, we may want to make its serializer support this behavior too; for this the serializer should inherit `ExtendableSerializer`. 

This serializer supertype will add a serializer method field `extra` to be populated with the fields that do not match the model's fields.

It is noteworthy that if we need take this `extra` field into account when dealing with serialized data, see for example:

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
