"""
URL configuration for holly project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

import django_eventstream
from django.conf import settings
from django.contrib import admin, sitemaps
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path, reverse
from django.views import defaults as default_views
from ninja import NinjaAPI
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.routers.obtain import obtain_pair_router, obtain_token, refresh_token_sliding
from ninja_jwt.routers.verify import verify_token

from holly.github_ext.api.router import router as github_ext_router
from holly.github_ext.sitemaps import RepositoryDetailSitemap
from holly.holly.api.custom_auth_views import auth_router as custom_auth_router  # Import custom_auth_router
from holly.holly.api.views import router as holly_router
from holly.users.api.router import router as users_oauth_router  # Import users OAuth router

all_sitemaps = {"gitrepo": RepositoryDetailSitemap}

# Initialize the Django Ninja API
api = NinjaAPI(
    title="Holly API",
    version="1.0.0",
    description="API for Holly",
    docs_url="/docs",
    csrf=not settings.DEBUG,
    auth=JWTAuth(),
)

# Include our app routers
api.add_router("/holly", holly_router, tags=["Holly"])
api.add_router("/github", github_ext_router, tags=["GitHub"])
api.add_router("/auth", custom_auth_router, tags=["Authentication"])  # Add custom_auth_router
api.add_router("/users", users_oauth_router, tags=["Users"])  # Add users OAuth router
api.add_router("/token", tags=["Auth"], router=obtain_pair_router)

# Add EE-specific routers if available
try:
    from backend.config.urls_ee import setup_ee_urls
    setup_ee_urls(api)
except ImportError:
    pass  # EE not available


urlpatterns = [
    # Default JWT views
    path("_api/auth/login/", obtain_token, name="jwt-obtain-token"),
    path("_api/auth/refresh/", refresh_token_sliding, name="jwt-refresh-token"),
    path("_api/auth/verify/", verify_token, name="jwt-verify-token"),  # Optional
    # Note: Custom register and logout will be added via a Ninja router included in `api.urls`
    path("_accounts/social/", include("allauth.socialaccount.urls")),
    path("_accounts/", include("allauth.urls")),
    path("_django-admin/", admin.site.urls),
    path("_bg-tasks/", include("holly.background_tasks.urls")),
    path("_github-app/", include("holly.github_ext.urls")),  # GitHub App OAuth callbacks
    path("_users/", include("holly.users.urls", namespace="users")),  # User URLs
    path("_holly/", include("holly.holly.urls", namespace="holly")),  # Holly App URLs
    path("_api/", api.urls),  # Django Ninja API URLs
    re_path(r"^events/", include(django_eventstream.urls), {"channels": ["test"]}),
    re_path(r"sitemap.xml$", sitemap, {"sitemaps": all_sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns = [
        *urlpatterns,
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
            *urlpatterns,
        ]
