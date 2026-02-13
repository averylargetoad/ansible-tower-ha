# Test Suite for Ansible Tower HA Deployment

This directory contains comprehensive tests for the Ansible Tower HA deployment framework.

## Test Categories

### 1. Static Analysis Tests (`static/`)
- **YAML Linting**: Validates all YAML files for syntax and style
- **Ansible Linting**: Checks Ansible best practices and conventions
- **Jinja2 Template Validation**: Tests template rendering with various inputs

### 2. Syntax Validation Tests (`syntax/`)
- **Playbook Syntax**: Validates Ansible playbook syntax
- **Inventory Validation**: Tests inventory file structure and variables
- **Role Structure**: Validates role directory structure and required files

### 3. Unit Tests (`unit/`)
- **Template Rendering**: Tests Jinja2 templates with mock data
- **Variable Validation**: Ensures all required variables are defined
- **Logic Tests**: Tests conditional logic in playbooks and roles

### 4. Integration Tests (`integration/`)
- **Molecule Tests**: Full role testing in isolated environments
- **End-to-End**: Complete deployment workflow testing
- **Service Connectivity**: Tests service interactions and dependencies

### 5. Configuration Tests (`config/`)
- **Generated Config Validation**: Validates generated service configurations
- **Network Configuration**: Tests IP assignment and networking logic
- **Security Configuration**: Validates security settings and encrypted variables

## Running Tests

### Quick Test Suite
```bash
# Run all static analysis tests
./tests/scripts/run-static-tests.sh

# Run syntax validation
./tests/scripts/run-syntax-tests.sh

# Run unit tests
./tests/scripts/run-unit-tests.sh
```

### Full Test Suite
```bash
# Run all tests
make test

# Run specific test category
make test-static
make test-syntax
make test-unit
make test-integration
```

### Prerequisites
```bash
# Install test dependencies
pip install -r tests/requirements.txt
```

## CI/CD Integration

Tests are designed to run in CI/CD pipelines with clear exit codes:
- **0**: All tests passed
- **1**: Test failures detected
- **2**: Configuration errors
- **3**: Missing dependencies

## Test Data

Test inventories and variable files are located in `tests/fixtures/` directory:
- `inventory-static.yml`: Static IP deployment test data
- `inventory-dns.yml`: DNS-based deployment test data
- `inventory-cloud.yml`: Cloud provider test data
- `vars-test.yml`: Test variables for template rendering

## Coverage Reporting

Test coverage reports are generated in `tests/coverage/` directory:
- HTML reports for detailed analysis
- JSON reports for CI/CD integration
- Summary reports for quick overview