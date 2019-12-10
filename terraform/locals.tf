locals {
  bucket_suffix                          = var.environment == "production" ? "" : "-${var.environment}"
  tf_state_bucket                        = "gfw-terraform${local.bucket_suffix}"
  tags                                   = data.terraform_remote_state.core.outputs.tags
  lambda_layer_geotrellis_summary_update = "../docker/geotrellis_summary_update/layer.zip"
  lambda_layer_shapely_pyyaml            = "../docker/shapely_pyyaml/layer.zip"
  name_suffix                            = "-${terraform.workspace}"
}