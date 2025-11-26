from unittest.mock import Mock, patch

import pytest

from holly.payments.models import SubscriptionPlan, SubscriptionPrice, SubscriptionStatusEnum, UserSubscription
from holly.payments.utils import timestamp_to_aware_datetime

TEST_PRODUCT_ID = "prod_RtPxatoz5m6KR7"
TEST_PRICE_ID = "price_1Qzd7tGZeaxULSqiTj8tiEcS"
TEST_SUBSCRIPTION_ID = "sub_1QzejYGZeaxULSqimzqKAsdS"
TEST_SUBSCRIPTION_START_DATE = timestamp_to_aware_datetime(1741268708)
TEST_SESSION_ID = "cs_test_1234567890"


@pytest.fixture
def mock_stripe_webhook():
    """Mock stripe.Webhook.construct_event to bypass signature verification"""
    with patch("stripe.Webhook.construct_event") as mock:
        yield mock


@pytest.fixture
def subscription_plan(db):
    """Fixture to create a subscription plan."""
    return SubscriptionPlan.objects.create(stripe_product_id=TEST_PRODUCT_ID, name="Test Plane", credits_per_month=100)


@pytest.fixture
def subscription_price(db, subscription_plan):
    """Fixture to create a subscription price."""
    return SubscriptionPrice.objects.create(
        plan=subscription_plan, stripe_price_id=TEST_PRICE_ID, price=1000, currency="usd", active=True
    )


@pytest.fixture
def user_subscription(db, customer, subscription_plan):
    """Fixture to create a user subscription."""
    return UserSubscription.objects.create(
        user=customer,
        plan=subscription_plan,
        stripe_subscription_id=TEST_SUBSCRIPTION_ID,
        status=SubscriptionStatusEnum.INCOMPLETE,
        start_date=TEST_SUBSCRIPTION_START_DATE,
    )


@pytest.fixture
def mock_stripe_client():
    """Create a mock Stripe client using `unittest.mock.Mock`."""
    stripe_mock = Mock()

    # Mock the `create_checkout_session` method to return a fake Stripe checkout session
    stripe_mock.create_checkout_session.return_value = {"id": TEST_SESSION_ID}

    # Mock the `cancel_subscription` method to return a simulated response
    stripe_mock.cancel_subscription.side_effect = lambda subscription_id, immediate: {
        "id": subscription_id,
        "status": "canceled" if immediate else "active",
        "current_period_end": 1700000000,  # Fake timestamp for scheduled cancellation
    }

    return stripe_mock
