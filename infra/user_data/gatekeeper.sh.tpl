#!/bin/bash
set -euxo pipefail

apt-get update -y
apt-get install -y python3 python3-pip

pip3 install flask requests

mkdir -p /opt/gatekeeper

# Create config.env for variables
cat > /opt/gatekeeper/config.env <<EOF
PROXY_IP=${proxy_ip}
EOF
    
wget https://raw.githubusercontent.com/DanielNicula/FinalProject/main/gatekeeper/gatekeeper.py -O /opt/gatekeeper/gatekeeper.py

nohup python3 /opt/gatekeeper/gatekeeper.py > /var/log/gatekeeper.log 2>&1 &