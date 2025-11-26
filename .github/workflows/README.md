# GitHub Actions Workflows

This directory contains GitHub Actions workflows for the GitHubMe project.

## Run Tests Workflow (`run_tests.yml`)

The `run_tests.yml` workflow runs tests for the Django project on every push and pull request to any branch.

### Workflow Features

- **Triggers**: Runs on every push and pull request to any branch
- **Environment**: Uses Ubuntu latest with Python 3.11
- **Services**: Spins up a Postgres 15 database for database tests
- **Package Management**: Uses `uv` for fast Python package installation
- **Test Execution**: Runs pytest on the Django project
- **Coverage**: Generates test coverage reports and uploads them to Codecov

### Environment Variables

The following environment variables are set for testing:

- `DJANGO_SETTINGS_MODULE`: Set to "config.settings.test"
- `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_TOKEN`: Set to test values for GitHub API tests
- `STRIPE_WEBHOOK_SECRET`, `STRIPE_SECRET_KEY`, `STRIPE_PUBLIC_KEY`: Set to test values for Stripe integration tests
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: Set to test values for AWS tests

### How It Works

1. The workflow checks out the repository
2. Sets up Python 3.11
3. Installs the UV package manager
4. Installs Python dependencies including dev dependencies
5. Sets up the test environment variables
6. Runs the tests with `pytest`
7. Generates a test coverage report
8. Uploads the coverage report to Codecov

### Customization

If you need to customize the workflow:

- To add more environment variables, add them to both the `Setup test environment` step and the `env` section of the `Run tests` step
- To change the database configuration, modify the `services` section
- To run specific tests, modify the pytest command in the `Run tests` step

### Troubleshooting

If tests are failing in CI but passing locally:

1. Check that all required environment variables are set
2. Verify that the tests are not depending on local filesystem structures
3. Make sure all dependencies are properly declared in pyproject.toml
4. Check for differences between your local database and the CI database
