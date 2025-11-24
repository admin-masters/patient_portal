# sharing/urls.py
from django.urls import path
from .views import ShareLinkView, PatientHomeView, PatientSubtopicView, PatientVideoView

app_name = "sharing"

urlpatterns = [
    # Token resolver (entry point from WhatsApp message)
    path("s/<str:token>/", ShareLinkView.as_view(), name="resolve"),

    # Patient browsing pages (keep ?t=<token> to continue tracking)
    path("p/<slug:slug>/<slug:lang>/", PatientHomeView.as_view(), name="patient_home"),
    path("p/<slug:slug>/<slug:lang>/subtopic/<slug:sub_slug>/", PatientSubtopicView.as_view(), name="patient_subtopic"),
    path("p/<slug:slug>/<slug:lang>/video/<slug:vid_slug>/", PatientVideoView.as_view(), name="patient_video"),
]
