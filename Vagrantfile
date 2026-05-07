# -*- mode: ruby -*-
# vi: set ft=ruby :

# Ansible Tower HA Deployment - Vagrant Configuration
# Creates 10 VMs for complete HA infrastructure:
# - 3 Tower nodes (HA cluster)
# - 3 Database nodes (primary + 2 standby replicas)
# - 2 Load balancer nodes (HAProxy + Keepalived)
# - 1 Monitoring node (Prometheus + Grafana)
# - 1 Collection development node
# - 1 Remote control node (Semaphore)

Vagrant.configure("2") do |config|
  # Base box - bento/rockylinux-8 is optimized for VirtualBox 6.1 on Intel macOS
  # Includes pre-built VirtualBox Guest Additions for reliable provisioning
  config.vm.box = "bento/rockylinux-8"

  # Global VM settings
  config.vm.boot_timeout = 600

  config.vm.provider "virtualbox" do |vb|
    vb.gui = false
    vb.check_guest_additions = false
  end

  # Disable synced folder for performance
  config.vm.synced_folder ".", "/vagrant", disabled: true

  # Global provisioning - install Python for Ansible
  config.vm.provision "shell", inline: <<-SHELL
    dnf update -y
    dnf install -y python3 python3-pip openssh-server
    systemctl enable sshd
    systemctl start sshd

    # Create ansible user with sudo privileges
    useradd -m -s /bin/bash ansible
    echo 'ansible ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/ansible
    mkdir -p /home/ansible/.ssh
    chmod 700 /home/ansible/.ssh
    chown ansible:ansible /home/ansible/.ssh

    # Allow password authentication for initial setup
    sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
    systemctl restart sshd

    # Set ansible user password (change this for production)
    echo 'ansible:ansible' | chpasswd
  SHELL

  # ===========================================
  # ANSIBLE TOWER HA CLUSTER (3 nodes)
  # ===========================================

  (1..3).each do |i|
    config.vm.define "tower-#{i}" do |tower|
      tower.vm.hostname = "tower-#{i}"
      tower.vm.network "private_network", ip: "192.168.56.#{10 + i}"

      tower.vm.provider "virtualbox" do |vb|
        vb.name = "tower-#{i}"
        vb.memory = "3072"  # 3GB RAM for Tower
        vb.cpus = 2
        vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
      end
    end
  end

  # ===========================================
  # POSTGRESQL HA CLUSTER (3 nodes)
  # ===========================================

  # Primary database node
  config.vm.define "db-primary" do |db|
    db.vm.hostname = "db-primary"
    db.vm.network "private_network", ip: "192.168.56.21"

    db.vm.provider "virtualbox" do |vb|
      vb.name = "db-primary"
      vb.memory = "4096"  # 4GB RAM for database
      vb.cpus = 2
      vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    end
  end

  # Standby database nodes
  (1..2).each do |i|
    config.vm.define "db-standby-#{i}" do |db|
      db.vm.hostname = "db-standby-#{i}"
      db.vm.network "private_network", ip: "192.168.56.#{21 + i}"

      db.vm.provider "virtualbox" do |vb|
        vb.name = "db-standby-#{i}"
        vb.memory = "4096"  # 4GB RAM for database
        vb.cpus = 2
        vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
      end
    end
  end

  # ===========================================
  # LOAD BALANCER NODES (2 nodes)
  # ===========================================

  (1..2).each do |i|
    config.vm.define "lb-#{i}" do |lb|
      lb.vm.hostname = "lb-#{i}"
      lb.vm.network "private_network", ip: "192.168.56.#{30 + i}"

      lb.vm.provider "virtualbox" do |vb|
        vb.name = "lb-#{i}"
        vb.memory = "2048"  # 2GB RAM for load balancer
        vb.cpus = 1
        vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
      end
    end
  end

  # ===========================================
  # COLLECTION DEVELOPMENT NODE
  # ===========================================

  config.vm.define "collection-dev" do |dev|
    dev.vm.hostname = "collection-dev"
    dev.vm.network "private_network", ip: "192.168.56.40"

    dev.vm.provider "virtualbox" do |vb|
      vb.name = "collection-dev"
      vb.memory = "2048"  # 2GB RAM for development
      vb.cpus = 1
      vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    end
  end

  # ===========================================
  # MONITORING NODE (Prometheus + Grafana)
  # ===========================================

  config.vm.define "monitoring" do |mon|
    mon.vm.hostname = "monitoring"
    mon.vm.network "private_network", ip: "192.168.56.50"

    mon.vm.provider "virtualbox" do |vb|
      vb.name = "monitoring"
      vb.memory = "4096"  # 4GB RAM for monitoring stack
      vb.cpus = 2
      vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    end
  end

  # ===========================================
  # REMOTE CONTROL NODE (Semaphore)
  # ===========================================

  config.vm.define "remote-control" do |control|
    control.vm.hostname = "remote-control"
    control.vm.network "private_network", ip: "192.168.56.60"

    control.vm.provider "virtualbox" do |vb|
      vb.name = "remote-control"
      vb.memory = "2048"  # 2GB RAM for Semaphore
      vb.cpus = 1
      vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    end
  end

  # ===========================================
  # POST-PROVISIONING MESSAGE
  # ===========================================

  config.trigger.after :up do |trigger|
    trigger.name = "Display deployment info"
    trigger.ruby do |env, machine|
      puts "\n" + "="*60
      puts "  ANSIBLE TOWER HA VAGRANT ENVIRONMENT READY"
      puts "="*60
      puts "\nCreated VMs:"
      puts "  Tower Cluster:    192.168.56.11-13 (3 nodes)"
      puts "  Database Cluster: 192.168.56.21-23 (1 primary + 2 standby)"
      puts "  Load Balancers:   192.168.56.31-32 (2 nodes)"
      puts "  VIP (Keepalived): 192.168.56.30 (virtual IP)"
      puts "  Collection Dev:   192.168.56.40"
      puts "  Monitoring:       192.168.56.50"
      puts "  Remote Control:   192.168.56.60"

      puts "\nNext Steps:"
      puts "  1. Create encrypted vault file:"
      puts "     ansible-vault encrypt group_vars/vault.yml"
      puts "  2. Test connectivity:"
      puts "     ansible all -i inventory/hosts.yml -m ping --ask-vault-pass"
      puts "  3. Deploy:"
      puts "     ansible-playbook -i inventory/hosts.yml site.yml --ask-vault-pass"

      puts "\nAccess after deployment:"
      puts "  Tower UI:    https://192.168.56.30"
      puts "  Grafana:     http://192.168.56.50:3000"
      puts "  Prometheus:  http://192.168.56.50:9090"
      puts "  HAProxy:     http://192.168.56.31:8080"
      puts "  Semaphore:   http://192.168.56.60:3000"
      puts "\n" + "="*60 + "\n"
    end
  end
end