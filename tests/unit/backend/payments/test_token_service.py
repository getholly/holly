import pytest
from django.contrib.auth import get_user_model

from holly.payments.models import CreditBalance
from holly.payments.services import (
    CreditService,
    InvalidCreditOperationError,
)

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def credit_balance(user):
    """Fixture to create a CreditBalance for the user with 100 credits."""
    return CreditBalance.objects.create(user=user, current_credits=100)


# ---------- Test Cases for add_credits ----------


def test_add_credits_new_user(user):
    """Test adding credits to a user without an existing balance."""
    assert CreditBalance.objects.filter(user=user).count() == 0
    CreditService.add_credits(user, 50)
    assert CreditBalance.objects.filter(user=user).count() == 1
    assert CreditBalance.objects.get(user=user).current_credits == 50


def test_add_credits_existing_balance(user, credit_balance):
    """Test adding credits to an existing balance."""
    CreditService.add_credits(user, 50)
    credit_balance.refresh_from_db()
    assert credit_balance.current_credits == 150  # 100 + 50


def test_add_credits_zero(user, credit_balance):
    """Test adding zero credits (should not change balance)."""
    CreditService.add_credits(user, 0)
    credit_balance.refresh_from_db()
    assert credit_balance.current_credits == 100  # No change


def test_add_credits_negative(user, credit_balance):
    """Test adding a negative number of credits (should raise error)."""
    with pytest.raises(InvalidCreditOperationError, match="Invalid credit operation."):
        CreditService.add_credits(user, -10)


def test_add_credits_large_value(user, credit_balance):
    """Test adding a very large number of credits."""
    CreditService.add_credits(user, 10**6)
    credit_balance.refresh_from_db()
    assert credit_balance.current_credits == 100 + 10**6


# ---------- Test Cases for increase_credits_up_to ----------


def test_increase_credits_up_to_existing_balance(user, credit_balance):
    """Test increasing credits up to the current balance."""
    CreditService.increase_credits_up_to(user, 100)
    credit_balance.refresh_from_db()
    assert credit_balance.current_credits == 100  # No change


def test_increase_credits_up_to_less_than_balance(user, credit_balance):
    """Test increasing credits up to a value less than the current balance."""
    CreditService.increase_credits_up_to(user, 50)
    credit_balance.refresh_from_db()
    assert credit_balance.current_credits == 100  # No change


def test_increase_credits_up_to_more_than_balance(user, credit_balance):
    """Test increasing credits up to a value more than the current balance."""
    CreditService.increase_credits_up_to(user, 150)
    credit_balance.refresh_from_db()
    assert credit_balance.current_credits == 150  # Increased to 150


def test_increase_credits_up_to_zero(user, credit_balance):
    """Test increasing credits up to zero (should not change balance)."""
    CreditService.increase_credits_up_to(user, 0)
    credit_balance.refresh_from_db()
    assert credit_balance.current_credits == 100  # No change


def test_increase_credits_up_to_negative(user, credit_balance):
    """Test increasing credits up to a negative value (should raise error)."""
    with pytest.raises(InvalidCreditOperationError, match="Invalid credit operation."):
        CreditService.increase_credits_up_to(user, -10)


# ---------- Test Cases for deduct_credits ----------


def test_deduct_credits_enough_balance(user, credit_balance):
    """Test deducting credits when the user has enough balance."""
    CreditService.deduct_credits(user, 50)
    credit_balance.refresh_from_db()
    assert credit_balance.current_credits == 50  # 100 - 50


def test_deduct_credits_exact_balance(user, credit_balance):
    """Test deducting exactly all available credits."""
    CreditService.deduct_credits(user, 100)
    credit_balance.refresh_from_db()
    assert credit_balance.current_credits == 0  # Exactly deducted


def test_deduct_more_credits_than_available(user, credit_balance):
    """Test trying to deduct more credits than available (should set to 0)."""
    result_credits = CreditService.deduct_credits(user, 150)
    assert result_credits == 0


def test_deduct_credits_no_balance(user):
    """Test deducting credits when the user has no creditBalance (should set to 0)."""
    result_credits = CreditService.deduct_credits(user, 10)
    assert result_credits == 0


def test_deduct_credits_zero(user, credit_balance):
    """Test deducting zero credits (should raise error)."""
    with pytest.raises(InvalidCreditOperationError, match="Invalid credit operation."):
        CreditService.deduct_credits(user, 0)


def test_deduct_credits_negative(user, credit_balance):
    """Test deducting a negative number of credits (should raise error)."""
    with pytest.raises(InvalidCreditOperationError, match="Invalid credit operation."):
        CreditService.deduct_credits(user, -10)


# ---------- Test Cases for get_user_credits ----------


def test_get_user_credits_existing_balance(user, credit_balance):
    """Test retrieving the credit balance when the user has credits."""
    assert CreditService.get_user_credits(user) == 100


def test_get_user_credits_no_balance(user):
    """Test retrieving the credit balance when the user has no record (should return 0)."""
    assert CreditService.get_user_credits(user) == 0  # Should return 0 instead of raising an error
