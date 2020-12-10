locals {
  bucket_suffix               = var.environment == "production" ? "" : "-${var.environment}"
  tags                        = var.tags
  name_suffix                 = "-${terraform.workspace}"
  project                     = "datapump"
}