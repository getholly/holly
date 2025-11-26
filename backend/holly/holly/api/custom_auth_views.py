from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import IntegrityError
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.security import HttpBearer
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.tokens import RefreshToken as NinjaJWTRefreshToken  # Alias to avoid clash if any

from holly.utils.email_utils import send_password_reset_email

# Using Django's default User model
User = get_user_model()

auth_router = Router()


# --- Schemas ---
class UserSignupSchema(Schema):
    email: str
    password: str


class UserResponseSchema(Schema):
    id: int
    email: str
    is_active: bool


class MessageSchema(Schema):
    message: str


class PasswordResetSuccessSchema(Schema):
    message: str
    email: str


class RefreshTokenSchema(Schema):
    refresh_token: str


class PasswordResetRequestSchema(Schema):
    email: str


class PasswordResetConfirmSchema(Schema):
    uidb64: str
    token: str  # This is the token from default_token_generator, sometimes called otp by frontend
    new_password: str


class UserDetailSchema(Schema):
    email: str
    avatar_url: str | None = None


# --- Signup Endpoint ---
@auth_router.post("/register/", auth=None, response={201: UserResponseSchema, 400: MessageSchema, 409: MessageSchema})
def register(request, payload: UserSignupSchema):
    """
    Register a new user.
    """
    if not payload.email or not payload.password:
        raise HttpError(400, "Email and password are required.")

    try:
        # Using email as username. Ensure your User model is set up for this if USERNAME_FIELD = 'email'
        # If User model uses 'username' and you want to use email for login,
        # you might need to set username = email.
        user = User.objects.create_user(
            email=payload.email,
            password=payload.password,
            is_active=True,  # Or False if email verification is a separate step before login
        )
        return 201, UserResponseSchema(id=user.id, email=user.email, is_active=user.is_active)
    except IntegrityError:  # This catches if username (email) already exists
        return 409, {"message": "User with this email already exists."}
    except Exception:
        # Log the exception e
        return 400, {"message": "Could not create user."}


# --- Logout Endpoint (Token Blacklisting) ---
# This endpoint uses JWTAuth for protection, meaning a valid access token must be provided.
class JWTAuthForLogout(HttpBearer):  # Use HttpBearer to define it's a JWT auth
    def authenticate(self, request, token):
        # This is a placeholder. In a real scenario, you'd integrate with how JWTAuth validates tokens.
        # For django-ninja-jwt, JWTAuth() class itself handles this when passed to auth_router.post(auth=JWTAuth())
        # This custom class isn't strictly necessary if JWTAuth() is used directly in the decorator.
        # However, if you need custom logic for specific auth type, this is how you might start.
        # For now, we rely on JWTAuth() in the decorator.
        pass


@auth_router.post("/logout/", response={200: MessageSchema, 400: MessageSchema}, auth=JWTAuth())
def logout(request, payload: RefreshTokenSchema):
    """
    Blacklist a refresh token to log the user out.
    The client should delete its local tokens after calling this.
    """
    if not payload.refresh_token:
        raise HttpError(400, "Refresh token is required.")
    try:
        token = NinjaJWTRefreshToken(payload.refresh_token)
        token.blacklist()
        return 200, {"message": "Successfully logged out. Refresh token blacklisted."}
    except Exception as e:
        # Log the exception e
        # This can happen if the token is already blacklisted, malformed, or expired.
        raise HttpError(400, f"Invalid token or could not blacklist: {e!s}")


# --- Password Reset Request Endpoint ---
@auth_router.post(
    "/password-reset/request/", auth=None, response={200: MessageSchema, 400: MessageSchema, 404: MessageSchema}
)
def password_reset_request(request, payload: PasswordResetRequestSchema):
    try:
        user = User.objects.get(email=payload.email)
    except User.DoesNotExist:
        # Important: Do not reveal whether the user exists or not to prevent enumeration attacks.
        # Always return a generic success message.
        # Log this attempt for monitoring if desired.
        # print(f"Password reset attempt for non-existent email: {payload.email}")
        return 200, {"message": "If an account with this email exists, a password reset link has been sent."}

    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

    reset_link = f"{settings.FRONTEND_URL}/reset-password-confirm?uidb64={uidb64}&token={token}"

    try:
        # Use the email utility function for better templating
        email_sent = send_password_reset_email(user.email, reset_link)
        if email_sent:
            return 200, {"message": "If an account with this email exists, a password reset link has been sent."}
        # Log the failure internally but still return success message for security
        return 200, {
            "message": "An error occurred while trying to send the password reset email. Please try again later."
        }
    except Exception:
        # Log the exception: print(f"Email sending failed: {e}")
        # Even if email sending fails, return a generic message to avoid leaking info.
        # For critical failures, you might have different internal alerting.
        return 200, {
            "message": "An error occurred while trying to send the password reset email. Please try again later."
        }


# --- Password Reset Confirm Endpoint ---
@auth_router.post("/password-reset/confirm/", auth=None, response={200: PasswordResetSuccessSchema, 400: MessageSchema})
def password_reset_confirm(request, payload: PasswordResetConfirmSchema):
    try:
        uid = force_str(urlsafe_base64_decode(payload.uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        # Log this error: print(f"Password reset confirm error - UID/User issue: {e}")
        user = None

    if user is not None and default_token_generator.check_token(user, payload.token):
        if not payload.new_password or len(payload.new_password) < 8:  # Basic validation
            raise HttpError(400, "Password must be at least 8 characters long.")
        user.set_password(payload.new_password)
        user.save()
        return 200, {"message": "Password has been reset successfully.", "email": user.email}
    # Log this: print(f"Password reset confirm failed for user {uid} with token {payload.token}")
    raise HttpError(400, "Invalid token or user ID. The reset link may have expired or been used already.")


# Note: The `auth_router` needs to be included in the main API router.
# e.g., in config/urls.py or where your main NinjaAPI instance is:
# from holly.holly.api.custom_auth_views import auth_router as custom_auth_api
# main_api.add_router("/auth", custom_auth_api, tags=["Authentication"])


# --- User Detail Endpoint ---
@auth_router.get("/me/", response=UserDetailSchema, auth=JWTAuth())
def get_user_details(request):
    """
    Retrieve details for the authenticated user.
    """
    user = request.auth  # User object is attached by JWTAuth
    if not user:
        raise HttpError(401, "Authentication credentials were not provided or were invalid.")

    # Placeholder for avatar_url. In a real application, you'd fetch this from the user's profile.
    # For example, if you have a UserProfile model linked to the User:
    # avatar_url = user.userprofile.avatar_url if hasattr(user, 'userprofile') else None
    avatar_url = None

    return UserDetailSchema(email=user.email, avatar_url=avatar_url)
