# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Ansible Tower High Availability deployment framework that creates production-ready HA infrastructure with complete monitoring, load balancing, and remote management capabilities. The project uses a modular Ansible playbook architecture with roles for each component and supports flexible deployment modes (static IPs, DNS, cloud providers).

## Common Commands

### Deployment Commands

```bash
# Full deployment (all components)
ansible-playbook -i inventory/hosts.yml site.yml --ask-vault-pass

# Component-specific deployments using tags
ansible-playbook -i inventory/hosts.yml site.yml --tags database --ask-vault-pass      # PostgreSQL HA cluster
ansible-playbook -i inventory/hosts.yml site.yml --tags tower --ask-vault-pass        # Tower cluster
ansible-playbook -i inventory/hosts.yml site.yml --tags loadbalancer --ask-vault-pass # HAProxy + Keepalived
ansible-playbook -i inventory/hosts.yml site.yml --tags monitoring --ask-vault-pass   # Prometheus + Grafana
ansible-playbook -i inventory/hosts.yml site.yml --tags remote_control --ask-vault-pass # Semaphore
ansible-playbook -i inventory/hosts.yml site.yml --tags collection --ask-vault-pass   # Collection dev environment
ansible-playbook -i inventory/hosts.yml site.yml --tags exporters --ask-vault-pass    # Monitoring exporters only

# Verify connectivity before deployment
ansible all -i inventory/hosts.yml -m ping
```

### Inventory Management

```bash
# Set up inventory for different deployment modes
cp inventory/examples/static-custom-subnets.yml inventory/hosts.yml  # Static IPs
cp inventory/examples/dynamic-dns.yml inventory/hosts.yml             # DNS-based
cp inventory/examples/aws-ec2-dynamic.yml inventory/hosts.yml         # AWS EC2
cp inventory/examples/mixed-environment.yml inventory/hosts.yml       # Hybrid

# Create and encrypt vault file
cp group_vars/vault.yml.example group_vars/vault.yml
ansible-vault encrypt group_vars/vault.yml
ansible-vault edit group_vars/vault.yml
```

### Maintenance Commands

```bash
# Backup Tower database
ansible-playbook -i inventory/hosts.yml playbooks/backup.yml --ask-vault-pass

# Scale Tower cluster (after adding node to inventory)
ansible-playbook -i inventory/hosts.yml site.yml --tags tower --limit new-tower-node

# Update Tower version (after updating tower_version in group_vars/all.yml)
ansible-playbook -i inventory/hosts.yml site.yml --tags tower --ask-vault-pass

# PostgreSQL failover - promote standby manually
# On standby node: touch /tmp/postgresql.trigger.13
# Then re-run: ansible-playbook -i inventory/hosts.yml site.yml --tags database --ask-vault-pass
```

## Architecture & Key Components

### Core Infrastructure Pattern
The deployment follows a 6-component architecture:
1. **PostgreSQL HA Cluster** (primary + 2 standby replicas with WAL streaming)
2. **Load Balancer Layer** (2 HAProxy nodes with Keepalived VIP failover)
3. **Tower HA Cluster** (3 Tower/AWX nodes in cluster configuration)
4. **Monitoring Stack** (Prometheus, Grafana, Alertmanager with exporters)
5. **Collection Development** (Isolated development environment with ansible-lint, molecule)
6. **Remote Control** (Semaphore for web-based playbook execution with alert integration)

### Flexible Inventory System
- **Static IP Mode**: Uses `use_static_ips: true` with subnet-based IP assignment
- **DNS Mode**: Uses `use_static_ips: false` with domain resolution
- **Cloud Dynamic**: Uses cloud provider inventory plugins (AWS, Azure, GCP)
- **Mixed Environment**: Combines static and dynamic assignment per host

### File Structure & Role Organization

```
site.yml                 # Main orchestration playbook (7 plays with dependency order)
inventory/hosts.yml       # Flexible inventory with IP assignment logic
inventory/examples/       # Pre-built inventory templates for different modes
group_vars/all.yml       # Global configuration (Tower versions, DB settings, monitoring)
group_vars/vault.yml     # Encrypted secrets (18 sensitive values)
roles/                   # Six specialized roles:
  ├── postgresql_ha/     # PostgreSQL primary-standby replication
  ├── tower_ha/          # Tower cluster deployment and configuration
  ├── monitoring/        # Prometheus + Grafana + Alertmanager stack
  ├── collection_dev/    # Ansible collection development environment
  └── remote_control/    # Semaphore web UI + API monitoring
templates/               # Top-level HAProxy and Keepalived configurations
```

## Development Patterns

### OS Abstraction Pattern
Roles use `include_vars: "{{ ansible_os_family }}.yml"` to handle RHEL vs Debian package differences automatically.

### Dynamic Configuration Templates
Jinja2 templates use inventory group iteration for automatic service discovery:
```jinja2
{% for host in groups['tower_cluster'] %}
  - targets: ['{{ hostvars[host].ansible_host }}:9100']
{% endfor %}
```

### Idempotent Operations with Markers
One-time operations use marker files to prevent re-execution:
```yaml
creates: /var/lib/semaphore/.migrated
```

### Health Check Polling
Services use retry loops to wait for readiness:
```yaml
until: service_ping.status == 200
retries: 30
delay: 10
```

## Key Configuration Points

### Network Configuration
- VIP (Keepalived): `192.168.1.30`
- Tower subnet: `192.168.1.10-19` (3 nodes)
- Database subnet: `192.168.1.20-29` (primary + 2 standby)
- Load balancer subnet: `192.168.1.30-39`
- Services subnet: `192.168.1.40-69` (monitoring, dev, control)

### Tag-Based Deployment Control
All components support granular deployment via tags: `database`, `tower`, `loadbalancer`, `monitoring`, `remote_control`, `collection`, `exporters`

### PostgreSQL HA Configuration
- Primary-standby streaming replication with `postgresql_wal_level: replica`
- Configurable connection pooling and performance tuning
- Automatic failover via trigger files

### Vault Integration
All sensitive data (passwords, API keys, encryption keys) stored in encrypted `group_vars/vault.yml` with 18 different credentials for various services.

## Access Points Post-Deployment

- **Tower Web UI**: `https://192.168.1.30` (VIP)
- **Grafana**: `http://192.168.1.50:3000`
- **Prometheus**: `http://192.168.1.50:9090`
- **HAProxy Stats**: `http://192.168.1.31:8080`
- **Semaphore UI**: `http://192.168.1.60:3000`
- **Collection Dev**: SSH to `developer@192.168.1.40`

## Working with This Codebase

When modifying this deployment:
1. **Test inventory changes** with `ansible all -m ping` before full deployment
2. **Use tags** for component-specific deployments to avoid full infrastructure rebuilds
3. **Update group_vars/all.yml** for version changes and global configuration
4. **Follow the dependency order** in site.yml: Database → Load Balancer → Tower → Services
5. **Encrypt sensitive data** in vault.yml and use vault_ prefixed variable references
6. **Leverage the flexible inventory system** - copy appropriate example from inventory/examples/
7. **Use OS abstraction patterns** when adding new roles (separate RedHat.yml and Debian.yml vars)