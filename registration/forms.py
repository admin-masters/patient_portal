from django import forms
from geo.models import IndiaState

class DoctorSelfRegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=128)
    email = forms.EmailField()
    whatsapp_number = forms.RegexField(regex=r"^\\d{10}$", error_messages={"invalid": "Enter a 10-digit mobile number (no country code)."})
    imc_number = forms.CharField(max_length=32)
    clinic_number = forms.CharField(max_length=20, required=False)
    address = forms.CharField(widget=forms.Textarea)
    postal_code = forms.CharField(max_length=10)
    state = forms.ModelChoiceField(queryset=IndiaState.objects.none())
    photo = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["state"].queryset = IndiaState.objects.all().order_by("name")

    def clean_imc_number(self):
        return self.cleaned_data["imc_number"].strip().upper()

class FieldRepRegistrationForm(DoctorSelfRegistrationForm):
    fieldrep_number = forms.RegexField(
        regex=r"^\\d{10}$",
        error_messages={"invalid": "Enter a 10-digit Field Rep number (no country code)."},
        label="Field Rep Number"
    )
