from typing import List, Optional

from rest_framework.status import HTTP_200_OK

from core_backend.datastructures import Singleton
from core_backend.exceptions import RequestFailedException
from core_backend.services.concord.concord_authentication import ConcordAuthentication, ConcordDebugAuthentication
from core_backend.services.concord.concord_http_client import ConcordDebugHttpClient, ConcordHttpClient
from core_backend.services.concord.concord_interfaces import FaxJobFile, FaxJobRecipient, FaxJobStatus
from core_backend.services.concord.concord_response_handler import ConcordDebugResponseHandler, ConcordResponseHandler
from core_backend.settings import CONCORD_DEBUG, \
    CONCORD_USERNAME


class ConcordService(metaclass=Singleton):
    def __init__(
            self,
            authentication: Optional[ConcordAuthentication] = None,
            http_client: Optional[ConcordHttpClient] = None,
            response_handler: Optional[ConcordResponseHandler] = None
    ):
        params = [authentication, http_client, response_handler]
        if any(params):
            assert all(params), "Either all or none of the dependency injected parameters must be set"

            print("Dependency injected Concord init")
            self.authentication = authentication
            self.http_client = http_client
            self.response_handler = response_handler

        elif CONCORD_DEBUG:
            print("Debug Concord init")
            self.authentication = ConcordDebugAuthentication()
            self.http_client = ConcordDebugHttpClient(self.authentication)
            self.response_handler = ConcordDebugResponseHandler()

        else:
            print("Prod Concord init")
            self.authentication = ConcordAuthentication()
            self.http_client = ConcordHttpClient(self.authentication)
            self.response_handler = ConcordResponseHandler()

    @staticmethod
    def _validate_response(response):
        if response.status_code != HTTP_200_OK:
            raise RequestFailedException(response.status_code, response.text)

    def check_service(self) -> str:
        response = self.http_client.json_request({
            "CheckService": {}
        })

        self._validate_response(response)

        response_data = response.json()
        return self.response_handler.check_service(response_data)

    def get_fax_status(self, job_ids: List[str]) -> List[FaxJobStatus]:
        response = self.http_client.json_request({
            "GetFaxStatus": {
                "UserID": CONCORD_USERNAME,
                "FaxJobIds": [{"JobId": job_id} for job_id in job_ids],
            }
        })

        self._validate_response(response)

        response_data = response.json()
        return self.response_handler.get_fax_status(response_data, job_ids)

    def send_fax(self, fax_recipients: List[FaxJobRecipient], fax_files: List[FaxJobFile]) -> (List[str], float):
        response = self.http_client.json_request({
            "SendFax": {
                "UserID": CONCORD_USERNAME,
                "Recipients": [fax_recipient.to_dict() for fax_recipient in fax_recipients],
                "FaxJobFiles": [fax_file.to_dict() for fax_file in fax_files],
            }
        })

        self._validate_response(response)

        response_data = response.json()
        return self.response_handler.send_fax(response_data, fax_recipients, fax_files)
