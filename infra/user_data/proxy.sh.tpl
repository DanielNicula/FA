#!/bin/bash
set -euxo pipefail


apt-get update -y
apt-get install -y python3 python3-pip

pip3 install flask mysql-connector-python

mkdir -p /opt/proxy

# Create constants.py for variables
cat > /opt/proxy/constants.py <<EOF
MANAGER_IP = "${manager_ip}"
WORKER_IPS = [${join(", ", [for ip in worker_ips : "\"${ip}\""])}]
MYSQL_PASSWORD = "${mysql_password}"
EOF


# Download and run proxy.py
wget https://raw.githubusercontent.com/DanielNicula/FA/main/proxy/proxy.py -O /opt/proxy/proxy.py

cd /opt/proxy
sudo bash -c 'nohup python3 -u proxy.py > proxy.log 2>&1 &'

# Enable firewall for port 80 only
sudo ufw --force enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp