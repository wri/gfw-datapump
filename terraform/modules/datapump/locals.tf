locals {
  bucket_suffix               = var.environment == "production" ? "" : "-${var.environment}"
  tf_state_bucket             = "gfw-terraform${local.bucket_suffix}"
  tags                        = var.tags
  name_suffix                 = "-${terraform.workspace}"
  project                     = "datapump"
}