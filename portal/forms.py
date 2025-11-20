# portal/forms.py
from django import forms
from core.models import Language

class SearchForm(forms.Form):
    q = forms.CharField(max_length=200, required=False, label="Search term")
    language = forms.ModelChoiceField(
        queryset=Language.objects.filter(is_active=True).order_by("name"),
        required=False,
        empty_label="Any language",
        to_field_name="code",
        label="Language"
    )
