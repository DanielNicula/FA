#!/usr/bin/env bash
set -euo pipefail

# Functions
prompt_aws_creds() {
  echo "Validating AWS credentials..."
  if aws sts get-caller-identity >/dev/null 2>&1; then
    echo "AWS credentials are valid."
    return
  fi

  echo "Please enter your AWS credentials:"

  read -rp "AWS_ACCESS_KEY_ID: " AWS_ACCESS_KEY_ID
  read -rsp "AWS_SECRET_ACCESS_KEY: " AWS_SECRET_ACCESS_KEY && echo
  read -rp "AWS_SESSION_TOKEN: " AWS_SESSION_TOKEN

  echo "Validating AWS credentials..."
  if aws sts get-caller-identity >/dev/null 2>&1; then
    echo "AWS Credentials are valid."
  else
    echo "Still invalid. Exiting."
    exit 1
  fi
}


deploy() {
  echo "Running Terraform..."
  (
    cd infra
    terraform init -input=false
    terraform apply -auto-approve
  )
}

get_gatekeeper_host() {
  (
    cd infra
    terraform output -raw gatekeeper_public_ip
  )
}

get_gatekeeper_api_key() {
  (
    cd infra
    terraform output -raw gatekeeper_api_key
  )
}

benchmark() {
  local host=$1
  local api-key=$2

  echo "Benchmarking..."
  (
    cd benchmark
    python3 main.py --host "$host" --api-key "$api-key"
  )
}

# Main script
prompt_aws_creds
deploy

echo "Waiting 3 minutes for services to stabilize..."
sleep 180

GATEKEEPER_HOST=$(get_gatekeeper_host)
GATEKEEPER_API_KEY=$(get_gatekeeper_api_key)
benchmark "$GATEKEEPER_HOST" "$GATEKEEPER_API_KEY"

echo "Benchmarking complete!"

echo "Cleaning up resources..."
(
    cd cleanup
    pip3 install --break-system-packages -r requirements.txt
    python main.py
)
echo "Clean up complete!"

