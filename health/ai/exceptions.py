class AIExtractionError(Exception):
    """
    Raised when the AI response cannot be parsed.
    """
    pass


class InvalidMedicineData(Exception):
    """
    Raised when extracted medicine data is invalid.
    """
    pass