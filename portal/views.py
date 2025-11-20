# portal/views.py
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden
from django.urls import reverse, reverse_lazy

from clinics.models import Clinic
from .models import ClinicMember
from .forms import SearchForm
from .services import search_catalog, active_campaign_banners_for_clinic, language_choices

class PortalLoginView(LoginView):
    template_name = "portal/login.html"

    def get_success_url(self):
        slug = self.kwargs.get("slug")
        return reverse("portal:home", kwargs={"slug": slug})

class PortalLogoutView(LogoutView):
    next_page = None

    def get_next_page(self):
        slug = self.kwargs.get("slug")
        return reverse("portal:login", kwargs={"slug": slug})

class ClinicContextMixin:
    """
    Loads clinic by slug and verifies membership for the current user.
    """
    def dispatch(self, request, *args, **kwargs):
        self.clinic = get_object_or_404(Clinic, portal_slug=kwargs.get("slug"))
        return super().dispatch(request, *args, **kwargs)

    def user_is_member(self):
        if not self.request.user.is_authenticated:
            return False
        return ClinicMember.objects.filter(
            user=self.request.user, clinic=self.clinic, is_active=True
        ).exists()

class PortalHomeView(LoginRequiredMixin, ClinicContextMixin, FormView):
    template_name = "portal/home.html"
    form_class = SearchForm

    def get(self, request, *args, **kwargs):
        # Prefill language with clinic default language code, if not present
        self.clinic = get_object_or_404(Clinic, portal_slug=kwargs.get("slug"))
        if not self.user_is_member():
            return HttpResponseForbidden("You do not have access to this clinic's portal.")
        return super().get(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        lang_code = self.request.GET.get("language")
        if not lang_code:
            initial["language"] = self.clinic.default_language_id  # stored as code
        initial["q"] = self.request.GET.get("q") or ""
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["clinic"] = self.clinic
        ctx["banners"] = active_campaign_banners_for_clinic(
            clinic=self.clinic,
            lang_code=self.request.GET.get("language") or self.clinic.default_language_id
        )
        return ctx

    def form_valid(self, form):
        q = form.cleaned_data.get("q") or ""
        lang = None
        language_obj = form.cleaned_data.get("language")
        if language_obj:
            lang = language_obj.code

        localized, english = ([], [])
        if q.strip():
            localized, english = search_catalog(q.strip(), lang_code=lang, limit=50)

        ctx = self.get_context_data(form=form)
        ctx["results_localized"] = localized
        ctx["results_english"] = english
        ctx["query"] = q
        ctx["selected_language"] = lang
        return self.render_to_response(ctx)
