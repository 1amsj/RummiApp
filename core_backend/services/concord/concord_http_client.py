import json

import requests
from rest_framework.status import HTTP_200_OK

from core_backend.services.concord.concord_authentication import ConcordAuthentication
from core_backend.settings import CONCORD_API_URL


class ConcordHttpClient:
    def __init__(self, authentication: ConcordAuthentication):
        self.authentication = authentication

    def request(self, headers, payload):
        assert CONCORD_API_URL, "CONCORD_API_URL must be set"

        self.authentication.assert_authenticated()

        headers['Authorization'] = f"Bearer {self.authentication.access_token}"
        # TODO headers['x-ch-request-id'] = ..., we need to ask Concord about this when we get to production

        return requests.post(CONCORD_API_URL, headers=headers, data=payload)

    def soap_request(self, soap_body):
        headers = {
            'Content-Type': "application/soap+xml; charset=utf-8",
        }

        payload = f"""<?xml version="1.0" encoding="utf-8"?>
                      <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns="urn:FaxWS">
                      <soap:Header/>
                      <soap:Body>
                          {soap_body}
                      </soap:Body>
                      </soap:Envelope>"""

        return self.request(headers, payload)

    def json_request(self, json_payload):
        headers = {
            'Content-Type': "application/json; charset=utf-8",
        }

        payload = json.dumps(json_payload)

        return self.request(headers, payload)

# Debug
class ConcordDebugHttpClient(ConcordHttpClient):
    def request(self, headers, payload):
        print("Concord request:", headers, payload)

        response = requests.Response()
        response.status_code = HTTP_200_OK
        response._content = b'{"DEBUG": true}'

        return response
