import os


class DocumentService:

    ALLOWED_TYPES = [

        "Prescription",

        "X-Ray",

        "Blood Report",

        "MRI",

        "ECG",

        "Appointment",

        "Other",
    ]

    ALLOWED_EXTENSIONS = [

        ".pdf",

        ".png",

        ".jpg",

        ".jpeg",
    ]

    @staticmethod
    def is_valid_document_type(document_type):

        return document_type in DocumentService.ALLOWED_TYPES

    @staticmethod
    def is_valid_extension(filename):

        extension = os.path.splitext(filename)[1].lower()

        return extension in DocumentService.ALLOWED_EXTENSIONS

class DocumentExtractionService:

    @staticmethod
    def extract_text(file_path):
        from .ai_service import AIService

        ai_service = AIService()
        return ai_service.analyze_image(
            prompt="Extract the full medical document text and structured data as JSON.",
            file_path=file_path,
            system_prompt="Return only JSON.",
        )
