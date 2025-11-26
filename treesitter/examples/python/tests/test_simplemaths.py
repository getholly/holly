import pytest
from simplemaths.maths import add, divide, multiply, subtract


def test_add() -> None:
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0
    assert add(2.5, 3.5) == 6.0


def test_subtract() -> None:
    assert subtract(5, 3) == 2
    assert subtract(0, 0) == 0
    assert subtract(-1, -1) == 0
    assert subtract(10.5, 5.5) == 5.0


def test_multiply() -> None:
    assert multiply(2, 3) == 6
    assert multiply(0, 5) == 0
    assert multiply(-1, -1) == 1
    assert multiply(2.5, 2) == 5.0


def test_divide() -> None:
    assert divide(6, 3) == 2.0
    assert divide(5, 2) == 2.5
    assert divide(-6, 3) == -2.0

    # Test division by zero
    with pytest.raises(ZeroDivisionError):
        divide(5, 0)
