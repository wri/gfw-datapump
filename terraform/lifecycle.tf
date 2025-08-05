resource "aws_s3_bucket_lifecycle_configuration" "expire_results" {
  bucket = data.terraform_remote_state.core.outputs.pipelines_bucket

  # Remove nightly Geotrellis results from integrated alerts
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
  # Remove nightly logs for all Flagship EMR jobs
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
  # Remove data API batch jobs results.
  rule {
    id = "expire-jobs"

    filter {
      prefix = "analysis/jobs/"
    }

    expiration {
      days = 90
    }

    status = "Enabled"
  }
}
