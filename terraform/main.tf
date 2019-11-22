terraform {
  backend "s3" {
    bucket = "gfw-terraform-dev"
    key    = "state/terraform.tfstate"
    region = "us-east-1"
  }
}


resource "aws_iam_policy" "geotrellis_summary_update" {
  name = "geotrellis_summary_update"
  path = "/"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
      {
          "Effect": "Allow",
          "Action": [
              "secretsmanager:GetRandomPassword",
              "lambda:InvokeFunction",
              "secretsmanager:GetResourcePolicy",
              "secretsmanager:GetSecretValue",
              "secretsmanager:DescribeSecret",
              "secretsmanager:ListSecretVersionIds",
              "elasticmapreduce:RunJobFlow",
              "elasticmapreduce:DescribeCluster",
              "cloudformation:DescribeChangeSet",
              "cloudformation:DescribeStackResources",
              "cloudformation:DescribeStacks",
              "cloudformation:GetTemplate",
              "cloudformation:ListStackResources",
              "cloudwatch:*",
              "ec2:DescribeSecurityGroups",
              "ec2:DescribeSubnets",
              "ec2:DescribeVpcs",
              "events:*",
              "iam:GetPolicy",
              "iam:GetPolicyVersion",
              "iam:GetRole",
              "iam:GetRolePolicy",
              "iam:ListAttachedRolePolicies",
              "iam:ListRolePolicies",
              "iam:ListRoles",
              "iam:PassRole",
              "lambda:*",
              "logs:*",
              "s3:*"
          ],
          "Resource": "*"
      }
  ]
}
EOF
}

resource "aws_iam_role" "geotrellis_summary_update_states" {
  name = "geotrellis_summary_update_states"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement":
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "states.us-east-1.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
}
EOF
}

resource "aws_iam_role" "geotrellis_summary_update_lambda" {
  name = "geotrellis_summary_update_lambda"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement":
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
}
EOF
}

resource "aws_iam_role_policy_attachment" "geotrellis_summary_update_lambda" {
    role       = "${aws_iam_role.geotrellis_summary_update_lambda.name}"
    policy_arn = "${aws_iam_policy.geotrellis_summary_update.arn}"
}

resource "aws_iam_role_policy_attachment" "geotrellis_summary_update_states" {
    role       = "${aws_iam_role.geotrellis_summary_update_states.name}"
    policy_arn = "${aws_iam_policy.geotrellis_summary_update.arn}"
}

resource "aws_lambda_function" "submit_job" {
  function_name    = "submit-job_geotrellis-summary-update"
  filename         = "../lambdas/submit_job/function.zip"
  source_code_hash = "${filebase64sha256("../lambdas/submit_job/function.zip")}"
  role             = "${aws_iam_role.geotrellis_summary_update_lambda.arn}"
  runtime          = "python3.7"
  handler          = "function.handler"
  memory_size      = 128
  timeout          = 5
  publish          = true
}

resource "aws_lambda_function" "upload_results_to_datasets" {
  function_name    = "upload-results-to-datasets_geotrellis-summary-update"
  filename         = "../lambdas/upload_results_to_datasets/function.zip"
  source_code_hash = "${filebase64sha256("../lambdas/upload_results_to_datasets/function.zip")}"
  role             = "${aws_iam_role.geotrellis_summary_update_lambda.arn}"
  runtime          = "python3.7"
  handler          = "function.handler"
  memory_size      = 128
  timeout          = 5
  publish          = true
}

resource "aws_lambda_function" "check_datasets_saved" {
  function_name    = "check-datasets-saved_geotrellis-summary-update"
  filename         = "../lambdas/check_datasets_saved/function.zip"
  source_code_hash = "${filebase64sha256("../lambdas/check_datasets_saved/function.zip")}"
  role             = "${aws_iam_role.geotrellis_summary_update_lambda.arn}"
  runtime          = "python3.7"
  handler          = "function.handler"
  memory_size      = 128
  timeout          = 5
  publish          = true
}

resource "aws_sfn_state_machine" "geotrellis_summary_update" {
  name     = "geotrellis-summary-update"
  role_arn = "${aws_iam_role.geotrellis_summary_update_states.arn}"

  definition = "${file("../step_functions/geotrellis_summary_update.json")}"
}