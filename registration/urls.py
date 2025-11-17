# registration/urls.py
from django.urls import path
from .views import SelfRegistrationView, SelfRegistrationSuccessView

app_name = "registration"

urlpatterns = [
    path("r/<str:token>/", SelfRegistrationView.as_view(), name="self_register"),
    path("r/success/<slug:slug>/", SelfRegistrationSuccessView.as_view(), name="success"),
]
