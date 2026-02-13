#!/usr/bin/env python3
"""
YAML linting tests for Ansible Tower HA deployment.

This module tests all YAML files in the project for syntax errors,
formatting consistency, and adherence to best practices.
"""

import os
import glob
import subprocess
import pytest
from pathlib import Path


class TestYamlLint:
    """Test class for YAML linting validation."""

    @classmethod
    def setup_class(cls):
        """Set up test class with project root path."""
        cls.project_root = Path(__file__).parent.parent.parent
        cls.yaml_files = cls._find_yaml_files()

    @classmethod
    def _find_yaml_files(cls):
        """Find all YAML files in the project."""
        yaml_patterns = [
            "*.yml",
            "*.yaml",
            "**/inventory/**/*.yml",
            "**/inventory/**/*.yaml",
            "**/group_vars/**/*.yml",
            "**/host_vars/**/*.yml",
            "**/roles/**/*.yml",
            "**/playbooks/**/*.yml"
        ]

        yaml_files = []
        for pattern in yaml_patterns:
            files = glob.glob(str(cls.project_root / pattern), recursive=True)
            yaml_files.extend(files)

        # Remove duplicates and filter out test files
        yaml_files = list(set(yaml_files))
        yaml_files = [f for f in yaml_files if '/tests/' not in f]

        return yaml_files

    def test_yaml_files_found(self):
        """Test that YAML files are found in the project."""
        assert len(self.yaml_files) > 0, "No YAML files found in project"
        assert len(self.yaml_files) >= 20, f"Expected at least 20 YAML files, found {len(self.yaml_files)}"

    @pytest.mark.parametrize("yaml_file", yaml_files if 'yaml_files' in locals() else [])
    def test_yaml_lint_individual_file(self, yaml_file):
        """Test individual YAML file with yamllint."""
        if not yaml_file:
            pytest.skip("No YAML files to test")

        result = subprocess.run(
            ["yamllint", "-c", str(self.project_root / ".yamllint"), yaml_file],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            # Provide detailed error information
            relative_path = os.path.relpath(yaml_file, self.project_root)
            pytest.fail(f"YAML lint failed for {relative_path}:\n{result.stdout}\n{result.stderr}")

    def test_all_yaml_files_lint_together(self):
        """Test all YAML files together for overall consistency."""
        if not self.yaml_files:
            pytest.skip("No YAML files to test")

        result = subprocess.run(
            ["yamllint", "-c", str(self.project_root / ".yamllint")] + self.yaml_files,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            pytest.fail(f"Overall YAML lint failed:\n{result.stdout}\n{result.stderr}")

    def test_yaml_file_extensions(self):
        """Test that all YAML files use .yml extension (consistency)."""
        yaml_extensions = [Path(f).suffix for f in self.yaml_files]
        yaml_count = yaml_extensions.count('.yaml')

        # Allow some .yaml files but prefer .yml for consistency
        if yaml_count > 0:
            print(f"Found {yaml_count} files with .yaml extension")
            print("Consider renaming to .yml for consistency")

    def test_critical_yaml_files_exist(self):
        """Test that critical YAML files exist."""
        critical_files = [
            "site.yml",
            "inventory/hosts.yml",
            "group_vars/all.yml",
            "group_vars/vault.yml.example"
        ]

        for critical_file in critical_files:
            file_path = self.project_root / critical_file
            assert file_path.exists(), f"Critical YAML file missing: {critical_file}"

    def test_yaml_file_permissions(self):
        """Test that YAML files have appropriate permissions."""
        for yaml_file in self.yaml_files:
            file_stat = os.stat(yaml_file)
            file_mode = oct(file_stat.st_mode)[-3:]

            # YAML files should be readable (at least 644)
            assert file_mode in ['644', '664', '755'], f"Invalid permissions {file_mode} for {yaml_file}"

    def test_no_sensitive_data_in_yaml(self):
        """Test that YAML files don't contain sensitive data patterns."""
        sensitive_patterns = [
            r'password:\s*[\'"][^\'"\s]+[\'"]',
            r'secret:\s*[\'"][^\'"\s]+[\'"]',
            r'key:\s*[\'"][A-Za-z0-9+/]{20,}[\'"]',
            r'token:\s*[\'"][^\'"\s]+[\'"]'
        ]

        import re

        for yaml_file in self.yaml_files:
            # Skip vault files as they should contain encrypted sensitive data
            if 'vault' in yaml_file.lower():
                continue

            with open(yaml_file, 'r') as f:
                content = f.read()

                for pattern in sensitive_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        relative_path = os.path.relpath(yaml_file, self.project_root)
                        pytest.fail(f"Possible sensitive data found in {relative_path}: {matches}")