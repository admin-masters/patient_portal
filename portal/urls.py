# portal/urls.py
from django.urls import path
from .views import PortalLoginView, PortalLogoutView, PortalHomeView

app_name = "portal"

urlpatterns = [
    path("portal/<slug:slug>/login/", PortalLoginView.as_view(), name="login"),
    path("portal/<slug:slug>/logout/", PortalLogoutView.as_view(), name="logout"),
    path("portal/<slug:slug>/", PortalHomeView.as_view(), name="home"),
]
