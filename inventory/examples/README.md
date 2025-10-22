# Inventory Examples

This directory contains example inventory files for different deployment scenarios.

## Available Examples

### 1. `static-custom-subnets.yml`
**Static IP assignment with custom subnet ranges**
- Use when you need specific IP ranges for each component
- All IPs are statically assigned within defined subnets
- Good for on-premises deployments with controlled networking

**Usage:**
```bash
ansible-playbook -i inventory/examples/static-custom-subnets.yml site.yml
```

### 2. `dynamic-dns.yml`
**DNS-based dynamic assignment**
- Hosts are resolved via DNS (hostname.domain.com)
- No static IP configuration required
- Requires properly configured DNS infrastructure

**Usage:**
```bash
# Update ansible_domain in the file first
ansible-playbook -i inventory/examples/dynamic-dns.yml site.yml
```

### 3. `aws-ec2-dynamic.yml`
**AWS EC2 dynamic inventory**
- Uses AWS EC2 dynamic inventory plugin
- Instances grouped by tags (Role, Component, Environment)
- Requires properly tagged EC2 instances

**Prerequisites:**
```bash
pip install boto3 botocore
ansible-galaxy collection install amazon.aws
```

**Usage:**
```bash
# Configure AWS credentials first
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
ansible-playbook -i inventory/examples/aws-ec2-dynamic.yml site.yml
```

### 4. `azure-dynamic.yml`
**Azure dynamic inventory**
- Uses Azure Resource Manager dynamic inventory plugin
- VMs grouped by tags and resource groups
- Requires properly tagged Azure VMs

**Prerequisites:**
```bash
pip install azure-cli-core azure-mgmt-compute azure-mgmt-network
ansible-galaxy collection install azure.azcollection
```

**Usage:**
```bash
# Login to Azure CLI first
az login
ansible-playbook -i inventory/examples/azure-dynamic.yml site.yml
```

### 5. `gcp-dynamic.yml`
**Google Cloud Platform dynamic inventory**
- Uses GCP Compute Engine dynamic inventory plugin
- Instances grouped by labels and zones
- Requires properly labeled GCP instances

**Prerequisites:**
```bash
pip install google-cloud-compute
ansible-galaxy collection install google.cloud
```

**Usage:**
```bash
# Set up GCP authentication first
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
ansible-playbook -i inventory/examples/gcp-dynamic.yml site.yml
```

### 6. `mixed-environment.yml`
**Mixed static and dynamic assignment**
- Combines static on-premises hosts with dynamic cloud hosts
- Different deployment strategies per component
- Good for hybrid cloud deployments

**Usage:**
```bash
ansible-playbook -i inventory/examples/mixed-environment.yml site.yml
```

## Configuration Options

### Global Variables

All inventory files support these global configuration options:

#### IP Assignment Mode
```yaml
use_static_ips: true|false  # Enable/disable static IP mode
```

#### Network Configuration
```yaml
network_config:
  base_network: "192.168.1.0/24"
  subnets:
    tower_subnet: "192.168.1.10-19"
    database_subnet: "192.168.1.20-29"
  vips:
    loadbalancer_vip: "192.168.1.30"
```

#### Connection Settings
```yaml
default_ansible_user: ansible
default_ssh_port: 22
ansible_domain: "internal.company.com"  # For DNS resolution
```

## Customization

### For Static Deployments

1. Copy an example file to `inventory/hosts.yml`
2. Update IP addresses and subnets for your environment
3. Modify `default_ansible_user` if needed
4. Update vault variables

### For Dynamic Deployments

1. Choose the appropriate cloud provider example
2. Update project/subscription/resource group information
3. Ensure instances/VMs are properly tagged/labeled
4. Configure authentication for the cloud provider

### For Mixed Deployments

1. Start with the mixed-environment example
2. Define which components should be static vs dynamic
3. Configure DNS domain for dynamic hosts
4. Set appropriate users for different host types

## Required Tags/Labels for Cloud Providers

### AWS EC2 Tags
- `Role`: tower | database | loadbalancer | development | monitoring | control
- `Component`: tower-node1 | db-primary | lb-node1 | etc.
- `Environment`: production | staging | development
- `Project`: ansible-tower-ha
- `AnsibleUser`: ec2-user | ubuntu | centos (optional)
- `PostgreSQLRole`: primary | standby (database only)
- `KeepalivedPriority`: 100 | 90 (load balancers only)

### Azure VM Tags
Same as AWS but using underscores instead of camelCase

### GCP Instance Labels
Same structure but using hyphens instead of underscores:
- `role`: tower | database | loadbalancer | etc.
- `component`: tower-node1 | db-primary | etc.
- `ansible-user`: ansible | ubuntu | centos (optional)

## Testing Inventory

Before deploying, test your inventory configuration:

```bash
# List all hosts
ansible-inventory -i inventory/examples/your-inventory.yml --list

# Test connectivity
ansible all -i inventory/examples/your-inventory.yml -m ping

# View groups
ansible-inventory -i inventory/examples/your-inventory.yml --graph
```

## Troubleshooting

### Static IP Issues
- Verify IP ranges don't overlap
- Ensure IPs are available and not in use
- Check network routing and firewall rules

### Dynamic DNS Issues
- Verify DNS resolution: `nslookup hostname.domain.com`
- Check DNS server configuration
- Ensure forward and reverse DNS are configured

### Cloud Provider Issues
- Verify authentication (credentials, service accounts)
- Check instance/VM tags/labels
- Ensure instances are in correct regions/zones
- Verify security groups/network security groups allow SSH

### Mixed Environment Issues
- Check per-host ansible_host overrides
- Verify different ansible_user settings
- Test connectivity to each deployment type separately