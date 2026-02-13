#!/bin/bash
# Script to run all static analysis tests for Ansible Tower HA deployment

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TESTS_DIR="$PROJECT_ROOT/tests"

echo "===================="
echo "Static Analysis Tests"
echo "===================="
echo "Project root: $PROJECT_ROOT"
echo

# Check if yamllint is installed
if ! command -v yamllint &> /dev/null; then
    echo "ERROR: yamllint is not installed"
    echo "Install with: pip install yamllint"
    exit 1
fi

# Check if ansible-lint is installed
if ! command -v ansible-lint &> /dev/null; then
    echo "ERROR: ansible-lint is not installed"
    echo "Install with: pip install ansible-lint"
    exit 1
fi

# Create reports directory
mkdir -p "$TESTS_DIR/reports"

echo "1. Running YAML Lint tests..."
echo "------------------------------"

# Run yamllint on all YAML files
echo "Running yamllint on project files..."
yamllint -c "$PROJECT_ROOT/.yamllint" -f standard "$PROJECT_ROOT" > "$TESTS_DIR/reports/yamllint-report.txt" 2>&1 || {
    echo "YAML Lint issues found:"
    cat "$TESTS_DIR/reports/yamllint-report.txt"
    exit 1
}

# Run Python-based YAML lint tests
echo "Running pytest YAML lint tests..."
cd "$PROJECT_ROOT"
python -m pytest tests/static/test_yaml_lint.py -v --tb=short \
    --html="$TESTS_DIR/reports/yaml-lint-report.html" \
    --json-report --json-report-file="$TESTS_DIR/reports/yaml-lint-report.json" || {
    echo "Python YAML lint tests failed"
    exit 1
}

echo "✓ YAML Lint tests passed"
echo

echo "2. Running Ansible Lint tests..."
echo "---------------------------------"

# Run ansible-lint on playbooks and roles
echo "Running ansible-lint on site.yml..."
ansible-lint site.yml > "$TESTS_DIR/reports/ansible-lint-site.txt" 2>&1 || {
    echo "Ansible lint issues found in site.yml:"
    cat "$TESTS_DIR/reports/ansible-lint-site.txt"
    exit 1
}

# Run ansible-lint on all roles
echo "Running ansible-lint on roles..."
for role_dir in "$PROJECT_ROOT/roles"/*; do
    if [ -d "$role_dir" ]; then
        role_name=$(basename "$role_dir")
        echo "  Checking role: $role_name"
        ansible-lint "$role_dir" > "$TESTS_DIR/reports/ansible-lint-$role_name.txt" 2>&1 || {
            echo "Ansible lint issues found in role $role_name:"
            cat "$TESTS_DIR/reports/ansible-lint-$role_name.txt"
            exit 1
        }
    fi
done

echo "✓ Ansible Lint tests passed"
echo

echo "3. Running configuration validation..."
echo "--------------------------------------"

# Validate JSON files (like Grafana dashboards)
echo "Validating JSON files..."
find "$PROJECT_ROOT" -name "*.json" -not -path "*/tests/*" -not -path "*/.git/*" | while read -r json_file; do
    echo "  Validating: $(basename "$json_file")"
    python -m json.tool "$json_file" > /dev/null || {
        echo "Invalid JSON file: $json_file"
        exit 1
    }
done

echo "✓ Configuration validation passed"
echo

echo "4. Running Jinja2 template syntax check..."
echo "-------------------------------------------"

# Basic Jinja2 syntax check
echo "Checking Jinja2 templates..."
find "$PROJECT_ROOT" -name "*.j2" -not -path "*/tests/*" | while read -r template_file; do
    echo "  Checking: $(basename "$template_file")"
    python3 -c "
import jinja2
import sys
try:
    with open('$template_file', 'r') as f:
        template_content = f.read()
    jinja2.Template(template_content)
    print('  ✓ Valid template syntax')
except Exception as e:
    print(f'  ✗ Template syntax error: {e}')
    sys.exit(1)
" || {
        echo "Template syntax error in: $template_file"
        exit 1
    }
done

echo "✓ Jinja2 template syntax check passed"
echo

# Generate summary report
echo "5. Generating summary report..."
echo "-------------------------------"

SUMMARY_FILE="$TESTS_DIR/reports/static-analysis-summary.txt"
cat > "$SUMMARY_FILE" << EOF
Static Analysis Test Summary
============================
Date: $(date)
Project: Ansible Tower HA Deployment

Tests Executed:
- YAML Lint (yamllint + pytest)
- Ansible Lint (playbooks + roles)
- Configuration Validation (JSON files)
- Jinja2 Template Syntax Check

Results:
✓ All static analysis tests PASSED

Files Analyzed:
- YAML files: $(find "$PROJECT_ROOT" -name "*.yml" -o -name "*.yaml" | grep -v tests | wc -l)
- JSON files: $(find "$PROJECT_ROOT" -name "*.json" | grep -v tests | wc -l)
- Jinja2 templates: $(find "$PROJECT_ROOT" -name "*.j2" | wc -l)
- Ansible roles: $(find "$PROJECT_ROOT/roles" -maxdepth 1 -type d | grep -v '^'$PROJECT_ROOT'/roles$' | wc -l)

Reports generated in: tests/reports/
EOF

echo "Summary report generated: tests/reports/static-analysis-summary.txt"
echo

echo "========================"
echo "✓ All static tests PASSED"
echo "========================"

# Display quick stats
echo "Quick Stats:"
echo "  YAML files checked: $(find "$PROJECT_ROOT" -name "*.yml" -o -name "*.yaml" | grep -v tests | wc -l)"
echo "  JSON files checked: $(find "$PROJECT_ROOT" -name "*.json" | grep -v tests | wc -l)"
echo "  Jinja2 templates checked: $(find "$PROJECT_ROOT" -name "*.j2" | wc -l)"
echo "  Ansible roles checked: $(find "$PROJECT_ROOT/roles" -maxdepth 1 -type d | grep -v '^'$PROJECT_ROOT'/roles$' | wc -l)"
echo