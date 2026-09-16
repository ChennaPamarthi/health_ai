from django.contrib import admin

from .models import (
    Appointment,
    Caregiver,
    HealthJournal,
    MedicalDocument,
    MedicalReport,
    MedicineLog,
    MedicineSchedule,
    Prescription,
    PrescriptionMedicine,
    NotificationEvent,
    Reminder,
    User,
)


admin.site.register(User)
admin.site.register(Caregiver)
admin.site.register(MedicalDocument)
admin.site.register(Prescription)
admin.site.register(PrescriptionMedicine)
admin.site.register(MedicineSchedule)
admin.site.register(MedicineLog)
admin.site.register(Appointment)
admin.site.register(HealthJournal)
admin.site.register(Reminder)
admin.site.register(MedicalReport)
admin.site.register(NotificationEvent)
