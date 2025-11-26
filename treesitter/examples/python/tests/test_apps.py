from io import StringIO
from pathlib import Path
from unittest.mock import patch


def test_do_add() -> None:
    with patch("sys.stdout", new=StringIO()) as mock_stdout:
        # Get the path to do_add.py
        do_add_path = Path(__file__).parent.parent / "do_add.py"

        # Run the script
        with open(do_add_path) as script_file:
            script_code = script_file.read()
            exec(script_code, {})

        # Verify output
        assert mock_stdout.getvalue() == "The answer is: 42\n"


def test_do_multiply() -> None:
    with patch("sys.stdout", new=StringIO()) as mock_stdout:
        # Get the path to do_multiply.py
        do_multiply_path = Path(__file__).parent.parent / "do_multiply.py"

        # Run the script
        with open(do_multiply_path) as script_file:
            script_code = script_file.read()
            exec(script_code, {})

        # Verify output
        assert mock_stdout.getvalue() == "The answer is: 80\n"
