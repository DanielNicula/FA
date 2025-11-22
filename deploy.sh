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
  export AWS_DEFAULT_REGION=us-east-1

  echo "Validating AWS credentials..."
  if aws sts get-caller-identity >/dev/null 2>&1; then
    echo "AWS Credentials are valid."
  else
    echo "Still invalid. Exiting."
    exit 1
  fi
}


deploy() {
  # local registry=$1
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

benchmark() {
  local host=$1
  local count=$2
  local concurrency=$3

  echo "Benchmarking..."
  (
    cd benchmark
    mkdir -p results
    go run cmd/main.go -url "http://$host:80/new_request" -n $count -c $concurrency > "results/benchmark.txt" 2>&1
  )
}

# Main script
prompt_aws_creds
deploy
GATEKEEPER_HOST=$(get_gatekeeper_host)

# echo "Waiting 3 minutes for services to stabilize..."
# sleep 180

# benchmark "$GATEKEEPER_HOST" 1000 16 #benchmarking a revoir

# echo "Benchmarking complete!"

# echo "Cleaning up resources..."
# (
#     cd cleanup
#     pip3 install --break-system-packages -r requirements.txt
#     python main.py
# )
# echo "Clean up complete!"
