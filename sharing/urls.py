# sharing/urls.py
from django.urls import path
from .views import ShareLinkView

app_name = "sharing"
urlpatterns = [
    path("s/<str:token>/", ShareLinkView.as_view(), name="resolve"),
]
