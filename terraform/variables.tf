variable "aws_region" {
  type        = string
  default     = "ap-south-1" # Defaulting to Mumbai region (closest to Indian exchanges)
  description = "AWS deployment target region"
}
