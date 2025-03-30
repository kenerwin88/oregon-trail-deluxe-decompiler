#!/usr/bin/env python3
"""
Test runner for Oregon Trail Decompilation project.

This script discovers and runs all tests in the tests directory,
providing command-line options for controlling test execution.
"""

import sys
import unittest
import argparse
import logging
from pathlib import Path

# Ensure parent directory is in path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


def setup_logging(verbose=False):
    """Configure logging for tests"""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(levelname).1s %(module)s: %(message)s"
    )
    return logging.getLogger("test_runner")


def discover_and_run_tests(pattern="test_*.py", verbosity=1, test_dir=None):
    """Discover and run tests matching the given pattern

    Args:
        pattern: Pattern to match test files (default: test_*.py)
        verbosity: Test runner verbosity level (default: 1)
        test_dir: Directory containing tests (default: directory of this script)

    Returns:
        unittest.TestResult: Result of test execution
    """
    # Default to the directory containing this script
    if test_dir is None:
        test_dir = Path(__file__).parent

    # Discover and create test suite
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern=pattern)

    # Create and configure test runner
    runner = unittest.TextTestRunner(verbosity=verbosity)

    # Run tests
    return runner.run(suite)


def main():
    """Parse arguments and run tests"""
    parser = argparse.ArgumentParser(
        description="Run tests for Oregon Trail Decompilation project"
    )
    parser.add_argument(
        "--pattern",
        "-p",
        default="test_*.py",
        help="Pattern to match test files (default: test_*.py)",
    )
    parser.add_argument(
        "--pc8-only", action="store_true", help="Only run PC8 image conversion tests"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase verbosity (can be used multiple times)",
    )
    parser.add_argument(
        "--test-dir",
        default=None,
        help="Directory containing tests (default: directory of this script)",
    )
    args = parser.parse_args()

    # Configure logging
    logger = setup_logging(args.verbose > 0)

    # Override pattern for PC8-only tests
    if args.pc8_only:
        pattern = "test_*pc8*.py"
        logger.info("Running only PC8 image conversion tests")
    else:
        pattern = args.pattern

    logger.info(f"Discovering tests matching pattern: {pattern}")

    # Run tests
    result = discover_and_run_tests(
        pattern=pattern, verbosity=args.verbose + 1, test_dir=args.test_dir
    )

    # Print summary
    logger.info("\nTest Summary:")
    logger.info(f"  Ran {result.testsRun} tests")
    logger.info(f"  Failures: {len(result.failures)}")
    logger.info(f"  Errors: {len(result.errors)}")
    logger.info(f"  Skipped: {len(result.skipped)}")

    # Exit with appropriate status code
    if result.wasSuccessful():
        logger.info("All tests passed!")
        return 0
    else:
        logger.error("Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
