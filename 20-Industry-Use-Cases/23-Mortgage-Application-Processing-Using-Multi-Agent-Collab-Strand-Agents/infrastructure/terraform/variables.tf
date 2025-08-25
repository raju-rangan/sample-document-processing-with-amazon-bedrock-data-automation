variable "aws_region" {
  type = string
  default = "us-east-1"
}

variable "agent_name" {
  description = "AgentCore name"
  default = "dev"
  type        = string
}