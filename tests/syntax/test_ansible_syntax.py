#!/usr/bin/env python3
"""
Ansible syntax validation tests for Ansible Tower HA deployment.

This module tests all Ansible playbooks, roles, and inventory files
for syntax errors and structural correctness.
"""

import os
import glob
import subprocess
import pytest
import yaml
from pathlib import Path


class TestAnsibleSyntax:
    """Test class for Ansible syntax validation."""

    @classmethod
    def setup_class(cls):
        """Set up test class with project paths."""
        cls.project_root = Path(__file__).parent.parent.parent
        cls.playbook_files = cls._find_playbook_files()
        cls.role_directories = cls._find_role_directories()
        cls.inventory_files = cls._find_inventory_files()

    @classmethod
    def _find_playbook_files(cls):
        """Find all Ansible playbook files."""
        playbook_patterns = [
            "*.yml",
            "playbooks/*.yml",
            "roles/*/tasks/*.yml",
            "roles/*/handlers/*.yml"
        ]

        playbook_files = []
        for pattern in playbook_patterns:
            files = glob.glob(str(cls.project_root / pattern), recursive=True)
            playbook_files.extend(files)

        # Filter for actual playbooks (contain plays or tasks)
        validated_playbooks = []
        for playbook in playbook_files:
            if cls._is_ansible_playbook(playbook):
                validated_playbooks.append(playbook)

        return validated_playbooks

    @classmethod
    def _find_role_directories(cls):
        """Find all Ansible role directories."""
        roles_path = cls.project_root / "roles"
        if not roles_path.exists():
            return []

        return [str(d) for d in roles_path.iterdir() if d.is_dir()]

    @classmethod
    def _find_inventory_files(cls):
        """Find all inventory files."""
        inventory_patterns = [
            "inventory/*.yml",
            "inventory/*.yaml",
            "inventory/examples/*.yml"
        ]

        inventory_files = []
        for pattern in inventory_patterns:
            files = glob.glob(str(cls.project_root / pattern), recursive=True)
            inventory_files.extend(files)

        return inventory_files

    @classmethod
    def _is_ansible_playbook(cls, file_path):
        """Check if a YAML file is an Ansible playbook."""
        try:
            with open(file_path, 'r') as f:
                content = yaml.safe_load(f)

            if not content:
                return False

            # Check for playbook structure
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and ('hosts' in item or 'tasks' in item):
                        return True
            elif isinstance(content, dict):
                if 'tasks' in content or 'handlers' in content:
                    return True

            return False
        except Exception:
            return False

    def test_main_playbook_syntax(self):
        """Test main site.yml playbook syntax."""
        site_playbook = self.project_root / "site.yml"
        assert site_playbook.exists(), "Main site.yml playbook not found"

        result = subprocess.run([
            "ansible-playbook",
            "--syntax-check",
            str(site_playbook)
        ], capture_output=True, text=True)

        if result.returncode != 0:
            pytest.fail(f"Syntax check failed for site.yml:\n{result.stderr}")

    @pytest.mark.parametrize("playbook_file", playbook_files if 'playbook_files' in locals() else [])
    def test_individual_playbook_syntax(self, playbook_file):
        """Test individual playbook syntax."""
        if not playbook_file:
            pytest.skip("No playbook files to test")

        result = subprocess.run([
            "ansible-playbook",
            "--syntax-check",
            playbook_file
        ], capture_output=True, text=True)

        if result.returncode != 0:
            relative_path = os.path.relpath(playbook_file, self.project_root)
            pytest.fail(f"Syntax check failed for {relative_path}:\n{result.stderr}")

    @pytest.mark.parametrize("role_dir", role_directories if 'role_directories' in locals() else [])
    def test_role_structure(self, role_dir):
        """Test Ansible role directory structure."""
        if not role_dir:
            pytest.skip("No roles to test")

        role_path = Path(role_dir)
        role_name = role_path.name

        # Check for required role structure
        expected_dirs = ["tasks", "handlers", "templates", "vars", "defaults", "meta"]

        # At least tasks directory should exist
        tasks_dir = role_path / "tasks"
        assert tasks_dir.exists(), f"Role {role_name} missing tasks directory"

        # Check for main.yml in tasks
        main_tasks = tasks_dir / "main.yml"
        assert main_tasks.exists(), f"Role {role_name} missing tasks/main.yml"

        # Validate main.yml syntax
        result = subprocess.run([
            "ansible-playbook",
            "--syntax-check",
            str(main_tasks)
        ], capture_output=True, text=True)

        if result.returncode != 0:
            pytest.fail(f"Syntax error in {role_name}/tasks/main.yml:\n{result.stderr}")

    @pytest.mark.parametrize("inventory_file", inventory_files if 'inventory_files' in locals() else [])
    def test_inventory_syntax(self, inventory_file):
        """Test inventory file syntax."""
        if not inventory_file:
            pytest.skip("No inventory files to test")

        result = subprocess.run([
            "ansible-inventory",
            "--inventory", inventory_file,
            "--list"
        ], capture_output=True, text=True)

        if result.returncode != 0:
            relative_path = os.path.relpath(inventory_file, self.project_root)
            pytest.fail(f"Inventory syntax error in {relative_path}:\n{result.stderr}")

    def test_required_ansible_files(self):
        """Test that required Ansible files exist."""
        required_files = [
            "site.yml",
            "inventory/hosts.yml",
            "group_vars/all.yml"
        ]

        for required_file in required_files:
            file_path = self.project_root / required_file
            assert file_path.exists(), f"Required file missing: {required_file}"

    def test_ansible_version_compatibility(self):
        """Test Ansible version compatibility."""
        result = subprocess.run([
            "ansible-playbook", "--version"
        ], capture_output=True, text=True)

        assert result.returncode == 0, "Could not determine Ansible version"

        version_output = result.stdout
        # Extract version (e.g., "ansible-playbook [core 2.15.0]")
        if "2.1" in version_output:
            # Version 2.1x should be sufficient
            pass
        else:
            print(f"Warning: Ansible version might be incompatible: {version_output}")

    def test_role_dependencies(self):
        """Test role dependencies are properly defined."""
        for role_dir in self.role_directories:
            role_path = Path(role_dir)
            role_name = role_path.name
            meta_file = role_path / "meta" / "main.yml"

            if meta_file.exists():
                try:
                    with open(meta_file, 'r') as f:
                        meta_content = yaml.safe_load(f)

                    if meta_content and "dependencies" in meta_content:
                        dependencies = meta_content["dependencies"]
                        assert isinstance(dependencies, list), f"Role {role_name} has invalid dependencies format"

                        # Check each dependency
                        for dep in dependencies:
                            if isinstance(dep, str):
                                # Simple role name dependency
                                assert dep, f"Empty dependency in role {role_name}"
                            elif isinstance(dep, dict):
                                # Complex dependency with parameters
                                assert "role" in dep or "name" in dep, f"Invalid dependency structure in role {role_name}"
                except Exception as e:
                    pytest.fail(f"Error parsing meta/main.yml for role {role_name}: {e}")

    def test_no_deprecated_ansible_features(self):
        """Test that no deprecated Ansible features are used."""
        deprecated_patterns = [
            ("include:", "Use include_tasks or import_tasks instead"),
            ("sudo:", "Use become: yes instead"),
            ("sudo_user:", "Use become_user instead"),
            ("always_run:", "Use check_mode: no instead")
        ]

        for playbook_file in self.playbook_files:
            try:
                with open(playbook_file, 'r') as f:
                    content = f.read()

                for pattern, message in deprecated_patterns:
                    if pattern in content:
                        relative_path = os.path.relpath(playbook_file, self.project_root)
                        pytest.fail(f"Deprecated feature '{pattern}' found in {relative_path}: {message}")
            except Exception:
                continue  # Skip files that can't be read

    def test_variable_naming_conventions(self):
        """Test that variables follow naming conventions."""
        import re

        for playbook_file in self.playbook_files:
            try:
                with open(playbook_file, 'r') as f:
                    content = f.read()

                # Check for variable references that don't follow snake_case
                var_pattern = r'\{\{\s*([a-zA-Z][a-zA-Z0-9_]*)\s*\}\}'
                matches = re.findall(var_pattern, content)

                for var_name in matches:
                    # Variables should be snake_case
                    if not re.match(r'^[a-z][a-z0-9_]*$', var_name):
                        # Allow some exceptions for built-in Ansible variables
                        if var_name not in ['ansible_host', 'ansible_user', 'ansible_os_family', 'hostvars', 'groups', 'inventory_hostname']:
                            relative_path = os.path.relpath(playbook_file, self.project_root)
                            print(f"Warning: Variable '{var_name}' in {relative_path} doesn't follow snake_case convention")

            except Exception:
                continue  # Skip files that can't be read