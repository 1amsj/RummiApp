# CORE BE EXTRAS SYSTEM

## Concept

Due to the system's desired generic behavior, there's some information that needs to be stored in the database that does not belong to the field of any model. To solve this issue we implemented a system to be able to handle non-generic fields in a specific model, `Extra`.

The `Extra` model consists of:
- a [generic foreign key](https://docs.djangoproject.com/en/4.2/ref/contrib/contenttypes/#generic-relations),
- a relationship to the `Business` model, to be able to allow key overlap across several businesses,
- a `key` field, used to identify the extra field,
- a `data` JSON field, used to store the information.
