# GitHub App Integration

This document explains how to set up and use GitHub App integration with the githubme project.

## Why GitHub Apps?

GitHub Apps provide several advantages over traditional OAuth integrations:

1. **Fine-grained permissions**: GitHub Apps can request only the specific permissions they need.
2. **Repository-level installation**: Users can choose which repositories the app can access.
3. **Higher rate limits**: GitHub Apps have higher API rate limits than personal access tokens.
4. **Security**: GitHub Apps use short-lived tokens and don't require storing user credentials.
5. **Organization support**: GitHub Apps can be installed on organizations and accessed by multiple users.

## Setup Instructions

### 1. Create a GitHub App

1. Go to your GitHub profile settings or organization settings.
2. Select "Developer settings" > "GitHub Apps" > "New GitHub App".
3. Fill in the required information:

   - **Name**: A unique name for your app (e.g., "Githubme Private Repo Access")
   - **Homepage URL**: Your application's URL
   - **Callback URL**: `https://your-domain.com/_github-app/github-app-callback/`
   - **Request user authorization (OAuth) during installation**: Check this option
   - **Webhook**: Uncheck "Active" (unless you want to use webhooks)

4. Set the required permissions:

   - **Repository permissions**:
     - Contents: Read
     - Metadata: Read
   - **Organization permissions** (optional):
     - Members: Read

5. Set where the app can be installed: Account or Any account

6. Click "Create GitHub App".

7. On the next page, note your **App ID**.

8. Generate a private key by clicking "Generate a private key" and save the file.

### 2. Configure the Application

Add the following environment variables to your `.env.local` file:

```
# GitHub App Settings
GITHUB_APP_ID=your_github_app_id
GITHUB_APP_NAME=your_github_app_name
GITHUB_APP_PRIVATE_KEY_PATH=/path/to/your/private-key.pem
```

Make sure to use the actual values from your GitHub App. For the private key, include the entire key including the BEGIN and END lines.

### 3. Test Your Configuration

You can test your GitHub App configuration using the provided utility script:

```
cd /path/to/githubme
python scripts/test_github_app_setup.py
```

This script will verify:

- JWT token generation
- GitHub App API communication
- Installations discovery
- Installation token generation
- Repository access

### 4. Install the App

1. Log in to the githubme application
2. Connect your GitHub account (if not already connected)
3. Go to GitHub App Installations page (`/_github-app/installations/`)
4. Click "Install GitHub App"
5. Follow the GitHub installation process to select the repositories you want to grant access to
6. Once completed, you'll be redirected back to the application

## Using GitHub App Installations

Once you've installed the GitHub App, the application will automatically use it to access your repositories. The system will:

1. Try to use the GitHub App installation token first
2. Fall back to OAuth token if no GitHub App installation is available

You can manage your GitHub App installations by:

1. Going to your GitHub settings
2. Selecting "Applications" > "Installed GitHub Apps"
3. Finding your app in the list and clicking "Configure"

## Accessing Private Repositories

With GitHub App installed, you can now access private repositories in the following ways:

1. Browse the list of repositories (`/_github-app/repositories/`)
2. Use the repository analysis feature with any repository you've granted access to
3. Clone and explore private repositories you've allowed access to

## Troubleshooting

### Common Issues

1. **Installation not working**: Make sure your callback URL is correct and accessible
2. **Unable to access repositories**: Verify that you've selected the repositories during installation
3. **JWT generation errors**: Check that your private key is correctly formatted

### JWT Errors

If you receive JWT errors:

- Make sure the private key is properly formatted (includes BEGIN and END lines)
- Verify that the App ID is correct
- Check that the App installation is active

### API Rate Limit Issues

If you encounter API rate limit issues, you may need to:

- Reduce the frequency of requests
- Implement caching for repository data
- Use webhooks for real-time updates rather than polling

## Reference

- [GitHub Apps Documentation](https://docs.github.com/en/developers/apps/getting-started-with-apps/about-apps)
- [Creating a GitHub App](https://docs.github.com/en/developers/apps/building-github-apps/creating-a-github-app)
- [Installing GitHub Apps](https://docs.github.com/en/developers/apps/managing-github-apps/installing-github-apps)
