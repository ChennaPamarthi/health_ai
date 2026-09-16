from django.utils.dateparse import parse_date

from health.models import MedicalReport
from health.serializers import MedicalReportSerializer

from .base_agent import BaseAgent


class HealthReportAgent(BaseAgent):
    name = "Health Report Agent"

    REPORT_TYPES = {
        "Blood Report",
        "MRI",
        "ECG",
        "X-Ray",
        "Other",
    }

    def can_handle(self, data):
        return data.get("document_type") in self.REPORT_TYPES

    def process(self, patient, document, data):
        report_type = data.get("document_type") or document.document_type or "Other"
        if report_type not in dict(MedicalReport.REPORT_TYPE_CHOICES):
            report_type = "Other"

        report_date = parse_date(data.get("report_date") or "")

        report, _ = MedicalReport.objects.update_or_create(
            document=document,
            defaults={
                "patient": patient,
                "report_type": report_type,
                "report_title": data.get("report_title", ""),
                "summary": data.get("report_summary", ""),
                "findings": data.get("findings", ""),
                "recommendations": data.get("recommendations", ""),
                "report_date": report_date,
                "notes": data.get("notes", ""),
            },
        )

        return {
            "success": True,
            "report": report,
            "report_data": MedicalReportSerializer(report).data,
        }
