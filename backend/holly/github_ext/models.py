from allauth.socialaccount.models import SocialAccount
from django.db import models
from django.urls import reverse


# Persistence Layer: Django Model
class RepositoryDetail(models.Model):
    github_id = models.CharField(max_length=255, null=False, help_text="github repo id", unique=True)
    username = models.CharField(max_length=255, help_text="GitHub username/organization")
    repo = models.CharField(max_length=255, help_text="Repository name")
    commit_hash = models.CharField(max_length=40, blank=True)

    description = models.TextField(blank=True, default="")
    languages = models.JSONField(blank=True, default=dict)
    stargazers_count = models.IntegerField(default=0)
    watchers_count = models.IntegerField(default=0)
    forks_count = models.IntegerField(default=0)
    open_issues_count = models.IntegerField(default=0)
    subscribers_count = models.IntegerField(default=0)
    size = models.IntegerField(default=0)
    topics = models.JSONField(blank=True, default=list)

    private = models.BooleanField(default=True)

    file_tree = models.JSONField(blank=True, default=list)
    file_count = models.IntegerField(default=0)
    # New field to store token counts for files
    file_token_counts = models.JSONField(blank=True, default=dict)
    readme = models.TextField(blank=True)
    diagram = models.TextField(blank=True)
    explanation = models.TextField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("username", "repo")

    def __str__(self):
        return f"{self.username}/{self.repo}"

    def get_absolute_url(self):
        # Replace 'gitrepo_detail' with your actual view name
        # TODO: we may need to revisit where username is
        #  defined since it's currently the full repo url:
        #  https://github.com/Techarge/repo
        return reverse("home:analyse_repo", args=[self.username, self.repo])

    def get_total_token_count(self):
        """Return the total token count from all selected files"""
        return sum(self.file_token_counts.values()) if self.file_token_counts else 0


class GitHubAppInstallation(models.Model):
    """
    Model to track GitHub App installations linked to social accounts.
    """

    social_account = models.ForeignKey(SocialAccount, on_delete=models.CASCADE)
    installation_id = models.CharField(max_length=100)
    account_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=50, choices=[("user", "User"), ("organization", "Organization")])
    installed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("social_account", "installation_id")

    def __str__(self):
        return f"{self.account_name} - {self.installation_id}"
