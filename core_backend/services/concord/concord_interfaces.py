import base64
from enum import Enum

# DTOs for request
class FaxJobRecipient:
    def __init__(
            self,
            fax_number,
            company=None,
            title=None,
            name=None,
            secure_csid=None,
            first_name=None,
            last_name=None,
            address1=None,
            address2=None,
            city=None,
            state=None,
            zipcode=None,
            country=None,
            voice_number=None,
            **kwargs
    ):
        self.RecipFaxNumber = fax_number
        self.RecipCompany = company
        self.RecipTitle = title
        self.RecipName = name
        self.RecipSecureCSID = secure_csid
        self.RecipFirstName = first_name
        self.RecipLastName = last_name
        self.RecipAddress1 = address1
        self.RecipAddress2 = address2
        self.RecipCity = city
        self.RecipState = state
        self.RecipZipcode = zipcode
        self.RecipCountry = country
        self.RecipVoiceNumber = voice_number

        for attr in [f'RecipField{i}' for i in range(1, 13)]:  # RecipField1 ~ RecipField12
            setattr(self, attr, kwargs.get(attr, None))

    def to_dict(self):
        return self.__dict__


class FileFormats(int, Enum):
    TIFF_G3 = 1
    TIFF_G4 = 2
    TIFF_MERGE_COVER_FILES = 4
    WORD_DOCUMENT = 100
    PDF_DOCUMENT = 101
    RTF_DOCUMENT = 102
    EXCEL_DOCUMENT = 103
    POWERPOINT_DOCUMENT = 104
    TEXT_FILE = 105
    VISIO_DOCUMENT = 106
    GIF_IMAGE = 107
    JPEG_IMAGE = 108
    COLOR_TIFF = 109
    MHTML_COVER_OBSOLETE = 110
    MHTML = 111
    PNG = 120


class FaxJobFile:
    def __init__(self, file_index: int, file_type_id: FileFormats, file_data: bytes):
        self.FileIndex = file_index
        self.FileTypeId = file_type_id
        self.FileData = base64.b64encode(file_data)

    def to_dict(self):
        return {
            "FileIndex": self.FileIndex,
            "FileTypeId": self.FileTypeId,
            "FileData": self.FileData.decode('utf-8'),
        }


class FaxJobScheduleStartType(int, Enum):
    IMMEDIATE = 0
    SCHEDULED = 1


class FaxJobDetails:
    def __init__(
            self,
            schedule_start_type,
            schedule_start_date=None,
            expiry_date=None,
            sender_csid=None,
            sender_name=None,
            sender_company=None,
            sender_phone=None,
            cover_text=None,
            cover_name=None,
            cover_subject=None,
            reference_id=None,
            resolution=None,
            sender_fax=None,
            software_client=None,
            notify_type=None,
            notify_include_delivered_image=None,
            notify_destination=None,
            notify_auth_user=None,
            notify_auth_password=None,
            **kwargs
    ):
        self.JobScheduleStartType = schedule_start_type
        self.JobScheduleStartDate = schedule_start_date
        self.JobExpiryDate = expiry_date
        self.SenderCSID = sender_csid
        self.SenderName = sender_name
        self.SenderCompany = sender_company
        self.SenderPhone = sender_phone
        self.CoverText = cover_text
        self.CoverName = cover_name
        self.CoverSubject = cover_subject
        self.ReferenceId = reference_id
        self.Resolution = resolution
        self.SenderFax = sender_fax
        self.SoftwareClient = software_client
        self.NotifyType = notify_type
        self.NotifyIncludeDeliveredImage = notify_include_delivered_image
        self.NotifyDestination = notify_destination
        self.NotifyAuthUser = notify_auth_user
        self.NotifyAuthPassword = notify_auth_password

        for attr in [f'UserField{i}' for i in range(1, 13)]:  # UserField1 ~ UserField12
            setattr(self, attr, kwargs.get(attr, None))

    def to_dict(self):
        return self.__dict__


# DTOs for response
class FaxStatusCode(int, Enum):
    SUCCESS = 1
    FAILURE = 2
    IN_PROGRESS = 3
    DEBUG = -1


class FaxJobStatus:
    def __init__(self, job_id: str, status_code: FaxStatusCode, status_message: str, error_code: int = None, error_message: str = None):
        self.job_id = job_id
        self.status_code = status_code
        self.status_message = status_message
        self.error_code = error_code
        self.error_message = error_message

# DTOs for notification
class FaxNotifyType(int, Enum):
    NONE = 0
    EMAIL = 1
    HTTP_GET = 2
    HTTP_POST = 3


class FaxPushNotification:
    def __init__(
        self,
        account_id,
        reference_id,
        job_id,
        job_status_id,
        status_description,
        page_count,
        delivery_date_time,
        delivery_duration,
        remote_csid,
        error_code,
        error_string,
    ):
        self.account_id = account_id
        self.reference_id = reference_id
        self.job_id = job_id
        self.job_status_id = job_status_id
        self.status_description = status_description
        self.page_count = page_count
        self.delivery_date_time = delivery_date_time
        self.delivery_duration = delivery_duration
        self.remote_csid = remote_csid
        self.error_code = error_code
        self.error_string = error_string

    @staticmethod
    def from_request_data(data) -> 'FaxPushNotification':
        return FaxPushNotification(
            account_id=data.get('AccountId'),
            reference_id=data.get('ReferenceId'),
            job_id=data.get('FaxJobId'),
            job_status_id=int(data.get('FaxJobStatusId')),
            status_description=data.get('StatusDescription'),
            page_count=data.get('PageCount'),
            delivery_date_time=data.get('FaxDeliveryDateTime'),
            delivery_duration=data.get('FaxDeliveryDuration'),
            remote_csid=data.get('RemoteFaxCSID'),
            error_code=data.get('ErrorCode'),
            error_string=data.get('ErrorString'),
        )
