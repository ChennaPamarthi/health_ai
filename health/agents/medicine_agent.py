from .base_agent import BaseAgent
from health.services.medicine_service import MedicineService


class MedicineAgent(BaseAgent):

    name = "Medicine Agent"

    def can_handle(self, data):

        return data.get("document_type") == "Prescription"

    def process(
        self,
        patient,
        document,
        data,
    ):

        result = MedicineService.create_prescription(
            patient=patient,
            document=document,
            ai_data=data,
        )

        return {
            "success": True,
            "prescription": result["prescription"],
            "medicines": result["medicines"],
        }