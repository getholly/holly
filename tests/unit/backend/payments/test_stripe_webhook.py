import json
from pathlib import Path
from unittest.mock import patch

import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse

from holly.payments.models import SubscriptionPrice, UserSubscription
from holly.payments.services import SubscriptionService
from holly.payments.stripe_webhook_handling import StripeWebhookError
from holly.payments.tests.conftest import TEST_SUBSCRIPTION_ID
from holly.payments.utils import timestamp_to_aware_datetime

pytestmark = pytest.mark.django_db

# Constants
WEBHOOK_SECRET = settings.STRIPE_WEBHOOK_SECRET
WEBHOOK_URL = reverse("payments:stripe_webhook")


@pytest.fixture
def load_event_data():
    """Fixture to load Stripe event data from JSON files"""

    def _load(event_name):
        with Path(f"./holly/payments/tests/stripe_webhook_data/{event_name}.json").open() as f:
            return json.load(f)

    return _load


@pytest.fixture
def stripe_client_mock():
    """Mock StripeClient to prevent real API calls."""
    with patch("holly.payments.external_services.stripe_client.StripeClient") as mock:
        yield mock


@pytest.fixture
def subscription_service(stripe_client_mock):
    """Create a real SubscriptionService with a mocked Stripe client."""
    return SubscriptionService(stripe_client_mock)


@pytest.mark.parametrize(
    "event_name",
    [
        "checkout_session_completed",
        "checkout_session_async_payment_succeeded",
        "checkout_session_async_payment_failed",
        "invoice_payment_succeeded",
        "invoice_payment_failed",
        "plan_created",
        "plan_updated",
    ],
)
def test_valid_webhook_events(client: Client, load_event_data, mock_stripe_webhook, event_name):
    """Test valid Stripe webhook events"""
    event_data = load_event_data(event_name)
    mock_stripe_webhook.return_value = event_data

    response = client.post(
        WEBHOOK_URL,
        data=json.dumps(event_data),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="valid_signature",
    )

    assert response.status_code == 200
    mock_stripe_webhook.assert_called_once()


def test_price_created_webhook(client: Client, load_event_data, mock_stripe_webhook, subscription_plan):
    """Test handling of Stripe `price.created` webhook event."""
    event_data = load_event_data("price_created")
    mock_stripe_webhook.return_value = event_data

    response = client.post(
        WEBHOOK_URL,
        data=json.dumps(event_data),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="valid_signature",
    )

    assert response.status_code == 200
    mock_stripe_webhook.assert_called_once()

    # Verify price was created in the database
    price = SubscriptionPrice.objects.get(stripe_price_id=event_data["data"]["object"]["id"])
    assert price.plan == subscription_plan
    assert price.price == event_data["data"]["object"]["unit_amount"]
    assert price.currency == event_data["data"]["object"]["currency"]
    assert price.active == event_data["data"]["object"]["active"]


def test_price_created_without_plan(client: Client, load_event_data, mock_stripe_webhook):
    """Test handling of `price.created` when no matching SubscriptionPlan exists."""
    event_data = load_event_data("price_created")
    mock_stripe_webhook.return_value = event_data
    with pytest.raises(StripeWebhookError):
        client.post(
            WEBHOOK_URL,
            data=json.dumps(event_data),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="valid_signature",
        )

    # Ensure price was NOT created in the database
    assert not SubscriptionPrice.objects.filter(stripe_price_id=event_data["data"]["object"]["id"]).exists()


def test_price_updated_webhook(client: Client, load_event_data, mock_stripe_webhook, subscription_price):
    """Test handling of Stripe `price.updated` webhook event."""
    event_data = load_event_data("price_updated")
    mock_stripe_webhook.return_value = event_data

    response = client.post(
        WEBHOOK_URL,
        data=json.dumps(event_data),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="valid_signature",
    )

    assert response.status_code == 200
    mock_stripe_webhook.assert_called_once()

    # Verify price was updated in the database
    updated_price = SubscriptionPrice.objects.get(stripe_price_id=event_data["data"]["object"]["id"])
    assert updated_price.price == event_data["data"]["object"]["unit_amount"]
    assert updated_price.currency == event_data["data"]["object"]["currency"]
    assert updated_price.active == event_data["data"]["object"]["active"]


def test_handle_subscription_create_success(  # noqa: PLR0913
    client: Client, load_event_data, customer, subscription_price, stripe_client_mock, mock_stripe_webhook
):
    """Test `handle_stripe_subscription_create` processes a valid subscription webhook correctly."""
    event_data = load_event_data("customer_subscription_created")

    # Ensure no subscription exists before processing
    assert not UserSubscription.objects.filter(user=customer).exists()

    # Simulate a webhook request
    mock_stripe_webhook.return_value = event_data
    response = client.post(
        WEBHOOK_URL,
        data=json.dumps(event_data),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="valid_signature",  # Mock signature verification
    )

    assert response.status_code == 200

    # Ensure subscription was created in the database
    subscription = UserSubscription.objects.get(user=customer)
    assert subscription.stripe_subscription_id == TEST_SUBSCRIPTION_ID
    assert subscription.plan == subscription_price.plan
    assert subscription.status == event_data["data"]["object"]["status"]
    assert subscription.start_date == timestamp_to_aware_datetime(event_data["data"]["object"]["start_date"])
    assert subscription.is_active is False
    assert subscription.ended_at is None


