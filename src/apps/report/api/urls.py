from django.urls import path
from .views import ReportCreateView, ReportDetailView

urlpatterns = [
    path("", ReportCreateView.as_view(), name="report-create"),
    path("<uuid:report_id>/", ReportDetailView.as_view(), name="report-detail"),
]
