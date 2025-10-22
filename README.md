# Ansible Tower High Availability Deployment

A comprehensive Ansible playbook for deploying a production-ready, high-availability Ansible Tower infrastructure with monitoring, remote control, and collection development capabilities.

## Architecture Overview

This deployment creates a complete Ansible Tower HA environment with:

### Core Infrastructure
- **3 Ansible Tower Nodes** - Clustered Tower/AWX instances for redundancy
- **3 PostgreSQL Nodes** - Primary-standby replication for database HA
- **2 Load Balancers** - HAProxy with Keepalived for VIP failover
- **1 Collection Development Server** - Dedicated environment for Ansible collection development

### Monitoring & Observability
- **Prometheus** - Metrics collection and alerting
- **Grafana** - Visualization and dashboards
- **Alertmanager** - Alert routing and management
- **Exporters** - Node, PostgreSQL, and HAProxy metrics

### Remote Control & Management
- **Ansible Semaphore** - Web-based Ansible playbook execution
- **API Monitoring** - Webhook endpoint for Prometheus alerts
- **Automated Remediation** - Alert-triggered playbook execution

## Infrastructure Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Load Balancer VIP                       │
│                    192.168.1.30 (Floating)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼──────┐              ┌───────▼──────┐
│   HAProxy 1  │              │   HAProxy 2  │
│ 192.168.1.31 │              │ 192.168.1.32 │
└──────┬───────┘              └──────┬────────┘
       │                             │
       └──────────────┬──────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐ ┌────▼──────┐ ┌───▼────────┐
│  Tower Node1 │ │Tower Node2│ │Tower Node3 │
│ 192.168.1.11 │ │192.168.1.12│ │192.168.1.13│
└──────┬───────┘ └─────┬─────┘ └─────┬──────┘
       │               │              │
       └───────────────┼──────────────┘
                       │
              ┌────────▼────────┐
              │  PostgreSQL HA  │
              │   Primary DB    │
              │  192.168.1.21   │
              └────────┬────────┘
                       │
        ┌──────────────┼──────────────┐
        │                             │
┌───────▼──────┐              ┌───────▼──────┐
│PostgreSQL    │              │PostgreSQL    │
│Standby 1     │              │Standby 2     │
│192.168.1.22  │              │192.168.1.23  │
└──────────────┘              └──────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Monitoring  │  │   Remote     │  │  Collection  │
│   Server     │  │   Control    │  │  Dev Server  │
│192.168.1.50  │  │192.168.1.60  │  │192.168.1.40  │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Prerequisites

### Control Machine
- Ansible 2.15+
- Python 3.9+
- SSH access to all target hosts

### Target Hosts
- RHEL/CentOS 8+ or Ubuntu 20.04+
- Minimum 4GB RAM per node (8GB recommended for Tower nodes)
- 50GB disk space per node
- Python 3 installed
- Sudo access for deployment user

### Network Requirements
- All hosts must be able to communicate with each other
- DNS resolution or /etc/hosts entries configured
- Firewall rules allowing required ports (configured automatically)

## Flexible Inventory System

This deployment supports multiple inventory configurations to accommodate different environments:

### Deployment Modes

#### 1. Static IP Assignment (Default)
- **Use case**: On-premises deployments, controlled networking
- **Configuration**: Set `use_static_ips: true`
- **Features**: IPs assigned within defined subnet ranges
- **Example**: Tower nodes use 192.168.1.10-19, Database nodes use 192.168.1.20-29

#### 2. Dynamic DNS Assignment
- **Use case**: DNS-managed environments, hybrid deployments
- **Configuration**: Set `use_static_ips: false` with `ansible_domain`
- **Features**: Hosts resolved via DNS (hostname.domain.com)
- **Example**: tower-node1.internal.company.com

#### 3. Cloud Provider Dynamic
- **Use case**: AWS EC2, Azure VMs, GCP Compute Engine
- **Configuration**: Use cloud provider inventory plugins
- **Features**: Automatic discovery via instance tags/labels
- **Example**: AWS EC2 instances tagged with Role=tower

#### 4. Mixed Environments
- **Use case**: Hybrid cloud + on-premises deployments
- **Configuration**: Per-host overrides combining static and dynamic
- **Features**: Different assignment modes per component
- **Example**: On-prem databases with cloud Tower nodes

### Available Inventory Examples

The `inventory/examples/` directory contains ready-to-use configurations:

- `static-custom-subnets.yml` - Static IPs with custom subnet ranges
- `dynamic-dns.yml` - DNS-based hostname resolution
- `aws-ec2-dynamic.yml` - AWS EC2 dynamic inventory with tag-based grouping
- `azure-dynamic.yml` - Azure VM dynamic inventory
- `gcp-dynamic.yml` - Google Cloud Platform dynamic inventory
- `mixed-environment.yml` - Hybrid static/dynamic deployment

### Quick Configuration

