# Python Example Project

This is a simple Python project that demonstrates basic functionality with type hints and testing.

## Project Structure

- `simplemaths/`: A package for simple math operations
  - `maths.py`: Contains functions for add, subtract, multiply, divide
  - `__init__.py`: Exports the `add` function
- `greet/`: A package for greeting functions
  - `say.py`: Contains functions for greet, farewell, and answer
  - `__init__.py`: Exports the greeting functions
- `do_add.py`: A simple script that uses the add function
- `do_multiply.py`: A simple script that uses the multiply function
- `tests/`: Contains test cases for the project

## Type Checking

This project uses mypy for static type checking. Run the type checker with:

```bash
# From project root
./run_mypy.sh
```

## Running Tests

Run the tests with coverage using:

```bash
# From project root
./run_tests.sh
```

This will run all tests and generate a coverage report.

## Type Annotations

All functions in this project are properly annotated with type hints according to Python 3.10+ syntax.
