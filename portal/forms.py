# portal/forms_share.py
from django import forms
from django.core.validators import RegexValidator
from core.models import Language
from content.models import Subtopic, Video, VideoI18n
from django import forms
from core.models import Language

class ShareForm(forms.Form):
    SHARE_CHOICES = [("video", "Single video"), ("subtopic", "Subtopic")]

    # Common
    patient_msisdn = forms.RegexField(
        regex=r"^\d{10}$",
        error_messages={"invalid": "Enter a 10-digit WhatsApp number (no country code)."},
        label="Patient WhatsApp number"
    )
    language = forms.ModelChoiceField(
        queryset=Language.objects.filter(is_active=True).order_by("name"),
        to_field_name="code",
        empty_label=None
    )
    # Selection
    share_kind = forms.ChoiceField(choices=SHARE_CHOICES, widget=forms.RadioSelect, initial="video")
    subtopic = forms.ModelChoiceField(queryset=Subtopic.objects.filter(is_active=True).select_related("therapy_area").order_by("therapy_area__name", "slug"),
                                      required=False)
    video = forms.ModelChoiceField(queryset=Video.objects.none(), required=False)

    # Typeahead (optional)
    q = forms.CharField(max_length=200, required=False, label="Type to search titles/keywords")

    def clean(self):
        data = super().clean()
        kind = data.get("share_kind")
        if kind == "video":
            if not data.get("video"):
                self.add_error("video", "Choose a video.")
        elif kind == "subtopic":
            if not data.get("subtopic"):
                self.add_error("subtopic", "Choose a subtopic.")
        # language must be set (always)
        if not data.get("language"):
            self.add_error("language", "Choose a language.")
        return data


class SearchForm(forms.Form):
    q = forms.CharField(max_length=200, required=False, label="Search term")
    language = forms.ModelChoiceField(
        queryset=Language.objects.filter(is_active=True).order_by("name"),
        required=False,
        empty_label="Any language",
        to_field_name="code",
        label="Language"
    )
