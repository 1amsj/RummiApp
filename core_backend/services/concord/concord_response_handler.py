import json
import time
import uuid
from typing import List

from core_api.decorators import raise_instead
from core_backend.exceptions import RequestFailedException, UnexpectedResponseException
from core_backend.services.concord.concord_interfaces import FaxJobFile, FaxJobRecipient, FaxJobStatus, FaxStatusCode

# Response handler
handle_key_error = raise_instead(UnexpectedResponseException, KeyError, 'Missing key: ')


class ConcordResponseHandler:
    @handle_key_error
    def check_service(self, response_data):
        check_service_response = response_data["CheckServiceResponse"]
        return check_service_response["return"]

    @handle_key_error
    def get_fax_status(self, response_data, job_ids: List[str]):
        check_service_response = response_data["GetFaxStatusResponse"]
        was_successful = check_service_response["return"]

        if not was_successful:
            error_details = check_service_response["WSError"]
            raise RequestFailedException(response_data.status_code, json.dumps(error_details))

        fax_status_list = check_service_response["FaxStatusList"]

        ret_fax_status_list = []
        for fax_status in fax_status_list:
            ws_error = fax_status.get("Error", [])

            ret_fax_status_list.append(
                FaxJobStatus(
                    job_id=fax_status["FaxJobId"],
                    status_code=fax_status["FaxJobStatusId"],
                    status_message=fax_status["StatusDescription"],
                    error_code=ws_error.get("ErrorCode", None),
                    error_message=ws_error.get("ErrorMessage", None),
                )
            )

        return ret_fax_status_list

    @handle_key_error
    def send_fax(self, response_data, fax_recipients: List[FaxJobRecipient], fax_files: List[FaxJobFile]):
        send_fax_response = response_data["SendFaxResponse"]
        was_successful = send_fax_response["return"]

        if not was_successful:
            error_details = send_fax_response["WSError"]
            raise RequestFailedException(response_data.status_code, json.dumps(error_details))

        fax_job_ids = send_fax_response["FaxJobIds"]
        job_ids = [fax_job_id["JobId"] for fax_job_id in fax_job_ids]

        time_to_begin_job = send_fax_response["TTFP"]  # Time To First Print

        job_begin_time = time.time() + time_to_begin_job

        return job_ids, job_begin_time

# Debug
class ConcordDebugResponseHandler(ConcordResponseHandler):
    def check_service(self, response_data):
        return "DEBUG CONCORD"

    def get_fax_status(self, response_data, job_ids: List[str]):
        return [
            FaxJobStatus(
                job_id=job_id,
                status_code=FaxStatusCode.DEBUG,
                status_message="DEBUG_STATUS_MESSAGE",
                error_code=None,
                error_message=None,
            )
            for job_id in job_ids
        ]

    def send_fax(self, response_data, fax_recipients: List[FaxJobRecipient], fax_files: List[FaxJobFile]):
        return (
            [f"DEBUG_JOB_ID_{uuid.uuid4().hex}" for _ in fax_recipients],
            time.time() + 5,
        )
