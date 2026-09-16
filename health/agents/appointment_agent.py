from datetime import datetime

from .base_agent import BaseAgent

from health.models import Appointment


class AppointmentAgent(BaseAgent):

    name = "Appointment Agent"

    def can_handle(self, data):

        return (
            data.get("document_type") == "Appointment"
        )

    def process(
        self,
        patient,
        data,
    ):

        appointment_date = datetime.now().date()
        appointment_time = datetime.now().time().replace(
            second=0,
            microsecond=0,
        )

        date_string = data.get(
            "appointment_date"
        )

        if date_string:

            try:

                appointment_date = datetime.strptime(
                    date_string,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                pass

        time_string = data.get(
            "appointment_time"
        )

        if time_string:

            try:

                appointment_time = datetime.strptime(
                    time_string,
                    "%H:%M"
                ).time()

            except ValueError:

                pass

        appointment = Appointment.objects.create(

            patient=patient,

            doctor_name=data.get(
                "doctor_name",
                ""
            ),

            hospital_name=data.get(
                "hospital_name",
                ""
            ),

            department=data.get(
                "department",
                ""
            ),

            appointment_date=appointment_date,

            appointment_time=appointment_time,

            purpose=data.get(
                "purpose",
                ""
            ),

            notes=data.get(
                "notes",
                ""
            ),
        )

        return {

            "success": True,

            "appointment": appointment,
        }
