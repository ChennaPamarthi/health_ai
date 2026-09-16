from django.contrib.auth.models import User as AuthUser

from health.models import User


class UserService:
    @staticmethod
    def get_patient_for_auth_user(auth_user):
        if not auth_user or not auth_user.is_authenticated:
            return None

        email = (getattr(auth_user, "email", "") or "").strip().lower()
        username = (getattr(auth_user, "username", "") or "").strip()
        full_name = (
            auth_user.get_full_name().strip()
            if hasattr(auth_user, "get_full_name")
            else ""
        )

        patient = None

        if email:
            patient = User.objects.filter(email__iexact=email).first()

        if patient is None and username:
            patient = User.objects.filter(email__iexact=username).first()

        if patient is None:
            fallback_email = email or f"{username or 'patient'}@local.health"
            patient = User.objects.create(
                full_name=full_name or username or "Patient",
                email=fallback_email,
                primary_email=fallback_email,
                primary_phone_number="",
                phone="",
                role="patient",
                gender="",
                address="",
                emergency_contact="",
            )
            return patient

        updates = []
        if full_name and patient.full_name != full_name:
            patient.full_name = full_name
            updates.append("full_name")
        if email and patient.email.lower() != email:
            patient.email = email
            updates.append("email")
        if email and getattr(patient, "primary_email", "") != email:
            patient.primary_email = email
            updates.append("primary_email")
        if patient.role != "patient":
            patient.role = "patient"
            updates.append("role")
        if updates:
            patient.save(update_fields=updates)

        return patient

    @staticmethod
    def ensure_auth_user_profile(auth_user):
        if not auth_user or not auth_user.is_authenticated:
            return None

        if not auth_user.email and auth_user.username:
            auth_user.email = f"{auth_user.username}@local.health"
            auth_user.save(update_fields=["email"])

        return UserService.get_patient_for_auth_user(auth_user)
