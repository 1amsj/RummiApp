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
