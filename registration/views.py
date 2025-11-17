# registration/views.py
from django.views.generic import FormView, TemplateView
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import Http404
from .models import RegistrationLink, DoctorRegistration
from .forms import DoctorSelfRegistrationForm
from .services import upsert_doctor_and_clinic_from_form

def _serialize_payload(form, doctor, clinic):
    """Return a JSON-serializable snapshot of submitted fields."""
    cd = dict(form.cleaned_data)

    # Replace IndiaState model with a primitive structure
    st = cd.get("state")
    cd["state"] = (
        {"id": st.id, "name": st.name, "iso_code": getattr(st, "iso_code", None)} if st else None
    )

    # Replace UploadedFile with just the filename (content is not stored)
    if "photo" in cd:
        photo = cd["photo"]
        cd["photo"] = getattr(photo, "name", None)

    # Include the resolved photo_url we saved (if any)
    cd["photo_url"] = getattr(doctor, "photo_url", None)

    return cd

class SelfRegistrationView(FormView):
    template_name = "registration/register.html"
    form_class = DoctorSelfRegistrationForm

    def dispatch(self, request, *args, **kwargs):
        self.link = get_object_or_404(RegistrationLink, token=kwargs.get("token"))
        if not self.link.is_self:
            raise Http404("Not a self-registration link.")
        if not self.link.is_valid_now:
            raise Http404("Registration link is inactive or expired.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["link"] = self.link
        return ctx

    def form_valid(self, form):
        # Create/Update doctor & clinic
        doctor, clinic, is_new = upsert_doctor_and_clinic_from_form(
            self.request, form, language_code="en"
        )

        # Count usage
        self.link.mark_used()

        # JSON-safe snapshot
        safe_payload = _serialize_payload(form, doctor, clinic)

        # Audit
        DoctorRegistration.objects.create(
            registration_link=self.link,
            doctor=doctor,
            clinic=clinic,
            is_new_doctor=is_new,
            payload_snapshot=safe_payload,
            result="success",
            ip=self.request.META.get("REMOTE_ADDR"),
            user_agent=self.request.META.get("HTTP_USER_AGENT"),
        )

        # Success redirect
        self.success_url = reverse("registration:success", kwargs={"slug": clinic.portal_slug})
        return super().form_valid(form)

class SelfRegistrationSuccessView(TemplateView):
    template_name = "registration/success.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        slug = kwargs.get("slug")
        ctx["portal_url"] = self.request.build_absolute_uri(f"/portal/{slug}/")
        return ctx
