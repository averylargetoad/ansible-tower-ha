# Makefile for Ansible Tower HA deployment testing

.PHONY: help test test-static test-syntax test-unit test-integration install-deps clean coverage

# Default target
help:
	@echo "Available targets:"
	@echo "  test          - Run all tests"
	@echo "  test-static   - Run static analysis tests (yamllint, ansible-lint)"
	@echo "  test-syntax   - Run syntax validation tests"
	@echo "  test-unit     - Run unit tests"
	@echo "  test-integration - Run integration tests with Molecule"
	@echo "  install-deps  - Install test dependencies"
	@echo "  clean         - Clean test artifacts"
	@echo "  coverage      - Generate test coverage report"

# Install test dependencies
install-deps:
	@echo "Installing test dependencies..."
	pip install -r tests/requirements.txt

# Run all tests
test: test-static test-syntax test-unit
	@echo "All tests completed successfully!"

# Static analysis tests
test-static:
	@echo "Running static analysis tests..."
	@tests/scripts/run-static-tests.sh

# Syntax validation tests
test-syntax:
	@echo "Running syntax validation tests..."
	@tests/scripts/run-syntax-tests.sh

# Unit tests
test-unit:
	@echo "Running unit tests..."
	@tests/scripts/run-unit-tests.sh

# Integration tests (requires Docker)
test-integration:
	@echo "Running integration tests..."
	@tests/scripts/run-integration-tests.sh

# Generate coverage report
coverage:
	@echo "Generating test coverage report..."
	@tests/scripts/generate-coverage.sh

# Clean test artifacts
clean:
	@echo "Cleaning test artifacts..."
	rm -rf tests/coverage/
	rm -rf tests/reports/
	rm -rf tests/.pytest_cache/
	rm -rf tests/__pycache__/
	find tests -name "*.pyc" -delete
	find tests -name "*.pyo" -delete

# Pre-commit hook target
pre-commit: test-static test-syntax
	@echo "Pre-commit checks completed!"

# CI target
ci: install-deps test coverage
	@echo "CI pipeline completed!"