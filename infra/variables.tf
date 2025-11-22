variable "aws_region" {
  type        = string
  default     = "us-east-1"
}

variable "mysql_password" {
  type        = string
  description = "Root password used for MySQL"
  default     = "password"
}