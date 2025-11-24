#!/bin/bash
set -euxo pipefail

apt-get update -y
apt-get install -y python3 python3-pip

pip3 install flask requests

mkdir -p /opt/gatekeeper

# Create config.env for variables
cat > /opt/gatekeeper/constants.py <<EOF
PROXY_IP="${proxy_ip}"
API_KEY="${api_key}"
EOF
    
wget https://raw.githubusercontent.com/DanielNicula/FA/main/gatekeeper/gatekeeper.py -O /opt/gatekeeper/gatekeeper.py

cd /opt/gatekeeper
sudo bash -c 'nohup python3 -u gatekeeper.py > gatekeeper.log 2>&1 &'