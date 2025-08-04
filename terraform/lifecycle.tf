resource "aws_s3_bucket_lifecycle_configuration" "expire_results" {
  bucket = data.terraform_remote_state.core.outputs.pipelines_bucket

  rule {
    id = "expire-results"

    filter {
      prefix = "geotrellis/results/"
    }

    expiration {
      days = 45
    }

    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "expire_logs" {
  bucket = data.terraform_remote_state.core.outputs.pipelines_bucket

  rule {
    id = "expire-logs"

    filter {
      prefix = "geotrellis/logs/"
    }

    expiration {
      days = 45
    }

    status = "Enabled"
  }
}