```bash
# Static deployment (default)
cp inventory/hosts.yml inventory/my-hosts.yml
# Edit IP addresses and deploy

# DNS-based deployment
cp inventory/examples/dynamic-dns.yml inventory/my-hosts.yml
# Set ansible_domain and deploy

# AWS cloud deployment
cp inventory/examples/aws-ec2-dynamic.yml inventory/my-hosts.yml
# Tag EC2 instances and deploy
```

For detailed configuration instructions, see `inventory/examples/README.md`.

## Quick Start

### 1. Clone/Copy the Deployment

```bash
cd ansible-tower-ha
```

### 2. Configure Inventory

The inventory system is flexible and supports multiple deployment modes. Choose the approach that fits your environment:

#### Option A: Static IP Deployment (Default)
Edit `inventory/hosts.yml` with your IP addresses:

```yaml
# Set deployment mode
use_static_ips: true

# Update network configuration for your environment
network_config:
  base_network: "192.168.1.0/24"
  subnets:
    tower_subnet: "192.168.1.10-19"        # Adjust to your network
    database_subnet: "192.168.1.20-29"
    # ... other subnets

# Hosts will use static IPs within defined ranges
tower-node1:
  ansible_host: "192.168.1.11"  # Or use template: "{{ '192.168.1.11' if use_static_ips else ... }}"
  ansible_user: ansible
```

#### Option B: Use Pre-built Examples
Copy and customize an example inventory:

```bash
# For static deployment with custom subnets
cp inventory/examples/static-custom-subnets.yml inventory/hosts.yml

# For DNS-based deployment
cp inventory/examples/dynamic-dns.yml inventory/hosts.yml

# For AWS EC2 deployment
cp inventory/examples/aws-ec2-dynamic.yml inventory/hosts.yml

# Then edit the copied file for your environment
vim inventory/hosts.yml
```

### 3. Configure Variables

Review and modify `group_vars/all.yml` for your environment:

```yaml
tower_version: "3.8.6"
postgresql_version: 13
collection_namespace: myorg
```

### 4. Create Vault File

```bash
# Copy example vault file
cp group_vars/vault.yml.example group_vars/vault.yml

# Edit with your passwords
vim group_vars/vault.yml

# Encrypt the vault
ansible-vault encrypt group_vars/vault.yml
```

### 5. Verify Connectivity

```bash
ansible all -i inventory/hosts.yml -m ping
```

### 6. Deploy Infrastructure

```bash
# Full deployment
ansible-playbook -i inventory/hosts.yml site.yml --ask-vault-pass

# Or deploy specific components with tags
ansible-playbook -i inventory/hosts.yml site.yml --tags database --ask-vault-pass
ansible-playbook -i inventory/hosts.yml site.yml --tags tower --ask-vault-pass
ansible-playbook -i inventory/hosts.yml site.yml --tags monitoring --ask-vault-pass
```

## Deployment Tags

Use tags to deploy specific components:

- `database` - PostgreSQL HA cluster
- `postgresql` - PostgreSQL configuration
- `loadbalancer` - HAProxy and Keepalived
- `haproxy` - Just HAProxy
- `tower` - Ansible Tower nodes
- `awx` - Alternative tag for Tower
- `collection` - Collection development server
- `development` - Development tools
- `monitoring` - Prometheus, Grafana, Alertmanager
- `prometheus` - Just Prometheus
- `grafana` - Just Grafana
- `remote_control` - Semaphore server
- `semaphore` - Alternative tag for remote control
- `exporters` - Monitoring exporters

## Post-Deployment Configuration

### Access Tower Web Interface

1. Navigate to: `https://192.168.1.30` (VIP)
2. Login with credentials from vault:
   - Username: `admin`
   - Password: `vault_tower_admin_password`

### Access Monitoring

**Grafana:**
- URL: `http://192.168.1.50:3000`
- Username: `admin`
- Password: `vault_grafana_admin_password`

**Prometheus:**
- URL: `http://192.168.1.50:9090`

**Alertmanager:**
- URL: `http://192.168.1.50:9093`

**HAProxy Stats:**
- URL: `http://192.168.1.31:8080` or `http://192.168.1.32:8080`
- Username: `admin`
- Password: `vault_lb_stats_password`

### Access Remote Control

**Semaphore UI:**
- URL: `http://192.168.1.60:3000`
- Username: `admin`
- Password: `vault_semaphore_admin_password`

### Collection Development

SSH to the collection development server:

```bash
ssh developer@192.168.1.40

# Initialize a new collection
init-collection.sh my_collection

# Navigate to collection
cd ~/collections/ansible_collections/myorg/my_collection

# Build collection
ansible-build

# Test collection
ansible-test
```

## Monitoring & Alerting

### Metrics Collected

- **System Metrics**: CPU, memory, disk, network
- **Tower Metrics**: API response times, job statistics
- **PostgreSQL Metrics**: Connections, replication lag, queries
- **HAProxy Metrics**: Request rates, backend health, response times

### Alert Rules

Configured alerts include:
- Tower node down
- High CPU/memory usage
- Low disk space
- PostgreSQL replication lag
- Database connection issues
- HAProxy backend failures

### Alert Notifications

