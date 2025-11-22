#!/bin/bash
set -euxo pipefail


apt-get update -y
apt-get install -y python3 python3-pip

pip3 install flask mysql-connector-python

mkdir -p /opt/proxy

# Create config.py for constants
cat > /opt/proxy/config.py <<EOF
MANAGER_IP = "${manager_ip}"
WORKER_IPS = [${worker_ips}]
MYSQL_PASSWORD = "${mysql_password}"
EOF


# Download and run proxy.py
wget https://raw.githubusercontent.com/DanielNicula/FA/main/proxy/proxy.py -O /opt/proxy/proxy.py

cd /opt/proxy
sudo bash -c 'nohup python3 proxy.py > /var/log/proxy.log 2>&1 &'