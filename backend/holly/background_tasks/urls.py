"""
URL patterns for background tasks.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("task/<str:task_id>/", views.task_status, name="task_status"),
]
