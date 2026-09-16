import os


class FileService:

    IMAGE_EXTENSIONS = (
        ".jpg",
        ".jpeg",
        ".png",
    )

    PDF_EXTENSION = ".pdf"

    @staticmethod
    def get_extension(file_path):

        return os.path.splitext(file_path)[1].lower()

    @classmethod
    def is_pdf(cls, file_path):

        return cls.get_extension(file_path) == cls.PDF_EXTENSION

    @classmethod
    def is_image(cls, file_path):

        return cls.get_extension(file_path) in cls.IMAGE_EXTENSIONS