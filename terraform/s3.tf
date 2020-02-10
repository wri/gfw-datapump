resource "aws_s3_bucket_object" "extent_1x1" {
  bucket = data.terraform_remote_state.core.outputs.pipelines_bucket
  key    = "geotrellis/features/extent_1x1.json"
  source = "files/extent_1x1.json"
  etag   = filemd5("../docker/datapump_utils/layer.zip")
}