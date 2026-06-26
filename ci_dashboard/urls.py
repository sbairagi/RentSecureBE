"""
URL configuration for ci_dashboard app.
"""

from django.urls import path

from ci_dashboard import views

app_name = "ci_dashboard"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("run/", views.run_workflow, name="run"),
    path("rerun/<uuid:run_id>/", views.rerun_workflow, name="rerun"),
    path("history/", views.history, name="history"),
    path("workflows/", views.workflow_list, name="workflows"),
    path("logs/<uuid:run_id>/", views.logs, name="logs"),
    path("logs/<uuid:run_id>/sse/", views.sse_logs, name="sse_logs"),
    path("logs/<uuid:run_id>/download/", views.download_logs, name="download_logs"),
    path("logs/<uuid:run_id>/export-pdf/", views.export_pdf, name="export_pdf"),
    path("job/<uuid:job_run_id>/", views.job_detail, name="job_detail"),
    path("cancel/<uuid:run_id>/", views.cancel_workflow, name="cancel"),
    path("graph/<uuid:run_id>/", views.workflow_graph, name="graph"),
    path("graph/<uuid:run_id>/json/", views.workflow_graph_json, name="graph_json"),
]
