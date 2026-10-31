output "ecr_repository_url" {
  value       = aws_ecr_repository.backtest_repo.repository_url
  description = "The secure URL endpoint of Upstox Backtest private cloud Docker registry"
}
# Output printed on terraform apply: ecr_repository_url = "591019227587.dkr.ecr.ap-south-1.amazonaws.com/backtest-upstox-app"