# registration/urls.py
from django.urls import path
from .views import SelfRegistrationView, SelfRegistrationSuccessView
from .views import FieldRepRegistrationView  # new


app_name = "registration"

urlpatterns = [
    path("r/<str:token>/", SelfRegistrationView.as_view(), name="self_register"),
    path("fr/<str:token>/", FieldRepRegistrationView.as_view(), name="fieldrep_register"),  # new
    path("r/success/<slug:slug>/", SelfRegistrationSuccessView.as_view(), name="success"),
]
