# CORE BE MODELS AND RELATIONS

## Business model

The `Business` model consists only of a `name` field. This is what will be used to distinguish between different business in the same system. For example if we want to have coexisting "interpretation" and "care" businesses, each with their own bookings, services and invoices, we need to distinguish them using this field. For this reason, this field is asked for in almost every endpoint as a URL path param.


## People models

- `User`: represents a person related to the system. This holds their basic data such as names, ids, contacts, locations and other fields of interest. 
   
   Every person relevant to the system will have a user, but this user does not necessarily have to be able to access via password.

### Roles

Not to be confused with [Django's permissions and groups](https://docs.djangoproject.com/en/5.0/topics/auth/default/).

Roles represent each person's interactions with the system. They expose a set of role values that are used to link them to other data. These roles may or may not be unique per user and they store information relevant only to that specific kind of interaction and no other, if a piece of information is relevant across all roles, it most likely belongs at the user level.

All roles can be linked to `Company` to represent that they are related to said company. For example a provider working for a contractor.

The roles are:

- `Operator`: represents a person in charge of maintaining or controlling the system. One per user. These people usually are those who will create or curate bookings.

- `Payer`: represents a person that will pay for a booking's invoice. One per user. They don't necessarily need to be the entity to be invoiced, they can be a claims adjuster for example.

- `Provider`☆: represents the person who provides the service. Multiple or none per user. This role stores the information about the payment of the service provider; if a different contract type or payment methods are to be used for different services, different provider roles are to be created.

- `Recipient`☆: represents the beneficiary of a booking. One per user. Usually this model is not used on its own but rather an `Affiliation` is used instead.

- `Requester`: represents the person who requested a booking to be created. One per user.

- `Agent`☆: represents any miscellaneous role that needs to be kept track of in the system. Multiple or none per user. The `role` field is used to identify the role in question (i.e. lawyer).


In the places where we would want to represent a beneficiary of a booking, we use `Affiliation` instead of `Recipient`.
- `Affiliation`☆: represents the relationship between a recipient and a company, where the recipient is being covered under a `Company`, for example an insurance. The field `company` can be `null`, in which case this is interpreted to be only the recipient.


## Service models

- `Service`☆:

- `ServiceRoot`:

- `Category`:

- `ServiceArea`:


## Booking models

- `Booking`☆:

- `Event`☆:

- `Authorization`☆:

- `Offer`☆:

- `Report`☆:

- `Expense`:


## System models

- `Notification`: represents a notification. This is used to store information and keep track of the notifications sent. This contains all the information related to the payload, priority, data, template to be used, times of interest, job id, etc.

- `ExternalApiToken`: represents a token for an external API. This is used to authenticate the system with external services.

- `UniqueCondition`: used to generically represent a unique constraint in database.


## Other models

- `Contact`: represents contact information. A single `Contact` row stores phone, email, fax and the context for each.

- `Company`: represents a company. This can be used to detail relationships between users, roles and bookings. These are generic and have a `type` field to distinguish between them. For example a `Company` can be a contractor, an insurance, a hospital, etc. A company can have a parent company.

- `Language`: represents a language.

- `Location`: represents a location or an address.

- `Note`: represents a note. Used for the user to store arbitrary information that is not representable in the system. This can be used to automatically produce notes for the user, for example when a notification is sent, a note is created for the user to be able to see this information from the booking.


## Billing models

These are still a work in progress


## Observations

`Rule`, `Ledger` and `Invoice` are some placeholder models currently not in use.

Every model is [soft deletable](_soft_deletion.md), except for `UniqueCondition`, `ExternalApiToken` and the placeholders.

Models marked with a star (☆) in this file are [extendable](_extras_system).

Every model keeps track of its [history](_historical_models.md), except for `Extra`, `UniqueCondition`, `Business`, `Note`, `ExternalApiToken` and the placeholders.
