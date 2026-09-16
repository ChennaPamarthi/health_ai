from datetime import datetime, timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User as AuthUser
from django.db.models import Count
from django.shortcuts import redirect, render
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import LoginForm, RegisterForm
from .models import (
    Appointment,
    Caregiver,
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
from .serializers import (
    AnalyticsSummarySerializer,
    AppointmentSerializer,
    CaregiverSerializer,
    MedicalDocumentSerializer,
    MedicalReportSerializer,
    ManualPrescriptionEntrySerializer,
    ManualAppointmentEntrySerializer,
    ManualReportEntrySerializer,
    MedicineLogCreateSerializer,
    MedicineLogSerializer,
    NotificationEventSerializer,
    PrescriptionMedicineSerializer,
    PrescriptionSerializer,
    ReminderPreviewSerializer,
)
from .services.document_service import DocumentService
from .services.caregiver_service import CaregiverService
from .services.medicine_service import MedicineService
from .services.reminder_service import ReminderService
from .services.user_service import UserService
from .services.validation_service import ValidationService


def get_patient_for_request(request):
    if not request.user.is_authenticated:
        return None
    return UserService.ensure_auth_user_profile(request.user)


class AuthenticatedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_patient(self, request):
        return get_patient_for_request(request)


def combine_date_time(day, clock_time):
    value = datetime.combine(day, clock_time)
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    return value


def build_medicine_status(medicine):
    latest_log = (
        MedicineLog.objects.filter(schedule__medicine=medicine)
        .order_by("-scheduled_datetime", "-created_at")
        .first()
    )
    if latest_log:
        return latest_log.status
    if medicine.schedules.filter(is_enabled=True).exists():
        return "Active"
    return "Inactive"


def build_today_reminders(patient):
    today = timezone.localdate()
    now = timezone.localtime().time()
    reminder_rows = {}

    schedules = (
        MedicineSchedule.objects.filter(
            medicine__prescription__patient=patient,
            is_enabled=True,
        )
        .select_related(
            "medicine",
            "medicine__prescription",
            "medicine__prescription__patient",
        )
        .prefetch_related("logs")
        .order_by("reminder_time")
    )

    payload = []
    todays_reminders = (
        Reminder.objects.filter(
            schedule__medicine__prescription__patient=patient,
            reminder_datetime__date=today,
        )
        .select_related(
            "schedule",
            "schedule__medicine",
            "schedule__medicine__prescription",
            "schedule__medicine__prescription__patient",
        )
        .order_by("schedule__reminder_time", "reminder_datetime")
    )

    for reminder in todays_reminders:
        schedule = reminder.schedule
        medicine = schedule.medicine
        prescription = medicine.prescription
        log = (
            MedicineLog.objects.filter(
                schedule=schedule,
                scheduled_datetime__date=today,
            )
            .order_by("-scheduled_datetime", "-created_at")
            .first()
        )

        status_value = log.status if log else reminder.status
        response_status = log.status if log else reminder.response_status
        key = (schedule.id, reminder.reminder_datetime.date())
        reminder_rows[key] = reminder.id

        payload.append(
            {
                "id": reminder.id,
                "schedule_id": schedule.id,
                "reminder_id": reminder.id,
                "medicine_id": medicine.id,
                "medicine_name": medicine.medicine_name,
                "patient_name": patient.full_name,
                "doctor_name": prescription.doctor_name,
                "reminder_time": schedule.reminder_time,
                "reminder_datetime": reminder.reminder_datetime,
                "status": status_value,
                "message": reminder.message or f"Take {medicine.medicine_name} ({medicine.dosage or 'No dosage'})",
                "dosage": medicine.dosage,
                "frequency": medicine.frequency or [],
                "schedule_status": schedule.status,
                "response_status": response_status,
                "reminder_key": reminder.reminder_key,
                "escalated_at": reminder.escalated_at,
                "delivered_at": reminder.delivered_at,
            }
        )

    for schedule in schedules:
        schedule_key = (schedule.id, today)
        if schedule_key in reminder_rows:
            continue

        medicine = schedule.medicine
        prescription = medicine.prescription
        latest_log = schedule.logs.filter(
            scheduled_datetime__date=today,
        ).order_by("-scheduled_datetime", "-created_at").first()
        latest_reminder = Reminder.objects.filter(
            schedule=schedule,
            reminder_datetime__date=today,
        ).order_by("-reminder_datetime", "-created_at").first()

        if latest_log:
            status_value = latest_log.status
        elif schedule.reminder_time <= now:
            status_value = "Pending"
        else:
            status_value = "Upcoming"

        payload.append(
            {
                "id": schedule.id,
                "schedule_id": schedule.id,
                "reminder_id": getattr(latest_reminder, "id", None),
                "medicine_id": medicine.id,
                "medicine_name": medicine.medicine_name,
                "patient_name": patient.full_name,
                "doctor_name": prescription.doctor_name,
                "reminder_time": schedule.reminder_time,
                "reminder_datetime": combine_date_time(today, schedule.reminder_time),
                "status": status_value,
                "message": f"Take {medicine.medicine_name} ({medicine.dosage or 'No dosage'})",
                "dosage": medicine.dosage,
                "frequency": medicine.frequency or [],
                "schedule_status": schedule.status,
                "response_status": getattr(latest_reminder, "response_status", "Pending"),
                "reminder_key": getattr(latest_reminder, "reminder_key", ""),
                "escalated_at": getattr(latest_reminder, "escalated_at", None),
                "delivered_at": getattr(latest_reminder, "delivered_at", None),
            }
        )

    payload.sort(key=lambda item: (item["reminder_time"], item["medicine_name"]))
    return payload


def build_dashboard_summary(patient):
    documents = MedicalDocument.objects.filter(patient=patient)
    reports = (
        MedicalReport.objects.filter(patient=patient)
        .select_related("patient", "document")
    )
    prescriptions = (
        Prescription.objects.filter(patient=patient)
        .select_related("patient")
        .prefetch_related("medicines")
    )
    medicines = (
        PrescriptionMedicine.objects.filter(prescription__patient=patient)
        .select_related("prescription", "prescription__patient")
        .prefetch_related("schedules")
    )
    appointments = Appointment.objects.filter(patient=patient).select_related("patient")
    logs = MedicineLog.objects.filter(
        schedule__medicine__prescription__patient=patient
    ).select_related("schedule", "schedule__medicine")

    taken_count = logs.filter(status="Taken").count()
    missed_count = logs.filter(status="Missed").count()
    pending_count = logs.filter(status__in=["Pending", "Sent"]).count()
    total_logs = taken_count + missed_count + pending_count
    adherence = round((taken_count / total_logs) * 100, 2) if total_logs else 0

    recent_prescriptions = PrescriptionSerializer(
        prescriptions.order_by("-created_at")[:5],
        many=True,
    ).data
    recent_appointments = AppointmentSerializer(
        appointments.order_by("appointment_date", "appointment_time")[:5],
        many=True,
    ).data
    recent_medicines = PrescriptionMedicineSerializer(
        medicines.order_by("-created_at")[:5],
        many=True,
    ).data
    recent_documents = MedicalDocumentSerializer(
        documents.order_by("-uploaded_at")[:5],
        many=True,
    ).data
    recent_reports = MedicalReportSerializer(
        reports.order_by("-created_at")[:5],
        many=True,
    ).data

    recent_activity = []
    for item in recent_documents:
        recent_activity.append(
            {
                "type": "Document",
                "title": item.get("document_type", "Document"),
                "subtitle": item.get("title") or item.get("description") or item.get("status"),
                "timestamp": item.get("uploaded_at"),
            }
        )
    for item in recent_reports:
        recent_activity.append(
            {
                "type": "Report",
                "title": item.get("report_type_display") or item.get("report_type") or "Report",
                "subtitle": item.get("report_title") or item.get("summary") or item.get("notes"),
                "timestamp": item.get("created_at"),
            }
        )
    for item in prescriptions.order_by("-created_at")[:5]:
        recent_activity.append(
            {
                "type": "Prescription",
                "title": item.doctor_name or "Prescription",
                "subtitle": item.patient.full_name,
                "timestamp": item.created_at.isoformat(),
            }
        )
    for item in appointments.order_by("-created_at")[:5]:
        recent_activity.append(
            {
                "type": "Appointment",
                "title": item.doctor_name,
                "subtitle": item.patient.full_name,
                "timestamp": item.created_at.isoformat(),
            }
        )

    recent_activity.sort(key=lambda entry: entry["timestamp"] or "", reverse=True)

    today_reminders = build_today_reminders(patient)

    return {
        "total_documents": documents.count(),
        "total_prescriptions": prescriptions.count(),
        "total_medicines": medicines.count(),
        "total_appointments": appointments.count(),
        "total_reminders": len(today_reminders),
        "total_reports": reports.count(),
        "taken_count": taken_count,
        "missed_count": missed_count,
        "pending_count": pending_count,
        "adherence_percentage": adherence,
        "active_medicines": medicines.filter(is_active=True).count(),
        "recent_prescriptions": recent_prescriptions,
        "recent_appointments": recent_appointments,
        "recent_medicines": recent_medicines,
        "recent_documents": recent_documents,
        "recent_reports": recent_reports,
        "recent_activity": recent_activity[:5],
        "today_reminders": today_reminders[:5],
    }


def build_analytics_summary(patient):
    today = timezone.localdate()
    logs = MedicineLog.objects.filter(
        schedule__medicine__prescription__patient=patient
    ).select_related(
        "schedule",
        "schedule__medicine",
        "schedule__medicine__prescription",
        "schedule__medicine__prescription__patient",
    )

    days = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        day_logs = logs.filter(scheduled_datetime__date=day)
        taken = day_logs.filter(status="Taken").count()
        missed = day_logs.filter(status="Missed").count()
        pending = day_logs.filter(status__in=["Pending", "Sent"]).count()
        total = taken + missed + pending
        adherence = round((taken / total) * 100, 2) if total else 0
        days.append(
            {
                "date": day.isoformat(),
                "label": day.strftime("%a"),
                "total": total,
                "taken": taken,
                "missed": missed,
                "pending": pending,
                "adherence_percentage": adherence,
            }
        )

    top_missed = list(
        logs.filter(status="Missed")
        .values("schedule__medicine__medicine_name")
        .annotate(missed_count=Count("id"))
        .order_by("-missed_count")[:5]
    )

    return {
        "summary": build_dashboard_summary(patient),
        "daily": days,
        "top_missed_medicines": top_missed,
    }


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = LoginForm(request.POST or None)
    error_message = ""

    if request.method == "POST" and form.is_valid():
        identifier = form.cleaned_data["identifier"].strip()
        password = form.cleaned_data["password"]

        auth_user = (
            AuthUser.objects.filter(username__iexact=identifier).first()
            or AuthUser.objects.filter(email__iexact=identifier).first()
        )

        if auth_user is not None:
            user = authenticate(
                request,
                username=auth_user.username,
                password=password,
            )
            if user is not None:
                login(request, user)
                UserService.ensure_auth_user_profile(user)
                return redirect("dashboard")

        error_message = "Invalid credentials."

    return render(
        request,
        "login.html",
        {
            "form": form,
            "error_message": error_message,
        },
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = RegisterForm(request.POST or None)
    error_message = ""

    if request.method == "POST" and form.is_valid():
        user = form.save()
        user.email = form.cleaned_data["email"]
        user.first_name = form.cleaned_data.get("first_name", "")
        user.last_name = form.cleaned_data.get("last_name", "")
        user.save(update_fields=["email", "first_name", "last_name"])

        login(request, user)
        UserService.ensure_auth_user_profile(user)
        return redirect("dashboard")

    if request.method == "POST" and not form.is_valid():
        error_message = "Please fix the errors below."

    return render(
        request,
        "register.html",
        {
            "form": form,
            "error_message": error_message,
        },
    )


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required(login_url="login")
def dashboard(request):
    return render(request, "dashboard.html")


@login_required(login_url="login")
def upload_page(request):
    return render(request, "upload.html")


@login_required(login_url="login")
def prescriptions_page(request):
    return render(request, "prescriptions.html")


@login_required(login_url="login")
def medicines_page(request):
    return render(request, "medicines.html")


@login_required(login_url="login")
def reminders_page(request):
    return render(request, "reminders.html")


@login_required(login_url="login")
def caregivers_page(request):
    return render(request, "caregivers.html")


@login_required(login_url="login")
def appointments_page(request):
    return render(request, "appointments.html")


@login_required(login_url="login")
def reports_page(request):
    return render(request, "reports.html")


@login_required(login_url="login")
def analytics_page(request):
    return render(request, "analytics.html")


@login_required(login_url="login")
def settings_page(request):
    return render(request, "settings.html")


class MedicalDocumentUploadView(AuthenticatedAPIView):
    def post(self, request):
        patient = self.get_patient(request)
        if patient is None:
            return Response(
                {"success": False, "message": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if "file" not in request.FILES:
            return Response(
                {"success": False, "message": "File is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            ValidationService.validate(request.FILES["file"])
        except Exception as error:
            return Response(
                {"success": False, "message": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = request.data.copy()
        payload["patient"] = patient.pk
        payload.setdefault("document_type", "Other")
        payload.setdefault("title", "")
        payload.setdefault("description", "")

        serializer = MedicalDocumentSerializer(data=payload)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Validation failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        document = serializer.save()
        result = DocumentService.process_document(document)

        if not result["success"]:
            return Response(
                {
                    "success": False,
                    "message": result["error"],
                    "document_id": document.id,
                    "status": document.status,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_data = {
            "success": True,
            "document": MedicalDocumentSerializer(document).data,
            "document_id": document.id,
            "document_type": document.document_type,
            "status": document.status,
            "processing_time": result["processing_time"],
            "extracted_text": document.extracted_text,
            "classification": document.classification,
            "classification_confidence": float(document.classification_confidence or 0),
            "vision_confidence": float(document.vision_confidence or 0),
            "needs_review": document.needs_review,
            "structured_payload": document.structured_payload,
            "editable_payload": document.structured_payload,
            "requires_user_review": bool(document.structured_payload.get("medicines")),
            "workflow_result": {},
        }

        workflow_result = result.get("workflow_result") or {}
        if workflow_result.get("prescription"):
            prescription = workflow_result["prescription"]
            medicines = workflow_result.get("medicines") or []
            response_data["workflow_result"] = {
                "type": "Prescription",
                "prescription": PrescriptionSerializer(prescription).data,
                "medicines": PrescriptionMedicineSerializer(medicines, many=True).data,
            }
            response_data["prescription_id"] = prescription.id
            response_data["medicine_count"] = len(medicines)
        elif workflow_result.get("appointment"):
            appointment = workflow_result["appointment"]
            response_data["workflow_result"] = {
                "type": "Appointment",
                "appointment": AppointmentSerializer(appointment).data,
            }
            response_data["appointment_id"] = appointment.id
        elif workflow_result.get("report"):
            report = workflow_result["report"]
            response_data["workflow_result"] = {
                "type": "Health Report",
                "report": MedicalReportSerializer(report).data
                if hasattr(report, "_meta")
                else workflow_result.get("report_data", report),
            }
            response_data["report_id"] = getattr(report, "id", None)

        return Response(response_data, status=status.HTTP_201_CREATED)


class MedicalDocumentAPIView(AuthenticatedAPIView):
    def get(self, request):
        patient = self.get_patient(request)
        documents = MedicalDocument.objects.filter(patient=patient).order_by("-uploaded_at")
        return Response(MedicalDocumentSerializer(documents, many=True).data)

    def delete(self, request, pk):
        patient = self.get_patient(request)
        try:
            document = MedicalDocument.objects.get(pk=pk, patient=patient)
        except MedicalDocument.DoesNotExist:
            return Response(
                {"success": False, "message": "Document not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if document.file:
            document.file.delete(save=False)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ManualPrescriptionEntryAPIView(AuthenticatedAPIView):
    def post(self, request):
        patient = self.get_patient(request)
        serializer = ManualPrescriptionEntrySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Validation failed.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = serializer.validated_data
        document = None
        document_id = payload.get("document_id")
        if document_id:
            try:
                document = MedicalDocument.objects.get(pk=document_id, patient=patient)
            except MedicalDocument.DoesNotExist:
                return Response(
                    {"success": False, "message": "Document not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        ai_data = {
            "doctor_name": payload.get("doctor_name", ""),
            "hospital_name": payload.get("hospital_name", ""),
            "diagnosis": payload.get("diagnosis", ""),
            "prescription_date": payload.get("prescription_date").isoformat() if payload.get("prescription_date") else "",
            "review_date": payload.get("review_date").isoformat() if payload.get("review_date") else "",
            "notes": payload.get("notes", ""),
            "medicines": payload.get("medicines", []),
        }

        result = MedicineService.create_prescription(
            patient=patient,
            document=document,
            ai_data=ai_data,
        )

        prescription = result["prescription"]
        medicines = result["medicines"]
        return Response(
            {
                "success": True,
                "prescription": PrescriptionSerializer(prescription).data,
                "medicines": PrescriptionMedicineSerializer(medicines, many=True).data,
                "medicine_count": len(medicines),
            },
            status=status.HTTP_201_CREATED,
        )


class ManualAppointmentEntryAPIView(AuthenticatedAPIView):
    def post(self, request):
        patient = self.get_patient(request)
        serializer = ManualAppointmentEntrySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Validation failed.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = serializer.validated_data
        document = None
        document_id = payload.get("document_id")
        if document_id:
            try:
                document = MedicalDocument.objects.get(pk=document_id, patient=patient)
            except MedicalDocument.DoesNotExist:
                return Response(
                    {"success": False, "message": "Document not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        appointment = Appointment.objects.create(
            patient=patient,
            doctor_name=payload.get("doctor_name", ""),
            hospital_name=payload.get("hospital_name", ""),
            department=payload.get("department", ""),
            appointment_date=payload.get("appointment_date") or timezone.localdate(),
            appointment_time=payload.get("appointment_time") or datetime.now().time().replace(second=0, microsecond=0),
            purpose=payload.get("purpose", ""),
            notes=payload.get("notes", ""),
        )

        return Response(
            {
                "success": True,
                "appointment": AppointmentSerializer(appointment).data,
                "document_id": getattr(document, "id", None),
            },
            status=status.HTTP_201_CREATED,
        )


class ManualReportEntryAPIView(AuthenticatedAPIView):
    def post(self, request):
        patient = self.get_patient(request)
        serializer = ManualReportEntrySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Validation failed.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = serializer.validated_data
        document_id = payload.get("document_id")
        if not document_id:
            return Response(
                {"success": False, "message": "document_id is required for report creation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            document = MedicalDocument.objects.get(pk=document_id, patient=patient)
        except MedicalDocument.DoesNotExist:
            return Response(
                {"success": False, "message": "Document not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        report_type = payload.get("report_type") or document.document_type or "Other"
        if report_type not in dict(MedicalReport.REPORT_TYPE_CHOICES):
            report_type = "Other"

        report, _ = MedicalReport.objects.update_or_create(
            document=document,
            defaults={
                "patient": patient,
                "report_type": report_type,
                "report_title": payload.get("report_title", ""),
                "summary": payload.get("summary", ""),
                "findings": payload.get("findings", ""),
                "recommendations": payload.get("recommendations", ""),
                "report_date": payload.get("report_date"),
                "notes": payload.get("notes", ""),
            },
        )

        return Response(
            {
                "success": True,
                "report": MedicalReportSerializer(report).data,
                "document_id": document.id,
            },
            status=status.HTTP_201_CREATED,
        )


class MedicinesAPIView(AuthenticatedAPIView):
    def get(self, request):
        patient = self.get_patient(request)
        medicines = (
            PrescriptionMedicine.objects.filter(prescription__patient=patient)
            .select_related("prescription", "prescription__patient")
            .prefetch_related("schedules")
            .order_by("medicine_name")
        )

        query = request.query_params.get("q", "").strip().lower()
        if query:
            medicines = medicines.filter(
                medicine_name__icontains=query
            ) | medicines.filter(
                dosage__icontains=query
            ) | medicines.filter(
                prescription__doctor_name__icontains=query
            )

        medicines = medicines.distinct()

        payload = []
        for medicine in medicines:
            item = PrescriptionMedicineSerializer(medicine).data
            item["status"] = build_medicine_status(medicine)
            payload.append(item)

        return Response(payload)


class MedicineDetailAPIView(AuthenticatedAPIView):
    def get_object(self, pk, patient):
        return PrescriptionMedicine.objects.select_related(
            "prescription",
            "prescription__patient",
        ).prefetch_related("schedules").get(
            pk=pk,
            prescription__patient=patient,
        )

    def get(self, request, pk):
        patient = self.get_patient(request)
        medicine = self.get_object(pk, patient)
        payload = PrescriptionMedicineSerializer(medicine).data
        payload["status"] = build_medicine_status(medicine)
        return Response(payload)

    def put(self, request, pk):
        patient = self.get_patient(request)
        medicine = self.get_object(pk, patient)
        serializer = PrescriptionMedicineSerializer(medicine, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            payload = PrescriptionMedicineSerializer(medicine).data
            payload["status"] = build_medicine_status(medicine)
            return Response(payload)

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    patch = put

    def delete(self, request, pk):
        patient = self.get_patient(request)
        medicine = self.get_object(pk, patient)
        medicine.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MedicineLogAPIView(AuthenticatedAPIView):
    def post(self, request):
        patient = self.get_patient(request)
        serializer = MedicineLogCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated = serializer.validated_data
        medicine = PrescriptionMedicine.objects.select_related(
            "prescription",
            "prescription__patient",
        ).prefetch_related("schedules").get(
            pk=validated["medicine_id"],
            prescription__patient=patient,
        )

        schedule = None
        schedule_id = validated.get("schedule_id")
        if schedule_id:
            schedule = medicine.schedules.filter(pk=schedule_id).first()
        if schedule is None:
            schedule = medicine.schedules.filter(is_enabled=True).order_by("reminder_time").first()

        if schedule is None:
            return Response(
                {"success": False, "message": "No active schedule found for this medicine."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        scheduled_datetime = combine_date_time(
            timezone.localdate(),
            schedule.reminder_time,
        )

        log, _ = MedicineLog.objects.get_or_create(
            schedule=schedule,
            scheduled_datetime=scheduled_datetime,
            defaults={
                "status": validated["status"],
                "notes": validated.get("notes", ""),
                "taken_at": timezone.now() if validated["status"] == "Taken" else None,
            },
        )

        log.status = validated["status"]
        log.notes = validated.get("notes", "")
        if validated["status"] == "Taken" and log.taken_at is None:
            log.taken_at = timezone.now()
        if validated["status"] != "Taken":
            log.taken_at = None
        log.save()

        return Response(MedicineLogSerializer(log).data, status=status.HTTP_201_CREATED)


class RemindersTodayAPIView(AuthenticatedAPIView):
    def get(self, request):
        patient = self.get_patient(request)
        return Response(ReminderPreviewSerializer(build_today_reminders(patient), many=True).data)


class PrescriptionsAPIView(AuthenticatedAPIView):
    def get(self, request):
        patient = self.get_patient(request)
        prescriptions = (
            Prescription.objects.filter(patient=patient)
            .select_related("patient")
            .prefetch_related("medicines", "medicines__schedules")
            .order_by("-created_at")
        )
        return Response(PrescriptionSerializer(prescriptions, many=True).data)


class PrescriptionDetailAPIView(AuthenticatedAPIView):
    def get_object(self, pk, patient):
        return Prescription.objects.select_related("patient").prefetch_related(
            "medicines",
            "medicines__schedules",
        ).get(
            pk=pk,
            patient=patient,
        )

    def get(self, request, pk):
        patient = self.get_patient(request)
        prescription = self.get_object(pk, patient)
        return Response(PrescriptionSerializer(prescription).data)

    def delete(self, request, pk):
        patient = self.get_patient(request)
        prescription = self.get_object(pk, patient)
        document = prescription.document
        if document and document.file:
            document.file.delete(save=False)
        prescription.delete()
        if document is not None:
            document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AppointmentsAPIView(AuthenticatedAPIView):
    def get(self, request):
        patient = self.get_patient(request)
        appointments = Appointment.objects.filter(patient=patient).select_related("patient").order_by(
            "appointment_date",
            "appointment_time",
        )
        return Response(AppointmentSerializer(appointments, many=True).data)


class ReportsAPIView(AuthenticatedAPIView):
    def get(self, request):
        patient = self.get_patient(request)
        reports = MedicalReport.objects.filter(patient=patient).select_related(
            "patient",
            "document",
        ).order_by("-created_at")
        return Response(MedicalReportSerializer(reports, many=True).data)


class ReportDetailAPIView(AuthenticatedAPIView):
    def get_object(self, pk, patient):
        return MedicalReport.objects.select_related("patient", "document").get(
            pk=pk,
            patient=patient,
        )

    def get(self, request, pk):
        patient = self.get_patient(request)
        return Response(MedicalReportSerializer(self.get_object(pk, patient)).data)


class AppointmentDetailAPIView(AuthenticatedAPIView):
    def get_object(self, pk, patient):
        return Appointment.objects.select_related("patient").get(pk=pk, patient=patient)

    def get(self, request, pk):
        patient = self.get_patient(request)
        return Response(AppointmentSerializer(self.get_object(pk, patient)).data)


class MedicineScheduleDetailAPIView(AuthenticatedAPIView):
    def get_object(self, pk, patient):
        return MedicineSchedule.objects.select_related(
            "medicine",
            "medicine__prescription",
            "medicine__prescription__patient",
        ).get(
            pk=pk,
            medicine__prescription__patient=patient,
        )

    def delete(self, request, pk):
        patient = self.get_patient(request)
        schedule = self.get_object(pk, patient)
        schedule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DashboardSummaryAPIView(AuthenticatedAPIView):
    def get(self, request):
        patient = self.get_patient(request)
        return Response(build_dashboard_summary(patient))


class AnalyticsSummaryAPIView(AuthenticatedAPIView):
    def get(self, request):
        patient = self.get_patient(request)
        summary = build_analytics_summary(patient)
        payload = {
            "total_prescriptions": summary["summary"]["total_prescriptions"],
            "total_medicines": summary["summary"]["total_medicines"],
            "total_appointments": summary["summary"]["total_appointments"],
            "total_reminders": summary["summary"]["total_reminders"],
            "total_reports": summary["summary"]["total_reports"],
            "taken_count": summary["summary"]["taken_count"],
            "missed_count": summary["summary"]["missed_count"],
            "pending_count": summary["summary"]["pending_count"],
            "adherence_percentage": summary["summary"]["adherence_percentage"],
            "active_medicines": summary["summary"]["active_medicines"],
            "recent_activity": summary["summary"]["recent_activity"],
        }
        return Response(
            {
                "summary": AnalyticsSummarySerializer(payload).data,
                "daily": summary["daily"],
                "top_missed_medicines": summary["top_missed_medicines"],
            }
        )


class CaregiversAPIView(AuthenticatedAPIView):
    def get(self, request):
        patient = self.get_patient(request)
        caregivers = Caregiver.objects.filter(patient=patient).order_by("-is_primary", "name")
        return Response(CaregiverSerializer(caregivers, many=True).data)

    def post(self, request):
        patient = self.get_patient(request)
        payload = request.data.copy()
        payload["patient"] = patient.pk
        serializer = CaregiverSerializer(data=payload)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Caregiver validation failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        caregiver = serializer.save(patient=patient)
        if caregiver.is_primary:
            Caregiver.objects.filter(patient=patient).exclude(pk=caregiver.pk).update(is_primary=False)

        return Response(CaregiverSerializer(caregiver).data, status=status.HTTP_201_CREATED)


class CaregiverDetailAPIView(AuthenticatedAPIView):
    def get_object(self, pk, patient):
        return Caregiver.objects.get(pk=pk, patient=patient)

    def get(self, request, pk):
        patient = self.get_patient(request)
        caregiver = self.get_object(pk, patient)
        return Response(CaregiverSerializer(caregiver).data)

    def put(self, request, pk):
        patient = self.get_patient(request)
        caregiver = self.get_object(pk, patient)
        serializer = CaregiverSerializer(caregiver, data=request.data, partial=False)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Caregiver validation failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        caregiver = serializer.save()
        if caregiver.is_primary:
            Caregiver.objects.filter(patient=patient).exclude(pk=caregiver.pk).update(is_primary=False)
        return Response(CaregiverSerializer(caregiver).data)

    patch = put

    def delete(self, request, pk):
        patient = self.get_patient(request)
        caregiver = self.get_object(pk, patient)
        caregiver.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationHistoryAPIView(AuthenticatedAPIView):
    def get(self, request):
        patient = self.get_patient(request)
        events = NotificationEvent.objects.filter(
            reminder__schedule__medicine__prescription__patient=patient
        ).select_related(
            "reminder",
            "reminder__schedule",
            "reminder__schedule__medicine",
        ).order_by("-created_at")
        return Response(NotificationEventSerializer(events, many=True).data)


class ReminderResponseAPIView(AuthenticatedAPIView):
    def post(self, request):
        patient = self.get_patient(request)
        reminder_id = request.data.get("reminder_id")
        action = str(request.data.get("action", "")).strip().lower()

        if not reminder_id or not action:
            return Response(
                {"success": False, "message": "reminder_id and action are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            reminder = Reminder.objects.select_related(
                "schedule",
                "schedule__medicine",
                "schedule__medicine__prescription",
            ).get(pk=reminder_id, schedule__medicine__prescription__patient=patient)
        except Reminder.DoesNotExist:
            return Response(
                {"success": False, "message": "Reminder not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        reminder_service = ReminderService()
        action_map = {
            "taken": reminder_service.mark_taken,
            "skipped": reminder_service.mark_skipped,
            "snooze": reminder_service.mark_snoozed,
        }

        if action not in action_map:
            return Response(
                {"success": False, "message": "Unsupported action."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reminder = action_map[action](reminder)
        log = MedicineLog.objects.filter(
            schedule=reminder.schedule,
            scheduled_datetime__date=reminder.reminder_datetime.date(),
        ).order_by("-created_at").first()

        if log is not None:
            status_map = {
                "taken": "Taken",
                "skipped": "Skipped",
                "snooze": "Snooze",
            }
            log.status = status_map[action]
            if action == "taken":
                log.taken_at = timezone.now()
            log.save(update_fields=["status", "taken_at", "updated_at"])

        NotificationEvent.objects.create(
            reminder=reminder,
            recipient_user=patient,
            recipient_label=patient.full_name,
            channel="manual",
            status="Taken" if action == "taken" else "Skipped" if action == "skipped" else "Snooze",
            taken_at=timezone.now() if action == "taken" else None,
            skipped_at=timezone.now() if action == "skipped" else None,
        )

        return Response(
            {
                "success": True,
                "reminder": ReminderPreviewSerializer(build_today_reminders(patient), many=True).data,
                "action": action,
            }
        )


class ReminderDetailAPIView(AuthenticatedAPIView):
    def get_object(self, pk, patient):
        return Reminder.objects.select_related(
            "schedule",
            "schedule__medicine",
            "schedule__medicine__prescription",
        ).get(pk=pk, schedule__medicine__prescription__patient=patient)

    def delete(self, request, pk):
        patient = self.get_patient(request)
        reminder = self.get_object(pk, patient)
        reminder.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
