locals {
  bucket_suffix               = var.environment == "production" ? "" : "-${var.environment}"
  tf_state_bucket             = "gfw-terraform-test"
  tags                        = var.tags
  name_suffix                 = "-${terraform.workspace}"
  project                     = "datapump"
}