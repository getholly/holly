# Generated migration to backfill GitHubAccountInstallation from old GitHubAppInstallation

from django.db import migrations


def migrate_installations_forward(apps, schema_editor):
    """
    Migrate installations from old GitHubAppInstallation (linked to SocialAccount)
    to new GitHubAccountInstallation (linked to UserGitHubAccount).
    """
    GitHubAppInstallation = apps.get_model("github_ext", "GitHubAppInstallation")
    GitHubAccountInstallation = apps.get_model("users", "GitHubAccountInstallation")
    UserGitHubAccount = apps.get_model("users", "UserGitHubAccount")

    migrated_count = 0
    skipped_count = 0

    for old_install in GitHubAppInstallation.objects.all():
        try:
            # Find the UserGitHubAccount for this social_account
            user_github_account = UserGitHubAccount.objects.get(
                social_account=old_install.social_account
            )

            # Create in new model if it doesn't exist
            _, created = GitHubAccountInstallation.objects.get_or_create(
                user_github_account=user_github_account,
                installation_id=old_install.installation_id,
                defaults={
                    "account_name": old_install.account_name,
                    "account_type": old_install.account_type,
                    "permissions": {},  # Old model doesn't have this field
                    "repository_selection": "selected",  # Default assumption
                },
            )
            if created:
                migrated_count += 1

        except UserGitHubAccount.DoesNotExist:
            # Skip if no UserGitHubAccount exists for this social_account
            # This can happen if the OAuth account was created before the new model migration
            skipped_count += 1
            continue

    print(f"Migrated {migrated_count} installations, skipped {skipped_count} (no matching UserGitHubAccount)")


def migrate_installations_backward(apps, schema_editor):
    """
    Backward migration: copy back from new model to old model if needed.
    """
    GitHubAppInstallation = apps.get_model("github_ext", "GitHubAppInstallation")
    GitHubAccountInstallation = apps.get_model("users", "GitHubAccountInstallation")

    for new_install in GitHubAccountInstallation.objects.all():
        social_account = new_install.user_github_account.social_account

        GitHubAppInstallation.objects.get_or_create(
            social_account=social_account,
            installation_id=new_install.installation_id,
            defaults={
                "account_name": new_install.account_name,
                "account_type": new_install.account_type,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_usergithubaccount_githubaccountinstallation"),
        ("github_ext", "__first__"),  # Depends on github_ext app existing
    ]

    operations = [
        migrations.RunPython(migrate_installations_forward, migrate_installations_backward),
    ]

