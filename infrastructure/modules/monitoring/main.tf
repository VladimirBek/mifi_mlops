resource "yandex_logging_group" "app_logs" {
  folder_id = var.folder_id
  name      = "credit-scoring-${var.environment}-logs"
  retention_period = "168h" # 7 days
}
