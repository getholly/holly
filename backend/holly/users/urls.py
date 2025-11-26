from django.urls import path

from .views import mark_tour_completed

app_name = "users"
urlpatterns = [
    path("tour/complete/", mark_tour_completed, name="mark_tour_completed"),
]
