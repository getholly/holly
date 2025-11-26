# Email System

This documentation describes the email system implementation for the GithubMe application.

## Overview

The GithubMe application uses Django with the `django-anymail` package to send emails through the Postmark service. This provides reliable email delivery with tracking capabilities.

## Configuration

### Settings

Email settings are defined in the following files:

- `config/settings/email.py` - Base email settings
- `config/settings/local.py` - Development settings, uses console backend by default
- `config/settings/production.py` - Production settings, uses Postmark backend
- `config/settings/test.py` - Test settings, uses locmem backend

### Environment Variables

The following environment variables should be set in your `.env.local` file for development or in your production environment:

```
POSTMARK_SERVER_TOKEN=your_postmark_server_token
POSTMARK_INBOUND_SECRET=your_postmark_inbound_secret
```

## Email Templates

Email templates are stored in the `githubme/templates/emails/` directory. Each email template requires:

- A plain text version (`template_name.txt`)
- An HTML version (`template_name.html`)

Available templates:

- `welcome.txt/html` - Sent to new users
- `password_reset.txt/html` - Sent for password reset requests

## Utility Functions

The `githubme/utils/email_utils.py` module provides the following functions:

### `send_email()`

Generic email sending function with support for:

- HTML and plain text content
- Multiple recipients (To, CC, BCC)
- Email attachments
- Email tags for tracking
- Custom headers
- Metadata

### Helper Functions

- `send_welcome_email(user_email, username)` - Sends welcome email to new users
- `send_password_reset_email(user_email, reset_url)` - Sends password reset emails

## Example Usage

```python
from holly.utils.email_utils import send_welcome_email, send_password_reset_email

# Send welcome email
send_welcome_email(user_email="user@example.com", username="John Doe")

# Send password reset email
send_password_reset_email(
    user_email="user@example.com",
    reset_url="https://github.me.uk/reset-password/token123"
)
```

See `githubme/utils/email_example.py` for a complete example.

## Running Tests

Tests for the email functionality can be run with:

```bash
python manage.py test holly.utils.tests
```

## Troubleshooting

### Local Development

During local development, emails are sent to the console by default unless you set `POSTMARK_SERVER_TOKEN` in your environment.

### Postmark API Issues

If emails are not being sent correctly in production:

1. Check that `POSTMARK_SERVER_TOKEN` is set correctly
2. Verify Postmark account status
3. Check server logs for any error messages
4. Verify email template existence and format

## Security Considerations

- Email templates should not contain sensitive information
- Password reset links should expire and be secure
- User email addresses should be treated as sensitive information
