from datetime import datetime, time
import re

from health.models import (
    MedicineSchedule,
    Prescription,
    PrescriptionMedicine,
)


class MedicineService:
    DEFAULT_TIMES = {
        "Morning": time(8, 0),
        "Afternoon": time(13, 0),
        "Evening": time(18, 0),
        "Night": time(20, 0),
    }

    @staticmethod
    def normalize_frequency(value):
        if value in (None, ""):
            return []
        if isinstance(value, str):
            parts = [
                part.strip()
                for part in re.split(r"[,/|]+", value)
                if part.strip()
            ]
            return parts or [value.strip()]
        if isinstance(value, (list, tuple, set)):
            return [
                str(item).strip()
                for item in value
                if str(item).strip()
            ]
        return [str(value).strip()]

    @classmethod
    def create_prescription(cls, patient, document, ai_data):
        """
        Create a prescription with medicines and reminder schedules.
        """
        prescription = Prescription.objects.create(
            patient=patient,
            document=document,
            doctor_name=ai_data.get("doctor_name", ""),
            hospital_name=ai_data.get("hospital_name", ""),
            diagnosis=ai_data.get("diagnosis", ""),
            prescription_date=cls.parse_date(ai_data.get("prescription_date")),
            review_date=cls.parse_date(ai_data.get("review_date")),
            notes=ai_data.get("notes", ""),
        )

        medicines = []

        for item in ai_data.get("medicines", []):
            if not isinstance(item, dict):
                continue

            frequency = cls.normalize_frequency(item.get("frequency", []))
            frequency = [
                entry.title()
                for entry in frequency
                if entry
            ]

            if not any(
                str(item.get(field, "")).strip()
                for field in ("medicine_name", "strength", "dosage", "duration")
            ):
                continue

            quantity = item.get("quantity", 1)
            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                quantity = 1

            medicine = PrescriptionMedicine.objects.create(
                prescription=prescription,
                medicine_name=item.get("medicine_name", ""),
                strength=item.get("strength", ""),
                dosage=item.get("dosage", ""),
                duration=item.get("duration", ""),
                quantity=quantity,
                frequency=frequency,
                food_instruction=item.get("food_instruction") or "After Food",
                special_instruction=item.get("special_instruction", ""),
            )

            cls.create_schedule(medicine)
            medicines.append(medicine)

        return {
            "prescription": prescription,
            "medicines": medicines,
        }

    @classmethod
    def create_schedule(cls, medicine):
        for frequency in cls.normalize_frequency(medicine.frequency):
            frequency = str(frequency).title()
            reminder_time = cls.DEFAULT_TIMES.get(frequency)
            if reminder_time is None:
                continue

            MedicineSchedule.objects.create(
                medicine=medicine,
                reminder_time=reminder_time,
                start_date=datetime.today().date(),
                status="Active",
            )

    @staticmethod
    def parse_date(value):
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None