Configure alert destinations in:
- `roles/monitoring/templates/alertmanager.yml.j2`

Supported integrations:
- Email
- Slack
- PagerDuty
- Webhook (Semaphore API)

## Remote Control & Automation

### Semaphore Features

- Web-based playbook execution
- Scheduled jobs
- Access control and RBAC
- Audit logging
- API for automation

### Alert-Triggered Remediation

The deployment includes an API monitoring endpoint that receives Prometheus alerts and can trigger automated remediation playbooks.

Configure custom remediation in:
`/usr/local/bin/semaphore-api-monitor.py` on the remote control server

## Maintenance Operations

### Backup

```bash
# Backup Tower database
ansible-playbook -i inventory/hosts.yml playbooks/backup.yml --ask-vault-pass

# Backup configuration
tar -czf tower-config-backup.tar.gz /etc/tower/
```

### Scale Tower Cluster

1. Add new node to `inventory/hosts.yml`
2. Run Tower deployment:
```bash
ansible-playbook -i inventory/hosts.yml site.yml --tags tower --limit new-tower-node
```

### Update Tower

1. Update `tower_version` in `group_vars/all.yml`
2. Run Tower deployment:
```bash
ansible-playbook -i inventory/hosts.yml site.yml --tags tower --ask-vault-pass
```

### PostgreSQL Failover

The standby nodes automatically sync from primary. To promote a standby:

```bash
# On standby node
touch /tmp/postgresql.trigger.13

# Update primary_conninfo on other nodes
# Re-run database deployment
ansible-playbook -i inventory/hosts.yml site.yml --tags database --ask-vault-pass
```

## Troubleshooting

### Tower Not Accessible

1. Check HAProxy status:
```bash
systemctl status haproxy
```

2. Check Tower services:
```bash
systemctl status ansible-tower
systemctl status supervisord
```

3. Check logs:
```bash
tail -f /var/log/tower/tower.log
```

### Database Issues

1. Check PostgreSQL status:
```bash
systemctl status postgresql
```

2. Check replication status:
```bash
sudo -u postgres psql -c "SELECT * FROM pg_stat_replication;"
```

3. Check logs:
```bash
tail -f /var/log/postgresql/postgresql-13-main.log
```

### Monitoring Issues

1. Check Prometheus:
```bash
systemctl status prometheus
curl http://localhost:9090/-/healthy
```

2. Check exporters:
```bash
systemctl status node_exporter
curl http://localhost:9100/metrics
```

3. Check Grafana:
```bash
systemctl status grafana-server
```

## Security Considerations

1. **Vault Encryption**: Always encrypt sensitive data with ansible-vault
2. **SSH Keys**: Use SSH keys instead of passwords
3. **Firewall**: Only open required ports
4. **SSL/TLS**: Use valid certificates for production (not self-signed)
5. **Network Segmentation**: Place database on separate network
6. **Regular Updates**: Keep all components updated
7. **Audit Logging**: Monitor access logs regularly

## Project Structure

```
ansible-tower-ha/
├── inventory/
│   ├── hosts.yml                    # Main inventory file (flexible assignment)
│   └── examples/                    # Example inventory configurations
│       ├── README.md                # Inventory configuration guide
│       ├── static-custom-subnets.yml # Static IPs with custom subnets
│       ├── dynamic-dns.yml          # DNS-based hostname resolution
│       ├── aws-ec2-dynamic.yml      # AWS EC2 dynamic inventory
│       ├── azure-dynamic.yml        # Azure VM dynamic inventory
│       ├── gcp-dynamic.yml          # GCP Compute Engine dynamic inventory
│       └── mixed-environment.yml    # Hybrid static/dynamic deployment
├── group_vars/
│   ├── all.yml                      # Global variables
│   └── vault.yml.example            # Vault template (expanded)
├── roles/
│   ├── postgresql_ha/               # PostgreSQL HA role
│   ├── tower_ha/                    # Tower HA role
│   ├── collection_dev/              # Collection development role
│   ├── monitoring/                  # Monitoring stack role (Prometheus/Grafana)
│   └── remote_control/              # Semaphore role
├── templates/
│   ├── haproxy.cfg.j2              # HAProxy configuration
│   └── keepalived.conf.j2          # Keepalived configuration
├── site.yml                         # Main playbook
├── .gitignore                       # Git ignore file
└── README.md                        # This file
```

## Contributing

To extend this deployment:

1. Add new roles in `roles/` directory
2. Update `site.yml` with new plays
3. Add variables to `group_vars/all.yml`
4. Update this README with new features

## License

This playbook is provided as-is for deploying Ansible Tower infrastructure.

## Support

For issues and questions:
- Check logs on affected hosts
- Review Grafana dashboards for metrics
- Check Prometheus alerts
- Review Tower job output

## References

- [Ansible Tower Documentation](https://docs.ansible.com/ansible-tower/)
- [PostgreSQL Replication](https://www.postgresql.org/docs/current/warm-standby.html)
- [HAProxy Documentation](http://www.haproxy.org/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Ansible Semaphore](https://docs.ansible-semaphore.com/)