def test_handle_subscription_create_no_user(client: Client, load_event_data, mock_stripe_webhook):
    """Test `handle_stripe_subscription_create` returns 500 when the user is missing."""
    event_data = load_event_data("customer_subscription_created")

    mock_stripe_webhook.return_value = event_data
    with pytest.raises(StripeWebhookError):
        client.post(
            WEBHOOK_URL,
            data=json.dumps(event_data),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="valid_signature",
        )


def test_handle_subscription_create_no_price(
    client: Client, subscription_plan, load_event_data, customer, mock_stripe_webhook
):
    """Test `handle_stripe_subscription_create` throws StripeWebhookError when the price ID is not found."""

    event_data = load_event_data("customer_subscription_created")

    mock_stripe_webhook.return_value = event_data
    with pytest.raises(StripeWebhookError):
        client.post(
            WEBHOOK_URL,
            data=json.dumps(event_data),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="valid_signature",
        )


def test_handle_subscription_update_success(
    client: Client, load_event_data, stripe_client_mock, user_subscription, mock_stripe_webhook
):
    """Test `handle_stripe_subscription_update` processes a valid subscription update webhook correctly."""
    event_data = load_event_data("customer_subscription_updated")

    assert UserSubscription.objects.filter(stripe_subscription_id=TEST_SUBSCRIPTION_ID).exists()

    mock_stripe_webhook.return_value = event_data
    response = client.post(
        WEBHOOK_URL,
        data=json.dumps(event_data),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="valid_signature",
    )

    assert response.status_code == 200

    # Ensure subscription was updated in the database
    subscription = UserSubscription.objects.get(stripe_subscription_id=TEST_SUBSCRIPTION_ID)
    assert subscription.status == event_data["data"]["object"]["status"]
    assert subscription.start_date == timestamp_to_aware_datetime(event_data["data"]["object"]["start_date"])
    assert subscription.ended_at is None


def test_handle_subscription_update_no_subscription(client: Client, load_event_data, mock_stripe_webhook):
    """Test `handle_stripe_subscription_update` throws StripeWebhookError when the subscription is missing."""
    event_data = load_event_data("customer_subscription_updated")

    assert not UserSubscription.objects.filter(stripe_subscription_id=TEST_SUBSCRIPTION_ID).exists()

    mock_stripe_webhook.return_value = event_data
    with pytest.raises(StripeWebhookError):
        client.post(
            WEBHOOK_URL,
            data=json.dumps(event_data),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="valid_signature",
        )


def test_handle_subscription_update_no_ended_at(
    client: Client, load_event_data, user_subscription, mock_stripe_webhook
):
    """Test `handle_stripe_subscription_update` when no `current_period_end` is provided."""
    event_data = load_event_data("customer_subscription_updated")
    event_data["data"]["object"].pop("ended_at")  # Remove the field

    mock_stripe_webhook.return_value = event_data

    response = client.post(
        WEBHOOK_URL,
        data=json.dumps(event_data),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="valid_signature",
    )

    assert response.status_code == 200

    # Ensure subscription is updated correctly in the database
    subscription = UserSubscription.objects.get(stripe_subscription_id=TEST_SUBSCRIPTION_ID)
    assert subscription.status == event_data["data"]["object"]["status"]
    assert subscription.ended_at is None


def test_handle_subscription_delete_success(
    client: Client, load_event_data, user_subscription, stripe_client_mock, mock_stripe_webhook
):
    """Test `handle_stripe_subscription_delete` processes a valid subscription deletion webhook correctly."""
    event_data = load_event_data("customer_subscription_deleted")

    assert UserSubscription.objects.filter(stripe_subscription_id=TEST_SUBSCRIPTION_ID).exists()

    mock_stripe_webhook.return_value = event_data
    response = client.post(
        WEBHOOK_URL,
        data=json.dumps(event_data),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="valid_signature",  # Mock signature verification
    )

    assert response.status_code == 200

    # Ensure subscription was updated in the database
    subscription = UserSubscription.objects.get(stripe_subscription_id=TEST_SUBSCRIPTION_ID)
    assert subscription.status == event_data["data"]["object"]["status"]
    assert subscription.ended_at == timestamp_to_aware_datetime(event_data["data"]["object"]["ended_at"])
    assert subscription.is_active is False


def test_handle_subscription_delete_no_subscription(client: Client, load_event_data, mock_stripe_webhook):
    """Test `handle_stripe_subscription_delete` throws StripeWebhookError when the subscription is missing."""
    event_data = load_event_data("customer_subscription_deleted")

    # Ensure the subscription does NOT exist
    assert not UserSubscription.objects.filter(stripe_subscription_id=TEST_SUBSCRIPTION_ID).exists()
    mock_stripe_webhook.return_value = event_data
    with pytest.raises(StripeWebhookError):
        client.post(
            WEBHOOK_URL,
            data=json.dumps(event_data),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="valid_signature",
        )
