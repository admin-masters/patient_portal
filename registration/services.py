# registration/services.py
from django.db import transaction
from django.utils.text import slugify
from django.core.files.storage import default_storage
from django.conf import settings
from datetime import datetime
import pathlib
import uuid

from accounts.models import Doctor
from clinics.models import Clinic, DoctorClinic
from core.models import Language

def _unique_portal_slug(base: str) -> str:
    base_slug = slugify(base)[:54]  # leave room for suffix
    slug = base_slug
    i = 1
    while Clinic.objects.filter(portal_slug=slug).exists():
        i += 1
        slug = f"{base_slug}-{i}"
    return slug

def _save_photo_and_get_url(request, file_obj) -> str | None:
    if not file_obj:
        return None
    # Save under media/doctors/photos/<uuid>.<ext>; build an absolute URL from MEDIA_URL
    ext = pathlib.Path(file_obj.name).suffix or ".jpg"
    name = f"doctors/photos/{uuid.uuid4().hex}{ext}"
    saved = default_storage.save(name, file_obj)
    media_url = getattr(settings, "MEDIA_URL", "/media/")
    return request.build_absolute_uri(f"{media_url}{saved}")

@transaction.atomic
def upsert_doctor_and_clinic_from_form(request, form, *, language_code="en"):
    """
    - If doctor exists (by IMC), update fields.
    - Else create new doctor.
    - Find or create clinic (by exact address + state + postal_code).
    - Link doctor to clinic via DoctorClinic (is_primary=True if created doctor).
    Returns: (doctor, clinic, is_new_doctor)
    """
    cd = form.cleaned_data
    imc = cd["imc_number"]

    # find or create doctor by IMC
    doctor = Doctor.objects.filter(imc_number=imc).first()
    is_new_doctor = doctor is None
    if doctor is None:
        doctor = Doctor(
            full_name=cd["full_name"],
            email=cd["email"],
            whatsapp_number=cd["whatsapp_number"],
            imc_number=imc,
            clinic_number=cd.get("clinic_number") or None,
            address=cd["address"],
            postal_code=cd["postal_code"],
            state=cd["state"],
        )
    else:
        # Update details on self‑registration
        doctor.full_name = cd["full_name"]
        doctor.email = cd["email"]
        doctor.whatsapp_number = cd["whatsapp_number"]
        doctor.clinic_number = cd.get("clinic_number") or doctor.clinic_number
        doctor.address = cd["address"]
        doctor.postal_code = cd["postal_code"]
        doctor.state = cd["state"]

    # optional photo upload → URL
    photo_url = _save_photo_and_get_url(request, cd.get("photo"))
    if photo_url:
        doctor.photo_url = photo_url
    doctor.save()

    # clinic find-or-create
    clinic = (Clinic.objects
              .filter(address=cd["address"], state=cd["state"], postal_code=cd["postal_code"])
              .first())
    if clinic is None:
        # default language must exist (seeded in Sprint 0)
        Language.objects.get(code=language_code)
        clinic = Clinic.objects.create(
            name=f"Clinic of Dr. {cd['full_name']}",
            address=cd["address"],
            postal_code=cd["postal_code"],
            state=cd["state"],
            phone_number=cd.get("clinic_number") or None,
            portal_slug=_unique_portal_slug(f"clinic-of-dr-{cd['full_name']}"),
            default_language_id=language_code,
        )

    DoctorClinic.objects.get_or_create(doctor=doctor, clinic=clinic, defaults={"is_primary": True})

    return doctor, clinic, is_new_doctor
