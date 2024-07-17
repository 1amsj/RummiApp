import math
import time
from warnings import warn

import requests
from django.db import transaction
from rest_framework.status import HTTP_200_OK

from core_api.constants import CONCORD_API_NAME
from core_api.decorators import raise_instead
from core_backend.exceptions import AuthenticationFailedException
from core_backend.models import ExternalApiToken
from core_backend.settings import CONCORD_CLIENT_ID, CONCORD_CLIENT_SECRET, CONCORD_DEBUG, \
    CONCORD_LOGIN_URL, \
    CONCORD_PASSWORD, \
    CONCORD_USERNAME

handle_key_error = raise_instead(AuthenticationFailedException, KeyError,
                                 "Concord authentication response is missing key: ")


class ConcordAuthentication:
    SCOPE = "FaxWS offline_access"

    def __init__(self):
        self.access_token = None
        self.expiration_timestamp = None
        self.refresh_token = None

        if not CONCORD_CLIENT_ID:
            return

        self._load_existing_token()

    def _load_existing_token(self):
        api_token_data = (
            ExternalApiToken.objects
            .filter(
                api_name=CONCORD_API_NAME,
                client_id=CONCORD_CLIENT_ID,
                expiration_timestamp__gt=time.time(),
                scope=self.SCOPE,
            )
            .first()
        )

        if not api_token_data:
            return

        self.access_token = api_token_data.access_token
        self.expiration_timestamp = api_token_data.expiration_timestamp
        self.refresh_token = api_token_data.refresh_token

    def _build_authentication_payload(self, is_refresh):
        payload = {
            "client_id": CONCORD_CLIENT_ID,
            "scope": self.SCOPE,
        }

        if CONCORD_CLIENT_SECRET:
            payload["grant_type"] = "client_credentials"
            payload["client_secret"] = CONCORD_CLIENT_SECRET

        elif CONCORD_USERNAME and CONCORD_PASSWORD:
            payload["grant_type"] = "password"
            payload["username"] = CONCORD_USERNAME
            payload["password"] = CONCORD_PASSWORD

        else:
            raise ValueError("Client secret or username and password must be set")

        if is_refresh:
            payload["grant_type"] = "refresh_token"
            payload["refresh_token"] = self.refresh_token

        return payload

    @handle_key_error
    def _handle_authentication_response(self, response_data):
        self.access_token = response_data["access_token"]
        self.expiration_timestamp = time.time() + response_data["expires_in"]
        self.refresh_token = response_data["refresh_token"]

        if response_data["token_type"] != "Bearer":
            warn(f"Token type is not Bearer: {response_data['token_type']}")

        ExternalApiToken.objects.update_or_create(
            api_name=CONCORD_API_NAME,
            client_id=CONCORD_CLIENT_ID,
            defaults={
                "access_token": self.access_token,
                "expiration_timestamp": self.expiration_timestamp,
                "refresh_token": self.refresh_token,
                "scope": self.SCOPE,
            }
        )

    @transaction.atomic
    def authenticate(self, is_refresh):
        assert not CONCORD_DEBUG, "Tried to setup prod Concord service in debug mode"
        assert CONCORD_LOGIN_URL, "CONCORD_LOGIN_URL must be set"

        if CONCORD_CLIENT_ID is None:
            raise ValueError("Client ID must be set")

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        payload = self._build_authentication_payload(is_refresh)

        response = requests.post(CONCORD_LOGIN_URL, headers=headers, data=payload)

        if response.status_code != HTTP_200_OK:
            raise AuthenticationFailedException(
                f"Concord log in failed. Response: [{response.status_code}] {response.text}")

        response_data = response.json()
        self._handle_authentication_response(response_data)

    def assert_authenticated(self):
        if self.access_token is None or time.time() > self.expiration_timestamp:
            is_refresh = bool(self.refresh_token)
            self.authenticate(is_refresh)


# Debug
class ConcordDebugAuthentication(ConcordAuthentication):
    # noinspection PyMissingConstructor
    def __init__(self):
        self.access_token = True
        self.expiration_timestamp = math.inf
        self.refresh_token = True

    def authenticate(self, is_refresh):
        pass

    def assert_authenticated(self):
        pass
