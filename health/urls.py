from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    # Frontend pages
    path("", views.dashboard, name="dashboard"),
    path("upload/", views.upload_page, name="upload"),
    path("prescriptions/", views.prescriptions_page, name="prescriptions"),
    path("medicines/", views.medicines_page, name="medicines"),
    path("reminders/", views.reminders_page, name="reminders"),
    path("caregivers/", views.caregivers_page, name="caregivers"),
    path("appointments/", views.appointments_page, name="appointments"),
    path("reports/", views.reports_page, name="reports"),
    path("analytics/", views.analytics_page, name="analytics"),
    path("settings/", views.settings_page, name="settings"),

    # API endpoints
    path("api/documents/upload/", views.MedicalDocumentUploadView.as_view(), name="api-document-upload"),
    path("api/documents/", views.MedicalDocumentAPIView.as_view(), name="api-documents"),
    path("api/documents/<int:pk>/", views.MedicalDocumentAPIView.as_view(), name="api-document-detail"),
    path("api/prescriptions/manual/", views.ManualPrescriptionEntryAPIView.as_view(), name="api-manual-prescription"),
    path("api/appointments/manual/", views.ManualAppointmentEntryAPIView.as_view(), name="api-manual-appointment"),
    path("api/reports/manual/", views.ManualReportEntryAPIView.as_view(), name="api-manual-report"),
    path("api/medicines/", views.MedicinesAPIView.as_view(), name="api-medicines"),
    path("api/medicines/<int:pk>/", views.MedicineDetailAPIView.as_view(), name="api-medicine-detail"),
    path("api/schedules/<int:pk>/", views.MedicineScheduleDetailAPIView.as_view(), name="api-schedule-detail"),
    path("api/medicine-log/", views.MedicineLogAPIView.as_view(), name="api-medicine-log"),
    path("api/reminders/today/", views.RemindersTodayAPIView.as_view(), name="api-reminders-today"),
    path("api/reminders/respond/", views.ReminderResponseAPIView.as_view(), name="api-reminder-response"),
    path("api/reminders/<int:pk>/", views.ReminderDetailAPIView.as_view(), name="api-reminder-detail"),
    path("api/prescriptions/", views.PrescriptionsAPIView.as_view(), name="api-prescriptions"),
    path("api/prescriptions/<int:pk>/", views.PrescriptionDetailAPIView.as_view(), name="api-prescription-detail"),
    path("api/appointments/", views.AppointmentsAPIView.as_view(), name="api-appointments"),
    path("api/appointments/<int:pk>/", views.AppointmentDetailAPIView.as_view(), name="api-appointment-detail"),
    path("api/reports/", views.ReportsAPIView.as_view(), name="api-reports"),
    path("api/reports/<int:pk>/", views.ReportDetailAPIView.as_view(), name="api-report-detail"),
    path("api/caregivers/", views.CaregiversAPIView.as_view(), name="api-caregivers"),
    path("api/caregivers/<int:pk>/", views.CaregiverDetailAPIView.as_view(), name="api-caregiver-detail"),
    path("api/notifications/", views.NotificationHistoryAPIView.as_view(), name="api-notifications"),
    path("api/dashboard/summary/", views.DashboardSummaryAPIView.as_view(), name="api-dashboard-summary"),
    path("api/analytics/summary/", views.AnalyticsSummaryAPIView.as_view(), name="api-analytics-summary"),
]
