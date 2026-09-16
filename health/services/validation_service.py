import os


class ValidationService:

    ALLOWED_EXTENSIONS = (
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
    )

    MAX_FILE_SIZE = 20 * 1024 * 1024

    @classmethod
    def validate(cls, uploaded_file):

        extension = os.path.splitext(
            uploaded_file.name
        )[1].lower()

        if extension not in cls.ALLOWED_EXTENSIONS:

            raise ValueError(
                "Unsupported file format."
            )

        if uploaded_file.size > cls.MAX_FILE_SIZE:

            raise ValueError(
                "Maximum file size is 20MB."
            )

        return True