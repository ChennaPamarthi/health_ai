from .appointment_agent import AppointmentAgent
from .health_report_agent import HealthReportAgent
from .input_understanding_agent import InputUnderstandingAgent
from .medicine_agent import MedicineAgent


class AgentOrchestrator:
    """
    Coordinates all AI agents.
    """

    def __init__(self):
        self.input_agent = InputUnderstandingAgent()
        self.business_agents = [
            MedicineAgent(),
            AppointmentAgent(),
            HealthReportAgent(),
        ]

    def process(self, patient, document, ai_data):
        """
        Complete AI workflow.
        """
        routing = self.input_agent.process(ai_data)
        document_type = routing["document_type"]
        data = routing["data"]

        for agent in self.business_agents:
            if agent.can_handle({"document_type": document_type}):
                if isinstance(agent, MedicineAgent):
                    return agent.process(patient, document, data)

                if isinstance(agent, AppointmentAgent):
                    return agent.process(patient, data)

                if isinstance(agent, HealthReportAgent):
                    return agent.process(patient, document, data)

        return {
            "success": True,
            "document": document,
            "document_type": document_type,
            "data": data,
        }
