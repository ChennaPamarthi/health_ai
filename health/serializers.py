from datetime import date
import re

from django.utils import timezone
from rest_framework import serializers

from .models import (
    Appointment,
    Caregiver,
    HealthJournal,
    MedicalDocument,
    MedicalReport,
    MedicineLog,
    MedicineSchedule,
    NotificationEvent,
    Prescription,
    PrescriptionMedicine,
    Reminder,
    User,
)


def _normalize_frequency(value):
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


def _get_medicine_logs(medicine):
    return medicine.schedules.all().prefetch_related("logs")


def _get_medicine_status(medicine):
    latest_log = (
        MedicineLog.objects.filter(schedule__medicine=medicine)
        .select_related("schedule")
        .order_by("-scheduled_datetime", "-created_at")
        .first()
    )

    if latest_log:
        return latest_log.status

    if medicine.schedules.filter(is_enabled=True).exists():
        return "Active"

    return "Inactive"


def _get_medicine_counts(medicine):
    logs = MedicineLog.objects.filter(schedule__medicine=medicine)
    return {
        "schedule_count": medicine.schedules.count(),
        "taken_count": logs.filter(status="Taken").count(),
        "missed_count": logs.filter(status="Missed").count(),
        "pending_count": logs.filter(status__in=["Pending", "Sent"]).count(),
    }


def _get_medicine_range(medicine):
    start_dates = [
        schedule.start_date
        for schedule in medicine.schedules.all()
        if schedule.start_date
    ]
    end_dates = [
        schedule.end_date
        for schedule in medicine.schedules.all()
        if schedule.end_date
    ]

    start_date_value = min(start_dates) if start_dates else None
    end_date_value = max(end_dates) if end_dates else None

    remaining_days = None
    if end_date_value:
        remaining_days = (end_date_value - date.today()).days
        if remaining_days < 0:
            remaining_days = 0

    return start_date_value, end_date_value, remaining_days


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")


class MedicalDocumentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = MedicalDocument
        fields = (
            "id",
            "patient",
            "patient_name",
            "title",
            "description",
            "document_type",
            "file",
            "extracted_text",
            "classification",
            "classification_confidence",
            "vision_confidence",
            "needs_review",
            "structured_payload",
            "status",
            "uploaded_at",
            "updated_at",
        )
        read_only_fields = (
            "status",
            "uploaded_at",
            "updated_at",
            "extracted_text",
            "classification",
            "classification_confidence",
            "vision_confidence",
            "needs_review",
            "structured_payload",
            "patient_name",
        )

    def validate_file(self, value):
        allowed = [".pdf", ".png", ".jpg", ".jpeg"]
        filename = value.name.lower()

        if not any(filename.endswith(ext) for ext in allowed):
            raise serializers.ValidationError("Unsupported file format.")

        return value


class MedicineScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicineSchedule
        fields = (
            "id",
            "day_number",
            "reminder_time",
            "status",
            "start_date",
            "end_date",
            "is_enabled",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class MedicineLogSerializer(serializers.ModelSerializer):
    medicine_id = serializers.IntegerField(source="schedule.medicine.id", read_only=True)
    medicine_name = serializers.CharField(source="schedule.medicine.medicine_name", read_only=True)

    class Meta:
        model = MedicineLog
        fields = (
            "id",
            "schedule",
            "medicine_id",
            "medicine_name",
            "scheduled_datetime",
            "taken_at",
            "status",
            "reminder_sent",
            "reminder_sent_at",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class MedicineLogCreateSerializer(serializers.Serializer):
    medicine_id = serializers.IntegerField()
    schedule_id = serializers.IntegerField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=MedicineLog.STATUS_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class PrescriptionMedicineSerializer(serializers.ModelSerializer):
    prescription_id = serializers.IntegerField(source="prescription.id", read_only=True)
    patient_name = serializers.CharField(source="prescription.patient.full_name", read_only=True)
    doctor_name = serializers.CharField(source="prescription.doctor_name", read_only=True)
    hospital_name = serializers.CharField(source="prescription.hospital_name", read_only=True)
    prescription_date = serializers.DateField(source="prescription.prescription_date", read_only=True)
    review_date = serializers.DateField(source="prescription.review_date", read_only=True)
    status = serializers.SerializerMethodField()
    frequency_display = serializers.SerializerMethodField()
    schedule_count = serializers.SerializerMethodField()
    taken_count = serializers.SerializerMethodField()
    missed_count = serializers.SerializerMethodField()
    pending_count = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    remaining_days = serializers.SerializerMethodField()
    schedules = MedicineScheduleSerializer(many=True, read_only=True)
    recent_logs = serializers.SerializerMethodField()

    class Meta:
        model = PrescriptionMedicine
        fields = (
            "id",
            "prescription_id",
            "patient_name",
            "doctor_name",
            "hospital_name",
            "prescription_date",
            "review_date",
            "medicine_name",
            "strength",
            "dosage",
            "quantity",
            "frequency",
            "frequency_display",
            "duration",
            "food_instruction",
            "special_instruction",
            "is_active",
            "status",
            "schedule_count",
            "taken_count",
            "missed_count",
            "pending_count",
            "start_date",
            "end_date",
            "remaining_days",
            "schedules",
            "recent_logs",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_status(self, obj):
        return _get_medicine_status(obj)

    def get_frequency_display(self, obj):
        items = _normalize_frequency(obj.frequency)
        if not items:
            return ""
        return ", ".join(items)

    def validate_frequency(self, value):
        return _normalize_frequency(value)

    def get_schedule_count(self, obj):
        return _get_medicine_counts(obj)["schedule_count"]

    def get_taken_count(self, obj):
        return _get_medicine_counts(obj)["taken_count"]

    def get_missed_count(self, obj):
        return _get_medicine_counts(obj)["missed_count"]

    def get_pending_count(self, obj):
        return _get_medicine_counts(obj)["pending_count"]

    def get_start_date(self, obj):
        return _get_medicine_range(obj)[0]

    def get_end_date(self, obj):
        return _get_medicine_range(obj)[1]

    def get_remaining_days(self, obj):
        return _get_medicine_range(obj)[2]

    def get_recent_logs(self, obj):
        logs = (
            MedicineLog.objects.filter(schedule__medicine=obj)
            .select_related("schedule")
            .order_by("-scheduled_datetime", "-created_at")[:5]
        )
        return MedicineLogSerializer(logs, many=True).data


class PrescriptionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    medicine_count = serializers.SerializerMethodField()
    medicines = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = (
            "id",
            "patient_name",
            "doctor_name",
            "hospital_name",
            "diagnosis",
            "prescription_date",
            "review_date",
            "notes",
            "medicine_count",
            "medicines",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_medicine_count(self, obj):
        return obj.medicines.count()

    def get_medicines(self, obj):
        medicines = obj.medicines.all().prefetch_related("schedules")
        return PrescriptionMedicineSerializer(medicines, many=True).data


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = Appointment
        fields = (
            "id",
            "patient_name",
            "doctor_name",
            "hospital_name",
            "department",
            "appointment_date",
            "appointment_time",
            "purpose",
            "notes",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class MedicalReportSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    report_type_display = serializers.CharField(source="get_report_type_display", read_only=True)

    class Meta:
        model = MedicalReport
        fields = (
            "id",
            "patient_name",
            "report_type",
            "report_type_display",
            "report_title",
            "summary",
            "findings",
            "recommendations",
            "report_date",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class ManualPrescriptionEntrySerializer(serializers.Serializer):
    document_id = serializers.IntegerField(required=False, allow_null=True)
    doctor_name = serializers.CharField(required=False, allow_blank=True, default="")
    hospital_name = serializers.CharField(required=False, allow_blank=True, default="")
    diagnosis = serializers.CharField(required=False, allow_blank=True, default="")
    prescription_date = serializers.DateField(required=False, allow_null=True)
    review_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    medicines = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        allow_empty=False,
    )


class ManualAppointmentEntrySerializer(serializers.Serializer):
    document_id = serializers.IntegerField(required=False, allow_null=True)
    doctor_name = serializers.CharField(required=False, allow_blank=True, default="")
    hospital_name = serializers.CharField(required=False, allow_blank=True, default="")
    department = serializers.CharField(required=False, allow_blank=True, default="")
    appointment_date = serializers.DateField(required=False, allow_null=True)
    appointment_time = serializers.TimeField(required=False, allow_null=True)
    purpose = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ManualReportEntrySerializer(serializers.Serializer):
    document_id = serializers.IntegerField(required=False, allow_null=True)
    report_type = serializers.ChoiceField(choices=[choice[0] for choice in MedicalReport.REPORT_TYPE_CHOICES], required=False, default="Other")
    report_title = serializers.CharField(required=False, allow_blank=True, default="")
    summary = serializers.CharField(required=False, allow_blank=True, default="")
    findings = serializers.CharField(required=False, allow_blank=True, default="")
    recommendations = serializers.CharField(required=False, allow_blank=True, default="")
    report_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ReminderPreviewSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    schedule_id = serializers.IntegerField()
    reminder_id = serializers.IntegerField(required=False, allow_null=True)
    medicine_id = serializers.IntegerField()
    medicine_name = serializers.CharField()
    patient_name = serializers.CharField()
    doctor_name = serializers.CharField()
    reminder_time = serializers.TimeField()
    reminder_datetime = serializers.DateTimeField()
    status = serializers.CharField()
    message = serializers.CharField(allow_blank=True, required=False)
    dosage = serializers.CharField(allow_blank=True, required=False)
    frequency = serializers.ListField(child=serializers.CharField(), required=False)
    schedule_status = serializers.CharField(required=False)
    response_status = serializers.CharField(required=False)
    reminder_key = serializers.CharField(required=False, allow_blank=True)
    escalated_at = serializers.DateTimeField(required=False, allow_null=True)
    delivered_at = serializers.DateTimeField(required=False, allow_null=True)


class CaregiverSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = Caregiver
        fields = (
            "id",
            "patient",
            "patient_name",
            "name",
            "relationship",
            "email",
            "phone",
            "notification_preference",
            "enable_notifications",
            "is_primary",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at", "patient", "patient_name")

    def validate(self, attrs):
        preference = attrs.get("notification_preference", getattr(self.instance, "notification_preference", "email"))
        email = attrs.get("email", getattr(self.instance, "email", ""))
        phone = attrs.get("phone", getattr(self.instance, "phone", ""))

        if preference in {"email", "email_sms"} and not email:
            raise serializers.ValidationError({"email": "Email is required for email caregiver alerts."})
        if preference in {"sms", "email_sms"} and not phone:
            raise serializers.ValidationError({"phone": "Phone is required for SMS caregiver alerts."})
        return attrs


class NotificationEventSerializer(serializers.ModelSerializer):
    reminder_label = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = NotificationEvent
        fields = (
            "id",
            "reminder",
            "reminder_label",
            "patient_name",
            "recipient_label",
            "channel",
            "status",
            "delivered_at",
            "opened_at",
            "taken_at",
            "skipped_at",
            "escalated_at",
            "twilio_sid",
            "email_message_id",
            "error_message",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at", "reminder_label", "patient_name")

    def get_reminder_label(self, obj):
        try:
            return obj.reminder.schedule.medicine.medicine_name
        except Exception:
            return ""

    def get_patient_name(self, obj):
        return getattr(obj.recipient_user, "full_name", "")


class AnalyticsSummarySerializer(serializers.Serializer):
    total_prescriptions = serializers.IntegerField()
    total_medicines = serializers.IntegerField()
    total_appointments = serializers.IntegerField()
    total_reminders = serializers.IntegerField()
    total_reports = serializers.IntegerField()
    taken_count = serializers.IntegerField()
    missed_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    adherence_percentage = serializers.FloatField()
    active_medicines = serializers.IntegerField()
    recent_activity = serializers.ListField(child=serializers.DictField())
