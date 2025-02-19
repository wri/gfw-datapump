data "template_file" "sts_assume_role_lambda" {
  template = file("${var.policies_path}/sts_assume_role_lambda.json")
}

data "template_file" "sts_assume_role_states" {
  template = file("${var.policies_path}/sts_assume_role_states.json")
}

data "template_file" "datapump_policy" {
  template = file("${var.policies_path}/datapump.json")
}

data "template_file" "sfn_datapump" {
  template = file("${var.step_functions_path}/datapump.json.tmpl")
  vars = {
    lambda_dispatcher_arn = aws_lambda_function.dispatcher.arn,
    lambda_executor_arn = aws_lambda_function.executor.arn,
    lambda_postprocessor_arn = aws_lambda_function.postprocessor.arn,
    wait_time = var.sfn_wait_time
  }
}

# Terraform to create and upload layer.zip of the datapump source code
# and dependencies.

locals {
  layer_name = substr("python3.10-datapump-${terraform.workspace}_0.2.1", 0, 64)

}

# Build the Docker image and copy ZIP file to local folder
# Always build the zip file so we can do a hash on the entire source.
resource "null_resource" "build" {
  triggers = {
    curtime = timestamp()
  }

  provisioner "local-exec" {
    command     = "${path.module}/scripts/build.sh ${var.lambda_layers_path} ${local.layer_name}"
    interpreter = ["bash", "-c"]
  }
}

data "external" "layer_sha256" {
  program = [ "${path.module}/scripts/hash.sh", "${var.lambda_layers_path}/layer.zip"]
  depends_on = [null_resource.build]
}

resource "aws_s3_bucket_object" "py310_datapump_021" {
  bucket = var.pipelines_bucket
  key    = "lambda_layers/${local.layer_name}.zip"
  source = "${var.lambda_layers_path}/layer.zip"
  # This is what decides if the s3 upload of the layer will happen,
  # though terraform seems to do its own hash of the zip file as well.
  etag   = lookup(data.external.layer_sha256.result, "hash")
}

resource "aws_lambda_layer_version" "py310_datapump_021" {
  layer_name          = replace(local.layer_name, ".", "")
  s3_bucket           = aws_s3_bucket_object.py310_datapump_021.bucket
  s3_key              = aws_s3_bucket_object.py310_datapump_021.key
  compatible_runtimes = ["python3.10"]
  # This decides if the actual layer will be replaced in the lambda,
  # though terraform seems use its own etag of the zip file on S3 as well,
  # which means we always update the zip file.
  source_code_hash    = lookup(data.external.layer_sha256.result, "hash")
}
