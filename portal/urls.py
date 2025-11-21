from django.urls import path
from .views import PortalLoginView, PortalLogoutView, PortalHomeView
from .views_share import ShareComposeView, ShareConfirmView, ajax_videos_for_subtopic, ajax_languages_for_video, ajax_suggest_titles

app_name = "portal"

urlpatterns = [
    path("portal/<slug:slug>/login/", PortalLoginView.as_view(), name="login"),
    path("portal/<slug:slug>/logout/", PortalLogoutView.as_view(), name="logout"),
    path("portal/<slug:slug>/", PortalHomeView.as_view(), name="home"),

    path("portal/<slug:slug>/share/", ShareComposeView.as_view(), name="share"),
    path("portal/<slug:slug>/share/confirm/<str:token>/", ShareConfirmView.as_view(), name="share_confirm"),

    path("portal/<slug:slug>/ajax/videos/", ajax_videos_for_subtopic, name="ajax_videos"),
    path("portal/<slug:slug>/ajax/video-langs/", ajax_languages_for_video, name="ajax_video_langs"),
    path("portal/<slug:slug>/ajax/suggest/", ajax_suggest_titles, name="ajax_suggest"),
]
