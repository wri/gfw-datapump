locals {
  bucket_suffix                          = var.environment == "production" ? "" : "-${var.environment}"
  tf_state_bucket                        = "gfw-terraform${local.bucket_suffix}"
  tags                                   = data.terraform_remote_state.core.outputs.tags
  lambda_layer_datapump_utils = "../docker/datapump_utils/layer.zip"
  lambda_layer_shapely_pyyaml            = "../docker/shapely_pyyaml/layer.zip"
  name_suffix                            = "-${terraform.workspace}"
  project                                = "datapump"
}