from io import StringIO
from unittest.mock import patch

from greet.say import answer, farewell, greet


def test_greet() -> None:
    with patch("sys.stdout", new=StringIO()) as mock_stdout:
        greet("World")
        assert mock_stdout.getvalue() == "hello World\n"


def test_farewell() -> None:
    with patch("sys.stdout", new=StringIO()) as mock_stdout:
        farewell("World")
        assert mock_stdout.getvalue() == "Goodbye World\n"


def test_answer_int() -> None:
    with patch("sys.stdout", new=StringIO()) as mock_stdout:
        answer(42)
        assert mock_stdout.getvalue() == "The answer is: 42\n"


def test_answer_float() -> None:
    with patch("sys.stdout", new=StringIO()) as mock_stdout:
        answer(3.14)
        assert mock_stdout.getvalue() == "The answer is: 3.14\n"


def test_answer_str() -> None:
    with patch("sys.stdout", new=StringIO()) as mock_stdout:
        answer("forty-two")
        assert mock_stdout.getvalue() == "The answer is: forty-two\n"
