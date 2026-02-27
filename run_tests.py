"""
Test runner script for cryptocurrency trading bot.
"""
import sys
import pytest


def main():
    """Run all tests."""
    print("=" * 60)
    print("Running Trading Bot Unit Tests")
    print("=" * 60 + "\n")

    # Run pytest with verbose output
    args = [
        'tests/',
        '-v',  # Verbose
        '--tb=short',  # Short traceback format
        '--color=yes',  # Colored output
    ]

    # Add coverage if available
    try:
        import pytest_cov
        args.extend(['--cov=src', '--cov-report=term-missing'])
    except ImportError:
        print("Note: Install pytest-cov for coverage reports\n")

    # Run tests
    exit_code = pytest.main(args)

    print("\n" + "=" * 60)
    if exit_code == 0:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
