output "gatekeeper_public_ip" {
  value = aws_instance.gatekeeper.public_ip
}

output "proxy_private_ip" {
  value = aws_instance.proxy.private_ip
}

output "mysql_manager_private_ip" {
  value = aws_instance.mysql_manager.private_ip
}

output "mysql_worker_private_ips" {
  value = aws_instance.mysql_worker[*].private_ip
}

output "gatekeeper_api_key" {
  value = random_password.api_key.result
}