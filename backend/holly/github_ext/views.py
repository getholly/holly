import time

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from loguru import logger

from holly.github_ext.github_apps import GitHubAppIntegration

# Removed: list_repositories - template-based view, functionality moved to SPA


@login_required
def install_github_app(request):
    """
    Redirect to GitHub App installation page.
    """
    # Check if user has a GitHub social account
    if not SocialAccount.objects.filter(user=request.user, provider="github").exists():
        return HttpResponseRedirect(reverse("socialaccount_connections"))

    # Generate state parameter to prevent CSRF
    state = str(int(time.time()))
    request.session["github_app_install_state"] = state

    # Build the installation URL
    github_app = GitHubAppIntegration()
    install_url = github_app.get_installation_url(state)

    return HttpResponseRedirect(install_url)


@csrf_exempt
@login_required
def github_app_callback(request):
    """
    Handle the GitHub App installation callback.
    """
    installation_id = request.GET.get("installation_id")
    state = request.GET.get("state")

    logger.info(f"github app callback: {installation_id=} - {state=}/{request.session.get('github_app_install_state')}")

    # Verify state to prevent CSRF
    if not state or state != request.session.get("github_app_install_state"):
        return HttpResponse("Invalid state parameter", status=400)

    if not installation_id:
        return HttpResponse("No installation ID provided", status=400)

    # Get the user's primary GitHub account
    from holly.users.github_models import GitHubAccountInstallation

    primary_account = request.user.get_primary_github_account()
    if not primary_account:
        return HttpResponse("GitHub account not connected", status=400)

    # Get installation info using GitHub App credentials
    github_app = GitHubAppIntegration()
    installation_info = github_app.get_installation_info(installation_id)

    # Save the installation even if we couldn't fetch full info
    if installation_info:
        account_name = installation_info.get("account", {}).get("login", "")
        account_type = installation_info.get("account", {}).get("type", "").lower()
        permissions = installation_info.get("permissions", {})
        repository_selection = installation_info.get("repository_selection", "selected")
    else:
        # Fallback to minimal data
        account_name = primary_account.github_login
        account_type = "user"
        permissions = {}
        repository_selection = "selected"

    GitHubAccountInstallation.objects.update_or_create(
        user_github_account=primary_account,
        installation_id=installation_id,
        defaults={
            "account_name": account_name,
            "account_type": account_type,
            "permissions": permissions,
            "repository_selection": repository_selection,
        },
    )

    # Success - redirect to frontend SPA with success indicator
    # Frontend should handle showing success message
    return HttpResponseRedirect("/")


# Removed: github_app_success - template-based view, functionality moved to SPA
# Removed: list_installations - template-based view, functionality moved to SPA


@login_required
def get_repository_token(request, owner, repo):
    """
    Get an installation token for accessing a repository.
    """
    try:
        social_account = SocialAccount.objects.get(user=request.user, provider="github")
        installations = GitHubAppInstallation.objects.filter(social_account=social_account)

        if not installations.exists():
            return JsonResponse({"error": "No GitHub App installations found"}, status=400)

        # Find an installation that has access to the requested repository
        # For simplicity, we'll just use the first installation
        # In a real-world scenario, we would check which installation has access to the specific repo
        installation = installations.first()

        github_app = GitHubAppIntegration()
        token = github_app.get_installation_token(installation.installation_id)

        if not token:
            return JsonResponse({"error": "Failed to get installation token"}, status=500)

        # Return the token - in a real app, you might not want to expose this directly
        # Instead, you might use it to perform server-side actions
        return JsonResponse(
            {
                "success": True,
                "token": token,
                "token_type": "installation",
                "installation_id": installation.installation_id,
            }
        )

    except SocialAccount.DoesNotExist:
        return JsonResponse({"error": "GitHub account not connected"}, status=400)
    except Exception as e:  # noqa: BLE001
        return JsonResponse({"error": str(e)}, status=500)
