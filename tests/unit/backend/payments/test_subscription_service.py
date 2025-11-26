import pytest
from django.contrib.auth import get_user_model

from holly.payments.models import SubscriptionStatusEnum, UserSubscription
from holly.payments.services import (
    SubscriptionAlreadyActiveError,
    SubscriptionNotFoundError,
    SubscriptionService,
)
from holly.payments.tests.conftest import TEST_SESSION_ID, TEST_SUBSCRIPTION_ID

User = get_user_model()


@pytest.fixture
def subscription_service(mock_stripe_client):
    """Create an instance of SubscriptionService with the mock Stripe client."""
    return SubscriptionService(stripe_client=mock_stripe_client)


# ---------- Test Subscription Checkout Session ----------


def test_create_checkout_session(db, customer, subscription_plan, subscription_price, subscription_service):
    """Test creating a new Stripe Checkout session."""
    checkout_url = subscription_service.create_checkout_session(
        customer, subscription_price, success_url="https://example.com/success", cancel_url="https://example.com/cancel"
    )

    assert checkout_url == TEST_SESSION_ID


def test_create_checkout_session_already_active(db, customer, subscription_plan, subscription_service):
    """Test error when creating a checkout session while already subscribed."""
    UserSubscription.objects.create(user=customer, plan=subscription_plan, status=SubscriptionStatusEnum.ACTIVE)

    with pytest.raises(SubscriptionAlreadyActiveError):
        subscription_service.create_checkout_session(
            customer,
            subscription_plan,
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )


# ---------- Test Subscription Activation via Webhook ----------


def test_create_subscription(customer, subscription_plan, subscription_service):
    """Test activating a subscription when Stripe webhook is received."""
    subscription_service.webhook_create_subscription(
        customer, subscription_plan, TEST_SUBSCRIPTION_ID, status="active", start_date=1600000000
    )

    subscription = UserSubscription.objects.get(user=customer)
    assert subscription.stripe_subscription_id == TEST_SUBSCRIPTION_ID
    assert subscription.is_active is True


# ---------- Test Subscription Cancellation ----------


def test_cancel_subscription_immediately(customer, subscription_plan, subscription_service):
    """Test immediate cancellation of a subscription."""
    UserSubscription.objects.create(
        user=customer,
        plan=subscription_plan,
        status=SubscriptionStatusEnum.ACTIVE,
        stripe_subscription_id=TEST_SUBSCRIPTION_ID,
    )

    subscription_service.cancel_user_subscription_immediately(customer)

    UserSubscription.objects.get(user=customer)


def test_cancel_subscription_renewal(customer, subscription_plan, subscription_service):
    """Test scheduling cancellation at the end of the billing cycle."""
    UserSubscription.objects.create(
        user=customer,
        plan=subscription_plan,
        status=SubscriptionStatusEnum.ACTIVE,
        stripe_subscription_id="sub_mock_123",
    )

    subscription_service.cancel_user_subscription_renewal(customer)

    UserSubscription.objects.get(user=customer)


def test_cancel_subscription_not_found(customer, subscription_service):
    """Test error when canceling a subscription that doesn't exist."""
    with pytest.raises(SubscriptionNotFoundError):
        subscription_service.cancel_user_subscription_immediately(customer)
