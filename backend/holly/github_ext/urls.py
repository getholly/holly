from django.urls import path

from holly.github_ext import views as github_apps

urlpatterns = [
    path("install-github-app/", github_apps.install_github_app, name="install_github_app"),
    path("github-app-callback/", github_apps.github_app_callback, name="github_app_callback"),
    # Removed: github-app-success/ - template-based view
    # Removed: installations/ - template-based view
    # Removed: repositories/ - template-based view
    path("repository-token/<str:owner>/<str:repo>/", github_apps.get_repository_token, name="get_repository_token"),
]
