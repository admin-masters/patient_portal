from django.urls import path
from .views import analytics_dashboard, export_csv

app_name = "analytics"

urlpatterns = [
    path("ops/analytics/", analytics_dashboard, name="dashboard"),
    path("ops/analytics/export/<str:kind>.csv", export_csv, name="export"),
]
