from .base_agent import BaseAgent


class InputUnderstandingAgent(BaseAgent):
    """
    Classifies the extracted document and
    determines which downstream agent
    should process it.
    """

    name = "Input Understanding Agent"

    DOCUMENT_MAPPING = {
        "Prescription": "medicine",
        "Appointment": "appointment",
        "Blood Report": "health_report",
        "MRI": "health_report",
        "ECG": "health_report",
        "X-Ray": "health_report",
        "Other": "unknown",
    }

    def can_handle(self, data):
        """
        This is always the first agent,
        so it accepts every document.
        """
        return True

    def process(self, data):
        raw_document_type = str(data.get("document_type", "Other")).strip()
        normalized = raw_document_type.lower()

        canonical_map = {
            "prescription": "Prescription",
            "appointment": "Appointment",
            "blood report": "Blood Report",
            "mri": "MRI",
            "ecg": "ECG",
            "x-ray": "X-Ray",
            "other": "Other",
        }

        document_type = canonical_map.get(
            normalized,
            raw_document_type.title(),
        )

        route = self.DOCUMENT_MAPPING.get(document_type, "unknown")

        return {
            "success": True,
            "document_type": document_type,
            "next_agent": route,
            "data": data,
        }
