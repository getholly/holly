"""
URL patterns for the Holly app.
"""

from django.urls import path

from . import views
from .api.context_view import get_dev_context

# Removed: from .api.auth_views import login_view, logout_view

app_name = "holly"

urlpatterns = [
    # API endpoints
    path("api/credentials/", views.get_holly_credentials, name="credentials"),
    path("api/submit/<int:llm_id>/", views.submit_to_llm, name="submit_to_llm"),
    # Development API endpoints
    path("api/dev-context/", get_dev_context, name="dev_context"),
    # Removed: path("api/login/", login_view, name="login"),
    # Removed: path("api/logout/", logout_view, name="logout"),
    # View endpoints - should be done in the main view ..
    # path("<str:username>/<str:repo>/", views.HollyView.as_view(), name="holly_view"),
    # Removed: path("editor/", views.HollyView.as_view(), name="holly_view"),
]
